/** @type {import('tailwindcss').Config} */

// Cada color se referencia como canales RGB en una variable CSS, para poder
// usar los modificadores de opacidad de Tailwind (bg-signal-critica/10) y a
// la vez soportar el toggle de tema: las variables cambian de valor con la
// clase `.light` en <html> (ver src/index.css), sin tocar ninguna clase de
// componente.
function conVariable(nombre) {
  return `rgb(var(${nombre}) / <alpha-value>)`;
}

export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: ["class"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: conVariable("--color-ink"), // fondo base
          panel: conVariable("--color-ink-panel"), // paneles / tarjetas
          panelAlt: conVariable("--color-ink-panel-alt"), // hover / fila alterna
          line: conVariable("--color-ink-line"), // bordes finos
        },
        paper: {
          DEFAULT: conVariable("--color-paper"), // texto primario
          muted: conVariable("--color-paper-muted"), // texto secundario
          faint: conVariable("--color-paper-faint"), // texto terciario / placeholders
        },
        signal: {
          critica: conVariable("--color-signal-critica"),
          alta: conVariable("--color-signal-alta"),
          media: conVariable("--color-signal-media"),
          baja: conVariable("--color-signal-baja"),
        },
        action: {
          DEFAULT: conVariable("--color-action"), // único acento interactivo — nunca de severidad
          hover: conVariable("--color-action-hover"),
          dim: conVariable("--color-action-dim"),
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'IBM Plex Sans'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      borderRadius: {
        panel: "10px",
        chip: "6px",
      },
    },
  },
  plugins: [],
};
