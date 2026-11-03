"""Endpoints publicos del alumno: sin autenticacion, con codigo."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limites import ip_cliente, limitador_codigos
from app.schemas.participacion import AccederIn, EnviarIn, FormularioOut
from app.schemas.plantilla import PreguntaOut
from app.services import participacion
from app.services.participacion import CodigoRechazado

router = APIRouter(prefix="/api/participacion", tags=["participacion"])


@router.post("/acceder", response_model=FormularioOut)
def acceder(datos: AccederIn, request: Request, db: Session = Depends(get_db)):
    ip = ip_cliente(request)
    limitador_codigos.comprobar(ip)
    try:
        encuesta = participacion.acceder(db, datos.codigo)
    except CodigoRechazado:
        limitador_codigos.registrar_fallo(ip)
        raise
    return FormularioOut(
        asignatura_nombre=encuesta.asignatura_nombre,
        programa_nombre=encuesta.programa_nombre,
        curso_academico_etiqueta=encuesta.curso_academico_etiqueta,
        plantilla_nombre=encuesta.plantilla.nombre,
        preguntas=[PreguntaOut.model_validate(p) for p in encuesta.plantilla.preguntas],
    )


@router.post("/enviar", status_code=status.HTTP_204_NO_CONTENT)
def enviar(datos: EnviarIn, request: Request, db: Session = Depends(get_db)) -> None:
    ip = ip_cliente(request)
    limitador_codigos.comprobar(ip)
    try:
        participacion.enviar(db, datos)
    except CodigoRechazado:
        limitador_codigos.registrar_fallo(ip)
        raise
