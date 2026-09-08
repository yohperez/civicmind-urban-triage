"""
CivicMind — Dashboard de Triaje Urbano (Human-in-the-loop)

Ejecución local:
    uvicorn backend.main:app --reload --port 8000   # en una terminal
    streamlit run dashboard/app.py                   # en otra

Despliegue en Railway (servicio independiente del backend):
    Start command:  streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0
    Variable de entorno API_URL = <URL pública del servicio backend en Railway>

El dashboard NO asume que el backend está en localhost: lee la URL desde
la variable de entorno API_URL, con localhost:8000 como fallback para
desarrollo local. Esto es lo que permite que backend y dashboard vivan
como dos servicios Railway separados dentro del mismo repo.
"""

import os
import textwrap
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# --------------------------------------------------------------------------
# Configuración y branding
# --------------------------------------------------------------------------
IMG_DIR = Path(__file__).parent.parent / "img"
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="CivicMind — Triaje Urbano",
    page_icon=str(IMG_DIR / "favicon.png") if (IMG_DIR / "favicon.png").exists() else "🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _svg(nombre: str) -> str:
    """Lee un SVG de /img y lo devuelve como texto, para incrustarlo con st.markdown."""
    ruta = IMG_DIR / nombre
    if ruta.exists():
        return ruta.read_text(encoding="utf-8")
    return ""


def badge_urgencia(nivel: str) -> str:
    """Insignia SVG en línea (punto de color + etiqueta) para el nivel de urgencia."""
    colores = {
        "critica": "#DC2626",
        "alta": "#F59E0B",
        "media": "#EAB308",
        "baja": "#16A34A",
    }
    color = colores.get(nivel, "#64748B")
    etiqueta = nivel.upper()
    # HTML en una sola línea: si esto lleva saltos de línea con indentación,
    # Streamlit lo interpreta como bloque de código al incrustarlo en otro
    # st.markdown y deja de renderizar el HTML (ver nota en la tarjeta de resultado).
    return (
        f'<span style="display:inline-flex;align-items:center;gap:6px;'
        f'background:{color}1A;color:{color};font-weight:700;'
        f'padding:4px 12px;border-radius:999px;font-size:0.85rem;">'
        f'<svg width="10" height="10" viewBox="0 0 10 10">'
        f'<circle cx="5" cy="5" r="5" fill="{color}"/></svg> {etiqueta}</span>'
    )


ICONOS_CATEGORIA = {
    "infraestructura": ("#6366F1", "M2 20 L9 8 L16 20 Z M9 4 v3"),
    "limpieza": ("#0EA5E9", "M6 3 h8 l-1 14 a2 2 0 0 1 -2 2 h-2 a2 2 0 0 1 -2 -2 Z"),
    "seguridad": ("#F59E0B", "M10 2 L17 5 V11 C17 15 14 18 10 19 C6 18 3 15 3 11 V5 Z"),
    "sanidad": ("#EF4444", "M10 3 v14 M3 10 h14"),
    "transito": ("#8B5CF6", "M4 14 h12 M6 14 v3 M14 14 v3 M5 14 l1.5 -7 h7 L15 14"),
    "otros": ("#64748B", "M10 3 a7 7 0 1 0 0.001 0 Z"),
}


def icono_categoria(categoria: str, tamano: int = 26) -> str:
    color, path = ICONOS_CATEGORIA.get(categoria, ICONOS_CATEGORIA["otros"])
    # Igual que badge_urgencia: una sola línea, sin indentación, para no romper
    # el parseo del bloque HTML donde se incrusta.
    return (
        f'<svg width="{tamano}" height="{tamano}" viewBox="0 0 20 20" '
        f'style="vertical-align:middle;margin-right:6px;">'
        f'<circle cx="10" cy="10" r="10" fill="{color}1A"/>'
        f'<path d="{path}" stroke="{color}" stroke-width="1.6" fill="none" '
        f'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


# --------------------------------------------------------------------------
# Estilos
# --------------------------------------------------------------------------
st.markdown(
    textwrap.dedent("""\
    <style>
    .cm-hero { padding: 0.5rem 0 1.2rem 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 1.4rem; }
    .cm-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
               padding: 1.1rem 1.3rem; box-shadow: 0 1px 2px rgba(15,23,42,0.04); }
    .cm-caption { color: #64748B; font-size: 0.85rem; }
    .cm-section-title { font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 0.4rem; }
    </style>
    """).strip(),
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Cabecera / marca
# --------------------------------------------------------------------------
logo_svg = _svg("logo-civicmind.svg")
st.markdown(f'<div class="cm-hero">{logo_svg}</div>', unsafe_allow_html=True)

st.markdown(
    """
    **CivicMind** es el panel de control del motor de triaje: aquí un operador humano
    (Human-in-the-loop) revisa cómo el LLM clasifica cada incidencia ciudadana —
    categoría, urgencia y departamento — junto con el razonamiento paso a paso
    (Chain-of-Thought dentro de un ciclo ReAct) que justificó esa decisión, antes
    de darla por buena. Nada se registra "a ciegas": todo pasa primero por esta pantalla.
    """
)

with st.expander("🧭 Cómo funciona el pipeline (ReAct + Chain-of-Thought + validación type-safe)"):
    flow_svg = _svg("flow-react-cot.svg")
    if flow_svg:
        st.markdown(flow_svg, unsafe_allow_html=True)
    st.markdown(
        """
1. **Reporte** — el texto libre que escribe el ciudadano llega tal cual, sin estructurar.
2. **Thought** — el modelo razona en voz alta (Chain-of-Thought) sobre qué está describiendo el texto.
3. **Action** — con ese razonamiento, decide categoría, urgencia y departamento.
4. **Observation** — la salida se valida estrictamente contra un esquema Pydantic; si el modelo
   "alucina" un campo o un tipo incorrecto, el sistema se lo hace saber y le pide corregirlo
   (hasta 2 reintentos) en vez de romper el servicio.
5. **Operador (HITL)** — un humano ve el JSON *y* el razonamiento, y decide si lo valida o lo corrige.

**Sobre los sesgos:** el prompt de sistema instruye explícitamente al modelo para ignorar género,
origen, raza o barrio inferido del texto al determinar la urgencia — la gravedad se decide solo por
el riesgo objetivo descrito. Es una mitigación a nivel de prompt, no una garantía absoluta: por eso
la validación humana en este panel sigue siendo el último filtro.
        """
    )

st.divider()

# --------------------------------------------------------------------------
# Formulario de nueva incidencia
# --------------------------------------------------------------------------
st.markdown('<div class="cm-section-title">📝 Nueva incidencia</div>', unsafe_allow_html=True)

MODELOS_OLLAMA_SUGERIDOS = [
    "(usar OLLAMA_MODEL_DEFAULT del backend)",
    "gpt-oss:20b-cloud",
    "gpt-oss:120b-cloud",
    "gemma4:cloud",
    "gemma4:31b-cloud",
    "qwen3.5:cloud",
    "deepseek-v4-flash:cloud",
]

with st.form("nueva_incidencia"):
    texto = st.text_area(
        "Descripción libre de la incidencia",
        height=100,
        placeholder="Ej: Hay un socavón enorme en la calle principal, un coche casi cae dentro esta mañana.",
    )
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        proveedor = st.selectbox("Proveedor", ["local", "externo"], help="local = Ollama (on-premise o Cloud) · externo = API comercial")
    with col2:
        modelo_externo = st.text_input("Modelo externo (si aplica)", placeholder="ej. gemini-2.0-flash")
    with col3:
        comparar = st.checkbox("Comparar local vs. externo", help="Envía el mismo texto a ambos proveedores a la vez")

    st.caption("🦙 Modelo Ollama (aplica al proveedor **local**, sea on-premise o Ollama Cloud)")
    col4, col5 = st.columns([1, 1])
    with col4:
        modelo_ollama_preset = st.selectbox("Sugeridos", MODELOS_OLLAMA_SUGERIDOS)
    with col5:
        modelo_ollama_custom = st.text_input("…o escribe otro tag", placeholder="ej. minimax-m2.7:cloud")

    enviado = st.form_submit_button("🚀 Procesar incidencia", use_container_width=True)

if enviado and texto.strip():
    modelo_ollama = modelo_ollama_custom.strip() or (
        modelo_ollama_preset if modelo_ollama_preset != MODELOS_OLLAMA_SUGERIDOS[0] else None
    )

    def _payload_local():
        p = {"texto": texto, "proveedor": "local"}
        if modelo_ollama:
            p["modelo_ollama"] = modelo_ollama
        return p

    payloads = []
    if comparar:
        payloads.append(_payload_local())
        if modelo_externo:
            payloads.append({"texto": texto, "proveedor": "externo", "modelo_externo": modelo_externo})
        else:
            st.warning("Indica un modelo externo para poder comparar contra el proveedor local.")
    else:
        if proveedor == "local":
            payload = _payload_local()
        else:
            payload = {"texto": texto, "proveedor": "externo", "modelo_externo": modelo_externo}
        payloads.append(payload)

    resultados = []
    with st.spinner("El modelo está razonando (Thought → Action → Observation)…"):
        for p in payloads:
            try:
                resp = requests.post(f"{API_URL}/triaje", json=p, timeout=60)
                if resp.status_code == 200:
                    resultados.append(resp.json())
                else:
                    detalle = resp.json()
                    st.error(f"⚠️ El modelo no pasó la validación type-safe ({p['proveedor']}): {detalle}")
            except requests.RequestException as e:
                st.error(f"No se pudo contactar la API en `{API_URL}`: {e}")

    if resultados:
        st.markdown('<div class="cm-section-title">✅ Resultado</div>', unsafe_allow_html=True)
        cols = st.columns(len(resultados))
        for col, r in zip(cols, resultados):
            with col:
                t, m = r["triaje"], r["metricas"]
                icono = icono_categoria(t["categoria"])
                tarjeta_html = textwrap.dedent(f"""\
                    <div class="cm-card">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-weight:700;">{icono}{m['proveedor'].upper()} · {m['modelo']}</span>
                            {badge_urgencia(t['urgencia'])}
                        </div>
                        <p style="margin:0.8rem 0 0.2rem 0;"><b>Categoría:</b> {t['categoria']}</p>
                        <p style="margin:0.2rem 0;"><b>Departamento:</b> {t['departamento_asignado']}</p>
                        <p style="margin:0.2rem 0;"><b>Resumen:</b> {t['resumen']}</p>
                    </div>
                    """).strip()
                st.markdown(tarjeta_html, unsafe_allow_html=True)
                with st.expander("🧠 Ver razonamiento del modelo (CoT/ReAct)"):
                    st.write(t["razonamiento"])
                st.markdown(
                    f'<p class="cm-caption">⏱ {m["latencia_ms"]} ms · 💰 ${m["coste_estimado_usd"]} · '
                    f'🔤 {m["tokens_entrada"]}+{m["tokens_salida"]} tokens · 🔁 {m["reintentos"]} reintentos</p>',
                    unsafe_allow_html=True,
                )

st.divider()

# --------------------------------------------------------------------------
# Histórico
# --------------------------------------------------------------------------
st.markdown('<div class="cm-section-title">📋 Incidencias procesadas</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="cm-caption">Histórico servido por la API — útil para que el operador revise el volumen '
    "y la distribución de urgencias del día, y para comparar coste/latencia entre proveedores.</p>",
    unsafe_allow_html=True,
)

try:
    historico = requests.get(f"{API_URL}/incidencias", timeout=10).json()
    if historico:
        df = pd.json_normalize(historico)
        columnas_utiles = [c for c in [
            "texto", "triaje.categoria", "triaje.urgencia", "triaje.departamento_asignado",
            "metricas.proveedor", "metricas.modelo", "metricas.latencia_ms", "metricas.coste_estimado_usd",
        ] if c in df.columns]
        st.dataframe(df[columnas_utiles] if columnas_utiles else df, use_container_width=True)

        colA, colB, colC = st.columns(3)
        colA.metric("Total procesadas", len(df))
        if "triaje.urgencia" in df.columns:
            colB.metric("Críticas/Altas", int(df["triaje.urgencia"].isin(["critica", "alta"]).sum()))
        if "metricas.coste_estimado_usd" in df.columns:
            colC.metric("Coste acumulado", f"${df['metricas.coste_estimado_usd'].sum():.4f}")
    else:
        st.info("Aún no hay incidencias procesadas. Envía la primera desde el formulario de arriba ⬆️")
except requests.RequestException:
    st.warning(f"No se pudo conectar con la API en `{API_URL}`. ¿Está desplegado/corriendo el backend?")

st.divider()

# --------------------------------------------------------------------------
# Asistente CivicMind (chatbot) — local (Ollama) o externo (Gemini)
# --------------------------------------------------------------------------
st.markdown('<div class="cm-section-title">💬 Asistente CivicMind</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="cm-caption">Chatbot de apoyo para el operador: resuelve dudas sobre el pipeline, '
    "el criterio anti-sesgo, o el porqué de una clasificación — no vuelve a triar la incidencia "
    "(para eso usa el formulario de arriba). Comparte el mismo backend/proveedores que el motor "
    "de triaje, vía el endpoint <code>/chat</code>.</p>",
    unsafe_allow_html=True,
)

if "chat_historial" not in st.session_state:
    st.session_state.chat_historial = []  # [{"rol": "user"|"assistant", "contenido": str}, ...]

with st.expander("⚙️ Proveedor del asistente", expanded=False):
    col_chat1, col_chat2, col_chat3 = st.columns([1, 1, 1])
    with col_chat1:
        chat_proveedor = st.selectbox(
            "Proveedor", ["local", "externo"], key="chat_proveedor",
            help="local = Ollama (on-premise o Cloud) · externo = Gemini",
        )
    with col_chat2:
        if chat_proveedor == "local":
            chat_modelo_preset = st.selectbox("Modelo Ollama", MODELOS_OLLAMA_SUGERIDOS, key="chat_modelo_ollama_preset")
            chat_modelo_ollama_custom = st.text_input("…o escribe otro tag", key="chat_modelo_ollama_custom", placeholder="ej. minimax-m2.7:cloud")
            chat_modelo_externo = None
        else:
            chat_modelo_externo = st.text_input("Modelo Gemini", value="gemini-2.0-flash", key="chat_modelo_externo")
            chat_modelo_ollama_custom = ""
            chat_modelo_preset = MODELOS_OLLAMA_SUGERIDOS[0]
    with col_chat3:
        if st.button("🗑️ Vaciar conversación", use_container_width=True):
            st.session_state.chat_historial = []
            st.rerun()

# Pinta el historial ya existente
for turno in st.session_state.chat_historial:
    with st.chat_message(turno["rol"]):
        st.markdown(turno["contenido"])
        if turno.get("meta"):
            st.markdown(f'<p class="cm-caption">{turno["meta"]}</p>', unsafe_allow_html=True)

pregunta = st.chat_input("Pregúntale algo al asistente de CivicMind…")
if pregunta:
    st.session_state.chat_historial.append({"rol": "user", "contenido": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    chat_modelo_ollama = (chat_modelo_ollama_custom or "").strip() or (
        chat_modelo_preset if chat_modelo_preset != MODELOS_OLLAMA_SUGERIDOS[0] else None
    )

    payload_chat = {
        "mensaje": pregunta,
        # El backend solo espera rol/contenido de turnos anteriores, sin el actual.
        "historial": [
            {"rol": t["rol"], "contenido": t["contenido"]}
            for t in st.session_state.chat_historial[:-1]
        ],
        "proveedor": chat_proveedor,
    }
    if chat_proveedor == "local" and chat_modelo_ollama:
        payload_chat["modelo_ollama"] = chat_modelo_ollama
    if chat_proveedor == "externo" and chat_modelo_externo:
        payload_chat["modelo_externo"] = chat_modelo_externo

    with st.chat_message("assistant"):
        with st.spinner("El asistente está pensando…"):
            try:
                resp = requests.post(f"{API_URL}/chat", json=payload_chat, timeout=60)
                if resp.status_code == 200:
                    data = resp.json()
                    respuesta_txt = data["respuesta"]
                    m = data["metricas"]
                    meta = (
                        f'{m["proveedor"].upper()} · {m["modelo"]} · ⏱ {m["latencia_ms"]} ms · '
                        f'💰 ${m["coste_estimado_usd"]} · 🔤 {m["tokens_entrada"]}+{m["tokens_salida"]} tokens'
                    )
                    st.markdown(respuesta_txt)
                    st.markdown(f'<p class="cm-caption">{meta}</p>', unsafe_allow_html=True)
                    st.session_state.chat_historial.append(
                        {"rol": "assistant", "contenido": respuesta_txt, "meta": meta}
                    )
                else:
                    detalle = resp.json()
                    st.error(f"⚠️ El asistente no pudo responder: {detalle}")
            except requests.RequestException as e:
                st.error(f"No se pudo contactar la API en `{API_URL}`: {e}")

st.divider()
st.markdown(
    '<p class="cm-caption">CivicMind — Proyecto I, Módulo V: AI Engineering. '
    "Motor de triaje asistido por LLM, type-safe y multi-proveedor.</p>",
    unsafe_allow_html=True,
)
