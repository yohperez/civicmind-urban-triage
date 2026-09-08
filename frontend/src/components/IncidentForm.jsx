import { useState } from "react";

export const MODELOS_OLLAMA_SUGERIDOS = [
  { value: "", label: "Usar OLLAMA_MODEL_DEFAULT del backend" },
  { value: "gpt-oss:20b-cloud", label: "gpt-oss:20b-cloud" },
  { value: "gpt-oss:120b-cloud", label: "gpt-oss:120b-cloud" },
  { value: "gemma4:cloud", label: "gemma4:cloud" },
  { value: "gemma4:31b-cloud", label: "gemma4:31b-cloud" },
  { value: "qwen3.5:cloud", label: "qwen3.5:cloud" },
  { value: "deepseek-v4-flash:cloud", label: "deepseek-v4-flash:cloud" },
];

const inputClass =
  "w-full rounded-chip border border-ink-line bg-ink px-3 py-2 text-sm text-paper placeholder:text-paper-faint focus:border-action focus:outline-none";

export default function IncidentForm({ onSubmit, enviando }) {
  const [texto, setTexto] = useState("");
  const [proveedor, setProveedor] = useState("local");
  const [modeloExterno, setModeloExterno] = useState("");
  const [comparar, setComparar] = useState(false);
  const [modeloOllamaPreset, setModeloOllamaPreset] = useState("");
  const [modeloOllamaCustom, setModeloOllamaCustom] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!texto.trim()) return;

    const modeloOllama = modeloOllamaCustom.trim() || modeloOllamaPreset || undefined;

    const construirPayloadLocal = () => ({
      texto,
      proveedor: "local",
      ...(modeloOllama ? { modelo_ollama: modeloOllama } : {}),
    });

    const payloads = [];
    if (comparar) {
      payloads.push(construirPayloadLocal());
      if (modeloExterno) {
        payloads.push({ texto, proveedor: "externo", modelo_externo: modeloExterno });
      }
    } else if (proveedor === "local") {
      payloads.push(construirPayloadLocal());
    } else {
      payloads.push({ texto, proveedor: "externo", modelo_externo: modeloExterno });
    }

    onSubmit(payloads);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-panel border border-ink-line bg-ink-panel p-5"
    >
      <h2 className="font-display text-base font-semibold text-paper">Nueva incidencia</h2>

      <textarea
        className={`${inputClass} mt-4 h-24 resize-none`}
        placeholder="Ej: Hay un socavón enorme en la calle principal, un coche casi cae dentro esta mañana."
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
      />

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <label className="text-xs text-paper-muted">
          Proveedor
          <select
            className={`${inputClass} mt-1`}
            value={proveedor}
            onChange={(e) => setProveedor(e.target.value)}
            disabled={comparar}
          >
            <option value="local">local (Ollama)</option>
            <option value="externo">externo (API comercial)</option>
          </select>
        </label>

        <label className="text-xs text-paper-muted">
          Modelo externo
          <input
            className={`${inputClass} mt-1`}
            placeholder="ej. gemini-2.0-flash"
            value={modeloExterno}
            onChange={(e) => setModeloExterno(e.target.value)}
          />
        </label>

        <label className="flex items-end gap-2 pb-2 text-xs text-paper-muted">
          <input
            type="checkbox"
            className="h-4 w-4 accent-action"
            checked={comparar}
            onChange={(e) => setComparar(e.target.checked)}
          />
          Comparar local vs. externo
        </label>
      </div>

      <p className="mt-4 text-xs text-paper-faint">
        Modelo Ollama (proveedor local, on-premise o Cloud)
      </p>
      <div className="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-2">
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
          placeholder="…o escribe otro tag, ej. minimax-m2.7:cloud"
          value={modeloOllamaCustom}
          onChange={(e) => setModeloOllamaCustom(e.target.value)}
        />
      </div>

      <button
        type="submit"
        disabled={enviando || !texto.trim()}
        className="mt-5 w-full rounded-chip bg-action py-2.5 text-sm font-medium text-ink transition-colors hover:bg-action-hover disabled:cursor-not-allowed disabled:bg-ink-line disabled:text-paper-faint"
      >
        {enviando ? "Procesando…" : "Procesar incidencia"}
      </button>
    </form>
  );
}
