"""
Tests de las mejoras añadidas sobre el proyecto base: persistencia SQLite,
auditoría de sesgos, self-consistency y streaming SSE.

Ejecutar con:
    pytest tests/test_mejoras.py -v
"""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.llm.ollama_provider import OllamaProvider

client = TestClient(app)

RESPUESTA_ALTA = json.dumps({
    "categoria": "seguridad",
    "urgencia": "alta",
    "resumen": "Poste caído bloqueando la vía, cables expuestos",
    "departamento_asignado": "Seguridad Vial",
    "razonamiento": "Riesgo eléctrico inmediato para transeúntes.",
})

RESPUESTA_BAJA = json.dumps({
    "categoria": "seguridad",
    "urgencia": "baja",
    "resumen": "Poste caído bloqueando la vía, cables expuestos",
    "departamento_asignado": "Seguridad Vial",
    "razonamiento": "Riesgo eléctrico inmediato para transeúntes.",
})


# --------------------------------------------------------------------------
# Persistencia (SQLite en vez de lista en memoria)
# --------------------------------------------------------------------------

@patch.object(OllamaProvider, "_llamar_modelo")
def test_incidencia_persiste_y_aparece_en_historico(mock_llamar):
    mock_llamar.return_value = (RESPUESTA_ALTA, 40, 20)

    resp = client.post("/triaje", json={
        "texto": "Hay un poste caído con cables expuestos en la esquina.",
        "proveedor": "local",
        "lat": 40.4168,
        "lon": -3.7038,
    })
    assert resp.status_code == 200

    historico = client.get("/incidencias").json()
    assert any(i["texto"] == "Hay un poste caído con cables expuestos en la esquina." for i in historico)

    geo = client.get("/incidencias/geo").json()
    assert any(i["lat"] == 40.4168 and i["lon"] == -3.7038 for i in geo)


# --------------------------------------------------------------------------
# Auditoría de sesgos
# --------------------------------------------------------------------------

@patch.object(OllamaProvider, "_llamar_modelo")
def test_auditoria_sesgos_detecta_divergencia(mock_llamar):
    """Dos variantes con el mismo hecho pero distinta urgencia -> alerta activada."""
    mock_llamar.side_effect = [
        (RESPUESTA_ALTA, 40, 20),
        (RESPUESTA_BAJA, 40, 20),
    ]

    resp = client.post("/auditoria-sesgos", json={
        "variantes": [
            {"etiqueta": "Barrio A", "texto": "Poste caído con cables expuestos en Barrio A."},
            {"etiqueta": "Barrio B", "texto": "Poste caído con cables expuestos en Barrio B."},
        ],
        "proveedor": "local",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["urgencias_coinciden"] is False
    assert data["alerta"] is not None
    assert len(data["resultados"]) == 2


@patch.object(OllamaProvider, "_llamar_modelo")
def test_auditoria_sesgos_sin_divergencia(mock_llamar):
    mock_llamar.return_value = (RESPUESTA_ALTA, 40, 20)

    resp = client.post("/auditoria-sesgos", json={
        "variantes": [
            {"etiqueta": "Barrio A", "texto": "Poste caído con cables expuestos en Barrio A."},
            {"etiqueta": "Barrio B", "texto": "Poste caído con cables expuestos en Barrio B."},
        ],
        "proveedor": "local",
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["urgencias_coinciden"] is True
    assert data["alerta"] is None


def test_auditoria_sesgos_requiere_al_menos_dos_variantes():
    resp = client.post("/auditoria-sesgos", json={
        "variantes": [{"etiqueta": "Única", "texto": "Solo una variante no basta para comparar."}],
        "proveedor": "local",
    })
    assert resp.status_code == 422


# --------------------------------------------------------------------------
# Self-consistency
# --------------------------------------------------------------------------

@patch.object(OllamaProvider, "_llamar_modelo")
def test_consistencia_detecta_inconsistencia(mock_llamar):
    mock_llamar.side_effect = [
        (RESPUESTA_ALTA, 40, 20),
        (RESPUESTA_BAJA, 40, 20),
        (RESPUESTA_ALTA, 40, 20),
    ]

    resp = client.post("/triaje/consistencia", json={
        "texto": "Poste caído con cables expuestos en la vía pública.",
        "proveedor": "local",
        "repeticiones": 3,
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["es_consistente"] is False
    assert data["urgencia_mayoritaria"] == "alta"
    assert round(data["acuerdo_urgencia"], 2) == round(2 / 3, 2)


@patch.object(OllamaProvider, "_llamar_modelo")
def test_consistencia_perfecta(mock_llamar):
    mock_llamar.return_value = (RESPUESTA_ALTA, 40, 20)

    resp = client.post("/triaje/consistencia", json={
        "texto": "Poste caído con cables expuestos en la vía pública.",
        "proveedor": "local",
        "repeticiones": 3,
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["es_consistente"] is True
    assert data["acuerdo_urgencia"] == 1.0


# --------------------------------------------------------------------------
# Streaming SSE
# --------------------------------------------------------------------------

@patch.object(OllamaProvider, "_llamar_modelo_stream")
def test_triaje_stream_emite_tokens_y_resultado_final(mock_stream):
    mock_stream.return_value = iter([
        ('{"categoria": "seguridad", ', 20, 5),
        ('"urgencia": "alta", "resumen": "Poste caído", ', 20, 10),
        ('"departamento_asignado": "Seguridad Vial", "razonamiento": "Riesgo eléctrico."}', 20, 15),
    ])

    with client.stream("POST", "/triaje/stream", json={
        "texto": "Hay un poste caído con cables expuestos en la calle.",
        "proveedor": "local",
    }) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        eventos = []
        for linea in resp.iter_lines():
            if linea.startswith("data: "):
                eventos.append(json.loads(linea[len("data: "):]))

    tipos = [e["tipo"] for e in eventos]
    assert tipos.count("token") == 3
    assert tipos[-1] == "resultado"
    assert eventos[-1]["triaje"]["urgencia"] == "alta"
