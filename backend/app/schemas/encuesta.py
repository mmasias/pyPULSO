from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EncuestaIn(BaseModel):
    plantilla_id: int
    celda_programa_id: int
    celda_asignatura_id: int
    celda_curso_academico_id: int
    apertura: datetime
    cierre: datetime
    umbral_minimo: int = Field(ge=1, le=10000)

    @model_validator(mode="after")
    def _ventana(self):
        if self.apertura.tzinfo is None or self.cierre.tzinfo is None:
            raise ValueError("apertura y cierre deben llevar zona horaria")
        if self.cierre <= self.apertura:
            raise ValueError("cierre debe ser posterior a apertura")
        return self


class EncuestaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plantilla_id: int
    celda_programa_id: int
    celda_asignatura_id: int
    celda_curso_academico_id: int
    programa_nombre: str
    asignatura_nombre: str
    curso_academico_etiqueta: str
    apertura: datetime
    cierre: datetime
    umbral_minimo: int
    estado: str


class GenerarCodigosIn(BaseModel):
    cantidad: int = Field(ge=1, le=1000)


class CodigosOut(BaseModel):
    """Los codigos en claro solo existen en esta respuesta: no se guardan."""

    encuesta_id: int
    codigos: list[str]


class ParticipacionOut(BaseModel):
    encuesta_id: int
    codigos_emitidos: int
    respuestas: int
    umbral_minimo: int
    alcanza_umbral: bool
