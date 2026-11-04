export type TipoPregunta = "likert5" | "likert7" | "opcion_unica" | "texto_libre";

/** Escalas: maximo y rotulos de los extremos (el minimo es 1). */
export const ESCALAS: Partial<Record<TipoPregunta, { max: number; min_txt: string; max_txt: string }>> = {
  likert5: { max: 5, min_txt: "muy en desacuerdo", max_txt: "muy de acuerdo" },
  likert7: { max: 7, min_txt: "nada satisfecho o en total desacuerdo", max_txt: "totalmente satisfecho o en total acuerdo" },
};

/** Agrupa elementos consecutivos con la misma seccion. */
export function porSeccion<T extends { seccion?: string | null }>(lista: T[]): { seccion: string | null; elementos: T[] }[] {
  const bloques: { seccion: string | null; elementos: T[] }[] = [];
  for (const e of lista) {
    const s = e.seccion ?? null;
    const ultimo = bloques[bloques.length - 1];
    if (ultimo && ultimo.seccion === s) ultimo.elementos.push(e);
    else bloques.push({ seccion: s, elementos: [e] });
  }
  return bloques;
}

export interface Pregunta {
  id: number;
  orden: number;
  enunciado: string;
  tipo: TipoPregunta;
  obligatoria: boolean;
  opciones: string[];
  seccion: string | null;
}

export interface Plantilla {
  id: number;
  nombre: string;
  descripcion: string;
  version: number;
  estado: "Borrador" | "Publicada" | "Archivada";
  plantilla_origen_id: number | null;
  preguntas: Pregunta[];
}

export interface Encuesta {
  id: number;
  plantilla_id: number;
  programa_nombre: string;
  asignatura_nombre: string;
  curso_academico_etiqueta: string;
  apertura: string;
  cierre: string;
  umbral_minimo: number;
  estado: "Borrador" | "Abierta" | "Cerrada" | "Publicada";
}

export interface Formulario {
  asignatura_nombre: string;
  programa_nombre: string;
  curso_academico_etiqueta: string;
  plantilla_nombre: string;
  plantilla_descripcion: string;
  preguntas: Pregunta[];
}

export interface ResultadoPregunta {
  pregunta_id: number;
  orden: number;
  enunciado: string;
  tipo: TipoPregunta;
  seccion: string | null;
  n: number;
  media: number | null;
  distribucion: Record<string, number> | null;
  textos: string[] | null;
}

export interface Resultados {
  encuesta_id: number;
  estado: string;
  respuestas: number;
  umbral_minimo: number;
  publicable: boolean;
  preguntas: ResultadoPregunta[];
}

export interface Yo {
  email: string;
  es_gestor: boolean;
  es_profesor: boolean;
  es_director: boolean;
}

export interface Participacion {
  codigos_emitidos: number;
  respuestas: number;
  umbral_minimo: number;
  alcanza_umbral: boolean;
}

export interface ProgramaCatalogo {
  id: number;
  nombre: string;
  nivel: string;
  departamento: string | null;
}

export interface AsignaturaCatalogo {
  id: number;
  programa_id: number;
  codigo: string;
  nombre: string;
  creditos: number | null;
}

export interface CursoCatalogo {
  id: number;
  etiqueta: string;
  activo: boolean;
}
