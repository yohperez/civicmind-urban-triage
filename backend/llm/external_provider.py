"""
Proveedor externo — implementado con Gemini (google-genai) como proveedor
comercial de referencia para la comparación local vs. externo del reto.

Incluye manejo de rate limits con retry/backoff exponencial, tal como
exige el checklist del reto ("con manejo de rate limits del proveedor
externo (retry/backoff)").

Si en algún momento se quiere comparar contra OpenAI/Anthropic/Groq en
vez de (o además de) Gemini, el único método que hay que tocar es
`_llamar_api_real`: el resto (reintentos de rate limit, cálculo de
coste, integración con el flujo type-safe de `base.py`) es agnóstico
al proveedor.
"""

import time
import random

from google import genai
from google.genai import errors as genai_errors

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
    "gemini-2.0-flash-lite": (0.0000375, 0.00015),
    "gemini-1.5-flash": (0.000075, 0.0003),
    "gemini-1.5-pro": (0.00125, 0.005),
    # Precios de referencia — revisar contra la tarifa vigente de Google antes de la entrega.
    "gpt-4o-mini": (0.00015, 0.0006),
    "claude-haiku": (0.0008, 0.004),
}

_cliente_gemini: genai.Client | None = None


def _obtener_cliente_gemini() -> genai.Client:
    """Cliente perezoso y compartido entre llamadas (evita reabrir conexión cada vez)."""
    global _cliente_gemini
    if _cliente_gemini is None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY no está configurada. Añádela en .env (local) "
                "o en las Variables del servicio en Railway."
            )
        _cliente_gemini = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _cliente_gemini


class ExternalProvider(LLMProvider):
    nombre_proveedor = Proveedor.EXTERNO

    def __init__(self, modelo: str, temperatura: float = 0.2, top_p: float = 0.9):
        self.nombre_modelo = modelo
        self.temperatura = temperatura
        self.top_p = top_p

    def _llamar_api_real(self, mensajes: list[dict]) -> tuple[str, int, int]:
        """
        Llamada real a Gemini vía google-genai.

        `mensajes` sigue el formato OpenAI-style usado en base.py:
        [{"role": "system"|"user"|"assistant", "content": "..."}]
        Gemini separa la instrucción de sistema (`system_instruction`) del
        resto del historial, y llama "model" al rol que aquí es "assistant".
        """
        instruccion_sistema = ""
        contenidos = []
        for m in mensajes:
            if m["role"] == "system":
                instruccion_sistema = m["content"]
                continue
            rol_gemini = "model" if m["role"] == "assistant" else "user"
            contenidos.append({"role": rol_gemini, "parts": [{"text": m["content"]}]})

        cliente = _obtener_cliente_gemini()

        try:
            respuesta = cliente.models.generate_content(
                model=self.nombre_modelo,
                contents=contenidos,
                config={
                    "system_instruction": instruccion_sistema,
                    "temperature": self.temperatura,
                    "top_p": self.top_p,
                    # JSON mode: refuerza a nivel de API lo que ya pide el prompt,
                    # como segunda barrera antes de que Pydantic valide en base.py.
                    "response_mime_type": "application/json",
                },
            )
        except genai_errors.ClientError as e:
            if e.code == 429:
                raise RateLimitError(f"Rate limit de Gemini: {e.message}") from e
            raise
        except genai_errors.ServerError as e:
            # 5xx del lado de Google: tratamos como transitorio, igual que un rate limit.
            raise RateLimitError(f"Error transitorio del servidor de Gemini: {e.message}") from e

        texto = respuesta.text or ""
        uso = respuesta.usage_metadata
        tokens_entrada = uso.prompt_token_count if uso else 0
        tokens_salida = uso.candidates_token_count if uso else 0
        return texto, tokens_entrada, tokens_salida

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
