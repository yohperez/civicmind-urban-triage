"""
Dashboard interactivo (Human-in-the-loop) para el motor de triaje.

Ejecutar con:
    streamlit run dashboard/app.py

Requiere que la API (backend/main.py) esté corriendo en paralelo.
"""

import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Triaje de Incidencias — HITL", layout="wide")
st.title("🚦 Motor de Triaje LLM — Panel de validación humana")

# --- Formulario de entrada ---
with st.form("nueva_incidencia"):
    texto = st.text_area("Descripción de la incidencia", height=100)
    col1, col2 = st.columns(2)
    with col1:
        proveedor = st.selectbox("Proveedor", ["local", "externo"])
    with col2:
        modelo_externo = st.text_input(
            "Modelo externo (si aplica)", placeholder="ej. gemini-2.0-flash"
        )
    comparar = st.checkbox("Comparar local vs. externo simultáneamente")
    enviado = st.form_submit_button("Procesar incidencia")

if enviado and texto.strip():
    payloads = []
    if comparar:
        payloads.append({"texto": texto, "proveedor": "local"})
        if modelo_externo:
            payloads.append({"texto": texto, "proveedor": "externo", "modelo_externo": modelo_externo})
    else:
        payload = {"texto": texto, "proveedor": proveedor}
        if proveedor == "externo":
            payload["modelo_externo"] = modelo_externo
        payloads.append(payload)

    resultados = []
    for p in payloads:
        try:
            resp = requests.post(f"{API_URL}/triaje", json=p, timeout=60)
            if resp.status_code == 200:
                resultados.append(resp.json())
            else:
                st.error(f"Error del modelo ({p['proveedor']}): {resp.json()}")
        except requests.RequestException as e:
            st.error(f"No se pudo contactar la API: {e}")

    cols = st.columns(len(resultados)) if resultados else []
    for col, r in zip(cols, resultados):
        with col:
            t, m = r["triaje"], r["metricas"]
            st.subheader(f"{m['proveedor']} — {m['modelo']}")
            st.metric("Urgencia", t["urgencia"].upper())
            st.write(f"**Categoría:** {t['categoria']}")
            st.write(f"**Departamento:** {t['departamento_asignado']}")
            st.write(f"**Resumen:** {t['resumen']}")
            with st.expander("🧠 Razonamiento del LLM (CoT/ReAct)"):
                st.write(t["razonamiento"])
            st.caption(
                f"⏱ {m['latencia_ms']} ms · 💰 ${m['coste_estimado_usd']} · "
                f"🔤 {m['tokens_entrada']}+{m['tokens_salida']} tokens · "
                f"🔁 {m['reintentos']} reintentos"
            )

st.divider()

# --- Histórico / validación humana ---
st.subheader("📋 Incidencias procesadas")
try:
    historico = requests.get(f"{API_URL}/incidencias", timeout=10).json()
    if historico:
        df = pd.json_normalize(historico)
        st.dataframe(df, use_container_width=True)
        # TODO: añadir botones de validar/rechazar por fila (HITL real,
        # ej. escribiendo a una tabla `validaciones` en base de datos).
    else:
        st.info("Aún no hay incidencias procesadas.")
except requests.RequestException:
    st.warning("No se pudo conectar con la API. ¿Está corriendo `uvicorn backend.main:app`?")
