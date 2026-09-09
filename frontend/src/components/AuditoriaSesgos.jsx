import { useState } from "react";
import { auditarSesgos } from "../api.js";
import UrgencyBadge from "./UrgencyBadge.jsx";

const inputClass =
  "w-full rounded-chip border border-ink-line bg-ink px-3 py-2 text-sm text-paper placeholder:text-paper-faint focus:border-action focus:outline-none";

const VARIANTE_VACIA = () => ({ etiqueta: "", texto: "" });

/**
 * Herramienta de fairness testing (criterio C10 del enunciado): el
 * operador escribe 2-4 variantes del MISMO hecho, cambiando solo el dato
 * demográfico/de zona que quiere auditar (ej. barrio, nombre asociado a un
 * origen, género del reportante). El backend corre las mismas variantes por
 * el mismo LLM y compara si la urgencia/categoría cambia — evidencia
 * empírica de si el prompt anti-sesgo se sostiene en la práctica.
 *
 * A propósito NO se genera el texto de las variantes automáticamente: es el
 * humano quien decide qué comparar, evitando que el propio sistema fabrique
 * caracterización demográfica.
 */
export default function AuditoriaSesgos() {
  const [variantes, setVariantes] = useState([VARIANTE_VACIA(), VARIANTE_VACIA()]);
  const [proveedor, setProveedor] = useState("local");
  const [modeloExterno, setModeloExterno] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  function actualizarVariante(i, campo, valor) {
    setVariantes((prev) => prev.map((v, idx) => (idx === i ? { ...v, [campo]: valor } : v)));
  }

  function agregarVariante() {
    if (variantes.length >= 4) return;
    setVariantes((prev) => [...prev, VARIANTE_VACIA()]);
  }

  function quitarVariante(i) {
    if (variantes.length <= 2) return;
    setVariantes((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const listas = variantes.filter((v) => v.etiqueta.trim() && v.texto.trim());
    if (listas.length < 2) {
      setError("Escribe al menos 2 variantes completas (etiqueta + texto).");
      return;
    }

    setEnviando(true);
    setError(null);
    setResultado(null);
    try {
      const data = await auditarSesgos({
        variantes: listas,
        proveedor,
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
      <h2 className="font-display text-base font-semibold text-paper">Auditoría de sesgos</h2>
      <p className="mt-1 text-xs leading-relaxed text-paper-faint">
        Escribe la misma incidencia en 2–4 variantes que solo cambien el barrio, origen o género
        mencionado. Si la urgencia cambia entre variantes, el sistema lo marca como posible sesgo.
      </p>

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        {variantes.map((v, i) => (
          <div key={i} className="rounded-chip border border-ink-line bg-ink p-3">
            <div className="flex items-center justify-between">
              <input
                className={`${inputClass} max-w-[10rem]`}
                placeholder={`Etiqueta (ej. Barrio ${String.fromCharCode(65 + i)})`}
                value={v.etiqueta}
                onChange={(e) => actualizarVariante(i, "etiqueta", e.target.value)}
              />
              {variantes.length > 2 && (
                <button
                  type="button"
                  onClick={() => quitarVariante(i)}
                  className="ml-2 text-xs text-paper-faint hover:text-signal-critica"
                >
                  Quitar
                </button>
              )}
            </div>
            <textarea
              className={`${inputClass} mt-2 h-16 resize-none`}
              placeholder="Texto de la incidencia para esta variante..."
              value={v.texto}
              onChange={(e) => actualizarVariante(i, "texto", e.target.value)}
            />
          </div>
        ))}

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={agregarVariante}
            disabled={variantes.length >= 4}
            className="rounded-chip border border-ink-line px-3 py-1.5 text-xs text-paper-muted hover:border-action hover:text-action disabled:opacity-40"
          >
            + Añadir variante
          </button>

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
            disabled={enviando}
            className="ml-auto rounded-chip bg-action px-4 py-2 text-sm font-medium text-ink hover:bg-action-hover disabled:opacity-50"
          >
            {enviando ? "Auditando…" : "Auditar sesgos"}
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
            className={`mb-3 rounded-chip border px-4 py-3 text-sm ${
              resultado.alerta
                ? "border-signal-critica/40 bg-signal-critica/10 text-signal-critica"
                : "border-signal-baja/40 bg-signal-baja/10 text-signal-baja"
            }`}
          >
            {resultado.alerta ?? "Sin divergencia: todas las variantes recibieron la misma urgencia y categoría."}
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {resultado.resultados.map((r) => (
              <div key={r.etiqueta} className="rounded-chip border border-ink-line bg-ink p-3">
                <p className="font-display text-sm font-medium text-paper">{r.etiqueta}</p>
                <div className="mt-2 flex items-center gap-2">
                  <UrgencyBadge nivel={r.triaje.urgencia} />
                  <span className="text-xs text-paper-muted">{r.triaje.categoria}</span>
                </div>
                <p className="mt-2 text-xs text-paper-muted">{r.triaje.resumen}</p>
                <p className="mt-2 text-xs leading-relaxed text-paper-faint">{r.triaje.razonamiento}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
