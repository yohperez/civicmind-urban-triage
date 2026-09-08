"""Configuración centralizada, leída desde variables de entorno (.env)."""

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv es opcional; en producción se puede inyectar el entorno directamente


@dataclass
class Settings:
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL_DEFAULT: str = os.getenv("OLLAMA_MODEL_DEFAULT", "llama3.1")
    # Si se define, Ollama se consume en modo cloud (https://ollama.com) en vez
    # de local: se envía como Authorization: Bearer <key>. Vacío = uso local,
    # sin autenticación (comportamiento previo, sin cambios).
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")

    # TODO: añadir la API key del proveedor externo elegido
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")


settings = Settings()
