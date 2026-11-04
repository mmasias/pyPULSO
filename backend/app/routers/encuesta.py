from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.celda.catalogo import CatalogoCelda, get_catalogo
from app.core.auth import Usuario, get_gestor, get_usuario
from app.core.database import get_db
from app.schemas.encuesta import (
    CodigosOut,
    EncuestaIn,
    EncuestaOut,
    GenerarCodigosIn,
    ParticipacionOut,
)
from app.schemas.resultados import ResultadosOut
from app.services import encuestas, resultados

router = APIRouter(prefix="/api/encuestas", tags=["encuestas"])


@router.get("", response_model=list[EncuestaOut])
def listar(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario),
    catalogo: CatalogoCelda = Depends(get_catalogo),
):
    return encuestas.listar_visibles(db, usuario, catalogo)


@router.post("", response_model=EncuestaOut, status_code=status.HTTP_201_CREATED)
def crear(
    datos: EncuestaIn,
    db: Session = Depends(get_db),
    gestor: Usuario = Depends(get_gestor),
    catalogo: CatalogoCelda = Depends(get_catalogo),
):
    return encuestas.crear(db, datos, gestor, catalogo)


@router.get("/{encuesta_id}", response_model=EncuestaOut)
def obtener(
    encuesta_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario),
    catalogo: CatalogoCelda = Depends(get_catalogo),
):
    encuesta = encuestas.obtener(db, encuesta_id)
    encuestas.comprobar_acceso(usuario, encuesta, catalogo)
    return encuesta


@router.post(
    "/{encuesta_id}/codigos", response_model=CodigosOut, status_code=status.HTTP_201_CREATED
)
def generar_codigos(
    encuesta_id: int,
    datos: GenerarCodigosIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_gestor),
):
    codigos = encuestas.generar_codigos(db, encuesta_id, datos.cantidad)
    return CodigosOut(encuesta_id=encuesta_id, codigos=codigos)


@router.get("/{encuesta_id}/participacion", response_model=ParticipacionOut)
def participacion(
    encuesta_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_gestor)
):
    encuesta = encuestas.obtener(db, encuesta_id)
    n = encuestas.contar_respuestas(db, encuesta.id)
    return ParticipacionOut(
        encuesta_id=encuesta.id,
        codigos_emitidos=encuestas.contar_codigos(db, encuesta.id),
        respuestas=n,
        umbral_minimo=encuesta.umbral_minimo,
        alcanza_umbral=n >= encuesta.umbral_minimo,
    )


@router.post("/{encuesta_id}/abrir", response_model=EncuestaOut)
def abrir(encuesta_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_gestor)):
    return encuestas.abrir(db, encuesta_id)


@router.post("/{encuesta_id}/cerrar", response_model=EncuestaOut)
def cerrar(encuesta_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_gestor)):
    return encuestas.cerrar(db, encuesta_id)


@router.post("/{encuesta_id}/publicar", response_model=EncuestaOut)
def publicar(encuesta_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_gestor)):
    return encuestas.publicar(db, encuesta_id)


@router.get("/{encuesta_id}/resultados", response_model=ResultadosOut)
def ver_resultados(
    encuesta_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario),
    catalogo: CatalogoCelda = Depends(get_catalogo),
):
    encuesta = encuestas.obtener(db, encuesta_id)
    encuestas.comprobar_acceso(usuario, encuesta, catalogo)
    encuestas.comprobar_resultados(encuesta)
    return resultados.agregar(db, encuesta)
