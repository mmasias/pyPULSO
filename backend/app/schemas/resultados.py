from pydantic import BaseModel


class ResultadoPregunta(BaseModel):
    pregunta_id: int
    orden: int
    enunciado: str
    tipo: str
    seccion: str | None = None
    n: int
    media: float | None = None
    # escalas: claves "1".."N"; opcion_unica: etiqueta de la opcion.
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
