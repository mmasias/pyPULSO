from datetime import UTC

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import DateTime, TypeDecorator

from app.core.config import get_settings

engine = create_engine(
    get_settings().database_url, connect_args={"check_same_thread": False}
)
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
