import { useState } from "react";
import { evaluarConsistencia } from "../api.js";
import UrgencyBadge from "./UrgencyBadge.jsx";

const inputClass =
  "w-full rounded-chip border border-ink-line bg-ink px-3 py-2 text-sm text-paper placeholder:text-paper-faint focus:border-action focus:outline-none";

/**
 * Corre la MISMA incidencia N veces (POST /triaje/consistencia) y muestra
 * si el modelo es determinista en la práctica. Un acuerdo bajo es una señal
 * para el operador HITL de que esa incidencia necesita revisión manual más
 * cuidadosa en vez de confiar en una única pasada del LLM.
 */
export default function ConsistenciaPanel() {
  const [texto, setTexto] = useState("");
  const [proveedor, setProveedor] = useState("local");
  const [modeloExterno, setModeloExterno] = useState("");
  const [repeticiones, setRepeticiones] = useState(3);
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!texto.trim()) return;

    setEnviando(true);
    setError(null);
    setResultado(null);
    try {
      const data = await evaluarConsistencia({
        texto,
        proveedor,
        repeticiones: Number(repeticiones),
        ...(proveedor === "externo" ? { modelo_externo: modeloExterno } : {}),
      });
      setResultado(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section className="rounded-panel border border-ink-line bg-ink-panel p-5">
      <h2 className="font-display text-base font-semibold text-paper">Fiabilidad (self-consistency)</h2>
      <p className="mt-1 text-xs leading-relaxed text-paper-faint">
        Repite el mismo texto varias veces contra el modelo. Si la clasificación cambia entre
        repeticiones, es una señal de que el operador debería revisarla con más cuidado.
      </p>

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <textarea
          className={`${inputClass} h-20 resize-none`}
          placeholder="Describe la incidencia..."
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
        />

        <div className="flex flex-wrap items-center gap-3">
          <select
            className={`${inputClass} w-auto`}
            value={proveedor}
            onChange={(e) => setProveedor(e.target.value)}
          >
            <option value="local">Ollama (local)</option>
            <option value="externo">Externo (Gemini)</option>
          </select>

          {proveedor === "externo" && (
            <input
              className={`${inputClass} w-auto`}
              placeholder="gemini-2.0-flash"
              value={modeloExterno}
              onChange={(e) => setModeloExterno(e.target.value)}
            />
          )}

          <label className="flex items-center gap-2 text-xs text-paper-muted">
            Repeticiones
            <select
              className={`${inputClass} w-16`}
              value={repeticiones}
              onChange={(e) => setRepeticiones(e.target.value)}
            >
              {[2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>

          <button
            type="submit"
            disabled={enviando}
            className="ml-auto rounded-chip bg-action px-4 py-2 text-sm font-medium text-ink hover:bg-action-hover disabled:opacity-50"
          >
            {enviando ? "Evaluando…" : "Evaluar consistencia"}
          </button>
        </div>
      </form>

      {error && (
        <p className="mt-4 rounded-chip border border-signal-critica/40 bg-signal-critica/10 px-4 py-3 text-sm text-signal-critica">
          {error}
        </p>
      )}

      {resultado && (
        <div className="mt-5">
          <div
            className={`mb-3 flex flex-wrap items-center gap-3 rounded-chip border px-4 py-3 text-sm ${
              resultado.es_consistente
                ? "border-signal-baja/40 bg-signal-baja/10 text-signal-baja"
                : "border-signal-media/40 bg-signal-media/10 text-signal-media"
            }`}
          >
            <span>
              {resultado.es_consistente
                ? "Consistente: mismo resultado en todas las repeticiones."
                : "Inconsistente: el modelo varió entre repeticiones."}
            </span>
            <span className="ml-auto font-mono text-xs">
              urgencia {Math.round(resultado.acuerdo_urgencia * 100)}% · categoría{" "}
              {Math.round(resultado.acuerdo_categoria * 100)}%
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {resultado.ejecuciones.map((t, i) => (
              <div key={i} className="rounded-chip border border-ink-line bg-ink px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] text-paper-faint">#{i + 1}</span>
                  <UrgencyBadge nivel={t.urgencia} />
                  <span className="text-xs text-paper-muted">{t.categoria}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
