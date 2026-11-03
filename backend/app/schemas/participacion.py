from pydantic import BaseModel, Field

from app.schemas.plantilla import PreguntaOut


class AccederIn(BaseModel):
    codigo: str = Field(min_length=4, max_length=32)


class FormularioOut(BaseModel):
    asignatura_nombre: str
    programa_nombre: str
    curso_academico_etiqueta: str
    plantilla_nombre: str
    preguntas: list[PreguntaOut]


class ItemIn(BaseModel):
    pregunta_id: int
    valor_entero: int | None = None
    valor_texto: str | None = Field(default=None, max_length=2000)


class EnviarIn(BaseModel):
    codigo: str = Field(min_length=4, max_length=32)
    items: list[ItemIn] = Field(max_length=200)
