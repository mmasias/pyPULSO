"""Hash de contrasenas: PBKDF2-HMAC-SHA256 (biblioteca estandar).

Formato: pbkdf2_sha256$<iteraciones>$<sal hex>$<hash hex>.

Generar el hash para .env (la contrasena no se guarda en ningun fichero):
    python3 -m app.core.claves
"""

import getpass
import hashlib
import hmac
import secrets

ITERACIONES = 600_000


def generar(clave: str, iteraciones: int = ITERACIONES) -> str:
    sal = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, iteraciones)
    return f"pbkdf2_sha256${iteraciones}${sal.hex()}${h.hex()}"


def verificar(clave: str, codificado: str) -> bool:
    try:
        algoritmo, iteraciones, sal, esperado = codificado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        h = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), int(iteraciones))
    except ValueError:
        return False
    return hmac.compare_digest(h.hex(), esperado)


if __name__ == "__main__":
    print(generar(getpass.getpass("Contrasena: ")))
