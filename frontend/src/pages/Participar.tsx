import { useState } from "react";
import { post } from "../api/cliente";
import type { Formulario, Pregunta } from "../api/tipos";

type Valor = { entero?: number; texto?: string };

export default function Participar() {
  const [codigo, setCodigo] = useState("");
  const [formulario, setFormulario] = useState<Formulario | null>(null);
  const [valores, setValores] = useState<Record<number, Valor>>({});
  const [error, setError] = useState("");
  const [enviado, setEnviado] = useState(false);

  async function acceder(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      setFormulario(await post<Formulario>("/api/participacion/acceder", { codigo }, false));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const items = formulario!.preguntas
      .filter((p) => valores[p.id] !== undefined)
      .map((p) =>
        p.tipo === "texto_libre"
          ? { pregunta_id: p.id, valor_texto: valores[p.id].texto ?? "" }
          : { pregunta_id: p.id, valor_entero: valores[p.id].entero },
      );
    try {
      await post("/api/participacion/enviar", { codigo, items }, false);
      setEnviado(true);
      setCodigo("");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const fijar = (id: number, v: Valor) => setValores({ ...valores, [id]: v });

  if (enviado) {
    return (
      <div className="tarjeta">
        <h2>Respuesta registrada</h2>
        <p>El código ha quedado inutilizado. La respuesta se guarda sin ningún dato que la relacione con el código ni con usted.</p>
      </div>
    );
  }

  if (!formulario) {
    return (
      <form className="tarjeta" onSubmit={acceder}>
        <h2>Encuesta docente</h2>
        <p className="tenue">Introduzca el código de invitación que le ha facilitado su profesor o el gabinete de calidad.</p>
        <label htmlFor="codigo">Código</label>
        <input id="codigo" value={codigo} onChange={(e) => setCodigo(e.target.value)} autoComplete="off" maxLength={32} />
        <button type="submit">Acceder</button>
        {error && <p className="error">{error}</p>}
      </form>
    );
  }

  return (
    <form onSubmit={enviar}>
      <div className="tarjeta">
        <h2>{formulario.asignatura_nombre}</h2>
        <p className="tenue">
          {formulario.programa_nombre} · {formulario.curso_academico_etiqueta} · {formulario.plantilla_nombre}
        </p>
      </div>
      {formulario.preguntas.map((p) => (
        <CampoPregunta key={p.id} pregunta={p} valor={valores[p.id]} onCambio={(v) => fijar(p.id, v)} />
      ))}
      <button type="submit">Enviar respuesta</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}

function CampoPregunta({ pregunta, valor, onCambio }: { pregunta: Pregunta; valor?: Valor; onCambio: (v: Valor) => void }) {
  const nombre = `p${pregunta.id}`;
  return (
    <fieldset className="tarjeta">
      <legend>
        {pregunta.orden}. {pregunta.enunciado} {pregunta.obligatoria && <span className="tenue">(obligatoria)</span>}
      </legend>
      {pregunta.tipo === "likert5" && (
        <div className="likert">
          {[1, 2, 3, 4, 5].map((n) => (
            <label key={n}>
              <input type="radio" name={nombre} checked={valor?.entero === n} onChange={() => onCambio({ entero: n })} /> {n}
            </label>
          ))}
          <span className="tenue">1 = muy en desacuerdo · 5 = muy de acuerdo</span>
        </div>
      )}
      {pregunta.tipo === "opcion_unica" &&
        pregunta.opciones.map((op, i) => (
          <label key={i}>
            <input type="radio" name={nombre} checked={valor?.entero === i} onChange={() => onCambio({ entero: i })} /> {op}
          </label>
        ))}
      {pregunta.tipo === "texto_libre" && (
        <>
          <textarea rows={4} maxLength={2000} value={valor?.texto ?? ""} onChange={(e) => onCambio({ texto: e.target.value })} />
          <p className="tenue">Evite datos que permitan identificarle: los comentarios se muestran literalmente.</p>
        </>
      )}
    </fieldset>
  );
}
