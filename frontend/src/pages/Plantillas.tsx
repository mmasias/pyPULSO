import { useEffect, useState } from "react";
import { api, post } from "../api/cliente";
import type { Plantilla, TipoPregunta } from "../api/tipos";

export default function Plantillas() {
  const [plantillas, setPlantillas] = useState<Plantilla[]>([]);
  const [nombre, setNombre] = useState("");
  const [error, setError] = useState("");

  const cargar = async () => setPlantillas(await api<Plantilla[]>("/api/plantillas"));
  useEffect(() => {
    cargar().catch((e) => setError(e.message));
  }, []);

  async function accion(fn: () => Promise<unknown>) {
    setError("");
    try {
      await fn();
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <h2>Plantillas</h2>
      {error && <p className="error">{error}</p>}
      <div className="tarjeta">
        <label htmlFor="nombre">Nueva plantilla</label>
        <input id="nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} size={40} />
        <button onClick={() => accion(() => post("/api/plantillas", { nombre }))}>Crear</button>
      </div>
      {plantillas.map((p) => (
        <FichaPlantilla key={p.id} plantilla={p} accion={accion} />
      ))}
    </>
  );
}

function FichaPlantilla({ plantilla, accion }: { plantilla: Plantilla; accion: (fn: () => Promise<unknown>) => void }) {
  const [enunciado, setEnunciado] = useState("");
  const [tipo, setTipo] = useState<TipoPregunta>("likert5");
  const [opciones, setOpciones] = useState("");
  const base = `/api/plantillas/${plantilla.id}`;

  return (
    <div className="tarjeta">
      <h3>
        {plantilla.nombre} <span className="tenue">v{plantilla.version} · {plantilla.estado}</span>
      </h3>
      <ol>
        {plantilla.preguntas.map((q) => (
          <li key={q.id}>
            {q.enunciado} <span className="tenue">[{q.tipo}{q.opciones.length ? `: ${q.opciones.join(" / ")}` : ""}]</span>
          </li>
        ))}
      </ol>
      {plantilla.estado === "Borrador" ? (
        <>
          <input placeholder="Enunciado" value={enunciado} onChange={(e) => setEnunciado(e.target.value)} size={40} />
          <select value={tipo} onChange={(e) => setTipo(e.target.value as TipoPregunta)}>
            <option value="likert5">Escala 1-5</option>
            <option value="opcion_unica">Opción única</option>
            <option value="texto_libre">Texto libre</option>
          </select>
          {tipo === "opcion_unica" && (
            <input placeholder="Opciones separadas por ;" value={opciones} onChange={(e) => setOpciones(e.target.value)} />
          )}
          <button
            onClick={() =>
              accion(() =>
                post(`${base}/preguntas`, {
                  enunciado,
                  tipo,
                  obligatoria: tipo !== "texto_libre",
                  opciones: tipo === "opcion_unica" ? opciones.split(";").map((s) => s.trim()).filter(Boolean) : [],
                }),
              )
            }
          >
            Añadir pregunta
          </button>
          <p>
            <button onClick={() => accion(() => post(`${base}/publicar`))}>Publicar</button>
            <span className="tenue">Una plantilla publicada no se modifica: se versiona.</span>
          </p>
        </>
      ) : (
        <p>
          <button onClick={() => accion(() => post(`${base}/nueva-version`))}>Nueva versión</button>
          {plantilla.estado === "Publicada" && <button onClick={() => accion(() => post(`${base}/archivar`))}>Archivar</button>}
        </p>
      )}
    </div>
  );
}
