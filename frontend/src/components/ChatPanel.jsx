import { useEffect, useRef, useState } from "react";
import { enviarMensajeChat } from "../api.js";
import { MODELOS_OLLAMA_SUGERIDOS } from "./IncidentForm.jsx";

const inputClass =
  "w-full rounded-chip border border-ink-line bg-ink px-2.5 py-1.5 text-xs text-paper focus:border-action focus:outline-none";

export default function ChatPanel() {
  const [historial, setHistorial] = useState([]); // [{rol, contenido, meta?}]
  const [pregunta, setPregunta] = useState("");
  const [pensando, setPensando] = useState(false);
  const [proveedor, setProveedor] = useState("local");
  const [modeloExterno, setModeloExterno] = useState("gemini-2.0-flash");
  const [modeloOllamaPreset, setModeloOllamaPreset] = useState("");
  const [modeloOllamaCustom, setModeloOllamaCustom] = useState("");
  const [mostrarConfig, setMostrarConfig] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [historial, pensando]);

  async function enviar(e) {
    e.preventDefault();
    const mensaje = pregunta.trim();
    if (!mensaje || pensando) return;

    const nuevoHistorial = [...historial, { rol: "user", contenido: mensaje }];
    setHistorial(nuevoHistorial);
    setPregunta("");
    setPensando(true);

    const modeloOllama = modeloOllamaCustom.trim() || modeloOllamaPreset || undefined;
    const payload = {
      mensaje,
      historial: historial.map((t) => ({ rol: t.rol, contenido: t.contenido })),
      proveedor,
      ...(proveedor === "local" && modeloOllama ? { modelo_ollama: modeloOllama } : {}),
      ...(proveedor === "externo" && modeloExterno ? { modelo_externo: modeloExterno } : {}),
    };

    try {
      const data = await enviarMensajeChat(payload);
      const m = data.metricas;
      const meta = `${m.proveedor.toUpperCase()} · ${m.modelo} · ${m.latencia_ms} ms · $${m.coste_estimado_usd} · ${m.tokens_entrada}+${m.tokens_salida} tokens`;
      setHistorial((h) => [...h, { rol: "assistant", contenido: data.respuesta, meta }]);
    } catch (err) {
      setHistorial((h) => [
        ...h,
        { rol: "assistant", contenido: `⚠️ El asistente no pudo responder: ${err.message}`, error: true },
      ]);
    } finally {
      setPensando(false);
    }
  }

  return (
    <aside className="flex h-full w-80 shrink-0 flex-col border-l border-ink-line bg-ink">
      <div className="border-b border-ink-line px-4 py-4">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-sm font-semibold text-paper">
            Asistente CivicMind
          </h2>
          <button
            onClick={() => setMostrarConfig((v) => !v)}
            className="text-xs text-paper-faint hover:text-action"
          >
            {mostrarConfig ? "Cerrar" : "Proveedor"}
          </button>
        </div>
        <p className="mt-1 text-xs leading-relaxed text-paper-faint">
          Resuelve dudas sobre el pipeline o el criterio anti-sesgo — no vuelve a triar
          la incidencia.
        </p>

        {mostrarConfig && (
          <div className="mt-3 space-y-2 rounded-chip border border-ink-line bg-ink-panel p-3">
            <select
              className={inputClass}
              value={proveedor}
              onChange={(e) => setProveedor(e.target.value)}
            >
              <option value="local">local (Ollama)</option>
              <option value="externo">externo (Gemini)</option>
            </select>
            {proveedor === "local" ? (
              <>
                <select
                  className={inputClass}
                  value={modeloOllamaPreset}
                  onChange={(e) => setModeloOllamaPreset(e.target.value)}
                >
                  {MODELOS_OLLAMA_SUGERIDOS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
                <input
                  className={inputClass}
                  placeholder="…o escribe otro tag"
                  value={modeloOllamaCustom}
                  onChange={(e) => setModeloOllamaCustom(e.target.value)}
                />
              </>
            ) : (
              <input
                className={inputClass}
                value={modeloExterno}
                onChange={(e) => setModeloExterno(e.target.value)}
              />
            )}
            <button
              onClick={() => setHistorial([])}
              className="text-xs text-paper-faint hover:text-signal-critica"
            >
              Vaciar conversación
            </button>
          </div>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {historial.length === 0 && (
          <p className="text-xs text-paper-faint">
            Pregúntale algo al asistente de CivicMind…
          </p>
        )}
        {historial.map((turno, i) => (
          <div
            key={i}
            className={`rounded-panel px-3 py-2 text-sm ${
              turno.rol === "user"
                ? "ml-6 bg-action/15 text-paper"
                : turno.error
                ? "mr-2 border border-signal-critica/40 bg-signal-critica/10 text-signal-critica"
                : "mr-2 border border-ink-line bg-ink-panel text-paper"
            }`}
          >
            <p className="whitespace-pre-wrap leading-relaxed">{turno.contenido}</p>
            {turno.meta && (
              <p className="mt-1.5 font-mono text-[10px] text-paper-faint">{turno.meta}</p>
            )}
          </div>
        ))}
        {pensando && (
          <div className="mr-2 rounded-panel border border-ink-line bg-ink-panel px-3 py-2 text-xs text-paper-faint">
            El asistente está pensando…
          </div>
        )}
      </div>

      <form onSubmit={enviar} className="border-t border-ink-line p-3">
        <div className="flex gap-2">
          <input
            className={`${inputClass} flex-1`}
            placeholder="Escribe tu pregunta…"
            value={pregunta}
            onChange={(e) => setPregunta(e.target.value)}
          />
          <button
            type="submit"
            disabled={pensando || !pregunta.trim()}
            className="rounded-chip bg-action px-3 py-1.5 text-xs font-medium text-ink hover:bg-action-hover disabled:cursor-not-allowed disabled:bg-ink-line disabled:text-paper-faint"
          >
            Enviar
          </button>
        </div>
      </form>
    </aside>
  );
}
