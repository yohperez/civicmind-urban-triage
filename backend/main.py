"""
Motor de triaje asistido por LLM — API type-safe multi-proveedor.

Ejecutar con:
    uvicorn backend.main:app --reload --port 8000
"""

import json
import logging
from collections import Counter

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from backend.schemas import (
    IncidenciaRequest,
    TriajeCompleto,
    ErrorControlado,
    Proveedor,
    ChatRequest,
    ChatResponse,
    AuditoriaSesgosRequest,
    AuditoriaSesgosResponse,
    ResultadoVarianteAuditoria,
    ConsistenciaRequest,
    ConsistenciaResponse,
)
from backend.llm.base import TriajeInvalidoError
from backend.llm.ollama_provider import OllamaProvider
from backend.llm.external_provider import ExternalProvider, RateLimitError
from backend.db import init_db, guardar_incidencia, listar_incidencias as db_listar_incidencias
from google.genai import errors as genai_errors

logger = logging.getLogger("civicmind.backend")

app = FastAPI(
    title="Motor de Triaje LLM — Servicios Urbanos",
    description="API type-safe multi-proveedor para clasificación de incidencias ciudadanas (ReAct + CoT).",
    version="0.1.0",
)

# TODO: restringir origins en producción (aquí abierto para que el dashboard
# de Streamlit, que corre en otro puerto, pueda consumir la API en local).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def manejador_global_de_errores(request: Request, exc: Exception):
    """
    Red de seguridad: cualquier excepción no capturada explícitamente más
    abajo cae aquí, para que la respuesta SIEMPRE sea JSON (nunca la página
    de texto plano por defecto de Starlette). Así el dashboard puede
    mostrar el error real en vez de fallar al hacer resp.json().
    """
    logger.exception("Error no controlado en %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "error_no_controlado",
            "detalle": f"{type(exc).__name__}: {exc}",
        },
    )


# Se llama al importar el módulo (no en un evento "startup") a propósito:
# el TestClient de FastAPI/Starlette no siempre dispara los eventos de
# startup salvo que se use como context manager (`with TestClient(app)`),
# y aquí queremos que la tabla exista sí o sí antes de la primera petición,
# tanto en producción como en los tests. init_db() es barata e idempotente
# (CREATE TABLE IF NOT EXISTS), así que no hay coste real en llamarla aquí.
init_db()


def _obtener_proveedor(payload: IncidenciaRequest | ChatRequest):
    """
    Compartido entre /triaje y /chat: ambos payloads exponen los mismos
    campos (`proveedor`, `modelo_externo`, `modelo_ollama`), así que
    instanciar el proveedor LLM correcto es idéntico en los dos endpoints.
    """
    if payload.proveedor == Proveedor.LOCAL:
        return OllamaProvider(modelo=payload.modelo_ollama)
    if not payload.modelo_externo:
        raise HTTPException(
            status_code=422,
            detail="Debe indicar 'modelo_externo' cuando proveedor='externo'.",
        )
    return ExternalProvider(modelo=payload.modelo_externo)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/triaje",
    response_model=TriajeCompleto,
    responses={422: {"model": ErrorControlado}},
)
def procesar_incidencia(payload: IncidenciaRequest):
    """
    Recibe el texto de una incidencia, la clasifica vía LLM (ReAct+CoT)
    y devuelve el JSON validado + métricas de coste/latencia/tokens.

    Si el modelo alucina la estructura tras los reintentos internos,
    devuelve un 422 controlado en vez de tumbar el servicio.
    """
    proveedor = _obtener_proveedor(payload)

    try:
        triaje, metricas = proveedor.triar(payload.texto)
    except TriajeInvalidoError as e:
        raise HTTPException(
            status_code=422,
            detail=ErrorControlado(
                error="triaje_invalido",
                detalle=e.mensaje,
                intentos_realizados=e.intentos,
            ).model_dump(),
        )
    except RuntimeError as e:
        # Ej.: falta GEMINI_API_KEY en las variables de entorno del servicio.
        raise HTTPException(status_code=503, detail=f"Proveedor no disponible: {e}")
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=f"Rate limit persistente del proveedor externo: {e}")
    except genai_errors.ClientError as e:
        # Ej.: API key inválida (401/403), modelo inexistente (404), payload rechazado (400).
        raise HTTPException(status_code=502, detail=f"Gemini rechazó la petición ({e.code}): {e.message}")

    resultado = TriajeCompleto(triaje=triaje, metricas=metricas)
    guardar_incidencia(
        texto=payload.texto,
        triaje_dict=resultado.triaje.model_dump(),
        metricas_dict=resultado.metricas.model_dump(),
        lat=payload.lat,
        lon=payload.lon,
    )
    return resultado


@app.get("/incidencias")
def listar_incidencias():
    """Usado por el dashboard para pintar la tabla/histórico. Persistido en SQLite (backend/db.py)."""
    return db_listar_incidencias()


@app.get("/incidencias/geo")
def listar_incidencias_geo():
    """Solo las incidencias con lat/lon — usado por el mapa del dashboard."""
    return [i for i in db_listar_incidencias() if i["lat"] is not None and i["lon"] is not None]


@app.post(
    "/triaje/stream",
    responses={422: {"model": ErrorControlado}},
)
def procesar_incidencia_stream(payload: IncidenciaRequest):
    """
    Igual que /triaje pero vía Server-Sent Events: emite cada fragmento del
    razonamiento (ciclo ReAct) a medida que el modelo lo genera, y al final
    un evento "resultado" (o "error" si no valida). Pensado para que el
    dashboard muestre el pensamiento del modelo en vivo durante una demo,
    en vez de una barra de carga opaca.

    OJO: a diferencia de /triaje, aquí NO hay reintentos automáticos ni se
    guarda en el histórico — es un modo "solo demo/inspección". Para el
    flujo real (con reintentos y persistencia) se sigue usando /triaje.
    """
    proveedor = _obtener_proveedor(payload)

    def generador_eventos():
        try:
            for evento in proveedor.triar_stream(payload.texto):
                yield f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"
        except RuntimeError as e:
            yield f"data: {json.dumps({'tipo': 'error', 'detalle': f'Proveedor no disponible: {e}'}, ensure_ascii=False)}\n\n"
        except RateLimitError as e:
            yield f"data: {json.dumps({'tipo': 'error', 'detalle': f'Rate limit: {e}'}, ensure_ascii=False)}\n\n"
        except genai_errors.ClientError as e:
            yield f"data: {json.dumps({'tipo': 'error', 'detalle': f'Gemini rechazó la petición ({e.code}): {e.message}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generador_eventos(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post(
    "/auditoria-sesgos",
    response_model=AuditoriaSesgosResponse,
    responses={422: {"model": ErrorControlado}},
)
def auditar_sesgos(payload: AuditoriaSesgosRequest):
    """
    Corre el mismo pipeline de triaje sobre varias variantes de un mismo
    reporte (normalmente idénticas salvo el barrio/género/origen
    mencionado) y compara si la urgencia/categoría cambia entre ellas.

    Convierte la instrucción anti-sesgo del prompt (criterio C10) en algo
    verificable con datos, en vez de solo confiar en que el LLM la respete.
    Las variantes las escribe el operador humano (ver schemas.py) — el
    backend no genera automáticamente texto con caracterización
    demográfica.
    """
    proveedor = _obtener_proveedor(payload)
    resultados: list[ResultadoVarianteAuditoria] = []

    for variante in payload.variantes:
        try:
            triaje, metricas = proveedor.triar(variante.texto)
        except TriajeInvalidoError as e:
            raise HTTPException(
                status_code=422,
                detail=ErrorControlado(
                    error="triaje_invalido",
                    detalle=f"Variante '{variante.etiqueta}': {e.mensaje}",
                    intentos_realizados=e.intentos,
                ).model_dump(),
            )
        resultados.append(
            ResultadoVarianteAuditoria(etiqueta=variante.etiqueta, triaje=triaje, metricas=metricas)
        )

    urgencias = {r.triaje.urgencia for r in resultados}
    categorias = {r.triaje.categoria for r in resultados}
    urgencias_coinciden = len(urgencias) == 1
    categorias_coinciden = len(categorias) == 1

    alerta = None
    if not urgencias_coinciden:
        alerta = (
            "El nivel de urgencia cambió entre variantes que solo deberían diferir en "
            "un dato demográfico o de ubicación — revisar posible sesgo."
        )

    return AuditoriaSesgosResponse(
        resultados=resultados,
        urgencias_coinciden=urgencias_coinciden,
        categorias_coinciden=categorias_coinciden,
        alerta=alerta,
    )


@app.post(
    "/triaje/consistencia",
    response_model=ConsistenciaResponse,
    responses={422: {"model": ErrorControlado}},
)
def evaluar_consistencia(payload: ConsistenciaRequest):
    """
    Corre LA MISMA incidencia N veces (payload.repeticiones) y compara los
    resultados: si el modelo no es determinista en la práctica (temperatura
    > 0, o simplemente varía), el operador humano debería tratar esa
    incidencia con más cautela en vez de confiar en una única pasada.
    """
    proveedor = _obtener_proveedor(payload)
    ejecuciones = []

    for _ in range(payload.repeticiones):
        try:
            triaje, _metricas = proveedor.triar(payload.texto)
            ejecuciones.append(triaje)
        except TriajeInvalidoError as e:
            raise HTTPException(
                status_code=422,
                detail=ErrorControlado(
                    error="triaje_invalido",
                    detalle=f"Fallo en una de las repeticiones: {e.mensaje}",
                    intentos_realizados=e.intentos,
                ).model_dump(),
            )

    urgencia_top, conteo_urg = Counter(t.urgencia for t in ejecuciones).most_common(1)[0]
    categoria_top, conteo_cat = Counter(t.categoria for t in ejecuciones).most_common(1)[0]
    acuerdo_urg = conteo_urg / len(ejecuciones)
    acuerdo_cat = conteo_cat / len(ejecuciones)

    return ConsistenciaResponse(
        ejecuciones=ejecuciones,
        urgencia_mayoritaria=urgencia_top,
        acuerdo_urgencia=round(acuerdo_urg, 2),
        categoria_mayoritaria=categoria_top,
        acuerdo_categoria=round(acuerdo_cat, 2),
        es_consistente=(acuerdo_urg == 1.0 and acuerdo_cat == 1.0),
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={422: {"model": ErrorControlado}},
)
def chat(payload: ChatRequest):
    """
    Turno del asistente conversacional del dashboard (chatbot CivicMind).

    Reutiliza el mismo `LLMProvider` (Ollama o Gemini) que /triaje, pero
    llama a `.chat()` en vez de `.triar()`: aquí la respuesta es texto
    libre en lenguaje natural, sin validación Pydantic de un esquema fijo
    (no hay estructura que un chatbot deba cumplir).

    Errores de proveedor (Ollama caído, rate limit de Gemini, API key
    inválida...) se manejan igual que en /triaje, para que el dashboard
    pueda mostrar el mismo tipo de error controlado en ambos flujos.
    """
    proveedor = _obtener_proveedor(payload)
    historial = [{"role": m.rol.value, "content": m.contenido} for m in payload.historial]

    try:
        respuesta, metricas = proveedor.chat(payload.mensaje, historial=historial)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Proveedor no disponible: {e}")
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=f"Rate limit persistente del proveedor externo: {e}")
    except genai_errors.ClientError as e:
        raise HTTPException(status_code=502, detail=f"Gemini rechazó la petición ({e.code}): {e.message}")

    return ChatResponse(respuesta=respuesta, metricas=metricas)

