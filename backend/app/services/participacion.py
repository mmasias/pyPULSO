"""Participacion anonima del alumno con codigo de invitacion.

Invariante central (RUP/02-analisis/anonimato.md): marcar el codigo como
consumido y guardar la respuesta ocurren en la misma transaccion, pero no
queda ningun dato que relacione una cosa con la otra.
"""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.codigos import hash_codigo
from app.models import (
    CodigoInvitacion,
    Encuesta,
    Plantilla,
    Respuesta,
    RespuestaItem,
    TipoPregunta,
)
from app.schemas.participacion import EnviarIn
from app.services.errores import ErrorDominio, Invalido


class CodigoRechazado(ErrorDominio):
    """Fallo atribuible al codigo: cuenta para el limitador por IP."""

    estado_http = 403


def _localizar(db: Session, codigo: str) -> tuple[CodigoInvitacion, Encuesta]:
    registro = db.scalar(
        select(CodigoInvitacion).where(CodigoInvitacion.codigo_hash == hash_codigo(codigo))
    )
    if registro is None:
        raise CodigoRechazado("Codigo no valido")
    if registro.consumido:
        raise CodigoRechazado("Codigo ya utilizado")
    encuesta = db.get(Encuesta, registro.encuesta_id)
    if encuesta is None or not encuesta.admite_respuestas(datetime.now(UTC)):
        raise ErrorDominio("La encuesta no esta abierta")
    return registro, encuesta


def acceder(db: Session, codigo: str) -> Encuesta:
    """Valida el codigo sin consumirlo y devuelve la encuesta."""
    _, encuesta = _localizar(db, codigo)
    return encuesta


def _validar_items(plantilla: Plantilla, datos: EnviarIn) -> list[RespuestaItem]:
    preguntas = {p.id: p for p in plantilla.preguntas}
    vistos: set[int] = set()
    items: list[RespuestaItem] = []
    for item in datos.items:
        pregunta = preguntas.get(item.pregunta_id)
        if pregunta is None:
            raise Invalido(f"Pregunta {item.pregunta_id} ajena a la encuesta")
        if item.pregunta_id in vistos:
            raise Invalido(f"Pregunta {item.pregunta_id} respondida dos veces")
        vistos.add(item.pregunta_id)

        if pregunta.tipo == TipoPregunta.TEXTO_LIBRE:
            texto = (item.valor_texto or "").strip()
            if item.valor_entero is not None:
                raise Invalido(f"Pregunta {pregunta.id}: se esperaba texto")
            if not texto:
                vistos.discard(pregunta.id)
                continue
            items.append(RespuestaItem(pregunta_id=pregunta.id, valor_texto=texto))
            continue

        if item.valor_texto is not None or item.valor_entero is None:
            raise Invalido(f"Pregunta {pregunta.id}: se esperaba valor entero")
        if pregunta.tipo == TipoPregunta.LIKERT5:
            limite = range(1, 6)
        else:
            limite = range(len(pregunta.opciones))
        if item.valor_entero not in limite:
            raise Invalido(f"Pregunta {pregunta.id}: valor fuera de rango")
        items.append(RespuestaItem(pregunta_id=pregunta.id, valor_entero=item.valor_entero))

    faltan = [p.orden for p in plantilla.preguntas if p.obligatoria and p.id not in vistos]
    if faltan:
        raise Invalido(f"Faltan preguntas obligatorias: {faltan}")
    return items


def enviar(db: Session, datos: EnviarIn) -> None:
    registro, encuesta = _localizar(db, datos.codigo)
    items = _validar_items(encuesta.plantilla, datos)

    # Consumo condicional: si dos envios concurrentes usan el mismo codigo,
    # solo uno actualiza la fila.
    resultado = db.execute(
        update(CodigoInvitacion)
        .where(CodigoInvitacion.id == registro.id, CodigoInvitacion.consumido.is_(False))
        .values(consumido=True)
    )
    if resultado.rowcount != 1:
        db.rollback()
        raise CodigoRechazado("Codigo ya utilizado")

    db.add(Respuesta(encuesta_id=encuesta.id, items=items))
    db.commit()
