import random
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Encuesta, RespuestaItem, Respuesta, TipoPregunta
from app.schemas.resultados import ResultadoPregunta, ResultadosOut
from app.services.encuestas import contar_respuestas

_azar = random.SystemRandom()


def agregar(db: Session, encuesta: Encuesta) -> ResultadosOut:
    """Agregados por pregunta. Por debajo del umbral no se devuelve ningun
    dato de contenido, a nadie: con pocas respuestas el agregado identifica
    al respondente."""
    n = contar_respuestas(db, encuesta.id)
    publicable = n >= encuesta.umbral_minimo
    salida = ResultadosOut(
        encuesta_id=encuesta.id,
        estado=encuesta.estado,
        respuestas=n,
        umbral_minimo=encuesta.umbral_minimo,
        publicable=publicable,
        preguntas=[],
    )
    if not publicable:
        return salida

    items = db.scalars(
        select(RespuestaItem)
        .join(Respuesta, RespuestaItem.respuesta_id == Respuesta.id)
        .where(Respuesta.encuesta_id == encuesta.id)
    ).all()
    por_pregunta: dict[int, list[RespuestaItem]] = {}
    for item in items:
        por_pregunta.setdefault(item.pregunta_id, []).append(item)

    for pregunta in encuesta.plantilla.preguntas:
        propios = por_pregunta.get(pregunta.id, [])
        r = ResultadoPregunta(
            pregunta_id=pregunta.id,
            orden=pregunta.orden,
            enunciado=pregunta.enunciado,
            tipo=pregunta.tipo,
            n=len(propios),
        )
        if pregunta.tipo == TipoPregunta.LIKERT5:
            valores = [i.valor_entero for i in propios]
            conteo = Counter(valores)
            r.distribucion = {str(k): conteo.get(k, 0) for k in range(1, 6)}
            r.media = round(sum(valores) / len(valores), 2) if valores else None
        elif pregunta.tipo == TipoPregunta.OPCION_UNICA:
            conteo = Counter(i.valor_entero for i in propios)
            r.distribucion = {op: conteo.get(k, 0) for k, op in enumerate(pregunta.opciones)}
        else:
            textos = [i.valor_texto for i in propios if i.valor_texto]
            _azar.shuffle(textos)
            r.textos = textos
        salida.preguntas.append(r)
    return salida
