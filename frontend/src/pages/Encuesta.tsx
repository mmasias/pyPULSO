import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, post } from "../api/cliente";
import type { Encuesta as TEncuesta, Participacion, Resultados, Yo } from "../api/tipos";

export default function Encuesta() {
  const { id } = useParams();
  const base = `/api/encuestas/${id}`;
  const [yo, setYo] = useState<Yo | null>(null);
  const [encuesta, setEncuesta] = useState<TEncuesta | null>(null);
  const [part, setPart] = useState<Participacion | null>(null);
  const [res, setRes] = useState<Resultados | null>(null);
  const [codigos, setCodigos] = useState<string[]>([]);
  const [cantidad, setCantidad] = useState("30");
  const [error, setError] = useState("");

  async function cargar() {
    const y = await api<Yo>("/api/yo");
    setYo(y);
    setEncuesta(await api<TEncuesta>(base));
    if (y.es_gestor) setPart(await api<Participacion>(`${base}/participacion`));
    setRes(await api<Resultados>(`${base}/resultados`));
  }

  useEffect(() => {
    cargar().catch((e) => setError(e.message));
  }, [id]);

  async function accion(fn: () => Promise<unknown>) {
    setError("");
    try {
      await fn();
      await cargar();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function descargar() {
    const blob = new Blob([codigos.join("\n") + "\n"], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `codigos-encuesta-${id}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  if (!encuesta) return <p className="error">{error}</p>;

  return (
    <>
      <div className="tarjeta">
        <h2>{encuesta.asignatura_nombre}</h2>
        <p className="tenue">
          {encuesta.programa_nombre} · {encuesta.curso_academico_etiqueta} · {encuesta.estado}
          <br />
          {new Date(encuesta.apertura).toLocaleString()} - {new Date(encuesta.cierre).toLocaleString()} · umbral {encuesta.umbral_minimo}
        </p>
        {error && <p className="error">{error}</p>}
      </div>

      {yo?.es_gestor && part && (
        <div className="tarjeta">
          <h3>Participación</h3>
          <p>
            {part.respuestas} respuestas de {part.codigos_emitidos} códigos emitidos ·{" "}
            <span className={part.alcanza_umbral ? "ok" : "error"}>{part.alcanza_umbral ? "alcanza" : "no alcanza"} el umbral</span>
          </p>
          {(encuesta.estado === "Borrador" || encuesta.estado === "Abierta") && (
            <p>
              <input type="number" min={1} max={1000} value={cantidad} onChange={(e) => setCantidad(e.target.value)} />
              <button onClick={() => accion(async () => setCodigos((await post<{ codigos: string[] }>(`${base}/codigos`, { cantidad: Number(cantidad) })).codigos))}>
                Emitir códigos
              </button>
            </p>
          )}
          {encuesta.estado === "Borrador" && <button onClick={() => accion(() => post(`${base}/abrir`))}>Abrir</button>}
          {encuesta.estado === "Abierta" && <button onClick={() => accion(() => post(`${base}/cerrar`))}>Cerrar</button>}
          {encuesta.estado === "Cerrada" && <button onClick={() => accion(() => post(`${base}/publicar`))}>Publicar resultados</button>}
        </div>
      )}

      {codigos.length > 0 && (
        <div className="tarjeta">
          <h3>Códigos emitidos ({codigos.length})</h3>
          <p className="error">Se muestran solo ahora: el sistema no los guarda en claro. Descárguelos antes de salir.</p>
          <button onClick={descargar}>Descargar .txt</button>
          <div className="codigos">{codigos.map((c) => <div key={c}>{c}</div>)}</div>
        </div>
      )}

      {res && (
        <div className="tarjeta">
          <h3>Resultados</h3>
          {!res.publicable ? (
            <p className="tenue">
              {res.respuestas} respuestas, por debajo del umbral ({res.umbral_minimo}). No se muestra ningún resultado.
            </p>
          ) : (
            res.preguntas.map((p) => (
              <div key={p.pregunta_id}>
                <h4>{p.orden}. {p.enunciado} <span className="tenue">(n={p.n})</span></h4>
                {p.media !== null && <p>Media: {p.media}</p>}
                {p.distribucion && (
                  <table>
                    <tbody>
                      {Object.entries(p.distribucion).map(([k, v]) => (
                        <tr key={k}><td>{k}</td><td>{v}</td></tr>
                      ))}
                    </tbody>
                  </table>
                )}
                {p.textos && <ul>{p.textos.map((t, i) => <li key={i}>{t}</li>)}</ul>}
              </div>
            ))
          )}
        </div>
      )}
    </>
  );
}
