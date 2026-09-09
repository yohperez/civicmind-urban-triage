# Se construye con contexto en la raíz del repo (ver docker-compose.yml:
# `context: .`), porque backend/ importa como paquete `backend.xxx` y
# necesita también requirements.txt, que vive en la raíz.
FROM python:3.12-slim

WORKDIR /app

# curl: usado por el healthcheck de docker-compose.yml (GET /health).
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
