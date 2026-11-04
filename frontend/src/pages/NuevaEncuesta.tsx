import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, post } from "../api/cliente";
import type { AsignaturaCatalogo, CursoCatalogo, Encuesta, Plantilla, ProgramaCatalogo } from "../api/tipos";

export default function NuevaEncuesta() {
  const navegar = useNavigate();
  const [plantillas, setPlantillas] = useState<Plantilla[]>([]);
  const [programas, setProgramas] = useState<ProgramaCatalogo[]>([]);
  const [asignaturas, setAsignaturas] = useState<AsignaturaCatalogo[]>([]);
  const [cursos, setCursos] = useState<CursoCatalogo[]>([]);
  const [f, setF] = useState({ plantilla_id: "", programa: "", asignatura: "", curso: "", apertura: "", cierre: "", umbral: "5" });
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api<Plantilla[]>("/api/plantillas").then((ps) => setPlantillas(ps.filter((p) => p.estado === "Publicada"))),
      api<ProgramaCatalogo[]>("/api/catalogo/programas").then(setProgramas),
      api<CursoCatalogo[]>("/api/catalogo/cursos-academicos").then(setCursos),
    ]).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (f.programa)
      api<AsignaturaCatalogo[]>(`/api/catalogo/programas/${f.programa}/asignaturas`).then((as) =>
        setAsignaturas(
          // La asignatura ENCUESTA (encuestas del programa entero) primero.
          [...as].sort((a, b) => Number(b.codigo === "ENC") - Number(a.codigo === "ENC") || a.codigo.localeCompare(b.codigo)),
        ),
      );
  }, [f.programa]);

  const niveles = [...new Set(programas.map((p) => p.nivel))];
  const programaElegido = programas.find((p) => String(p.id) === f.programa);
  const asignaturaElegida = asignaturas.find((a) => String(a.id) === f.asignatura);

  const campo = (k: keyof typeof f) => ({
    value: f[k],
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setF(k === "programa" ? { ...f, programa: e.target.value, asignatura: "" } : { ...f, [k]: e.target.value }),
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
      navegar(`/app/encuestas/${enc.id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <form className="tarjeta" onSubmit={crear}>
      <label>Plantilla (publicada)</label>
      <select {...campo("plantilla_id")} required>
        <option value="" />
        {plantillas.map((p) => <option key={p.id} value={p.id}>{p.nombre} v{p.version}</option>)}
      </select>
      <label>Programa</label>
      <select {...campo("programa")} required>
        <option value="" />
        {niveles.map((nivel) => (
          <optgroup key={nivel} label={nivel}>
            {programas.filter((p) => p.nivel === nivel).map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
          </optgroup>
        ))}
      </select>
      <label>Asignatura</label>
      <select {...campo("asignatura")} required disabled={!f.programa}>
        <option value="" />
        {asignaturas.map((a) => (
          <option key={a.id} value={a.id}>
            {a.codigo} · {a.nombre}{a.creditos !== null ? ` (${a.creditos} cr.)` : ""}
          </option>
        ))}
      </select>
      {asignaturaElegida?.codigo === "ENC" && (
        <p className="aviso-ambito">
          {programaElegido?.nivel === "Institucional"
            ? "Encuesta institucional: los resultados solo los ve el gestor de calidad."
            : "Encuesta del programa entero: los resultados los ven el gestor y la dirección de este programa. Las encuestas del personal administrativo y de la facultad van en los programas PAS y FACULTAD."}
        </p>
      )}
      <label>Curso académico</label>
      <select {...campo("curso")} required>
        <option value="" />
        {cursos.map((c) => <option key={c.id} value={c.id}>{c.etiqueta}{c.activo ? " (activo)" : ""}</option>)}
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
