import { useCallback, useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import IncidentForm from "./components/IncidentForm.jsx";
import ResultCards from "./components/ResultCards.jsx";
import HistoryTable from "./components/HistoryTable.jsx";
import ChatPanel from "./components/ChatPanel.jsx";
import { triar, listarIncidencias } from "./api.js";

export default function App() {
  const [resultados, setResultados] = useState([]);
  const [enviandoTriaje, setEnviandoTriaje] = useState(false);
  const [errorTriaje, setErrorTriaje] = useState(null);

  const [historico, setHistorico] = useState([]);
  const [cargandoHistorico, setCargandoHistorico] = useState(true);
  const [errorHistorico, setErrorHistorico] = useState(false);

  const recargarHistorico = useCallback(async () => {
    setCargandoHistorico(true);
    try {
      const data = await listarIncidencias();
      setHistorico(data);
      setErrorHistorico(false);
    } catch {
      setErrorHistorico(true);
    } finally {
      setCargandoHistorico(false);
    }
  }, []);

  useEffect(() => {
    recargarHistorico();
  }, [recargarHistorico]);

  async function handleSubmit(payloads) {
    setEnviandoTriaje(true);
    setErrorTriaje(null);
    const nuevos = [];
    for (const p of payloads) {
      try {
        const r = await triar(p);
        nuevos.push(r);
      } catch (err) {
        setErrorTriaje(
          `El modelo no pasó la validación type-safe (${p.proveedor}): ${err.message}`
        );
      }
    }
    setResultados(nuevos);
    setEnviandoTriaje(false);
    if (nuevos.length) recargarHistorico();
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <main className="flex-1 overflow-y-auto px-8 py-8">
        <header className="mb-8 max-w-3xl border-b border-ink-line pb-6">
          <h1 className="font-display text-2xl font-semibold text-paper">
            Panel de triaje — revisión humana
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-paper-muted">
            Un operador (Human-in-the-loop) revisa cómo el LLM clasifica cada
            incidencia — categoría, urgencia y departamento — junto con el
            razonamiento paso a paso que justificó la decisión, antes de darla por
            buena. Nada se registra a ciegas.
          </p>
        </header>

        <IncidentForm onSubmit={handleSubmit} enviando={enviandoTriaje} />

        {errorTriaje && (
          <p className="mt-4 rounded-chip border border-signal-critica/40 bg-signal-critica/10 px-4 py-3 text-sm text-signal-critica">
            {errorTriaje}
          </p>
        )}

        <ResultCards resultados={resultados} />

        <div className="my-8 border-t border-ink-line" />

        <HistoryTable
          historico={historico}
          cargando={cargandoHistorico}
          error={errorHistorico}
        />

        <p className="mt-10 text-xs text-paper-faint">
          CivicMind — Proyecto I, Módulo V: AI Engineering. Motor de triaje asistido
          por LLM, type-safe y multi-proveedor.
        </p>
      </main>

      <ChatPanel />
    </div>
  );
}
