const PASOS = [
  {
    n: 1,
    titulo: "Reporte",
    detalle: "El texto libre del ciudadano llega tal cual, sin estructurar.",
  },
  {
    n: 2,
    titulo: "Thought",
    detalle: "El modelo razona en voz alta (Chain-of-Thought) sobre qué describe el texto.",
  },
  {
    n: 3,
    titulo: "Action",
    detalle: "Decide categoría, urgencia y departamento con ese razonamiento.",
  },
  {
    n: 4,
    titulo: "Observation",
    detalle: "La salida se valida contra un esquema estricto; si falla, se le pide corregir (2 reintentos).",
  },
  {
    n: 5,
    titulo: "Operador (HITL)",
    detalle: "Un humano ve el JSON y el razonamiento, y decide si lo valida o lo corrige.",
  },
];

export default function Sidebar() {
  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-ink-line bg-ink">
      <div className="flex items-center gap-2 border-b border-ink-line px-5 py-5">
        <img src="/logo-civicmind.svg" alt="" className="h-6 w-6" />
        <div>
          <p className="font-display text-sm font-semibold leading-none text-paper">
            CivicMind
          </p>
          <p className="mt-1 text-xs leading-none text-paper-faint">Triaje Urbano</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5">
        <p className="mb-4 text-xs font-medium text-paper-muted">
          Pipeline del motor de triaje
        </p>
        <ol className="relative space-y-5 border-l border-ink-line pl-5">
          {PASOS.map((paso) => (
            <li key={paso.n} className="relative">
              <span className="absolute -left-[27px] flex h-5 w-5 items-center justify-center rounded-full border border-ink-line bg-ink-panel font-mono text-[10px] text-paper-muted">
                {paso.n}
              </span>
              <p className="font-display text-sm font-medium text-paper">{paso.titulo}</p>
              <p className="mt-1 text-xs leading-relaxed text-paper-faint">{paso.detalle}</p>
            </li>
          ))}
        </ol>

        <div className="mt-8 rounded-panel border border-ink-line bg-ink-panel p-4">
          <p className="text-xs leading-relaxed text-paper-muted">
            El prompt de sistema instruye al modelo a ignorar género, origen, raza o
            barrio inferido del texto al fijar la urgencia. Es una mitigación a nivel de
            prompt, no una garantía — por eso la validación humana sigue siendo el
            último filtro.
          </p>
        </div>
      </div>
    </aside>
  );
}
