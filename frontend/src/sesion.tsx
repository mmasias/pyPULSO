import { useEffect, useState } from "react";
import { Navigate, NavLink, Outlet, useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { api, post } from "./api/cliente";
import type { Yo } from "./api/tipos";
import { Marco, Titular } from "./Marco";

export function useUsuario(): Yo {
  return useOutletContext<Yo>();
}

function roles(yo: Yo): string {
  return [yo.es_gestor && "Gestor de calidad", yo.es_director && "Director de programa", yo.es_profesor && "Profesor"]
    .filter(Boolean)
    .join(" · ");
}

function titular(ruta: string, yo: Yo): [string, string] {
  if (ruta.startsWith("/app/plantillas")) return ["Plantillas", "Catálogo institucional de cuestionarios"];
  if (ruta.startsWith("/app/encuestas/nueva")) return ["Nueva encuesta", "Sobre el catálogo académico de UNIB"];
  if (ruta.startsWith("/app/encuestas/")) return ["Encuesta", "Participación y resultados"];
  return ["Encuestas", yo.es_gestor ? "Todas las encuestas" : "Resultados publicados de sus asignaturas y programas"];
}

/** Zona privada: sin sesion valida, vuelve a la pagina de entrada. */
export function ZonaPrivada() {
  const [yo, setYo] = useState<Yo | null | undefined>(undefined);
  const navegar = useNavigate();
  const ruta = useLocation().pathname;

  useEffect(() => {
    api<Yo>("/api/yo").then(setYo, () => setYo(null));
  }, []);

  if (yo === undefined) return null;
  if (yo === null) return <Navigate to="/" replace />;

  async function salir() {
    await post("/api/auth/logout").catch(() => undefined);
    navegar("/", { replace: true });
  }

  const clase = ({ isActive }: { isActive: boolean }) => (isActive ? "activo" : "");
  const [titulo, subtitulo] = titular(ruta, yo);
  return (
    <Marco
      inicio="/app"
      navegacion={
        <div className="cabecera-derecha">
          <nav>
            <NavLink to="/app" end className={clase}>Encuestas</NavLink>
            {yo.es_gestor && <NavLink to="/app/plantillas" className={clase}>Plantillas</NavLink>}
          </nav>
          <div className="usuario">
            <span>
              {yo.email}
              <br />
              <small>{roles(yo)}</small>
            </span>
            <button className="secundario" onClick={salir}>Cerrar sesión</button>
          </div>
        </div>
      }
    >
      <Titular titulo={titulo} subtitulo={subtitulo} />
      <main>
        <Outlet context={yo} />
      </main>
    </Marco>
  );
}

/** Rutas solo para el gestor dentro de la zona privada. */
export function SoloGestor() {
  const yo = useUsuario();
  return yo.es_gestor ? <Outlet context={yo} /> : <Navigate to="/app" replace />;
}
