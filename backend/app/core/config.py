import os
from dataclasses import dataclass, field
from functools import lru_cache


def _lista(valor: str) -> list[str]:
    return [e.strip().lower() for e in valor.split(",") if e.strip()]


@dataclass(frozen=True)
class Settings:
    entorno: str = "dev"
    database_url: str = "sqlite:///./pulso.db"
    codigo_pepper: str = ""
    gestores_emails: list[str] = field(default_factory=list)
    frontend_url: str = "http://localhost:5173"
    celda_stub_path: str = "app/data/celda_stub.json"

    @property
    def es_dev(self) -> bool:
        return self.entorno == "dev"


@lru_cache
def get_settings() -> Settings:
    entorno = os.getenv("PULSO_ENV", "dev")
    pepper = os.getenv("CODIGO_PEPPER", "")
    if entorno != "dev" and not pepper:
        # Sin pepper, los hashes de los codigos serian recalculables por
        # fuerza bruta con solo leer la base de datos.
        raise RuntimeError("CODIGO_PEPPER es obligatorio fuera de dev")
    return Settings(
        entorno=entorno,
        database_url=os.getenv("DATABASE_URL", "sqlite:///./pulso.db"),
        codigo_pepper=pepper or "dev-insecure-pepper",
        gestores_emails=_lista(os.getenv("GESTORES_EMAILS", "")),
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:5173"),
        celda_stub_path=os.getenv("CELDA_STUB_PATH", "app/data/celda_stub.json"),
    )
