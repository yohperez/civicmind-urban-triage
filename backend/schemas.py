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
    lat: float | None = Field(
        default=None, ge=-90, le=90, description="Latitud opcional del reporte (para el mapa del dashboard)"
    )
    lon: float | None = Field(
        default=None, ge=-180, le=180, description="Longitud opcional del reporte (para el mapa del dashboard)"
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


class RolChat(str, Enum):
    """Rol de cada turno en el historial del chatbot (formato OpenAI-style)."""
    USER = "user"
    ASSISTANT = "assistant"


class MensajeChat(BaseModel):
    """Un turno del historial de conversación del asistente CivicMind."""
    rol: RolChat
    contenido: str


class ChatRequest(BaseModel):
    """Payload del endpoint /chat — el asistente conversacional del dashboard."""
    mensaje: str = Field(..., min_length=1, description="Pregunta o mensaje del usuario")
    historial: list[MensajeChat] = Field(
        default_factory=list,
        description="Turnos previos de la conversación (sin incluir el mensaje actual)",
    )
    proveedor: Proveedor = Field(default=Proveedor.LOCAL, description="local (Ollama) vs externo (Gemini)")
    modelo_externo: str | None = Field(default=None, description="Modelo Gemini si proveedor='externo'")
    modelo_ollama: str | None = Field(default=None, description="Override del modelo Ollama si proveedor='local'")


class ChatResponse(BaseModel):
    """Lo que devuelve el endpoint /chat: la respuesta del asistente + métricas."""
    respuesta: str
    metricas: MetricasRespuesta


# --------------------------------------------------------------------------
# Auditoría de sesgos — criterio C10 (control de sesgos éticos)
# --------------------------------------------------------------------------
# Deja que el operador escriba manualmente cada variante (en vez de que el
# backend genere automáticamente sustituciones demográficas): así el propio
# equipo humano decide qué comparar, y evitamos que el sistema fabrique por
# su cuenta texto con caracterización étnica/de género, que sería
# contraproducente incluso en una herramienta pensada para detectar sesgo.

class VarianteAuditoria(BaseModel):
    """Una de las variantes de texto a comparar (misma incidencia, distinto dato demográfico/de zona)."""
    etiqueta: str = Field(..., min_length=1, max_length=60, description="Nombre corto, ej. 'Barrio A' / 'Barrio B'")
    texto: str = Field(..., min_length=10, description="Texto de la incidencia para esta variante")


class AuditoriaSesgosRequest(BaseModel):
    """Payload de POST /auditoria-sesgos."""
    variantes: list[VarianteAuditoria] = Field(..., min_length=2, max_length=6)
    proveedor: Proveedor = Field(default=Proveedor.LOCAL)
    modelo_externo: str | None = None
    modelo_ollama: str | None = None


class ResultadoVarianteAuditoria(BaseModel):
    etiqueta: str
    triaje: TriajeResponse
    metricas: MetricasRespuesta


class AuditoriaSesgosResponse(BaseModel):
    """
    Resultado de correr todas las variantes con el mismo LLM. Si
    `urgencias_coinciden` es False, dos textos que solo difieren en un dato
    demográfico/de ubicación recibieron distinta urgencia — evidencia
    empírica y accionable de sesgo, en vez de solo confiar en la
    instrucción anti-sesgo del prompt.
    """
    resultados: list[ResultadoVarianteAuditoria]
    urgencias_coinciden: bool
    categorias_coinciden: bool
    alerta: str | None = None


# --------------------------------------------------------------------------
# Self-consistency — fiabilidad del triaje
# --------------------------------------------------------------------------

class ConsistenciaRequest(BaseModel):
    """Payload de POST /triaje/consistencia: corre la MISMA incidencia N veces."""
    texto: str = Field(..., min_length=10)
    proveedor: Proveedor = Field(default=Proveedor.LOCAL)
    modelo_externo: str | None = None
    modelo_ollama: str | None = None
    repeticiones: int = Field(default=3, ge=2, le=5)


class ConsistenciaResponse(BaseModel):
    """
    Si `es_consistente` es False, el modelo no dio siempre la misma
    urgencia/categoría para el mismo texto — señal de que el operador
    humano (HITL) debería revisar esta incidencia con más cuidado en vez
    de confiar ciegamente en una única pasada.
    """
    ejecuciones: list[TriajeResponse]
    urgencia_mayoritaria: Urgencia
    acuerdo_urgencia: float
    categoria_mayoritaria: Categoria
    acuerdo_categoria: float
    es_consistente: bool
