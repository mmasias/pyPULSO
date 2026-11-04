"""Identidad del personal (gestor, profesor, director).

El alumno NO se autentica: participa con un codigo de invitacion.

La identidad viaja en una cookie de sesion firmada (core/sesion.py), que
emite POST /api/auth/login con usuario y contrasena. v1 tiene una unica
cuenta, configurada por entorno (ACCESO_USUARIO, ACCESO_CLAVE_HASH), con rol
Gestor de calidad. El login institucional (previsiblemente el Google OAuth
de pyCelda) sustituira al endpoint, no a la cookie. Ver
RUP/03-diseño/README.md#autenticacion.

Solo en dev se acepta ademas la cabecera X-Dev-User, para tests y curl.
"""

from dataclasses import dataclass

from fastapi import Cookie, Depends, Header, HTTPException, status

from app.celda.catalogo import CatalogoCelda, get_catalogo
from app.core import sesion
from app.core.config import get_settings


@dataclass(frozen=True)
class Usuario:
    email: str
    es_gestor: bool
    es_profesor: bool
    es_director: bool

    @property
    def tiene_rol(self) -> bool:
        return self.es_gestor or self.es_profesor or self.es_director


def es_cuenta_acceso(nombre: str) -> bool:
    cuenta = get_settings().acceso_usuario
    return bool(cuenta) and nombre.strip().casefold() == cuenta.casefold()


def resolver(email: str, catalogo: CatalogoCelda, *, sesion_valida: bool = True) -> Usuario:
    """`sesion_valida=False` para identidades sin credencial (X-Dev-User):
    nunca adoptan la cuenta de acceso, que solo se obtiene con contrasena."""
    if sesion_valida and es_cuenta_acceso(email):
        return Usuario(
            email=get_settings().acceso_usuario,
            es_gestor=True,
            es_profesor=False,
            es_director=False,
        )
    email = email.strip().lower()
    return Usuario(
        email=email,
        es_gestor=email in get_settings().gestores_emails,
        es_profesor=catalogo.es_profesor(email),
        es_director=catalogo.es_director(email),
    )


def get_usuario(
    pulso_sesion: str | None = Cookie(default=None),
    x_dev_user: str | None = Header(default=None),
    catalogo: CatalogoCelda = Depends(get_catalogo),
) -> Usuario:
    email = sesion.leer(pulso_sesion)
    if email is not None:
        return resolver(email, catalogo)
    if get_settings().es_dev and x_dev_user:
        return resolver(x_dev_user, catalogo, sesion_valida=False)
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")


def get_gestor(usuario: Usuario = Depends(get_usuario)) -> Usuario:
    if not usuario.es_gestor:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere rol Gestor de calidad")
    return usuario
