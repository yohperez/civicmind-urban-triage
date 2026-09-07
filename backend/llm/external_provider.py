"""
Proveedor externo — API comercial (Gemini / GPT / Claude) o capa gratuita
tipo Groq / Hugging Face.

Incluye manejo de rate limits con retry/backoff exponencial, tal como
exige el checklist del reto ("con manejo de rate limits del proveedor
externo (retry/backoff)").

NOTA: esto es un ESQUELETO. La llamada real a cada SDK (google-genai,
openai, anthropic, groq...) se implementa en `_llamar_api_real`, que
por ahora es un placeholder — sustituir según qué proveedor se elija
para la comparación pedida en el reto (uno comercial + uno local).
"""

import time
import random

from backend.llm.base import LLMProvider
from backend.schemas import Proveedor
from backend.config import settings

MAX_REINTENTOS_RATE_LIMIT = 4
BACKOFF_BASE_SEGUNDOS = 1.5


class RateLimitError(Exception):
    """Se lanza internamente cuando el proveedor externo devuelve 429."""
    pass


# TODO: Precios de referencia por 1K tokens (entrada, salida) en USD.
# Actualizar con los precios vigentes del proveedor elegido.
PRECIOS_POR_1K_TOKENS = {
    "gemini-2.0-flash": (0.000075, 0.0003),
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-haiku": (0.0008, 0.004),
}


class ExternalProvider(LLMProvider):
    nombre_proveedor = Proveedor.EXTERNO

    def __init__(self, modelo: str, temperatura: float = 0.2, top_p: float = 0.9):
        self.nombre_modelo = modelo
        self.temperatura = temperatura
        self.top_p = top_p

    def _llamar_api_real(self, mensajes: list[dict]) -> tuple[str, int, int]:
        """
        TODO: implementar la llamada real al SDK correspondiente, ej.:

            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resp = client.models.generate_content(model=self.nombre_modelo, ...)

        Debe devolver (texto, tokens_entrada, tokens_salida) y lanzar
        RateLimitError si la API responde 429 / rate-limited, para que
        el retry/backoff de abajo la capture.
        """
        raise NotImplementedError(
            "Conectar aquí el SDK del proveedor externo elegido "
            "(Gemini / GPT / Claude / Groq)."
        )

    def _llamar_modelo(self, mensajes: list[dict]) -> tuple[str, int, int]:
        for intento in range(MAX_REINTENTOS_RATE_LIMIT):
            try:
                return self._llamar_api_real(mensajes)
            except RateLimitError:
                if intento == MAX_REINTENTOS_RATE_LIMIT - 1:
                    raise
                espera = BACKOFF_BASE_SEGUNDOS * (2 ** intento) + random.uniform(0, 0.5)
                time.sleep(espera)
        raise RateLimitError("Rate limit persistente tras reintentos.")

    def _calcular_coste(self, tokens_entrada: int, tokens_salida: int) -> float:
        precio_in, precio_out = PRECIOS_POR_1K_TOKENS.get(self.nombre_modelo, (0.0, 0.0))
        return round((tokens_entrada / 1000) * precio_in + (tokens_salida / 1000) * precio_out, 6)
