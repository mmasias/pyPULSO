import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/cliente";
import type { Encuesta } from "../api/tipos";
import { useUsuario } from "../sesion";

export default function Encuestas() {
  const yo = useUsuario();
  const [encuestas, setEncuestas] = useState<Encuesta[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Encuesta[]>("/api/encuestas").then(setEncuestas, (e) => setError(e.message));
  }, []);

  return (
    <>
      {yo.es_gestor && (
        <p className="fila-acciones">
          <Link to="/app/encuestas/nueva"><button>Nueva encuesta</button></Link>
          <Link to="/app/plantillas"><button className="secundario">Plantillas</button></Link>
        </p>
      )}
      {error && <p className="error">{error}</p>}
      <div className="tarjeta">
        {encuestas === null ? null : encuestas.length === 0 ? (
          <p className="tenue">
            {yo.es_gestor ? "Todavía no hay encuestas. Cree una plantilla y después una encuesta." : "No hay resultados publicados de sus asignaturas o programas."}
          </p>
        ) : (
          <table>
            <thead>
              <tr><th>Asignatura</th><th>Programa</th><th>Curso</th><th>Estado</th></tr>
            </thead>
            <tbody>
              {encuestas.map((e) => (
                <tr key={e.id}>
                  <td><Link to={`/app/encuestas/${e.id}`}>{e.asignatura_nombre}</Link></td>
                  <td>{e.programa_nombre}</td>
                  <td>{e.curso_academico_etiqueta}</td>
                  <td><span className={`etiqueta ${e.estado}`}>{e.estado}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
