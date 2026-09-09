import { useState } from "react";
import { triarStream } from "../api.js";
import UrgencyBadge from "./UrgencyBadge.jsx";

const inputClass =
  "w-full rounded-chip border border-ink-line bg-ink px-3 py-2 text-sm text-paper placeholder:text-paper-faint focus:border-action focus:outline-none";

/**
 * Muestra el razonamiento del modelo apareciendo token a token (Server-Sent
 * Events, ver POST /triaje/stream), en vez de esperar en silencio a que el
 * JSON completo llegue. Pensado sobre todo para la demo en vivo de la
 * presentación oral: hace visible el ciclo ReAct (Thought/Action/
 * Observation) mientras ocurre.
 *
 * OJO: este modo no guarda en el histórico ni reintenta ante alucinaciones
 * (a diferencia de /triaje) — es un modo de inspección, no el flujo de
 * producción.
 */
export default function TriajeStreaming() {
  const [texto, setTexto] = useState("");
  const [proveedor, setProveedor] = useState("local");
  const [modeloExterno, setModeloExterno] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [textoEnVivo, setTextoEnVivo] = useState("");
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!texto.trim()) return;

    setStreaming(true);
    setTextoEnVivo("");
    setResultado(null);
    setError(null);

    try {
      await triarStream(
        {
          texto,
          proveedor,
          ...(proveedor === "externo" ? { modelo_externo: modeloExterno } : {}),
        },
        {
          onToken: (fragmento) => setTextoEnVivo((prev) => prev + fragmento),
          onResultado: (evento) => setResultado(evento),
          onError: (detalle) => setError(detalle),
        }
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setStreaming(false);
    }
  }

  return (
    <section className="rounded-panel border border-ink-line bg-ink-panel p-5">
      <h2 className="font-display text-base font-semibold text-paper">Razonamiento en vivo (streaming)</h2>
      <p className="mt-1 text-xs leading-relaxed text-paper-faint">
        Ve el ciclo ReAct (Thought → Action → Observation) del modelo apareciendo en tiempo real,
        antes de que se cierre en el JSON final.
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

          <button
            type="submit"
            disabled={streaming}
            className="ml-auto rounded-chip bg-action px-4 py-2 text-sm font-medium text-ink hover:bg-action-hover disabled:opacity-50"
          >
            {streaming ? "Razonando…" : "Triar en vivo"}
          </button>
        </div>
      </form>

      {(textoEnVivo || streaming) && (
        <pre className="mt-4 max-h-56 overflow-y-auto whitespace-pre-wrap rounded-chip border border-ink-line bg-ink p-3 font-mono text-xs text-paper-muted">
          {textoEnVivo}
          {streaming && <span className="animate-pulse text-action">▍</span>}
        </pre>
      )}

      {error && (
        <p className="mt-4 rounded-chip border border-signal-critica/40 bg-signal-critica/10 px-4 py-3 text-sm text-signal-critica">
          {error}
        </p>
      )}

      {resultado && (
        <div className="mt-4 rounded-chip border border-ink-line bg-ink p-3">
          <div className="flex items-center gap-2">
            <UrgencyBadge nivel={resultado.triaje.urgencia} />
            <span className="text-xs text-paper-muted">{resultado.triaje.categoria}</span>
            <span className="ml-auto text-xs text-paper-faint">
              {resultado.metricas.latencia_ms.toFixed(0)} ms
            </span>
          </div>
          <p className="mt-2 text-sm text-paper">{resultado.triaje.resumen}</p>
          <p className="mt-1 text-xs text-paper-faint">→ {resultado.triaje.departamento_asignado}</p>
        </div>
      )}
    </section>
  );
}
