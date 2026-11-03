from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import Usuario, get_gestor
from app.core.database import get_db
from app.schemas.plantilla import PlantillaIn, PlantillaOut, PreguntaIn
from app.services import plantillas

router = APIRouter(prefix="/api/plantillas", tags=["plantillas"])


@router.get("", response_model=list[PlantillaOut])
def listar(db: Session = Depends(get_db), _: Usuario = Depends(get_gestor)):
    return plantillas.listar(db)


@router.post("", response_model=PlantillaOut, status_code=status.HTTP_201_CREATED)
def crear(datos: PlantillaIn, db: Session = Depends(get_db), _: Usuario = Depends(get_gestor)):
    return plantillas.crear(db, datos)


@router.get("/{plantilla_id}", response_model=PlantillaOut)
def obtener(plantilla_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_gestor)):
    return plantillas.obtener(db, plantilla_id)


@router.post("/{plantilla_id}/preguntas", response_model=PlantillaOut)
def anadir_pregunta(
    plantilla_id: int,
    datos: PreguntaIn,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_gestor),
):
    return plantillas.anadir_pregunta(db, plantilla_id, datos)


@router.post("/{plantilla_id}/publicar", response_model=PlantillaOut)
def publicar(plantilla_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_gestor)):
    return plantillas.publicar(db, plantilla_id)


@router.post("/{plantilla_id}/archivar", response_model=PlantillaOut)
def archivar(plantilla_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_gestor)):
    return plantillas.archivar(db, plantilla_id)


@router.post(
    "/{plantilla_id}/nueva-version",
    response_model=PlantillaOut,
    status_code=status.HTTP_201_CREATED,
)
def nueva_version(
    plantilla_id: int, db: Session = Depends(get_db), _: Usuario = Depends(get_gestor)
):
    return plantillas.nueva_version(db, plantilla_id)
