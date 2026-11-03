// Identidad del personal en desarrollo: cabecera X-Dev-User (ver backend
// app/core/auth.py). Se sustituira por el login OAuth institucional.
const CLAVE_DEV_USER = "pulso.devUser";

export function devUser(): string {
  try {
    return localStorage.getItem(CLAVE_DEV_USER) ?? "";
  } catch {
    return "";
  }
}

export function setDevUser(email: string): void {
  try {
    localStorage.setItem(CLAVE_DEV_USER, email);
  } catch {
    /* almacenamiento no disponible: la sesion dura lo que la pestana */
  }
}

export class ErrorApi extends Error {
  constructor(
    public estado: number,
    mensaje: string,
  ) {
    super(mensaje);
  }
}

export async function api<T>(ruta: string, opciones: RequestInit = {}, personal = true): Promise<T> {
  const cabeceras: Record<string, string> = { "Content-Type": "application/json" };
  if (personal && devUser()) cabeceras["X-Dev-User"] = devUser();
  const r = await fetch(ruta, { ...opciones, headers: { ...cabeceras, ...(opciones.headers ?? {}) } });
  if (!r.ok) {
    let detalle = r.statusText;
    try {
      const cuerpo = await r.json();
      detalle = typeof cuerpo.detail === "string" ? cuerpo.detail : JSON.stringify(cuerpo.detail);
    } catch {
      /* cuerpo no JSON */
    }
    if (r.status === 429) detalle += ` (reintentar en ${r.headers.get("Retry-After")} s)`;
    throw new ErrorApi(r.status, detalle);
  }
  return (r.status === 204 ? undefined : await r.json()) as T;
}

export const post = <T,>(ruta: string, cuerpo?: unknown, personal = true) =>
  api<T>(ruta, { method: "POST", body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo) }, personal);
