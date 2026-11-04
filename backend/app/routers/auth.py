from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.core import claves, sesion
from app.core.auth import es_cuenta_acceso
from app.core.config import get_settings
from app.core.limites import ip_cliente, limitador_login

router = APIRouter(prefix="/api/auth", tags=["sesion"])


class LoginIn(BaseModel):
    usuario: str = Field(min_length=1, max_length=200)
    clave: str = Field(min_length=1, max_length=200)


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
def login(datos: LoginIn, request: Request, response: Response) -> None:
    ip = ip_cliente(request)
    limitador_login.reservar(ip)
    settings = get_settings()
    # Se verifica siempre el hash (aunque el usuario no coincida) para que
    # el tiempo de respuesta no revele si el usuario existe.
    hash_ = settings.acceso_clave_hash or claves.generar("relleno", iteraciones=1)
    clave_ok = claves.verificar(datos.clave, hash_)
    if not (settings.acceso_clave_hash and es_cuenta_acceso(datos.usuario) and clave_ok):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contraseña incorrectos")
    limitador_login.liberar(ip)
    sesion.emitir(response, settings.acceso_usuario)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    sesion.borrar(response)
