import { HEX_POR_NIVEL } from "./UrgencyBadge.jsx";
import { useI18n } from "../i18n/I18nContext.jsx";

function StatChip({ label, value }) {
  return (
    <div className="rounded-panel border border-ink-line bg-ink-panel px-4 py-3">
      <p className="text-xs text-paper-faint">{label}</p>
      <p className="mt-1 font-mono text-lg text-paper">{value}</p>
    </div>
  );
}

export default function HistoryTable({ historico, cargando, error }) {
  const { t, traducirCategoria, traducirUrgencia } = useI18n();
  const total = historico.length;
  const criticasAltas = historico.filter((h) =>
    ["critica", "alta"].includes(h?.triaje?.urgencia)
  ).length;
  const costeAcumulado = historico
    .reduce((acc, h) => acc + (h?.metricas?.coste_estimado_usd ?? 0), 0)
    .toFixed(4);

  return (
    <div>
      <h2 className="font-display text-base font-semibold text-paper">
        {t("historial.heading")}
      </h2>
      <p className="mt-1 text-xs text-paper-muted">{t("historial.subtitulo")}</p>

      {error && (
        <p className="mt-4 rounded-chip border border-signal-critica/40 bg-signal-critica/10 px-4 py-3 text-sm text-signal-critica">
          {t("historial.errorApi")}
        </p>
      )}

      {!error && !cargando && total === 0 && (
        <p className="mt-4 rounded-chip border border-ink-line bg-ink-panel px-4 py-3 text-sm text-paper-muted">
          {t("historial.vacio")}
        </p>
      )}

      {!error && total > 0 && (
        <>
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <StatChip label={t("historial.total")} value={total} />
            <StatChip label={t("historial.criticasAltas")} value={criticasAltas} />
            <StatChip label={t("historial.costeAcumulado")} value={`$${costeAcumulado}`} />
          </div>

          <div className="mt-4 overflow-x-auto rounded-panel border border-ink-line">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-ink-line bg-ink-panel text-xs text-paper-faint">
                  <th className="px-4 py-2.5 font-medium">{t("historial.colTexto")}</th>
                  <th className="px-4 py-2.5 font-medium">{t("historial.colCategoria")}</th>
                  <th className="px-4 py-2.5 font-medium">{t("historial.colUrgencia")}</th>
                  <th className="px-4 py-2.5 font-medium">{t("historial.colDepartamento")}</th>
                  <th className="px-4 py-2.5 font-medium">{t("historial.colProveedor")}</th>
                  <th className="px-4 py-2.5 text-right font-medium">{t("historial.colLatencia")}</th>
                  <th className="px-4 py-2.5 text-right font-medium">{t("historial.colCoste")}</th>
                </tr>
              </thead>
              <tbody>
                {historico.map((h, i) => {
                  const color = HEX_POR_NIVEL[h?.triaje?.urgencia] ?? "#2C3641";
                  return (
                    <tr
                      key={i}
                      className="border-b border-ink-line last:border-0 hover:bg-ink-panelAlt"
                      style={{ borderLeft: `3px solid ${color}` }}
                    >
                      <td className="max-w-xs truncate px-4 py-2.5 text-paper">
                        {h.texto}
                      </td>
                      <td className="px-4 py-2.5 text-paper-muted">
                        {traducirCategoria(h?.triaje?.categoria)}
                      </td>
                      <td className="px-4 py-2.5 text-paper-muted">
                        {traducirUrgencia(h?.triaje?.urgencia)}
                      </td>
                      <td className="px-4 py-2.5 text-paper-muted">
                        {h?.triaje?.departamento_asignado}
                      </td>
                      <td className="px-4 py-2.5 text-paper-muted">
                        {h?.metricas?.proveedor}/{h?.metricas?.modelo}
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono text-xs text-paper-muted">
                        {h?.metricas?.latencia_ms} ms
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono text-xs text-paper-muted">
                        ${h?.metricas?.coste_estimado_usd}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
