import random
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, insert, select, update
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
    RespuestaItem,
)
from app.schemas.encuesta import EncuestaIn
from app.services import plantillas
from app.services.errores import ErrorDominio, Invalido, NoEncontrado, Prohibido


_azar = random.SystemRandom()


def obtener(db: Session, encuesta_id: int) -> Encuesta:
    encuesta = db.get(Encuesta, encuesta_id)
    if encuesta is None:
        raise NoEncontrado("Encuesta no encontrada")
    return _cerrar_si_vencida(db, encuesta)


def _cerrar_si_vencida(db: Session, encuesta: Encuesta) -> Encuesta:
    if encuesta.estado == EstadoEncuesta.ABIERTA and encuesta.cierre <= datetime.now(UTC):
        _pasar_a_cerrada(db, encuesta.id)
        db.commit()
        db.refresh(encuesta)
    return encuesta


def _pasar_a_cerrada(db: Session, encuesta_id: int) -> bool:
    """Transicion Abierta -> Cerrada, atomica. False si otra peticion ya la hizo.

    El UPDATE condicional va primero: abre la transaccion de escritura y
    toma el cerrojo de SQLite antes de leer las respuestas. Asi, dos cierres
    simultaneos no barajan dos veces (duplicarian respuestas) y ningun envio
    concurrente puede colarse entre la lectura y el borrado: el envio
    re-comprueba el estado dentro de su propia escritura
    (services/participacion.py). El llamante hace commit."""
    resultado = db.execute(
        update(Encuesta)
        .where(Encuesta.id == encuesta_id, Encuesta.estado == EstadoEncuesta.ABIERTA)
        .values(estado=EstadoEncuesta.CERRADA)
        .execution_options(synchronize_session=False)
    )
    if resultado.rowcount != 1:
        return False
    _barajar_respuestas(db, encuesta_id)
    return True


def _barajar_respuestas(db: Session, encuesta_id: int) -> None:
    """Reescribe las respuestas de la encuesta en orden aleatorio.

    Mientras la encuesta esta abierta, el orden fisico de las filas (rowid
    de SQLite) refleja el orden de llegada, que puede cruzarse con logs de
    acceso o con observaciones de `codigos_invitacion.consumido`. Al cerrar
    se borran y se reinsertan barajadas, con identificadores nuevos; con
    `PRAGMA secure_delete` las filas originales no quedan en paginas libres
    del fichero. Solo SQL de nucleo: no toca el mapa de identidad de la
    sesion ni descarta cambios pendientes del llamante.
    Ver RUP/02-analisis/anonimato.md."""
    de_la_encuesta = select(Respuesta.id).where(Respuesta.encuesta_id == encuesta_id)
    contenido: dict[str, list[tuple]] = {i: [] for i in db.scalars(de_la_encuesta)}
    for respuesta_id, pregunta_id, entero, texto in db.execute(
        select(
            RespuestaItem.respuesta_id,
            RespuestaItem.pregunta_id,
            RespuestaItem.valor_entero,
            RespuestaItem.valor_texto,
        ).where(RespuestaItem.respuesta_id.in_(de_la_encuesta))
    ):
        contenido[respuesta_id].append((pregunta_id, entero, texto))
    if not contenido:
        return
    db.execute(delete(RespuestaItem).where(RespuestaItem.respuesta_id.in_(de_la_encuesta)))
    db.execute(delete(Respuesta).where(Respuesta.encuesta_id == encuesta_id))

    lotes = list(contenido.values())
    _azar.shuffle(lotes)
    respuestas, items = [], []
    for lote in lotes:
        _azar.shuffle(lote)
        nuevo_id = uuid.uuid4().hex
        respuestas.append({"id": nuevo_id, "encuesta_id": encuesta_id})
        items.extend(
            {"id": uuid.uuid4().hex, "respuesta_id": nuevo_id, "pregunta_id": p,
             "valor_entero": e, "valor_texto": t}
            for p, e, t in lote
        )
    db.execute(insert(Respuesta), respuestas)
    if items:
        db.execute(insert(RespuestaItem), items)


def puede_ver(usuario: Usuario, encuesta: Encuesta, catalogo: CatalogoCelda) -> bool:
    if usuario.es_gestor:
        return True
    return catalogo.imparte(
        usuario.email, encuesta.celda_asignatura_id, encuesta.celda_curso_academico_id
    ) or catalogo.dirige(usuario.email, encuesta.celda_programa_id)


def listar_visibles(db: Session, usuario: Usuario, catalogo: CatalogoCelda) -> list[Encuesta]:
    abiertas = db.scalars(select(Encuesta.id).where(Encuesta.estado == EstadoEncuesta.ABIERTA))
    for encuesta_id in list(abiertas):
        _cerrar_si_vencida(db, db.get(Encuesta, encuesta_id))
    todas = list(db.scalars(select(Encuesta).order_by(Encuesta.id.desc())))
    if usuario.es_gestor:
        return todas
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
        asignatura_nombre=asignatura.etiqueta,
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
    if encuesta.estado != EstadoEncuesta.ABIERTA or not _pasar_a_cerrada(db, encuesta.id):
        db.rollback()
        raise ErrorDominio("Solo se cierra una encuesta Abierta")
    db.commit()
    db.refresh(encuesta)
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
    """Cierra (y baraja) las encuestas Abiertas cuya ventana ya termino.

    Las consultas ya cierran una encuesta vencida al leerla; esta funcion
    cubre las que nadie consulta, que si no conservarian el orden de llegada
    indefinidamente. Uso periodico: `python -m app.tareas` (README)."""
    ahora = ahora or datetime.now(UTC)
    vencidas = [
        e.id
        for e in db.scalars(select(Encuesta).where(Encuesta.estado == EstadoEncuesta.ABIERTA))
        if e.cierre <= ahora
    ]
    cerradas = 0
    for encuesta_id in vencidas:
        cerradas += _pasar_a_cerrada(db, encuesta_id)
        db.commit()
    return cerradas


def comprobar_acceso(usuario: Usuario, encuesta: Encuesta, catalogo: CatalogoCelda) -> None:
    if not puede_ver(usuario, encuesta, catalogo):
        raise Prohibido("Sin acceso a esta encuesta")
    if not usuario.es_gestor and encuesta.estado != EstadoEncuesta.PUBLICADA:
        raise Prohibido("Resultados no publicados")


def comprobar_resultados(encuesta: Encuesta) -> None:
    """Sin contenido mientras la encuesta admite respuestas, para ningun rol.

    Con resultados en vivo, dos consultas antes y despues de una respuesta
    aislan esa respuesta por diferencia, y el umbral deja de proteger nada.
    Cerrada la encuesta, el conjunto ya no cambia."""
    if encuesta.estado in (EstadoEncuesta.BORRADOR, EstadoEncuesta.ABIERTA):
        raise ErrorDominio("Resultados disponibles cuando la encuesta se cierre")
