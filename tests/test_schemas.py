"""Tests de validación pura de los esquemas Pydantic (sin FastAPI ni LLM)."""

import pytest
from pydantic import ValidationError

from backend.schemas import TriajeResponse, IncidenciaRequest


def test_triaje_response_valido():
    triaje = TriajeResponse(
        categoria="seguridad",
        urgencia="critica",
        resumen="Farola caída sobre la acera, cables expuestos",
        departamento_asignado="Seguridad Vial",
        razonamiento="Riesgo eléctrico inmediato para peatones.",
    )
    assert triaje.urgencia == "critica"


def test_triaje_response_categoria_invalida_rechazada():
    """Una categoría fuera del Enum debe ser rechazada — así se intercepta la alucinación."""
    with pytest.raises(ValidationError):
        TriajeResponse(
            categoria="categoria_inventada_por_el_modelo",
            urgencia="alta",
            resumen="texto",
            departamento_asignado="dpto",
            razonamiento="razon",
        )


def test_incidencia_request_texto_muy_corto():
    with pytest.raises(ValidationError):
        IncidenciaRequest(texto="hola")
