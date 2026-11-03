from pydantic import BaseModel


class ResultadoPregunta(BaseModel):
    pregunta_id: int
    orden: int
    enunciado: str
    tipo: str
    n: int
    media: float | None = None
    # likert5: claves "1".."5"; opcion_unica: etiqueta de la opcion.
    distribucion: dict[str, int] | None = None
    # texto_libre: orden aleatorio, sin identificador de respuesta.
    textos: list[str] | None = None


class ResultadosOut(BaseModel):
    encuesta_id: int
    estado: str
    respuestas: int
    umbral_minimo: int
    publicable: bool
    preguntas: list[ResultadoPregunta]
