import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class Respuesta(Base):
    """Lado CONTENIDO de la separacion identidad/respuesta.

    Sin referencia al codigo de invitacion, sin marca temporal y con
    identificador aleatorio (no autoincremental) para no exponer el orden de
    llegada. El contexto academico llega por la encuesta."""

    __tablename__ = "respuestas"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    encuesta_id: Mapped[int] = mapped_column(ForeignKey("encuestas.id"), index=True)

    items: Mapped[list["RespuestaItem"]] = relationship(
        back_populates="respuesta", cascade="all, delete-orphan"
    )


class RespuestaItem(Base):
    __tablename__ = "respuesta_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    respuesta_id: Mapped[str] = mapped_column(ForeignKey("respuestas.id"), index=True)
    pregunta_id: Mapped[int] = mapped_column(ForeignKey("preguntas.id"))
    # likert5: 1..5; opcion_unica: indice de la opcion.
    valor_entero: Mapped[int | None] = mapped_column(nullable=True)
    valor_texto: Mapped[str | None] = mapped_column(Text, nullable=True)

    respuesta: Mapped[Respuesta] = relationship(back_populates="items")
