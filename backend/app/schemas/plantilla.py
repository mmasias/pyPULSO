from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.plantilla import TipoPregunta


class PreguntaIn(BaseModel):
    enunciado: str = Field(min_length=1, max_length=1000)
    tipo: TipoPregunta
    obligatoria: bool = True
    opciones: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def _opciones_coherentes(self):
        if self.tipo == TipoPregunta.OPCION_UNICA and len(self.opciones) < 2:
            raise ValueError("opcion_unica requiere al menos 2 opciones")
        if self.tipo != TipoPregunta.OPCION_UNICA and self.opciones:
            raise ValueError("solo opcion_unica admite opciones")
        if any(not o.strip() or len(o) > 200 for o in self.opciones):
            raise ValueError("opciones vacias o de mas de 200 caracteres")
        return self


class PreguntaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    orden: int
    enunciado: str
    tipo: TipoPregunta
    obligatoria: bool
    opciones: list[str]


class PlantillaIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)
    descripcion: str = Field(default="", max_length=2000)


class PlantillaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str
    version: int
    estado: str
    plantilla_origen_id: int | None
    preguntas: list[PreguntaOut]
