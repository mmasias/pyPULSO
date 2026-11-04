import os
from dataclasses import dataclass, field
from functools import lru_cache


def _lista(valor: str) -> list[str]:
    return [e.strip().lower() for e in valor.split(",") if e.strip()]


@dataclass(frozen=True)
class Settings:
    entorno: str = "prod"
    database_url: str = "sqlite:///./pulso.db"
    codigo_pepper: str = ""
    session_secret: str = ""
    # Cuenta de acceso con contrasena (rol Gestor de calidad).
    acceso_usuario: str = ""
    acceso_clave_hash: str = ""
    gestores_emails: list[str] = field(default_factory=list)
    frontend_url: str = "http://localhost:5173"
    celda_stub_path: str = "app/data/celda_stub.json"

    @property
    def es_dev(self) -> bool:
        return self.entorno == "dev"


@lru_cache
def get_settings() -> Settings:
    # Sin PULSO_ENV se asume produccion: olvidar la variable no debe abrir
    # la identidad por cabecera ni la documentacion OpenAPI.
    entorno = os.getenv("PULSO_ENV", "prod")
    pepper = os.getenv("CODIGO_PEPPER", "")
    secreto = os.getenv("SESSION_SECRET", "")
    if entorno != "dev" and not pepper:
        # Sin pepper, los hashes de los codigos serian recalculables por
        # fuerza bruta con solo leer la base de datos.
        raise RuntimeError("CODIGO_PEPPER es obligatorio fuera de dev")
    if entorno != "dev" and len(secreto) < 32:
        # Con un secreto conocido cualquiera fabrica la cookie de sesion.
        raise RuntimeError("SESSION_SECRET (>= 32 caracteres) es obligatorio fuera de dev")
    return Settings(
        entorno=entorno,
        database_url=os.getenv("DATABASE_URL", "sqlite:///./pulso.db"),
        codigo_pepper=pepper or "dev-insecure-pepper",
        session_secret=secreto or "dev-insecure-session-secret",
        acceso_usuario=os.getenv("ACCESO_USUARIO", "").strip(),
        acceso_clave_hash=os.getenv("ACCESO_CLAVE_HASH", "").strip(),
        gestores_emails=_lista(os.getenv("GESTORES_EMAILS", "")),
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:5173"),
        celda_stub_path=os.getenv("CELDA_STUB_PATH", "app/data/celda_stub.json"),
    )
