import { useCallback, useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import IncidentForm from "./components/IncidentForm.jsx";
import ResultCards from "./components/ResultCards.jsx";
import HistoryTable from "./components/HistoryTable.jsx";
import ChatPanel from "./components/ChatPanel.jsx";
import MapaIncidencias from "./components/MapaIncidencias.jsx";
import AuditoriaSesgos from "./components/AuditoriaSesgos.jsx";
import TriajeStreaming from "./components/TriajeStreaming.jsx";
import ConsistenciaPanel from "./components/ConsistenciaPanel.jsx";
import { triar, listarIncidencias } from "./api.js";
import { useI18n } from "./i18n/I18nContext.jsx";

export default function App() {
  const { t } = useI18n();
  const [menuOpen, setMenuOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
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
        setErrorTriaje(`${t("app.errorPrefix")} (${p.proveedor}): ${err.message}`);
      }
    }
    setResultados(nuevos);
    setEnviandoTriaje(false);
    if (nuevos.length) recargarHistorico();
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />

      {/* Backdrop: shown on mobile whenever a drawer (menu or chat) is open. */}
      {(menuOpen || chatOpen) && (
        <div
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={() => {
            setMenuOpen(false);
            setChatOpen(false);
          }}
        />
      )}

      <main className="flex-1 overflow-y-auto px-4 py-5 sm:px-6 lg:px-8 lg:py-8">
        {/* Mobile-only top bar: hamburger for the pipeline sidebar, icon for the chat assistant. */}
        <div className="mb-5 flex items-center justify-between lg:hidden">
          <button
            type="button"
            onClick={() => setMenuOpen(true)}
            aria-label={t("nav.abrirMenu")}
            className="flex h-9 w-9 items-center justify-center rounded-chip border border-ink-line text-paper-muted"
          >
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <img src="/logo-mark.svg" alt="CivicMind" className="h-7 w-7" />
            <p className="font-display text-sm font-semibold text-paper">CivicMind</p>
          </div>
          <button
            type="button"
            onClick={() => setChatOpen(true)}
            aria-label={t("nav.abrirChat")}
            className="flex h-9 w-9 items-center justify-center rounded-chip border border-ink-line text-paper-muted"
          >
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <path
                d="M3 4.5h14a1 1 0 0 1 1 1V13a1 1 0 0 1-1 1H8l-3.5 3V14H3a1 1 0 0 1-1-1V5.5a1 1 0 0 1 1-1Z"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>

        <header className="mb-8 max-w-3xl border-b border-ink-line pb-6">
          <h1 className="font-display text-xl font-semibold text-paper sm:text-2xl">
            {t("app.titulo")}
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-paper-muted">
            {t("app.subtitulo")}
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

        <div className="my-8 border-t border-ink-line" />

        {/* Mejoras: mapa, streaming ReAct en vivo, auditoría de sesgos y self-consistency. */}
        <div className="space-y-6">
          <MapaIncidencias />
          <TriajeStreaming />
          <AuditoriaSesgos />
          <ConsistenciaPanel />
        </div>

        <p className="mt-10 text-xs text-paper-faint">{t("app.footer")}</p>
      </main>

      <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
}
