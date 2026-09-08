/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#12181F", // fondo base
          panel: "#1B232C", // paneles / tarjetas
          panelAlt: "#212B35", // hover / fila alterna
          line: "#2C3641", // bordes finos
        },
        paper: {
          DEFAULT: "#EDEEEA", // texto primario
          muted: "#8B95A1", // texto secundario
          faint: "#5B6572", // texto terciario / placeholders
        },
        signal: {
          critica: "#E5484D",
          alta: "#F5A623",
          media: "#E8C547",
          baja: "#4CAF7D",
        },
        action: {
          DEFAULT: "#4FB8C9", // único acento interactivo — nunca de severidad
          hover: "#6FC9D8",
          dim: "#2E4B50",
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
