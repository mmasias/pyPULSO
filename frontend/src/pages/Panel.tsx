import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, devUser, setDevUser } from "../api/cliente";
import type { Encuesta, Yo } from "../api/tipos";

export default function Panel() {
  const [email, setEmail] = useState(devUser());
  const [yo, setYo] = useState<Yo | null>(null);
  const [encuestas, setEncuestas] = useState<Encuesta[]>([]);
  const [error, setError] = useState("");

  async function cargar() {
    setError("");
    try {
      setYo(await api<Yo>("/api/yo"));
      setEncuestas(await api<Encuesta[]>("/api/encuestas"));
    } catch (err) {
      setYo(null);
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    if (devUser()) void cargar();
  }, []);

  return (
    <>
      <div className="tarjeta">
        <label htmlFor="email">Identidad (solo desarrollo, sustituye al login institucional)</label>
        <input id="email" value={email} onChange={(e) => setEmail(e.target.value)} size={32} />
        <button
          onClick={() => {
            setDevUser(email.trim());
            void cargar();
          }}
        >
          Entrar
        </button>
        {yo && (
          <p className="tenue">
            {yo.email}: {[yo.es_gestor && "Gestor de calidad", yo.es_director && "Director de programa", yo.es_profesor && "Profesor"].filter(Boolean).join(", ") || "sin rol"}
          </p>
        )}
        {error && <p className="error">{error}</p>}
      </div>

      {yo?.es_gestor && (
        <p>
          <Link to="/panel/plantillas">Plantillas</Link> · <Link to="/panel/encuestas/nueva">Nueva encuesta</Link>
        </p>
      )}

      {yo && (
        <div className="tarjeta">
          <h2>Encuestas</h2>
          {!yo.es_gestor && <p className="tenue">Solo se muestran encuestas publicadas de sus asignaturas o programas.</p>}
          <table>
            <thead>
              <tr><th>Asignatura</th><th>Programa</th><th>Curso</th><th>Estado</th></tr>
            </thead>
            <tbody>
              {encuestas.map((e) => (
                <tr key={e.id}>
                  <td><Link to={`/panel/encuestas/${e.id}`}>{e.asignatura_nombre}</Link></td>
                  <td>{e.programa_nombre}</td>
                  <td>{e.curso_academico_etiqueta}</td>
                  <td>{e.estado}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
