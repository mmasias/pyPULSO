"""Cookie de sesion del personal, firmada con HMAC-SHA256.

Contenido: email y caducidad. httpOnly (el JavaScript de la pagina no la
lee), SameSite=Lax y Secure fuera de dev. Sin estado en servidor: cerrar
sesion borra la cookie del navegador; una cookie copiada sigue valiendo
hasta su caducidad (DURACION). Con OAuth institucional cambiara como se
obtiene la identidad, no este mecanismo.
"""

import base64
import hashlib
import hmac
import time

from fastapi import Response

from app.core.config import get_settings

NOMBRE = "pulso_sesion"
DURACION = 8 * 3600


def _firma(datos: bytes) -> str:
    clave = get_settings().session_secret.encode()
    return hmac.new(clave, datos, hashlib.sha256).hexdigest()


def emitir(respuesta: Response, email: str) -> None:
    datos = f"{email}|{int(time.time()) + DURACION}".encode()
    valor = base64.urlsafe_b64encode(datos).decode() + "." + _firma(datos)
    respuesta.set_cookie(
        NOMBRE,
        valor,
        max_age=DURACION,
        httponly=True,
        samesite="lax",
        secure=not get_settings().es_dev,
        path="/",
    )


def borrar(respuesta: Response) -> None:
    respuesta.delete_cookie(NOMBRE, path="/")


def leer(valor: str | None) -> str | None:
    """Email de una cookie valida y vigente; None en cualquier otro caso."""
    if not valor or "." not in valor:
        return None
    cuerpo, firma = valor.rsplit(".", 1)
    try:
        datos = base64.urlsafe_b64decode(cuerpo.encode())
    except ValueError:
        return None
    if not hmac.compare_digest(firma, _firma(datos)):
        return None
    try:
        email, caduca = datos.decode().rsplit("|", 1)
        if int(caduca) < time.time():
            return None
    except ValueError:
        return None
    return email
