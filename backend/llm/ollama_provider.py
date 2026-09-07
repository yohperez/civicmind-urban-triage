"""
Proveedor local — Ollama.

Ecosistema abierto: modelo corre on-premise, sin coste por token y sin
enviar datos ciudadanos a terceros (criterio de privacidad del reto).

Requiere tener Ollama corriendo (`ollama serve`) y el modelo descargado,
ej. `ollama pull llama3.1` o `ollama pull mistral`.
"""

import requests

from backend.llm.base import LLMProvider
from backend.schemas import Proveedor
from backend.config import settings


class OllamaProvider(LLMProvider):
    nombre_proveedor = Proveedor.LOCAL

    def __init__(self, modelo: str = None, temperatura: float = 0.2, top_p: float = 0.9):
        self.nombre_modelo = modelo or settings.OLLAMA_MODEL_DEFAULT
        self.temperatura = temperatura  # baja temperatura: queremos consistencia, no creatividad
        self.top_p = top_p
        self.base_url = settings.OLLAMA_BASE_URL

    def _llamar_modelo(self, mensajes: list[dict]) -> tuple[str, int, int]:
        # TODO: envolver en try/except requests.RequestException y propagar
        # como error controlado si Ollama no está disponible.
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.nombre_modelo,
                "messages": mensajes,
                "stream": False,
                "options": {"temperature": self.temperatura, "top_p": self.top_p},
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        texto = data.get("message", {}).get("content", "")
        # Ollama no siempre reporta tokens exactos en todas las versiones;
        # se usa prompt_eval_count / eval_count si están disponibles.
        tokens_entrada = data.get("prompt_eval_count", 0)
        tokens_salida = data.get("eval_count", 0)
        return texto, tokens_entrada, tokens_salida

    def _calcular_coste(self, tokens_entrada: int, tokens_salida: int) -> float:
        return 0.0  # ejecución local, sin coste por token
