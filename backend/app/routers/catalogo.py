from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.celda.catalogo import CatalogoCelda, get_catalogo
from app.core.auth import Usuario, get_gestor

router = APIRouter(prefix="/api/catalogo", tags=["catalogo CELDA"])


@router.get("/programas")
def programas(
    _: Usuario = Depends(get_gestor), catalogo: CatalogoCelda = Depends(get_catalogo)
) -> list[dict]:
    return [asdict(p) for p in catalogo.programas()]


@router.get("/programas/{programa_id}/asignaturas")
def asignaturas(
    programa_id: int,
    _: Usuario = Depends(get_gestor),
    catalogo: CatalogoCelda = Depends(get_catalogo),
) -> list[dict]:
    return [asdict(a) for a in catalogo.asignaturas(programa_id)]


@router.get("/cursos-academicos")
def cursos(
    _: Usuario = Depends(get_gestor), catalogo: CatalogoCelda = Depends(get_catalogo)
) -> list[dict]:
    return [asdict(c) for c in catalogo.cursos_academicos()]
