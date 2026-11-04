from datetime import UTC

import sqlite3

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import DateTime, TypeDecorator

from app.core.config import get_settings

_url = get_settings().database_url
_es_sqlite = _url.startswith("sqlite")
engine = create_engine(
    _url, connect_args={"check_same_thread": False} if _es_sqlite else {}
)



@event.listens_for(Engine, "connect")
def _pragmas(conexion, _):
    # Toda conexion SQLite (tambien la de los tests): las filas borradas al
    # barajar respuestas (services/encuestas.py) se sobrescriben con ceros en
    # lugar de quedar recuperables en paginas libres del fichero.
    if isinstance(conexion, sqlite3.Connection):
        conexion.execute("PRAGMA secure_delete = ON")
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class DateTimeUTC(TypeDecorator):
    """DateTime que viaja siempre como UTC consciente de zona horaria.

    SQLite no preserva tzinfo: se normaliza a UTC naive al escribir y se
    re-adjunta UTC al leer (mismo patron que pyCelda, issue #419 de alli)."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value.replace(tzinfo=UTC)
        return value


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
