import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, post } from "../api/cliente";
import type { ElementoCatalogo, Encuesta, Plantilla } from "../api/tipos";

export default function NuevaEncuesta() {
  const navegar = useNavigate();
  const [plantillas, setPlantillas] = useState<Plantilla[]>([]);
  const [programas, setProgramas] = useState<ElementoCatalogo[]>([]);
  const [asignaturas, setAsignaturas] = useState<ElementoCatalogo[]>([]);
  const [cursos, setCursos] = useState<ElementoCatalogo[]>([]);
  const [f, setF] = useState({ plantilla_id: "", programa: "", asignatura: "", curso: "", apertura: "", cierre: "", umbral: "5" });
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api<Plantilla[]>("/api/plantillas").then((ps) => setPlantillas(ps.filter((p) => p.estado === "Publicada"))),
      api<ElementoCatalogo[]>("/api/catalogo/programas").then(setProgramas),
      api<ElementoCatalogo[]>("/api/catalogo/cursos-academicos").then(setCursos),
    ]).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (f.programa) api<ElementoCatalogo[]>(`/api/catalogo/programas/${f.programa}/asignaturas`).then(setAsignaturas);
  }, [f.programa]);

  const campo = (k: keyof typeof f) => ({
    value: f[k],
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value }),
  });

  async function crear(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const enc = await post<Encuesta>("/api/encuestas", {
        plantilla_id: Number(f.plantilla_id),
        celda_programa_id: Number(f.programa),
        celda_asignatura_id: Number(f.asignatura),
        celda_curso_academico_id: Number(f.curso),
        apertura: new Date(f.apertura).toISOString(),
        cierre: new Date(f.cierre).toISOString(),
        umbral_minimo: Number(f.umbral),
      });
      navegar(`/panel/encuestas/${enc.id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <form className="tarjeta" onSubmit={crear}>
      <h2>Nueva encuesta</h2>
      <label>Plantilla (publicada)</label>
      <select {...campo("plantilla_id")} required>
        <option value="" />
        {plantillas.map((p) => <option key={p.id} value={p.id}>{p.nombre} v{p.version}</option>)}
      </select>
      <label>Programa (CELDA)</label>
      <select {...campo("programa")} required>
        <option value="" />
        {programas.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
      </select>
      <label>Asignatura</label>
      <select {...campo("asignatura")} required>
        <option value="" />
        {asignaturas.map((a) => <option key={a.id} value={a.id}>{a.nombre}</option>)}
      </select>
      <label>Curso académico</label>
      <select {...campo("curso")} required>
        <option value="" />
        {cursos.map((c) => <option key={c.id} value={c.id}>{c.etiqueta}</option>)}
      </select>
      <label>Apertura</label>
      <input type="datetime-local" {...campo("apertura")} required />
      <label>Cierre</label>
      <input type="datetime-local" {...campo("cierre")} required />
      <label>Umbral mínimo de respuestas para publicar</label>
      <input type="number" min={1} {...campo("umbral")} required />
      <p><button type="submit">Crear</button></p>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
