from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EstadoPlantilla, Plantilla, Pregunta
from app.schemas.plantilla import PlantillaIn, PreguntaIn
from app.services.errores import ErrorDominio, NoEncontrado


def obtener(db: Session, plantilla_id: int) -> Plantilla:
    plantilla = db.get(Plantilla, plantilla_id)
    if plantilla is None:
        raise NoEncontrado("Plantilla no encontrada")
    return plantilla


def listar(db: Session) -> list[Plantilla]:
    return list(db.scalars(select(Plantilla).order_by(Plantilla.nombre, Plantilla.version)))


def crear(db: Session, datos: PlantillaIn) -> Plantilla:
    plantilla = Plantilla(nombre=datos.nombre, descripcion=datos.descripcion)
    db.add(plantilla)
    db.commit()
    return plantilla


def anadir_pregunta(db: Session, plantilla_id: int, datos: PreguntaIn) -> Plantilla:
    plantilla = obtener(db, plantilla_id)
    if not plantilla.editable:
        raise ErrorDominio("Solo se editan plantillas en Borrador; cree una nueva version")
    pregunta = Pregunta(
        orden=len(plantilla.preguntas) + 1,
        enunciado=datos.enunciado,
        tipo=datos.tipo,
        obligatoria=datos.obligatoria,
    )
    pregunta.opciones = datos.opciones
    plantilla.preguntas.append(pregunta)
    db.commit()
    return plantilla


def publicar(db: Session, plantilla_id: int) -> Plantilla:
    plantilla = obtener(db, plantilla_id)
    if plantilla.estado != EstadoPlantilla.BORRADOR:
        raise ErrorDominio("Solo se publica una plantilla en Borrador")
    if not plantilla.preguntas:
        raise ErrorDominio("Una plantilla sin preguntas no se publica")
    plantilla.estado = EstadoPlantilla.PUBLICADA
    db.commit()
    return plantilla


def archivar(db: Session, plantilla_id: int) -> Plantilla:
    plantilla = obtener(db, plantilla_id)
    if plantilla.estado != EstadoPlantilla.PUBLICADA:
        raise ErrorDominio("Solo se archiva una plantilla Publicada")
    plantilla.estado = EstadoPlantilla.ARCHIVADA
    db.commit()
    return plantilla


def nueva_version(db: Session, plantilla_id: int) -> Plantilla:
    origen = obtener(db, plantilla_id)
    if origen.estado == EstadoPlantilla.BORRADOR:
        raise ErrorDominio("Una plantilla en Borrador se edita, no se versiona")
    copia = Plantilla(
        nombre=origen.nombre,
        descripcion=origen.descripcion,
        version=origen.version + 1,
        plantilla_origen_id=origen.id,
    )
    for p in origen.preguntas:
        nueva = Pregunta(
            orden=p.orden, enunciado=p.enunciado, tipo=p.tipo, obligatoria=p.obligatoria
        )
        nueva.opciones = p.opciones
        copia.preguntas.append(nueva)
    db.add(copia)
    db.commit()
    return copia
