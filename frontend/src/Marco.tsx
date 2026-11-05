import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function Titular({ titulo, subtitulo }: { titulo: string; subtitulo?: string }) {
  return (
    <section className="titular">
      <div className="titular-interior">
        <h1>{titulo}</h1>
        {subtitulo && <p>{subtitulo}</p>}
      </div>
    </section>
  );
}

export function Marco({ navegacion, inicio = "/", children }: { navegacion?: ReactNode; inicio?: string; children: ReactNode }) {
  return (
    <>
      <header className="cabecera">
        <div className="cabecera-interior">
          <Link to={inicio} className="marca" aria-label="PULSO, inicio">PULSO</Link>
          {navegacion}
        </div>
      </header>
      {children}
      <footer className="pie">
        <div className="pie-interior">
          <span>PULSO · Plataforma Unificada de Levantamiento y Seguimiento de Opiniones</span>
        </div>
      </footer>
    </>
  );
}
