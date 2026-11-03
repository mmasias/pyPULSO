from fastapi import APIRouter, Depends

from app.core.auth import Usuario, get_usuario

router = APIRouter(prefix="/api", tags=["sesion"])


@router.get("/yo")
def yo(usuario: Usuario = Depends(get_usuario)) -> dict:
    return {
        "email": usuario.email,
        "es_gestor": usuario.es_gestor,
        "es_profesor": usuario.es_profesor,
        "es_director": usuario.es_director,
    }
