from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.celda.catalogo import CatalogoCelda
from app.core.auth import Usuario
from app.core.codigos import generar_codigo, hash_codigo
from app.models import (
    CodigoInvitacion,
    Encuesta,
    EstadoEncuesta,
    EstadoPlantilla,
    Respuesta,
)
from app.schemas.encuesta import EncuestaIn
from app.services import plantillas
from app.services.errores import ErrorDominio, Invalido, NoEncontrado, Prohibido


def obtener(db: Session, encuesta_id: int) -> Encuesta:
    encuesta = db.get(Encuesta, encuesta_id)
    if encuesta is None:
        raise NoEncontrado("Encuesta no encontrada")
    return encuesta


def puede_ver(usuario: Usuario, encuesta: Encuesta, catalogo: CatalogoCelda) -> bool:
    if usuario.es_gestor:
        return True
    return catalogo.imparte(
        usuario.email, encuesta.celda_asignatura_id, encuesta.celda_curso_academico_id
    ) or catalogo.dirige(usuario.email, encuesta.celda_programa_id)


def listar_visibles(db: Session, usuario: Usuario, catalogo: CatalogoCelda) -> list[Encuesta]:
    todas = db.scalars(select(Encuesta).order_by(Encuesta.id.desc()))
    if usuario.es_gestor:
        return list(todas)
    # Profesor y director solo ven encuestas Publicadas de su ambito.
    return [
        e
        for e in todas
        if e.estado == EstadoEncuesta.PUBLICADA and puede_ver(usuario, e, catalogo)
    ]


def crear(db: Session, datos: EncuestaIn, gestor: Usuario, catalogo: CatalogoCelda) -> Encuesta:
    plantilla = plantillas.obtener(db, datos.plantilla_id)
    if plantilla.estado != EstadoPlantilla.PUBLICADA:
        raise ErrorDominio("La plantilla debe estar Publicada")
    programa = catalogo.programa(datos.celda_programa_id)
    asignatura = catalogo.asignatura(datos.celda_asignatura_id)
    curso = catalogo.curso_academico(datos.celda_curso_academico_id)
    if programa is None or asignatura is None or curso is None:
        raise Invalido("Programa, asignatura o curso academico inexistente en CELDA")
    if asignatura.programa_id != programa.id:
        raise Invalido("La asignatura no pertenece al programa")
    encuesta = Encuesta(
        plantilla_id=plantilla.id,
        celda_programa_id=programa.id,
        celda_asignatura_id=asignatura.id,
        celda_curso_academico_id=curso.id,
        programa_nombre=programa.nombre,
        asignatura_nombre=asignatura.nombre,
        curso_academico_etiqueta=curso.etiqueta,
        apertura=datos.apertura,
        cierre=datos.cierre,
        umbral_minimo=datos.umbral_minimo,
        creada_por=gestor.email,
    )
    db.add(encuesta)
    db.commit()
    return encuesta


def generar_codigos(db: Session, encuesta_id: int, cantidad: int) -> list[str]:
    encuesta = obtener(db, encuesta_id)
    if encuesta.estado not in (EstadoEncuesta.BORRADOR, EstadoEncuesta.ABIERTA):
        raise ErrorDominio("Solo se emiten codigos en Borrador o Abierta")
    codigos: list[str] = []
    while len(codigos) < cantidad:
        codigo = generar_codigo()
        try:
            # Savepoint: una colision (improbable) solo descarta este codigo,
            # no los ya generados en la misma transaccion.
            with db.begin_nested():
                db.add(
                    CodigoInvitacion(encuesta_id=encuesta.id, codigo_hash=hash_codigo(codigo))
                )
        except IntegrityError:
            continue
        codigos.append(codigo)
    db.commit()
    return codigos


def contar_codigos(db: Session, encuesta_id: int) -> int:
    return db.scalar(
        select(func.count()).where(CodigoInvitacion.encuesta_id == encuesta_id)
    ) or 0


def contar_respuestas(db: Session, encuesta_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Respuesta).where(Respuesta.encuesta_id == encuesta_id)
    ) or 0


def abrir(db: Session, encuesta_id: int) -> Encuesta:
    encuesta = obtener(db, encuesta_id)
    if encuesta.estado != EstadoEncuesta.BORRADOR:
        raise ErrorDominio("Solo se abre una encuesta en Borrador")
    if contar_codigos(db, encuesta.id) < encuesta.umbral_minimo:
        raise ErrorDominio("Codigos emitidos insuficientes para alcanzar el umbral")
    encuesta.estado = EstadoEncuesta.ABIERTA
    db.commit()
    return encuesta


def cerrar(db: Session, encuesta_id: int) -> Encuesta:
    encuesta = obtener(db, encuesta_id)
    if encuesta.estado != EstadoEncuesta.ABIERTA:
        raise ErrorDominio("Solo se cierra una encuesta Abierta")
    encuesta.estado = EstadoEncuesta.CERRADA
    db.commit()
    return encuesta


def publicar(db: Session, encuesta_id: int) -> Encuesta:
    encuesta = obtener(db, encuesta_id)
    if encuesta.estado != EstadoEncuesta.CERRADA:
        raise ErrorDominio("Solo se publica una encuesta Cerrada")
    if contar_respuestas(db, encuesta.id) < encuesta.umbral_minimo:
        raise ErrorDominio("No alcanza el umbral minimo de participacion")
    encuesta.estado = EstadoEncuesta.PUBLICADA
    db.commit()
    return encuesta


def cerrar_vencidas(db: Session, ahora: datetime | None = None) -> int:
    """Cierra las encuestas Abiertas cuya ventana ya termino. Pensado para
    ejecutarse periodicamente; la recepcion de respuestas ya respeta la
    ventana por si misma (Encuesta.admite_respuestas)."""
    ahora = ahora or datetime.now(UTC)
    vencidas = [
        e
        for e in db.scalars(select(Encuesta).where(Encuesta.estado == EstadoEncuesta.ABIERTA))
        if e.cierre <= ahora
    ]
    for e in vencidas:
        e.estado = EstadoEncuesta.CERRADA
    db.commit()
    return len(vencidas)


def comprobar_acceso(usuario: Usuario, encuesta: Encuesta, catalogo: CatalogoCelda) -> None:
    if not puede_ver(usuario, encuesta, catalogo):
        raise Prohibido("Sin acceso a esta encuesta")
    if not usuario.es_gestor and encuesta.estado != EstadoEncuesta.PUBLICADA:
        raise Prohibido("Resultados no publicados")
