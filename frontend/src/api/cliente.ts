// La identidad del personal viaja en una cookie de sesion httpOnly que emite
// el backend (/api/auth/login): el JavaScript de la pagina no la ve ni la
// guarda. Mismo origen gracias al proxy de Vite (vite.config.ts).

export class ErrorApi extends Error {
  constructor(
    public estado: number,
    mensaje: string,
  ) {
    super(mensaje);
  }
}

export async function api<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const r = await fetch(ruta, {
    ...opciones,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(opciones.headers ?? {}) },
  });
  if (!r.ok) {
    let detalle = r.statusText;
    try {
      const cuerpo = await r.json();
      detalle = typeof cuerpo.detail === "string" ? cuerpo.detail : "Datos no válidos";
    } catch {
      /* cuerpo no JSON */
    }
    if (r.status === 429) detalle += ` (reintentar en ${r.headers.get("Retry-After")} s)`;
    throw new ErrorApi(r.status, detalle);
  }
  return (r.status === 204 ? undefined : await r.json()) as T;
}

export const post = <T,>(ruta: string, cuerpo?: unknown) =>
  api<T>(ruta, { method: "POST", body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo) });
