# CivicMind — Motor de triaje asistido por LLM (API type-safe, multi-proveedor)

Proyecto I — Módulo V: AI Engineering.

![CivicMind](img/logo-civicmind.svg)

Microservicio backend (FastAPI + Pydantic) que clasifica incidencias
ciudadanas mediante un LLM usando el framework **ReAct** + **Chain-of-Thought**,
más un frontend **React (Vite + Tailwind)** de marca propia (logo, favicon,
soporte multi-idioma y tema claro/oscuro) para validación humana
(Human-in-the-loop) y comparación entre un proveedor **local** (Ollama) y uno
**externo** (comercial: Gemini/GPT/Claude, o gratuito: Groq/Hugging Face).

El frontend incluye además un **asistente conversacional (chatbot)** —
también disponible en local (Ollama) o externo (Gemini) — para que el
operador humano pregunte en lenguaje natural sobre el pipeline, una
clasificación concreta o el criterio anti-sesgo, sin salir del panel.

Existe también una versión previa del dashboard en **Streamlit**
(`dashboard/app.py`), conservada en el repo pero sustituida por el frontend
React como interfaz principal — ver [`frontend/DEPLOY.md`](frontend/DEPLOY.md)
para el porqué de la migración.

🔗 **Repositorio:** [github.com/yohperez/civicmind-urban-triage](https://github.com/yohperez/civicmind-urban-triage)
🔗 **Frontend en producción:** [civicmind.up.railway.app](https://civicmind.up.railway.app/)
🔗 **Backend (API):** [backend-civicmind.up.railway.app](https://backend-civicmind.up.railway.app/)

## Por qué esta arquitectura (decisión de diseño)

Se prioriza **Ollama** como proveedor por defecto para:
- Prototipar sin depender de infraestructura de pago.
- Mantener la privacidad de los datos ciudadanos (el texto de la
  incidencia no sale del entorno local).
- Comparar, cuando se necesite, contra un proveedor comercial en
  coste/latencia/calidad — sin acoplar el resto del sistema a un único
  proveedor (de ahí la interfaz `LLMProvider` en `backend/llm/base.py`).

Backend, frontend y dashboard son **procesos independientes** que se
comunican por HTTP (nunca importan código el uno del otro), precisamente
para poder desplegarlos como servicios separados en Railway.

## Estructura

```
civicmind-urban-triage/
├── backend/
│   ├── main.py                   # Endpoint FastAPI (/triaje, /chat, /incidencias, /health)
│   ├── schemas.py                # Modelos Pydantic: triaje, métricas y chat (ChatRequest/ChatResponse)
│   ├── config.py                 # Variables de entorno
│   └── llm/
│       ├── base.py               # Lógica común: triar() (JSON+reintentos) y chat() (texto libre), métricas
│       ├── prompts.py            # SYSTEM_PROMPT (triaje ReAct+CoT) y CHAT_SYSTEM_PROMPT (chatbot)
│       ├── ollama_provider.py    # Proveedor local — usado tanto por /triaje como por /chat
│       └── external_provider.py  # Proveedor externo — Gemini (google-genai) + retry/backoff, JSON mode condicional
├── frontend/                     # React + Vite + Tailwind — interfaz principal (reemplaza a dashboard/)
│   ├── index.html
│   ├── src/
│   │   ├── App.jsx                   # Layout: Sidebar + formulario + resultados + histórico + chat
│   │   ├── api.js                    # Cliente HTTP hacia el backend (VITE_API_URL)
│   │   ├── i18n/
│   │   │   ├── translations.js       # Diccionarios es/en (UI + labels de categoría/urgencia)
│   │   │   └── I18nContext.jsx       # Provider: sincroniza idioma con la ruta /es · /en
│   │   ├── theme/
│   │   │   └── ThemeContext.jsx      # Provider: toggle de tema claro/oscuro (clase `.light` en <html>)
│   │   └── components/
│   │       ├── Sidebar.jsx           # Logo, pipeline del motor, toggles de idioma/tema
│   │       ├── IncidentForm.jsx      # Formulario de nueva incidencia
│   │       ├── ResultCards.jsx       # Tarjetas de resultado del triaje
│   │       ├── HistoryTable.jsx      # Histórico + estadísticas agregadas
│   │       ├── ChatPanel.jsx         # Asistente conversacional
│   │       ├── UrgencyBadge.jsx      # Badge de urgencia (color + etiqueta traducida)
│   │       └── CategoryIcon.jsx      # Icono por categoría
│   ├── public/
│   │   ├── logo-mark.svg             # Isotipo cuadrado (escudo + pulso) — usado en la sidebar/favicon
│   │   └── favicon.png
│   └── DEPLOY.md                     # Notas de despliegue específicas del frontend en Railway
├── dashboard/
│   └── app.py                    # Streamlit — versión previa del panel, conservada como referencia
├── img/
│   ├── logo-civicmind.svg        # Logo completo + wordmark (README, materiales, cabeceras grandes)
│   ├── logo-mark.svg             # Isotipo cuadrado — mismo asset que frontend/public/logo-mark.svg
│   ├── flow-react-cot.svg        # Ilustración del pipeline ReAct+CoT+HITL
│   ├── favicon.png               # Icono de pestaña del navegador (256px)
│   └── favicon-64.png            # Variante pequeña
├── tests/
│   ├── test_api.py               # Tests de endpoint con mocking del LLM
│   └── test_schemas.py           # Tests de validación Pydantic
├── data/
│   └── sample_incidencias.json
├── requirements.txt
├── Procfile                      # Start command del backend en Railway
├── .env.example
└── .gitignore
```

## Instalación local

```bash
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # rellenar API key del proveedor externo elegido
```

Instalar y arrancar Ollama por separado ([ollama.com](https://ollama.com)):

```bash
ollama pull llama3.1
ollama serve
```

## Ejecución local

Backend:
```bash
uvicorn backend.main:app --reload --port 8000
```

Frontend (en otra terminal, con el backend ya corriendo):
```bash
cd frontend
npm install
npm run dev
```

A diferencia del dashboard de Streamlit (que leía `API_URL` en cada arranque
del proceso), el frontend React incrusta `VITE_API_URL` **en tiempo de
build** — ver [`frontend/DEPLOY.md`](frontend/DEPLOY.md) para el detalle y
las implicaciones al desplegar. En local, si no se define, cae por defecto a
`http://localhost:8000`.

Dashboard Streamlit — versión previa, opcional (en otra terminal, con el
backend ya corriendo):
```bash
streamlit run dashboard/app.py
```
El dashboard lee la URL del backend de la variable de entorno `API_URL`
(por defecto `http://localhost:8000` en local).

## Interfaz: idioma y tema

El frontend soporta español e inglés y tema claro/oscuro, con toggles en la
cabecera de la sidebar:

- **Idioma** (`es` · `en`): sincronizado con la ruta — `/es` y `/en` — y
  persistido en `localStorage`. Todo el texto de interfaz vive en
  `frontend/src/i18n/translations.js`; los valores del backend (categoría,
  urgencia) son enums fijos en español (`schemas.py`) y se traducen solo a
  nivel de presentación, sin tocar el contrato de la API.
- **Tema** (claro/oscuro): oscuro por defecto (identidad visual original del
  proyecto), alternable con un botón junto al selector de idioma. Implementado
  con variables CSS (`frontend/src/index.css`) que Tailwind consume vía
  `rgb(var(--x) / <alpha-value>)`, así que ningún componente necesita lógica
  de tema propia — solo cambia el valor de las variables al aplicar la clase
  `.light` en `<html>` (`frontend/src/theme/ThemeContext.jsx`).

## Asistente conversacional (chatbot)

El panel incluye un chatbot (`💬 Asistente CivicMind`) para resolver dudas
del operador sin salir del dashboard: cómo funciona el pipeline ReAct+CoT,
qué significa cada nivel de urgencia, por qué se aplicó cierto criterio
anti-sesgo, o cuándo conviene local vs. externo. No vuelve a triar
incidencias — para eso sigue estando el formulario `📝 Nueva incidencia`.

- **Backend:** nuevo endpoint `POST /chat` (`backend/main.py`), que reutiliza
  el mismo `LLMProvider` que `/triaje` (misma instancia de `OllamaProvider` /
  `ExternalProvider`, mismo manejo de errores/rate-limit), pero llama a
  `LLMProvider.chat()` en vez de `.triar()`. `chat()` (nuevo en
  `backend/llm/base.py`) envía el historial de la conversación y devuelve
  texto libre — sin el bucle de extracción/validación JSON ni los
  reintentos por alucinación estructural que sí tiene `.triar()`, porque
  aquí no hay un esquema Pydantic que cumplir.
- **Prompt propio:** `CHAT_SYSTEM_PROMPT` en `backend/llm/prompts.py`
  define la personalidad y límites del asistente (responde en español,
  no clasifica incidencias, no inventa datos).
- **Gemini en modo texto libre:** `ExternalProvider._llamar_api_real` ahora
  acepta un flag `json_mode`; `/triaje` lo activa (fuerza
  `response_mime_type=application/json` como hacía antes) y `/chat` lo
  desactiva, para que Gemini responda en lenguaje natural en vez de JSON.
- **Dashboard:** interfaz de chat nativa de Streamlit (`st.chat_message` /
  `st.chat_input`), con selector de proveedor/modelo propio (independiente
  del formulario de triaje) y botón para vaciar la conversación. El
  historial vive en `st.session_state` mientras dura la sesión del navegador.
- **Proveedor y modelo:** exactamente los mismos que en `/triaje` — local
  (Ollama on-premise o Cloud, con los mismos tags sugeridos) o externo
  (Gemini, indicando el nombre del modelo).

## Despliegue en Railway

El repo se despliega como **servicios Railway independientes** apuntando al
mismo repositorio:

**1. Servicio backend**
- Root directory: `/` (raíz del repo)
- Start command: el del `Procfile` → `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Variables de entorno: las que correspondan del `.env.example` (API key del
  proveedor externo, `OLLAMA_BASE_URL` si usas un Ollama alcanzable en red)
- Railway te da una URL pública tipo `https://backend-civicmind.up.railway.app`

**2. Servicio frontend** (React/Vite — interfaz principal)
- Root directory: `/` (mismo repo)
- Watch path: `frontend/**`, build command `npm run build`, start command
  `npm run preview` — detalle completo, incluyendo el matiz de `VITE_API_URL`
  como variable de build-time, en [`frontend/DEPLOY.md`](frontend/DEPLOY.md)
- Variable de entorno **obligatoria**: `VITE_API_URL` = la URL pública del
  servicio backend del paso 1, definida **antes** del primer build

**3. Servicio dashboard** (Streamlit — opcional, versión previa)
- Root directory: `/` (mismo repo)
- Start command (sobrescribir manualmente en Settings → Deploy):
  ```
  streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0
  ```
- Variable de entorno **obligatoria**: `API_URL` = la URL pública del
  servicio backend del paso 1.

Backend y dashboard comparten el mismo `requirements.txt` (Nixpacks detecta
Python automáticamente); el frontend construye su propia imagen Node a
partir de `frontend/package.json`.

**Producción actual:** el frontend está desplegado en
[frontend-civicmind.up.railway.app](https://frontend-civicmind.up.railway.app/),
apuntando (vía `VITE_API_URL`) al servicio backend en
[backend-civicmind.up.railway.app](https://backend-civicmind.up.railway.app/).
El chatbot usa el mismo backend, así que no requiere ninguna variable de
entorno adicional en Railway más allá de las ya listadas para `/triaje`.

## Tests

```bash
pytest -v
```

Incluye tests con mocking para ambos endpoints — `/triaje` (validación
type-safe, reintentos, errores de proveedor) y `/chat` (respuesta de texto
libre, reenvío del historial de conversación, mismo manejo de errores que
`/triaje`) — tanto para el proveedor local como el externo.

## Identidad visual

- **Logo completo** (`img/logo-civicmind.svg`): escudo + señal de pulso +
  wordmark "CivicMind" + tagline, pensado para cabeceras anchas (README,
  landing, materiales de presentación). No usar en espacios cuadrados
  pequeños — se deforma al forzar su proporción 480:90 en un icono.
- **Isotipo / logo-mark** (`img/logo-mark.svg`,
  `frontend/public/logo-mark.svg`): recorte cuadrado del mismo escudo +
  pulso, sin wordmark, pensado para espacios reducidos — es el que usa la
  sidebar del frontend y el favicon. Mismo `viewBox` cuadrado para no
  distorsionarse a ningún tamaño.
- **Favicon** (`favicon.png` / `favicon-64.png`): versión reducida del
  mismo icono.
- **Ilustración de pipeline** (`img/flow-react-cot.svg`): diagrama del ciclo
  Reporte → Thought → Action → Observation → Operador (HITL).
- Los assets son placeholders con buen contraste y estilo consistente —
  sustitúyelos libremente si tienes una identidad de marca propia definida.

## Estado del esqueleto / TODOs pendientes

Este scaffold cubre la arquitectura completa y pasa los tests con el
LLM **mockeado**. El proveedor externo (Gemini) ya está implementado con
JSON mode + retry/backoff ante 429 y errores 5xx transitorios — solo hace
falta poner `GEMINI_API_KEY` en las variables de entorno (local o Railway).
Cómo conseguirla: [Google AI Studio](https://aistudio.google.com/apikey).

Antes de la entrega falta:

- [ ] Ajustar `Categoria` y los departamentos en `schemas.py` a los
      reales de la plataforma/ayuntamiento.
- [ ] Decidir persistencia (`INCIDENCIAS_PROCESADAS` es en memoria —
      sustituir por SQLite/Postgres si se quiere histórico real entre
      reinicios del servicio en Railway).
- [ ] Ajustar precios en `PRECIOS_POR_1K_TOKENS` a las tarifas vigentes.
- [ ] Añadir botones de validar/rechazar por incidencia en el dashboard
      (HITL real, no solo lectura).
- [ ] Revisar y documentar en la presentación oral los sesgos
      detectados y cómo el prompt los mitiga (criterio C10).
- [ ] El historial del chatbot solo vive en memoria del navegador (se pierde
      al recargar la página o entre sesiones) — evaluar si conviene
      persistirlo junto a `INCIDENCIAS_PROCESADAS` cuando se añada base
      de datos real.
- [ ] El frontend traduce texto de interfaz y las etiquetas de
      categoría/urgencia (es/en), pero no el contenido generado por el LLM
      (resumen, razonamiento) — depende del idioma en que responda el
      proveedor configurado.

## Glosario rápido

Ver el enunciado del reto (`Proyecto_I_Módulo_V__AI_Engineering.pdf`)
para el glosario completo (ReAct, CoT, type-safe, HITL, etc.).
