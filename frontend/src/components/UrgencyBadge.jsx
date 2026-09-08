const COLOR_POR_NIVEL = {
  critica: "signal-critica",
  alta: "signal-alta",
  media: "signal-media",
  baja: "signal-baja",
};

const HEX_POR_NIVEL = {
  critica: "#E5484D",
  alta: "#F5A623",
  media: "#E8C547",
  baja: "#4CAF7D",
};

export default function UrgencyBadge({ nivel }) {
  const hex = HEX_POR_NIVEL[nivel] ?? "#8B95A1";
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-chip px-2.5 py-1 text-xs font-medium tracking-wide"
      style={{ background: `${hex}1A`, color: hex }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: hex }} />
      {nivel}
    </span>
  );
}

export { COLOR_POR_NIVEL, HEX_POR_NIVEL };
