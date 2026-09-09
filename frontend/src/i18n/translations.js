export const CATEGORIA_LABELS = {
  es: {
    infraestructura: "Infraestructura",
    limpieza: "Limpieza",
    seguridad: "Seguridad",
    sanidad: "Sanidad",
    transito: "Tránsito",
    otros: "Otros",
  },
  en: {
    infraestructura: "Infrastructure",
    limpieza: "Sanitation",
    seguridad: "Public safety",
    sanidad: "Health",
    transito: "Traffic",
    otros: "Other",
  },
};

export const URGENCIA_LABELS = {
  es: { critica: "crítica", alta: "alta", media: "media", baja: "baja" },
  en: { critica: "critical", alta: "high", media: "medium", baja: "low" },
};

const es = {
  sidebar: {
    tagline: "Triaje Urbano",
    pipelineLabel: "Pipeline del motor de triaje",
    biasNote:
      "El prompt de sistema instruye al modelo a ignorar género, origen, raza o " +
      "barrio inferido del texto al fijar la urgencia. Es una mitigación a nivel de " +
      "prompt, no una garantía — por eso la validación humana sigue siendo el " +
      "último filtro.",
    pasos: [
      { n: 1, titulo: "Reporte", detalle: "El texto libre del ciudadano llega tal cual, sin estructurar." },
      { n: 2, titulo: "Thought", detalle: "El modelo razona en voz alta (Chain-of-Thought) sobre qué describe el texto." },
      { n: 3, titulo: "Action", detalle: "Decide categoría, urgencia y departamento con ese razonamiento." },
      { n: 4, titulo: "Observation", detalle: "La salida se valida contra un esquema estricto; si falla, se le pide corregir (2 reintentos)." },
      { n: 5, titulo: "Operador (HITL)", detalle: "Un humano ve el JSON y el razonamiento, y decide si lo valida o lo corrige." },
    ],
  },
  app: {
    titulo: "Panel de triaje — revisión humana",
    subtitulo:
      "Un operador (Human-in-the-loop) revisa cómo el LLM clasifica cada " +
      "incidencia — categoría, urgencia y departamento — junto con el " +
      "razonamiento paso a paso que justificó la decisión, antes de darla por " +
      "buena. Nada se registra a ciegas.",
    errorPrefix: "El modelo no pasó la validación type-safe",
    footer: "CivicMind — Proyecto I, Módulo V: AI Engineering. Motor de triaje asistido por LLM, type-safe y multi-proveedor.",
  },
  form: {
    heading: "Nueva incidencia",
    placeholder: "Ej: Hay un socavón enorme en la calle principal, un coche casi cae dentro esta mañana.",
    proveedor: "Proveedor",
    proveedorLocal: "local (Ollama)",
    proveedorExterno: "externo (API comercial)",
    modeloExterno: "Modelo externo",
    modeloExternoPlaceholder: "ej. gemini-2.0-flash",
    comparar: "Comparar local vs. externo",
    ollamaLabel: "Modelo Ollama (proveedor local, on-premise o Cloud)",
    ollamaCustomPlaceholder: "…o escribe otro tag, ej. minimax-m2.7:cloud",
    submit: "Procesar incidencia",
    submitting: "Procesando…",
    ollamaDefault: "Usar OLLAMA_MODEL_DEFAULT del backend",
  },
  results: {
    heading: "Resultado",
    categoria: "Categoría",
    departamento: "Departamento",
    resumen: "Resumen",
    verRazonamiento: "Ver razonamiento (CoT/ReAct)",
    ocultarRazonamiento: "Ocultar razonamiento (CoT/ReAct)",
    reintentos: "reintentos",
    tokens: "tokens",
  },
  historial: {
    heading: "Incidencias procesadas",
    subtitulo: "Histórico servido por la API — volumen y distribución de urgencias del día, coste/latencia por proveedor.",
    errorApi: "No se pudo conectar con la API. ¿Está desplegado/corriendo el backend?",
    vacio: "Aún no hay incidencias procesadas. Envía la primera desde el formulario de arriba.",
    total: "Total procesadas",
    criticasAltas: "Críticas / Altas",
    costeAcumulado: "Coste acumulado",
    colTexto: "Texto",
    colCategoria: "Categoría",
    colUrgencia: "Urgencia",
    colDepartamento: "Departamento",
    colProveedor: "Proveedor",
    colLatencia: "Latencia",
    colCoste: "Coste",
  },
  chat: {
    heading: "Asistente CivicMind",
    proveedorBtn: "Proveedor",
    cerrarBtn: "Cerrar",
    descripcion: "Resuelve dudas sobre el pipeline o el criterio anti-sesgo — no vuelve a triar la incidencia.",
    proveedorLocal: "local (Ollama)",
    proveedorExterno: "externo (Gemini)",
    ollamaCustomPlaceholder: "…o escribe otro tag",
    vaciar: "Vaciar conversación",
    vacio: "Pregúntale algo al asistente de CivicMind…",
    pensando: "El asistente está pensando…",
    inputPlaceholder: "Escribe tu pregunta…",
    enviar: "Enviar",
    errorPrefix: "El asistente no pudo responder",
  },
};

const en = {
  sidebar: {
    tagline: "Urban Triage",
    pipelineLabel: "Triage engine pipeline",
    biasNote:
      "The system prompt instructs the model to ignore gender, origin, race, or " +
      "neighborhood inferred from the text when setting urgency. It's a " +
      "prompt-level mitigation, not a guarantee — that's why human review is " +
      "still the last filter.",
    pasos: [
      { n: 1, titulo: "Report", detalle: "The citizen's free-form text arrives as-is, unstructured." },
      { n: 2, titulo: "Thought", detalle: "The model reasons out loud (Chain-of-Thought) about what the text describes." },
      { n: 3, titulo: "Action", detalle: "Decides category, urgency, and department from that reasoning." },
      { n: 4, titulo: "Observation", detalle: "The output is validated against a strict schema; if it fails, it's asked to correct (2 retries)." },
      { n: 5, titulo: "Operator (HITL)", detalle: "A human sees the JSON and the reasoning, and decides whether to approve or correct it." },
    ],
  },
  app: {
    titulo: "Triage panel — human review",
    subtitulo:
      "A human operator (Human-in-the-loop) reviews how the LLM classifies each " +
      "incident — category, urgency, and department — along with the " +
      "step-by-step reasoning behind the decision, before approving it. " +
      "Nothing is logged blindly.",
    errorPrefix: "The model failed type-safe validation",
    footer: "CivicMind — Project I, Module V: AI Engineering. Type-safe, multi-provider LLM-assisted triage engine.",
  },
  form: {
    heading: "New incident",
    placeholder: "E.g.: There's a huge pothole on the main street, a car almost fell in this morning.",
    proveedor: "Provider",
    proveedorLocal: "local (Ollama)",
    proveedorExterno: "external (commercial API)",
    modeloExterno: "External model",
    modeloExternoPlaceholder: "e.g. gemini-2.0-flash",
    comparar: "Compare local vs. external",
    ollamaLabel: "Ollama model (local provider, on-premise or Cloud)",
    ollamaCustomPlaceholder: "…or type another tag, e.g. minimax-m2.7:cloud",
    submit: "Process incident",
    submitting: "Processing…",
    ollamaDefault: "Use backend's OLLAMA_MODEL_DEFAULT",
  },
  results: {
    heading: "Result",
    categoria: "Category",
    departamento: "Department",
    resumen: "Summary",
    verRazonamiento: "View reasoning (CoT/ReAct)",
    ocultarRazonamiento: "Hide reasoning (CoT/ReAct)",
    reintentos: "retries",
    tokens: "tokens",
  },
  historial: {
    heading: "Processed incidents",
    subtitulo: "History served by the API — today's volume and urgency distribution, cost/latency per provider.",
    errorApi: "Couldn't connect to the API. Is the backend deployed/running?",
    vacio: "No incidents processed yet. Send the first one from the form above.",
    total: "Total processed",
    criticasAltas: "Critical / High",
    costeAcumulado: "Accumulated cost",
    colTexto: "Text",
    colCategoria: "Category",
    colUrgencia: "Urgency",
    colDepartamento: "Department",
    colProveedor: "Provider",
    colLatencia: "Latency",
    colCoste: "Cost",
  },
  chat: {
    heading: "CivicMind Assistant",
    proveedorBtn: "Provider",
    cerrarBtn: "Close",
    descripcion: "Answers questions about the pipeline or the anti-bias criteria — it doesn't re-triage the incident.",
    proveedorLocal: "local (Ollama)",
    proveedorExterno: "external (Gemini)",
    ollamaCustomPlaceholder: "…or type another tag",
    vaciar: "Clear conversation",
    vacio: "Ask the CivicMind assistant something…",
    pensando: "The assistant is thinking…",
    inputPlaceholder: "Type your question…",
    enviar: "Send",
    errorPrefix: "The assistant couldn't respond",
  },
};

export const TRANSLATIONS = { es, en };
