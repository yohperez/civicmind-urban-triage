# Mejoras añadidas sobre el proyecto base

Este documento resume las 6 mejoras implementadas encima del motor de
triaje original, y qué archivos tocó cada una. Todo está ya integrado y
probado (`pytest tests/ -v` → 23 tests, `npm run build` → sin errores);
solo falta copiar los archivos sobre tu repo y hacer commit.

## 1. Persistencia con SQLite

**Problema que resuelve:** `INCIDENCIAS_PROCESADAS` era una lista en
memoria — se perdía el histórico cada redeploy/reinicio en Railway.

**Archivos:**
- `backend/db.py` (nuevo) — `init_db()`, `guardar_incidencia()`, `listar_incidencias()`.
- `backend/main.py` — usa `backend/db.py` en vez de la lista; añade `GET /incidencias/geo`.
- `backend/schemas.py` — `IncidenciaRequest` gana `lat`/`lon` opcionales.

Sin dependencias nuevas (usa `sqlite3` de la librería estándar). Variable
opcional `CIVICMIND_DB_PATH` para apuntar a un volumen persistente en
Railway; si no se define, usa `./civicmind.db` en el filesystem del
contenedor.

## 2. Mapa de incidencias (geolocalización)

**Archivos:**
- `frontend/index.html` — añade Leaflet vía CDN (`<link>`/`<script>`).
- `frontend/src/components/MapaIncidencias.jsx` (nuevo).
- `frontend/src/api.js` — `listarIncidenciasGeo()`.
- `frontend/src/App.jsx` — monta `<MapaIncidencias />`.

Usa `window.L` (Leaflet por CDN) en vez de `react-leaflet`, para no tocar
`package.json`. Los marcadores se colorean por urgencia usando la misma
paleta que `UrgencyBadge.jsx`. Solo aparecen incidencias enviadas con
`lat`/`lon` en el payload de `/triaje` — es opcional, así que el resto del
flujo no cambia si no lo usas.

## 3. Auditoría de sesgos (panel comparativo — criterio C10)

**Archivos:**
- `backend/schemas.py` — `AuditoriaSesgosRequest/Response`, `VarianteAuditoria`.
- `backend/main.py` — `POST /auditoria-sesgos`.
- `frontend/src/components/AuditoriaSesgos.jsx` (nuevo).
- `frontend/src/api.js` — `auditarSesgos()`.

El operador escribe 2–4 variantes del **mismo hecho** (a propósito, no las
genera el backend — evita que el sistema fabrique caracterización
demográfica por su cuenta). Se corren por el mismo LLM y se compara si
`urgencia`/`categoria` divergen. Si divergen, se marca una alerta visible.
Esto convierte la instrucción anti-sesgo del `SYSTEM_PROMPT` en algo
**verificable con datos** — ideal para la sección "Sesgos detectados" de
tu presentación oral.

## 4. Razonamiento ReAct en vivo (streaming SSE)

**Archivos:**
- `backend/llm/base.py` — `triar_stream()`, `_llamar_modelo_stream()` (fallback por defecto).
- `backend/llm/ollama_provider.py` — streaming real (`stream: True` en `/api/chat`).
- `backend/llm/external_provider.py` — streaming real (`generate_content_stream` de Gemini).
- `backend/main.py` — `POST /triaje/stream` (Server-Sent Events).
- `frontend/src/components/TriajeStreaming.jsx` (nuevo).
- `frontend/src/api.js` — `triarStream()` (lee el stream con `fetch` + `ReadableStream`, no `EventSource`, porque este necesita POST con body).

Pensado para la demo en vivo: en vez de una barra de carga opaca, el
operador ve aparecer el ciclo Thought → Action → Observation token a
token. **No** reintenta automáticamente ni guarda en el histórico — para
eso sigue existiendo `/triaje`, que es el flujo "de verdad".

## 5. Fiabilidad / self-consistency

**Archivos:**
- `backend/schemas.py` — `ConsistenciaRequest/Response`.
- `backend/main.py` — `POST /triaje/consistencia`.
- `frontend/src/components/ConsistenciaPanel.jsx` (nuevo).
- `frontend/src/api.js` — `evaluarConsistencia()`.

Corre la misma incidencia N veces (2–5, configurable) y calcula el
% de acuerdo en `urgencia` y `categoria` (voto mayoritario). Si no hay
consenso total, marca la incidencia como "inconsistente" — señal para que
el operador HITL la revise con más cuidado en vez de fiarse de una única
pasada del LLM.

## 6. Docker Compose + CI

**Archivos:**
- `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `.env.example` (nuevos).
- `.github/workflows/ci.yml` (nuevo) — corre `pytest` y el build de Vite en cada push/PR.

Levanta Ollama + backend + frontend con un solo comando:

```bash
cp .env.example .env   # y rellena GEMINI_API_KEY si vas a probar el externo
docker compose up --build
docker compose exec ollama ollama pull llama3.1   # primera vez
```

## Tests nuevos

`tests/test_mejoras.py` (nuevo) — 7 tests con mocking cubriendo las 4
mejoras de backend (persistencia, auditoría de sesgos, consistencia,
streaming). Los 16 tests originales siguen pasando sin cambios.

## Cómo aplicar estos cambios a tu repo

1. Descarga el zip adjunto y descomprímelo.
2. Copia su contenido sobre `civicmind-urban-triage/`, sobrescribiendo los
   archivos existentes que coincidan (`backend/main.py`, `schemas.py`,
   `llm/base.py`, `llm/ollama_provider.py`, `llm/external_provider.py`,
   `frontend/index.html`, `frontend/src/App.jsx`, `frontend/src/api.js`) y
   añadiendo los nuevos.
3. `cd frontend && npm install` (por si acaso; no se añadió ninguna
   dependencia npm nueva, pero por si tu `node_modules` está desactualizado).
4. `pytest tests/ -v` para confirmar que todo pasa en tu entorno.
5. Commit y push — el workflow de CI se activará solo si copiaste
   `.github/workflows/ci.yml`.
