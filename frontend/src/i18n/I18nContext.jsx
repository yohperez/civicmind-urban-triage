import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { TRANSLATIONS, CATEGORIA_LABELS, URGENCIA_LABELS } from "./translations.js";

const I18nContext = createContext(null);

function detectarIdiomaInicial() {
  if (typeof window === "undefined") return "es";
  const segmento = window.location.pathname.split("/").filter(Boolean)[0];
  if (segmento === "en" || segmento === "es") return segmento;
  const guardado = window.localStorage.getItem("civicmind-lang");
  return guardado === "en" ? "en" : "es";
}

function get(obj, path) {
  return path.split(".").reduce((acc, k) => (acc == null ? acc : acc[k]), obj);
}

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(detectarIdiomaInicial);

  useEffect(() => {
    document.documentElement.lang = lang;
    window.localStorage.setItem("civicmind-lang", lang);

    const partes = window.location.pathname.split("/").filter(Boolean);
    if (partes[0] === "es" || partes[0] === "en") {
      partes[0] = lang;
    } else {
      partes.unshift(lang);
    }
    const nuevaRuta = `/${partes.join("/")}`;
    if (nuevaRuta !== window.location.pathname) {
      window.history.replaceState(null, "", nuevaRuta + window.location.search);
    }
  }, [lang]);

  const setLang = useCallback((next) => {
    setLangState(next === "en" ? "en" : "es");
  }, []);

  const t = useCallback(
    (path) => {
      const valor = get(TRANSLATIONS[lang], path);
      return valor ?? get(TRANSLATIONS.es, path) ?? path;
    },
    [lang]
  );

  const traducirCategoria = useCallback(
    (categoria) => CATEGORIA_LABELS[lang]?.[categoria] ?? categoria,
    [lang]
  );

  const traducirUrgencia = useCallback(
    (urgencia) => URGENCIA_LABELS[lang]?.[urgencia] ?? urgencia,
    [lang]
  );

  const value = useMemo(
    () => ({ lang, setLang, t, traducirCategoria, traducirUrgencia }),
    [lang, setLang, t, traducirCategoria, traducirUrgencia]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n debe usarse dentro de <I18nProvider>");
  return ctx;
}
