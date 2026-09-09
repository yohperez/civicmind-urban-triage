import { useI18n } from "../i18n/I18nContext.jsx";
import { useTheme } from "../theme/ThemeContext.jsx";

export default function Sidebar() {
  const { t } = useI18n();
  const pasos = t("sidebar.pasos");

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-ink-line bg-ink">
      <div className="flex items-center justify-between gap-2 border-b border-ink-line px-5 py-5">
        <div className="flex items-center gap-2.5">
          <img src="/logo-mark.svg" alt="CivicMind" className="h-9 w-9 shrink-0" />
          <div>
            <p className="font-display text-sm font-semibold leading-none text-paper">
              CivicMind
            </p>
            <p className="mt-1 text-xs leading-none text-paper-faint">
              {t("sidebar.tagline")}
            </p>
          </div>
        </div>
        <PreferenceToggles />
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5">
        <p className="mb-4 text-xs font-medium text-paper-muted">
          {t("sidebar.pipelineLabel")}
        </p>
        <ol className="relative space-y-5 border-l border-ink-line pl-5">
          {pasos.map((paso) => (
            <li key={paso.n} className="relative">
              <span className="absolute -left-[27px] flex h-5 w-5 items-center justify-center rounded-full border border-ink-line bg-ink-panel font-mono text-[10px] text-paper-muted">
                {paso.n}
              </span>
              <p className="font-display text-sm font-medium text-paper">{paso.titulo}</p>
              <p className="mt-1 text-xs leading-relaxed text-paper-faint">{paso.detalle}</p>
            </li>
          ))}
        </ol>

        <div className="mt-8 rounded-panel border border-ink-line bg-ink-panel p-4">
          <p className="text-xs leading-relaxed text-paper-muted">
            {t("sidebar.biasNote")}
          </p>
        </div>
      </div>
    </aside>
  );
}

function PreferenceToggles() {
  const { lang, setLang } = useI18n();
  const { theme, toggleTheme } = useTheme();
  const otherLang = lang === "es" ? "en" : "es";

  return (
    <div className="flex shrink-0 items-center gap-1">
      <button
        type="button"
        onClick={() => setLang(otherLang)}
        title={otherLang === "es" ? "Cambiar a español" : "Switch to English"}
        aria-label={otherLang === "es" ? "Cambiar a español" : "Switch to English"}
        className="rounded-chip border border-ink-line px-2 py-1 font-mono text-[10px] font-medium uppercase tracking-wide text-paper-muted transition-colors hover:border-action hover:text-action"
      >
        {lang}
      </button>
      <button
        type="button"
        onClick={toggleTheme}
        title={theme === "dark" ? "Light mode" : "Dark mode"}
        aria-label={theme === "dark" ? "Light mode" : "Dark mode"}
        className="flex h-[26px] w-[26px] items-center justify-center rounded-chip border border-ink-line text-paper-muted transition-colors hover:border-action hover:text-action"
      >
        {theme === "dark" ? (
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <path
              d="M17 10.6A7.2 7.2 0 0 1 9.4 3a7.2 7.2 0 1 0 7.6 7.6Z"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        ) : (
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="4" stroke="currentColor" strokeWidth="1.6" />
            <path
              d="M10 1.5v2M10 16.5v2M18.5 10h-2M3.5 10h-2M15.6 4.4l-1.4 1.4M5.8 14.2l-1.4 1.4M15.6 15.6l-1.4-1.4M5.8 5.8 4.4 4.4"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
            />
          </svg>
        )}
      </button>
    </div>
  );
}
