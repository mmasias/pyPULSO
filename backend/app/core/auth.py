"""Identidad del personal (gestor, profesor, director).

El alumno NO se autentica: participa con un codigo de invitacion.

v1: sin OAuth. En PULSO_ENV=dev la identidad llega en la cabecera
X-Dev-User; fuera de dev cualquier peticion de personal recibe 401 hasta
que se integre el login (previsiblemente el mismo Google OAuth de pyCelda,
dominio institucional). Ver RUP/03-diseño/README.md.
"""

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from app.celda.catalogo import CatalogoCelda, get_catalogo
from app.core.config import get_settings


@dataclass(frozen=True)
class Usuario:
    email: str
    es_gestor: bool
    es_profesor: bool
    es_director: bool


def get_usuario(
    x_dev_user: str | None = Header(default=None),
    catalogo: CatalogoCelda = Depends(get_catalogo),
) -> Usuario:
    settings = get_settings()
    if not settings.es_dev or not x_dev_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")
    email = x_dev_user.strip().lower()
    return Usuario(
        email=email,
        es_gestor=email in settings.gestores_emails,
        es_profesor=catalogo.es_profesor(email),
        es_director=catalogo.es_director(email),
    )


def get_gestor(usuario: Usuario = Depends(get_usuario)) -> Usuario:
    if not usuario.es_gestor:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere rol Gestor de calidad")
    return usuario
