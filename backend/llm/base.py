"""
Contrato común para cualquier proveedor de LLM (local o externo).

Aquí vive la lógica "type-safe" central del proyecto:
  1. Llamar al proveedor.
  2. Intentar parsear el JSON devuelto.
  3. Validar contra TriajeResponse (Pydantic).
  4. Si falla -> pedir corrección al modelo (hasta MAX_REINTENTOS veces),
     usando CORRECCION_PROMPT_TEMPLATE.
  5. Si sigue fallando -> lanzar TriajeInvalidoError controlado
     (nunca dejar que un ValidationError sin capturar tumbe el servicio).
"""

import json
import time
from abc import ABC, abstractmethod
from pydantic import ValidationError

from backend.schemas import TriajeResponse, MetricasRespuesta, Proveedor
from backend.llm.prompts import (
    SYSTEM_PROMPT,
    CORRECCION_PROMPT_TEMPLATE,
    CHAT_SYSTEM_PROMPT,
    construir_prompt_usuario,
)

MAX_REINTENTOS = 2


class TriajeInvalidoError(Exception):
    """Se lanza cuando el modelo no logra producir un JSON válido tras los reintentos."""
    def __init__(self, mensaje: str, intentos: int):
        self.mensaje = mensaje
        self.intentos = intentos
        super().__init__(mensaje)


class LLMProvider(ABC):
    """
    Cada proveedor (Ollama, Gemini, GPT, Claude, Groq...) implementa
    `_llamar_modelo`. Toda la lógica de validación/reintento/métricas
    se comparte aquí para no duplicarla por proveedor.
    """

    nombre_proveedor: Proveedor
    nombre_modelo: str

    @abstractmethod
    def _llamar_modelo(self, mensajes: list[dict], json_mode: bool = True) -> tuple[str, int, int]:
        """
        Debe devolver (texto_respuesta, tokens_entrada, tokens_salida).
        Implementado por cada subclase concreta (Ollama / externo).

        `json_mode` indica si se está pidiendo una salida JSON estricta
        (triaje) o texto libre (chatbot). Los proveedores que soportan un
        modo JSON forzado a nivel de API (ej. Gemini) deben desactivarlo
        cuando `json_mode=False`, o el chatbot respondería siempre en JSON.
        """
        raise NotImplementedError

    @abstractmethod
    def _calcular_coste(self, tokens_entrada: int, tokens_salida: int) -> float:
        """Coste estimado en USD. Los modelos locales normalmente devuelven 0.0."""
        raise NotImplementedError

    def _extraer_json(self, texto: str) -> dict:
        """
        Defensa adicional: aunque el prompt pide 'solo JSON', los LLMs a
        veces envuelven la respuesta en ```json ... ``` o añaden texto.
        Intentamos recortar al primer '{' y último '}' antes de fallar.
        """
        texto = texto.strip()
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            inicio = texto.find("{")
            fin = texto.rfind("}")
            if inicio != -1 and fin != -1 and fin > inicio:
                return json.loads(texto[inicio:fin + 1])
            raise

    def triar(self, texto_incidencia: str) -> tuple[TriajeResponse, MetricasRespuesta]:
        mensajes = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": construir_prompt_usuario(texto_incidencia)},
        ]

        tokens_entrada_total = 0
        tokens_salida_total = 0
        inicio = time.perf_counter()
        ultima_respuesta_cruda = ""
        ultimo_error = ""

        for intento in range(MAX_REINTENTOS + 1):
            respuesta_cruda, tok_in, tok_out = self._llamar_modelo(mensajes, json_mode=True)
            tokens_entrada_total += tok_in
            tokens_salida_total += tok_out
            ultima_respuesta_cruda = respuesta_cruda

            try:
                datos = self._extraer_json(respuesta_cruda)
                triaje = TriajeResponse.model_validate(datos)

                latencia_ms = (time.perf_counter() - inicio) * 1000
                metricas = MetricasRespuesta(
                    tokens_entrada=tokens_entrada_total,
                    tokens_salida=tokens_salida_total,
                    coste_estimado_usd=self._calcular_coste(tokens_entrada_total, tokens_salida_total),
                    latencia_ms=round(latencia_ms, 2),
                    proveedor=self.nombre_proveedor,
                    modelo=self.nombre_modelo,
                    reintentos=intento,
                )
                return triaje, metricas

            except (json.JSONDecodeError, ValidationError) as e:
                ultimo_error = str(e)
                # Pydantic/JSON interceptó la alucinación estructural.
                # Pedimos corrección explícita en el siguiente intento.
                mensajes.append({"role": "assistant", "content": respuesta_cruda})
                mensajes.append({
                    "role": "user",
                    "content": CORRECCION_PROMPT_TEMPLATE.format(
                        error=ultimo_error, respuesta_previa=respuesta_cruda
                    ),
                })

        # Se agotaron los reintentos: error controlado, el servicio sigue vivo.
        raise TriajeInvalidoError(
            f"El modelo no devolvió un JSON válido tras {MAX_REINTENTOS + 1} intentos. "
            f"Último error: {ultimo_error}. Última respuesta: {ultima_respuesta_cruda[:200]}",
            intentos=MAX_REINTENTOS + 1,
        )

    def chat(self, mensaje: str, historial: list[dict] | None = None) -> tuple[str, MetricasRespuesta]:
        """
        Turno del asistente conversacional del dashboard (chatbot).

        A diferencia de `triar()`, aquí la salida es texto libre: no hay
        esquema JSON que validar ni reintentos por alucinación estructural
        (no aplica — no hay estructura que romper). Reutiliza el mismo
        `_llamar_modelo` de cada proveedor (Ollama o Gemini), así que
        hereda gratis el manejo de errores/rate-limit ya implementado ahí.

        `historial` sigue el formato OpenAI-style [{"role", "content"}, ...]
        con los turnos previos de la conversación (sin incluir `mensaje`).
        """
        mensajes = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        mensajes.extend(historial or [])
        mensajes.append({"role": "user", "content": mensaje})

        inicio = time.perf_counter()
        respuesta_cruda, tok_in, tok_out = self._llamar_modelo(mensajes, json_mode=False)
        latencia_ms = (time.perf_counter() - inicio) * 1000

        metricas = MetricasRespuesta(
            tokens_entrada=tok_in,
            tokens_salida=tok_out,
            coste_estimado_usd=self._calcular_coste(tok_in, tok_out),
            latencia_ms=round(latencia_ms, 2),
            proveedor=self.nombre_proveedor,
            modelo=self.nombre_modelo,
            reintentos=0,
        )
        return respuesta_cruda.strip(), metricas
