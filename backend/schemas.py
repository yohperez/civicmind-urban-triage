"""
Esquemas Pydantic — el corazón de la robustez "type-safe" del sistema.

Estos modelos se usan en DOS sitios:
1. Para validar lo que entra por el endpoint (IncidenciaRequest).
2. Para forzar/validar lo que el LLM debe devolver (TriajeResponse).

Si el LLM alucina un campo, un tipo incorrecto, o texto fuera del JSON,
Pydantic lanzará un ValidationError que la API debe capturar (ver main.py)
y convertir en un error controlado — nunca debe tumbar el servicio.
"""

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class Proveedor(str, Enum):
    """Qué motor de inferencia se usa para esta petición."""
    LOCAL = "local"       # Ollama, ejecutado on-premise
    EXTERNO = "externo"   # API comercial (Gemini/GPT/Claude) o Groq/HF


class Categoria(str, Enum):
    """
    TODO: ajustar a las categorías reales del ayuntamiento/plataforma.
    Mantenerlo como Enum obliga al LLM (vía prompt) a elegir de una
    lista cerrada, reduciendo alucinaciones de clasificación.
    """
    INFRAESTRUCTURA = "infraestructura"
    LIMPIEZA = "limpieza"
    SEGURIDAD = "seguridad"
    SANIDAD = "sanidad"
    TRANSITO = "transito"
    OTROS = "otros"


class Urgencia(str, Enum):
    """
    Nivel de gravedad — es el campo que más le importa al operador humano
    en el dashboard (HITL), según las notas de la reunión de planificación.
    """
    CRITICA = "critica"
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class IncidenciaRequest(BaseModel):
    """Payload que envía el ciudadano / sistema de ingesta."""
    texto: str = Field(..., min_length=10, description="Descripción libre de la incidencia")
    proveedor: Proveedor = Field(default=Proveedor.LOCAL, description="local (Ollama) vs externo (API)")
    modelo_externo: str | None = Field(
        default=None,
        description="Nombre del modelo externo si proveedor='externo' (ej. 'gemini-2.0-flash')",
    )
    modelo_ollama: str | None = Field(
        default=None,
        description=(
            "Override opcional del modelo Ollama para esta petición "
            "(ej. 'gemma4:31b-cloud'). Si se omite, se usa OLLAMA_MODEL_DEFAULT."
        ),
    )


class TriajeResponse(BaseModel):
    """
    Lo que el LLM DEBE devolver. Este es el esquema que Pydantic usa
    para interceptar alucinaciones estructurales (ver llm/base.py).

    IMPORTANTE (criterio ético del checklist): el campo `razonamiento`
    NUNCA debe mencionar género, origen, raza o barrio inferido del texto —
    eso se controla en el prompt de sistema (ver llm/prompts.py), no aquí,
    pero se puede añadir una validación adicional si se detectan patrones.
    """
    categoria: Categoria
    urgencia: Urgencia
    resumen: str = Field(..., description="Resumen de la incidencia en ~10 palabras")
    departamento_asignado: str = Field(..., description="Departamento interno responsable")
    razonamiento: str = Field(..., description="Cadena de pensamiento (CoT) que justifica la clasificación")


class MetricasRespuesta(BaseModel):
    """Metadatos de observabilidad exigidos por el reto: coste, latencia, tokens."""
    tokens_entrada: int
    tokens_salida: int
    coste_estimado_usd: float
    latencia_ms: float
    proveedor: Proveedor
    modelo: str
    reintentos: int = 0


class TriajeCompleto(BaseModel):
    """Lo que finalmente devuelve el endpoint: triaje + métricas."""
    triaje: TriajeResponse
    metricas: MetricasRespuesta


class ErrorControlado(BaseModel):
    """Respuesta de error estandarizada cuando el LLM rompe el esquema."""
    error: str
    detalle: str
    intentos_realizados: int
