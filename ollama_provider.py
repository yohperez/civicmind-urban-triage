"""
Proveedor local — Ollama.

Ecosistema abierto: puede ejecutarse on-premise (`ollama serve` en localhost,
sin coste por token, sin enviar datos a terceros) o contra Ollama Cloud
(https://ollama.com), que es lo que permite usarlo desde un dashboard
desplegado en Railway sin depender de que tu máquina esté encendida.

Local:
    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_API_KEY=            (vacío)
    OLLAMA_MODEL_DEFAULT=llama3.1

Cloud (ollama.com):
    OLLAMA_BASE_URL=https://ollama.com
    OLLAMA_API_KEY=<tu api key de ollama.com>
    OLLAMA_MODEL_DEFAULT=gpt-oss:20b-cloud   # nota el sufijo -cloud

Mismo endpoint REST (/api/chat) en ambos casos; solo cambian base_url,
la cabecera Authorization, y el nombre del modelo.
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
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.api_key = settings.OLLAMA_API_KEY

    def _cabeceras(self) -> dict:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def _llamar_modelo(self, mensajes: list[dict]) -> tuple[str, int, int]:
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                headers=self._cabeceras(),
                json={
                    "model": self.nombre_modelo,
                    "messages": mensajes,
                    "stream": False,
                    "options": {"temperature": self.temperatura, "top_p": self.top_p},
                },
                timeout=120,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            # Error controlado: Ollama caído, API key inválida, modelo no
            # encontrado, timeout... nunca dejamos que tumbe el servicio.
            raise RuntimeError(f"No se pudo contactar Ollama ({self.base_url}): {exc}") from exc

        data = resp.json()
        texto = data.get("message", {}).get("content", "")
        # Ollama no siempre reporta tokens exactos en todas las versiones;
        # se usa prompt_eval_count / eval_count si están disponibles.
        tokens_entrada = data.get("prompt_eval_count", 0)
        tokens_salida = data.get("eval_count", 0)
        return texto, tokens_entrada, tokens_salida

    def _calcular_coste(self, tokens_entrada: int, tokens_salida: int) -> float:
        # Ollama Cloud tiene tier gratuito con límites de uso y planes de pago,
        # pero no expone coste por token en la respuesta — se deja en 0.0 igual
        # que en local. Si necesitas comparar coste real, documenta el plan
        # contratado aparte (no es un dato que devuelva la API).
        return 0.0
