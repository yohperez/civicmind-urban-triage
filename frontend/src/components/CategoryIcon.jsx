const ICONOS = {
  infraestructura: { color: "#6366F1", path: "M2 20 L9 8 L16 20 Z M9 4 v3" },
  limpieza: { color: "#0EA5E9", path: "M6 3 h8 l-1 14 a2 2 0 0 1 -2 2 h-2 a2 2 0 0 1 -2 -2 Z" },
  seguridad: { color: "#F59E0B", path: "M10 2 L17 5 V11 C17 15 14 18 10 19 C6 18 3 15 3 11 V5 Z" },
  sanidad: { color: "#EF4444", path: "M10 3 v14 M3 10 h14" },
  transito: { color: "#8B5CF6", path: "M4 14 h12 M6 14 v3 M14 14 v3 M5 14 l1.5 -7 h7 L15 14" },
  otros: { color: "#64748B", path: "M10 3 a7 7 0 1 0 0.001 0 Z" },
};

export default function CategoryIcon({ categoria, size = 22 }) {
  const { color, path } = ICONOS[categoria] ?? ICONOS.otros;
  return (
    <svg width={size} height={size} viewBox="0 0 20 20">
      <circle cx="10" cy="10" r="10" fill={`${color}1A`} />
      <path
        d={path}
        stroke={color}
        strokeWidth="1.6"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
