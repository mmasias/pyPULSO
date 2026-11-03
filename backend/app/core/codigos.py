import hashlib
import hmac
import secrets

from app.core.config import get_settings

# Sin 0/O, 1/I/L: se dictan y se copian a mano.
ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
LONGITUD = 10  # 31^10 ~ 8e14 combinaciones (~49 bits)


def generar_codigo() -> str:
    return "".join(secrets.choice(ALFABETO) for _ in range(LONGITUD))


def normalizar(codigo: str) -> str:
    return codigo.strip().upper().replace("-", "").replace(" ", "")


def hash_codigo(codigo: str) -> str:
    pepper = get_settings().codigo_pepper.encode()
    return hmac.new(pepper, normalizar(codigo).encode(), hashlib.sha256).hexdigest()
