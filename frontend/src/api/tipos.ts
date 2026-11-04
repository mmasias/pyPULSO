export type TipoPregunta = "likert5" | "opcion_unica" | "texto_libre";

export interface Pregunta {
  id: number;
  orden: number;
  enunciado: string;
  tipo: TipoPregunta;
  obligatoria: boolean;
  opciones: string[];
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
  preguntas: Pregunta[];
}

export interface ResultadoPregunta {
  pregunta_id: number;
  orden: number;
  enunciado: string;
  tipo: TipoPregunta;
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
