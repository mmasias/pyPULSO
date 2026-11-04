import { useState } from "react";
import { post } from "../api/cliente";
import { ESCALAS, porSeccion, type Formulario, type Pregunta } from "../api/tipos";

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
      setFormulario(await post<Formulario>("/api/participacion/acceder", { codigo }));
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
      await post("/api/participacion/enviar", { codigo, items });
      setEnviado(true);
      setCodigo("");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const fijar = (id: number, v: Valor | undefined) => {
    const nuevos = { ...valores };
    if (v === undefined) delete nuevos[id];
    else nuevos[id] = v;
    setValores(nuevos);
  };

  if (enviado) {
    return (
      <div className="tarjeta">
        <h2>Gracias por su participación</h2>
        <p>El código ha quedado inutilizado. La respuesta se guarda sin ningún dato que la relacione con el código ni con usted.</p>
      </div>
    );
  }

  if (!formulario) {
    return (
      <form className="tarjeta" onSubmit={acceder}>
        <h2>Acceso con código</h2>
        <p className="tenue">Introduzca el código de invitación que ha recibido.</p>
        <label htmlFor="codigo">Código</label>
        <div className="fila-acciones">
          <input id="codigo" value={codigo} onChange={(e) => setCodigo(e.target.value)} autoComplete="off" maxLength={32} />
          <button type="submit">Acceder</button>
        </div>
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
      {formulario.plantilla_descripcion && <p className="instruccion">{formulario.plantilla_descripcion}</p>}
      {porSeccion(formulario.preguntas).map((bloque, i) => (
        <section key={i}>
          {bloque.seccion && <h3 className="seccion">{bloque.seccion}</h3>}
          {bloque.elementos.map((p) => (
            <CampoPregunta key={p.id} pregunta={p} valor={valores[p.id]} onCambio={(v) => fijar(p.id, v)} />
          ))}
        </section>
      ))}
      <button type="submit">Enviar respuesta</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}

function CampoPregunta({ pregunta, valor, onCambio }: { pregunta: Pregunta; valor?: Valor; onCambio: (v: Valor | undefined) => void }) {
  const nombre = `p${pregunta.id}`;
  const escala = ESCALAS[pregunta.tipo];
  return (
    <fieldset className="tarjeta">
      <legend>
        {pregunta.orden}. {pregunta.enunciado} {pregunta.obligatoria && <span className="tenue">(obligatoria)</span>}
      </legend>
      {escala && (
        <>
          <div className="likert">
            {Array.from({ length: escala.max }, (_, k) => k + 1).map((n) => (
              <label key={n}>
                <input type="radio" name={nombre} checked={valor?.entero === n} onChange={() => onCambio({ entero: n })} /> {n}
              </label>
            ))}
          </div>
          <p className="tenue extremos">1 = {escala.min_txt} · {escala.max} = {escala.max_txt}</p>
        </>
      )}
      {pregunta.tipo === "opcion_unica" && (
        <div className="opciones">
          {pregunta.opciones.map((op, i) => (
            <label key={i}>
              <input type="radio" name={nombre} checked={valor?.entero === i} onChange={() => onCambio({ entero: i })} /> {op}
            </label>
          ))}
        </div>
      )}
      {!pregunta.obligatoria && pregunta.tipo !== "texto_libre" && valor !== undefined && (
        <button type="button" className="secundario borrar" onClick={() => onCambio(undefined)}>Borrar respuesta</button>
      )}
      {pregunta.tipo === "texto_libre" && (
        <>
          <textarea rows={4} maxLength={2000} value={valor?.texto ?? ""} onChange={(e) => onCambio({ texto: e.target.value })} />
          <p className="tenue">Evite datos que permitan identificarle: los comentarios se muestran literalmente.</p>
        </>
      )}
    </fieldset>
  );
}
