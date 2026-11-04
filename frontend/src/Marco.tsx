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
      <div className="barra-superior">
        <span>Universidad Internacional Iberoamericana · PULSO</span>
        <a href="https://www.unib.org" target="_blank" rel="noreferrer">unib.org</a>
      </div>
      <header className="cabecera">
        <div className="cabecera-interior">
          <Link to={inicio} aria-label="Inicio">
            <img src="/logo-unib.svg" alt="UNIB - Universidad Internacional Iberoamericana" />
          </Link>
          {navegacion}
        </div>
      </header>
      {children}
      <footer className="pie">
        <div className="pie-interior">
          <span>PULSO · Plataforma Unificada de Levantamiento y Seguimiento de Opiniones</span>
          <span>Universidad Internacional Iberoamericana · Arecibo, Puerto Rico</span>
        </div>
      </footer>
    </>
  );
}
