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

export async function listarIncidenciasGeo() {
  const resp = await fetch(`${API_URL}/incidencias/geo`);
  return parseOrThrow(resp);
}

export async function auditarSesgos(payload) {
  const resp = await fetch(`${API_URL}/auditoria-sesgos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseOrThrow(resp);
}

export async function evaluarConsistencia(payload) {
  const resp = await fetch(`${API_URL}/triaje/consistencia`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseOrThrow(resp);
}

/**
 * Consume POST /triaje/stream (Server-Sent Events sobre POST, por eso no se
 * usa el EventSource nativo del navegador -solo soporta GET-: se lee el
 * ReadableStream de fetch a mano y se parsean los bloques `data: {...}\n\n`).
 *
 * onToken(fragmentoTexto) se llama por cada trozo de razonamiento recibido.
 * onResultado({triaje, metricas}) se llama una vez, al final, si el JSON
 * acumulado valida. onError(detalle) se llama si el proveedor falla o el
 * JSON final no valida.
 */
export async function triarStream(payload, { onToken, onResultado, onError }) {
  const resp = await fetch(`${API_URL}/triaje/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!resp.ok || !resp.body) {
    await parseOrThrow(resp); // lanza con el detalle del error controlado
    return;
  }

  const lector = resp.body.getReader();
  const decodificador = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await lector.read();
    if (done) break;
    buffer += decodificador.decode(value, { stream: true });

    const bloques = buffer.split("\n\n");
    buffer = bloques.pop() ?? ""; // último bloque puede estar incompleto

    for (const bloque of bloques) {
      const linea = bloque.split("\n").find((l) => l.startsWith("data: "));
      if (!linea) continue;
      const evento = JSON.parse(linea.slice("data: ".length));

      if (evento.tipo === "token") onToken?.(evento.texto);
      else if (evento.tipo === "resultado") onResultado?.(evento);
      else if (evento.tipo === "error") onError?.(evento.detalle);
    }
  }
}

export { API_URL };
