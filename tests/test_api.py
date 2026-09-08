"""
Tests unitarios — usan mocking para simular respuestas del LLM sin
llamar a Ollama ni a una API externa real (requisito del checklist,
sección V. Testing).

Ejecutar con:
    pytest -v
"""

import json
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from backend.main import app
from backend.llm.ollama_provider import OllamaProvider
from backend.llm.external_provider import ExternalProvider

client = TestClient(app)

RESPUESTA_VALIDA = json.dumps({
    "categoria": "infraestructura",
    "urgencia": "alta",
    "resumen": "Socavón peligroso en calle principal",
    "departamento_asignado": "Obras Públicas",
    "razonamiento": "Riesgo estructural inminente, sin datos demográficos.",
})

RESPUESTA_INVALIDA = "Claro, aquí tienes la clasificación: es urgente."  # no es JSON


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch.object(OllamaProvider, "_llamar_modelo")
def test_triaje_input_valido(mock_llamar):
    """El endpoint debe devolver 200 y un JSON validado cuando el LLM responde bien."""
    mock_llamar.return_value = (RESPUESTA_VALIDA, 50, 30)

    resp = client.post("/triaje", json={
        "texto": "Hay un socavón enorme en la calle principal, casi cae un coche.",
        "proveedor": "local",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["triaje"]["categoria"] == "infraestructura"
    assert data["triaje"]["urgencia"] == "alta"
    assert data["metricas"]["proveedor"] == "local"
    assert data["metricas"]["reintentos"] == 0


@patch.object(OllamaProvider, "_llamar_modelo")
def test_triaje_maneja_alucinacion_estructural(mock_llamar):
    """
    Si el LLM alucina (no devuelve JSON válido) en TODOS los intentos,
    la API debe responder 422 controlado, no un 500 sin manejar.
    """
    mock_llamar.return_value = (RESPUESTA_INVALIDA, 20, 10)

    resp = client.post("/triaje", json={
        "texto": "Reporte de prueba que provocará una respuesta inválida.",
        "proveedor": "local",
    })

    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "triaje_invalido"


@patch.object(OllamaProvider, "_llamar_modelo")
def test_triaje_se_autocorrige_tras_un_fallo(mock_llamar):
    """Si el primer intento falla pero el segundo es válido, debe devolver 200 con reintentos=1."""
    mock_llamar.side_effect = [
        (RESPUESTA_INVALIDA, 20, 10),
        (RESPUESTA_VALIDA, 50, 35),
    ]

    resp = client.post("/triaje", json={
        "texto": "Reporte que falla una vez y luego se corrige.",
        "proveedor": "local",
    })

    assert resp.status_code == 200
    assert resp.json()["metricas"]["reintentos"] == 1


def test_input_invalido_texto_muy_corto():
    """Pydantic debe rechazar textos por debajo del min_length antes de llegar al LLM."""
    resp = client.post("/triaje", json={"texto": "corto", "proveedor": "local"})
    assert resp.status_code == 422


def test_proveedor_externo_sin_modelo_es_422():
    """Si proveedor='externo' pero no se indica modelo_externo, debe rechazarse antes de llamar a Gemini."""
    resp = client.post("/triaje", json={
        "texto": "Reporte de prueba sin modelo externo indicado.",
        "proveedor": "externo",
    })
    assert resp.status_code == 422


@patch.object(ExternalProvider, "_llamar_modelo")
def test_triaje_proveedor_externo_valido(mock_llamar):
    """El endpoint debe funcionar igual con Gemini que con Ollama (misma interfaz LLMProvider)."""
    mock_llamar.return_value = (RESPUESTA_VALIDA, 40, 22)

    resp = client.post("/triaje", json={
        "texto": "Hay un socavón enorme en la calle principal, casi cae un coche.",
        "proveedor": "externo",
        "modelo_externo": "gemini-2.0-flash",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["metricas"]["proveedor"] == "externo"
    assert data["metricas"]["modelo"] == "gemini-2.0-flash"


@patch("backend.llm.external_provider._obtener_cliente_gemini")
def test_triaje_sin_api_key_devuelve_503(mock_cliente):
    """Si GEMINI_API_KEY no está configurada, debe ser un 503 controlado, no un 500 crudo."""
    mock_cliente.side_effect = RuntimeError("GEMINI_API_KEY no está configurada.")

    resp = client.post("/triaje", json={
        "texto": "Reporte de prueba sin API key configurada en el entorno.",
        "proveedor": "externo",
        "modelo_externo": "gemini-2.0-flash",
    })

    assert resp.status_code == 503


@patch.object(ExternalProvider, "_llamar_modelo")
def test_triaje_gemini_rechaza_peticion_es_502_json(mock_llamar):
    """
    Antes de este fix, un ClientError de Gemini (ej. API key inválida, 400/403)
    no lo capturaba nadie y FastAPI devolvía texto plano -> el dashboard
    rompía con 'Expecting value: line 1 column 1'. Ahora debe ser 502 + JSON.
    """
    from google.genai import errors as genai_errors

    mock_llamar.side_effect = genai_errors.ClientError(
        code=403, response_json={"error": {"message": "API key not valid"}}
    )

    resp = client.post("/triaje", json={
        "texto": "Reporte de prueba con una API key de Gemini inválida.",
        "proveedor": "externo",
        "modelo_externo": "gemini-2.0-flash",
    })

    assert resp.status_code == 502
    assert resp.headers["content-type"].startswith("application/json")


@patch.object(ExternalProvider, "_llamar_modelo")
def test_error_no_controlado_sigue_siendo_json(mock_llamar):
    """
    Red de seguridad: cualquier excepción inesperada debe devolver JSON, nunca
    texto plano. Usamos un TestClient con raise_server_exceptions=False porque
    el comportamiento por defecto del TestClient relanza la excepción original
    para facilitar el debug en tests — en producción (Railway) el cliente HTTP
    real SIEMPRE recibe la respuesta JSON de nuestro exception_handler.
    """
    from fastapi.testclient import TestClient as _TestClient
    cliente_sin_relanzar = _TestClient(app, raise_server_exceptions=False)

    mock_llamar.side_effect = ValueError("algo totalmente inesperado")

    resp = cliente_sin_relanzar.post("/triaje", json={
        "texto": "Reporte de prueba que dispara una excepción no prevista.",
        "proveedor": "externo",
        "modelo_externo": "gemini-2.0-flash",
    })

    assert resp.status_code == 500
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json()["error"] == "error_no_controlado"


# --------------------------------------------------------------------------
# /chat — asistente conversacional del dashboard
# --------------------------------------------------------------------------

@patch.object(OllamaProvider, "_llamar_modelo")
def test_chat_local_devuelve_texto_libre(mock_llamar):
    """El chatbot (proveedor local) responde texto plano, sin exigir JSON."""
    mock_llamar.return_value = ("¡Claro! El pipeline usa ReAct + Chain-of-Thought.", 40, 15)

    resp = client.post("/chat", json={
        "mensaje": "¿Cómo funciona el pipeline de triaje?",
        "proveedor": "local",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["respuesta"] == "¡Claro! El pipeline usa ReAct + Chain-of-Thought."
    assert data["metricas"]["proveedor"] == "local"
    assert data["metricas"]["reintentos"] == 0
    # json_mode=False para el chatbot: no debe forzarse response_mime_type JSON.
    _, kwargs = mock_llamar.call_args
    assert kwargs.get("json_mode") is False


@patch.object(ExternalProvider, "_llamar_modelo")
def test_chat_externo_con_historial(mock_llamar):
    """El chatbot (Gemini) recibe y reenvía el historial previo de la conversación."""
    mock_llamar.return_value = ("Ollama es gratuito y mantiene los datos en local.", 60, 20)

    resp = client.post("/chat", json={
        "mensaje": "¿Y por qué usar Ollama en vez de Gemini?",
        "historial": [
            {"rol": "user", "contenido": "Hola, tengo una duda sobre los proveedores."},
            {"rol": "assistant", "contenido": "Claro, dime."},
        ],
        "proveedor": "externo",
        "modelo_externo": "gemini-2.0-flash",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["metricas"]["modelo"] == "gemini-2.0-flash"

    mensajes_enviados = mock_llamar.call_args[0][0]
    # system + 2 turnos de historial + mensaje actual = 4
    assert len(mensajes_enviados) == 4
    assert mensajes_enviados[0]["role"] == "system"
    assert mensajes_enviados[-1]["content"] == "¿Y por qué usar Ollama en vez de Gemini?"


def test_chat_proveedor_externo_sin_modelo_es_422():
    """Igual que /triaje: sin modelo_externo, proveedor='externo' se rechaza antes de llamar a Gemini."""
    resp = client.post("/chat", json={
        "mensaje": "¿Qué modelo estás usando?",
        "proveedor": "externo",
    })
    assert resp.status_code == 422
