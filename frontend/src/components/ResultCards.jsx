import { useState } from "react";
import UrgencyBadge, { HEX_POR_NIVEL } from "./UrgencyBadge.jsx";
import CategoryIcon from "./CategoryIcon.jsx";
import { useI18n } from "../i18n/I18nContext.jsx";

function ResultCard({ resultado }) {
  const { t, traducirCategoria } = useI18n();
  const [verRazonamiento, setVerRazonamiento] = useState(false);
  const { triaje: tr, metricas: m } = resultado;
  const borderColor = HEX_POR_NIVEL[tr.urgencia] ?? "#2C3641";

  return (
    <div
      className="rounded-panel border border-ink-line bg-ink-panel p-4"
      style={{ borderLeft: `3px solid ${borderColor}` }}
    >
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 text-sm font-medium text-paper">
          <CategoryIcon categoria={tr.categoria} />
          {m.proveedor.toUpperCase()} · {m.modelo}
        </span>
        <UrgencyBadge nivel={tr.urgencia} />
      </div>

      <dl className="mt-4 space-y-1.5 text-sm">
        <div className="flex gap-2">
          <dt className="w-28 shrink-0 text-paper-faint">{t("results.categoria")}</dt>
          <dd className="text-paper">{traducirCategoria(tr.categoria)}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-28 shrink-0 text-paper-faint">{t("results.departamento")}</dt>
          <dd className="text-paper">{tr.departamento_asignado}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-28 shrink-0 text-paper-faint">{t("results.resumen")}</dt>
          <dd className="text-paper">{tr.resumen}</dd>
        </div>
      </dl>

      <button
        onClick={() => setVerRazonamiento((v) => !v)}
        className="mt-3 text-xs font-medium text-action hover:text-action-hover"
      >
        {verRazonamiento ? t("results.ocultarRazonamiento") : t("results.verRazonamiento")}
      </button>
      {verRazonamiento && (
        <p className="mt-2 rounded-chip border border-ink-line bg-ink p-3 text-xs leading-relaxed text-paper-muted">
          {tr.razonamiento}
        </p>
      )}

      <p className="mt-3 font-mono text-[11px] text-paper-faint">
        {m.latencia_ms} ms · ${m.coste_estimado_usd} · {m.tokens_entrada}+{m.tokens_salida}{" "}
        {t("results.tokens")} · {m.reintentos} {t("results.reintentos")}
      </p>
    </div>
  );
}

export default function ResultCards({ resultados }) {
  const { t } = useI18n();
  if (!resultados.length) return null;
  return (
    <div className="mt-5">
      <h3 className="font-display text-sm font-semibold text-paper">{t("results.heading")}</h3>
      <div
        className={`mt-3 grid gap-4 ${
          resultados.length > 1 ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"
        }`}
      >
        {resultados.map((r, i) => (
          <ResultCard key={i} resultado={r} />
        ))}
      </div>
    </div>
  );
}
