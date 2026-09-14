import { useEffect, useRef, useState } from "react";
import { enviarMensajeChat } from "../api.js";
import { MODELOS_OLLAMA_SUGERIDOS_TAGS } from "./IncidentForm.jsx";
import { useI18n } from "../i18n/I18nContext.jsx";

const inputClass =
  "w-full rounded-chip border border-ink-line bg-ink px-2.5 py-1.5 text-xs text-paper focus:border-action focus:outline-none";

export default function ChatPanel({ open = false, onClose = () => {} }) {
  const { t } = useI18n();
  const [historial, setHistorial] = useState([]); // [{rol, contenido, meta?}]
  const [pregunta, setPregunta] = useState("");
  const [pensando, setPensando] = useState(false);
  const [proveedor, setProveedor] = useState("local");
  const [modeloExterno, setModeloExterno] = useState("gemini-2.0-flash");
  const [modeloOllamaPreset, setModeloOllamaPreset] = useState("");
  const [modeloOllamaCustom, setModeloOllamaCustom] = useState("");
  const [mostrarConfig, setMostrarConfig] = useState(false);
  const scrollRef = useRef(null);

  const MODELOS_OLLAMA_SUGERIDOS = MODELOS_OLLAMA_SUGERIDOS_TAGS.map((value) => ({
    value,
    label: value || t("form.ollamaDefault"),
  }));

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
      historial: historial.map((turno) => ({ rol: turno.rol, contenido: turno.contenido })),
      proveedor,
      ...(proveedor === "local" && modeloOllama ? { modelo_ollama: modeloOllama } : {}),
      ...(proveedor === "externo" && modeloExterno ? { modelo_externo: modeloExterno } : {}),
    };

    try {
      const data = await enviarMensajeChat(payload);
      const m = data.metricas;
      const meta = `${m.proveedor.toUpperCase()} · ${m.modelo} · ${m.latencia_ms} ms · $${m.coste_estimado_usd} · ${m.tokens_entrada}+${m.tokens_salida} ${t("results.tokens")}`;
      setHistorial((h) => [...h, { rol: "assistant", contenido: data.respuesta, meta }]);
    } catch (err) {
      setHistorial((h) => [
        ...h,
        { rol: "assistant", contenido: `⚠️ ${t("chat.errorPrefix")}: ${err.message}`, error: true },
      ]);
    } finally {
      setPensando(false);
    }
  }

  return (
    <aside
      className={`fixed inset-y-0 right-0 z-40 flex h-full w-[85vw] max-w-sm shrink-0 translate-x-full flex-col border-l border-ink-line bg-ink transition-transform duration-200 ease-out lg:static lg:z-auto lg:w-80 lg:max-w-none lg:translate-x-0 ${
        open ? "translate-x-0" : ""
      }`}
    >
      <div className="border-b border-ink-line px-4 py-4">
        <div className="flex items-center justify-between gap-2">
          <h2 className="font-display text-sm font-semibold text-paper">
            {t("chat.heading")}
          </h2>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMostrarConfig((v) => !v)}
              className="text-xs text-paper-faint hover:text-action"
            >
              {mostrarConfig ? t("chat.cerrarBtn") : t("chat.proveedorBtn")}
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label={t("nav.cerrarChat")}
              className="flex h-[22px] w-[22px] items-center justify-center rounded-chip border border-ink-line text-paper-muted lg:hidden"
            >
              <svg width="11" height="11" viewBox="0 0 20 20" fill="none">
                <path d="M4 4l12 12M16 4 4 16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        </div>
        <p className="mt-1 text-xs leading-relaxed text-paper-faint">
          {t("chat.descripcion")}
        </p>

        {mostrarConfig && (
          <div className="mt-3 space-y-2 rounded-chip border border-ink-line bg-ink-panel p-3">
            <select
              className={inputClass}
              value={proveedor}
              onChange={(e) => setProveedor(e.target.value)}
            >
              <option value="local">{t("chat.proveedorLocal")}</option>
              <option value="externo">{t("chat.proveedorExterno")}</option>
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
                  placeholder={t("chat.ollamaCustomPlaceholder")}
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
              {t("chat.vaciar")}
            </button>
          </div>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {historial.length === 0 && (
          <p className="text-xs text-paper-faint">{t("chat.vacio")}</p>
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
            {t("chat.pensando")}
          </div>
        )}
      </div>

      <form onSubmit={enviar} className="border-t border-ink-line p-3">
        <div className="flex gap-2">
          <input
            className={`${inputClass} flex-1`}
            placeholder={t("chat.inputPlaceholder")}
            value={pregunta}
            onChange={(e) => setPregunta(e.target.value)}
          />
          <button
            type="submit"
            disabled={pensando || !pregunta.trim()}
            className="rounded-chip bg-action px-3 py-1.5 text-xs font-medium text-ink hover:bg-action-hover disabled:cursor-not-allowed disabled:bg-ink-line disabled:text-paper-faint"
          >
            {t("chat.enviar")}
          </button>
        </div>
      </form>
    </aside>
  );
}
