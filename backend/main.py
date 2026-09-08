"""
Motor de triaje asistido por LLM — API type-safe multi-proveedor.

Ejecutar con:
    uvicorn backend.main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.schemas import IncidenciaRequest, TriajeCompleto, ErrorControlado, Proveedor
from backend.llm.base import TriajeInvalidoError
from backend.llm.ollama_provider import OllamaProvider
from backend.llm.external_provider import ExternalProvider, RateLimitError
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


# Almacén en memoria de incidencias procesadas, para que el dashboard las liste.
# TODO: sustituir por una base de datos real (SQLite/Postgres) antes de producción.
INCIDENCIAS_PROCESADAS: list[dict] = []


def _obtener_proveedor(payload: IncidenciaRequest):
    if payload.proveedor == Proveedor.LOCAL:
        return OllamaProvider()
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
    INCIDENCIAS_PROCESADAS.append({"texto": payload.texto, **resultado.model_dump()})
    return resultado


@app.get("/incidencias")
def listar_incidencias():
    """Usado por el dashboard de Streamlit para pintar la tabla/histórico."""
    return INCIDENCIAS_PROCESADAS

