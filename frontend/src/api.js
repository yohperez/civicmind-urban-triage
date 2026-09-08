// La URL del backend se fija en tiempo de BUILD (Vite), no en runtime como
// hacía Streamlit con os.getenv. Ver DEPLOY.md — hay que definir
// VITE_API_URL en Railway *antes* de que corra `npm run build`.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function parseOrThrow(resp) {
  if (resp.ok) return resp.json();
  let detalle;
  try {
    detalle = await resp.json();
  } catch {
    detalle = { error: "error_desconocido", detalle: resp.statusText };
  }
  const err = new Error(
    typeof detalle?.detail === "string"
      ? detalle.detail
      : JSON.stringify(detalle?.detail ?? detalle)
  );
  err.detalle = detalle;
  err.status = resp.status;
  throw err;
}

export async function triar(payload) {
  const resp = await fetch(`${API_URL}/triaje`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseOrThrow(resp);
}

export async function listarIncidencias() {
  const resp = await fetch(`${API_URL}/incidencias`);
  return parseOrThrow(resp);
}

export async function enviarMensajeChat(payload) {
  const resp = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseOrThrow(resp);
}

export { API_URL };
