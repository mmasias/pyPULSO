"""Tareas periodicas. Uso: `python -m app.tareas` (timer de systemd, README)."""

from app import models  # noqa: F401 -- registra las clases
from app.core.database import Base, SessionLocal, engine
from app.services.encuestas import cerrar_vencidas


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        print(f"Encuestas vencidas cerradas: {cerrar_vencidas(db)}")


if __name__ == "__main__":
    main()
