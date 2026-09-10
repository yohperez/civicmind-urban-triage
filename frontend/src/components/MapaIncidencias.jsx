import { useEffect, useRef, useState } from "react";
import { listarIncidenciasGeo } from "../api.js";
import { HEX_POR_NIVEL } from "./UrgencyBadge.jsx";

/**
 * Mapa con las incidencias que tienen lat/lon (campo opcional en
 * IncidenciaRequest, ver backend/schemas.py). Usa Leaflet cargado por CDN
 * en index.html (window.L) en vez de react-leaflet, para no tocar
 * package.json ni requerir `npm install` de una librería nueva.
 *
 * Requisito: <link>/<script> de Leaflet en frontend/index.html (ya añadidos).
 */
export default function MapaIncidencias() {
  const contenedorRef = useRef(null);
  const mapaRef = useRef(null);
  const capaMarcadoresRef = useRef(null);
  const [incidencias, setIncidencias] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(false);

  // Inicializa el mapa una sola vez.
  useEffect(() => {
    if (!window.L || mapaRef.current || !contenedorRef.current) return;
    mapaRef.current = window.L.map(contenedorRef.current, {
      zoomControl: true,
      attributionControl: true,
    }).setView([40.4168, -3.7038], 12); // Madrid por defecto; se reencuadra al cargar datos

    window.L.tileLayer(
  "https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
  {
    attribution: "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
    maxZoom: 16,
  }
).addTo(mapaRef.current);

    capaMarcadoresRef.current = window.L.layerGroup().addTo(mapaRef.current);

    return () => {
      mapaRef.current?.remove();
      mapaRef.current = null;
    };
  }, []);

  async function cargar() {
    setCargando(true);
    try {
      const data = await listarIncidenciasGeo();
      setIncidencias(data);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    cargar();
  }, []);

  // Repinta los marcadores cada vez que cambian las incidencias.
  useEffect(() => {
    const mapa = mapaRef.current;
    const capa = capaMarcadoresRef.current;
    if (!mapa || !capa || !window.L) return;

    capa.clearLayers();
    const puntos = [];

    for (const inc of incidencias) {
      const color = HEX_POR_NIVEL[inc.triaje?.urgencia] ?? "#8B95A1";
      const marcador = window.L.circleMarker([inc.lat, inc.lon], {
        radius: 8,
        color,
        fillColor: color,
        fillOpacity: 0.85,
        weight: 2,
      });
      marcador.bindPopup(
        `<strong>${inc.triaje?.categoria ?? ""}</strong> · ${inc.triaje?.urgencia ?? ""}<br/>` +
          `${(inc.triaje?.resumen ?? "").replace(/</g, "&lt;")}<br/>` +
          `<span style="opacity:.7">${inc.triaje?.departamento_asignado ?? ""}</span>`
      );
      marcador.addTo(capa);
      puntos.push([inc.lat, inc.lon]);
    }

    if (puntos.length) {
      mapa.fitBounds(puntos, { padding: [30, 30], maxZoom: 15 });
    }
  }, [incidencias]);

  return (
    <section className="rounded-panel border border-ink-line bg-ink-panel p-5">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="font-display text-base font-semibold text-paper">Mapa de incidencias</h2>
          <p className="mt-1 text-xs text-paper-faint">
            Solo se muestran las incidencias enviadas con lat/lon. Color = nivel de urgencia.
          </p>
        </div>
        <button
          type="button"
          onClick={cargar}
          className="rounded-chip border border-ink-line px-3 py-1.5 text-xs text-paper-muted hover:border-action hover:text-action"
        >
          Actualizar
        </button>
      </div>

      {error && (
        <p className="mb-3 rounded-chip border border-signal-critica/40 bg-signal-critica/10 px-3 py-2 text-xs text-signal-critica">
          No se pudo cargar el mapa de incidencias.
        </p>
      )}
      {!error && !cargando && incidencias.length === 0 && (
        <p className="mb-3 text-xs text-paper-faint">
          Aún no hay incidencias con coordenadas. Envía una desde el formulario incluyendo lat/lon.
        </p>
      )}

      <div ref={contenedorRef} className="h-80 w-full overflow-hidden rounded-chip border border-ink-line" />
    </section>
  );
}
