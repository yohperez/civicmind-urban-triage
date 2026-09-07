"""
Tests unitarios — usan mocking para simular respuestas del LLM sin
llamar a Ollama ni a una API externa real (requisito del checklist,
sección V. Testing).

Ejecutar con:
    pytest -v
"""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.llm.ollama_provider import OllamaProvider

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
