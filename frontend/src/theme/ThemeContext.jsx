import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const ThemeContext = createContext(null);

function detectarTemaInicial() {
  if (typeof window === "undefined") return "dark";
  const guardado = window.localStorage.getItem("civicmind-theme");
  if (guardado === "light" || guardado === "dark") return guardado;
  const prefiereClaro =
    window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
  return prefiereClaro ? "light" : "dark";
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(detectarTemaInicial);

  useEffect(() => {
    document.documentElement.classList.toggle("light", theme === "light");
    document.documentElement.style.colorScheme = theme;
    window.localStorage.setItem("civicmind-theme", theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }, []);

  const value = useMemo(() => ({ theme, setTheme, toggleTheme }), [theme, toggleTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme debe usarse dentro de <ThemeProvider>");
  return ctx;
}
