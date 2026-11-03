from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, DateTimeUTC
from app.models.plantilla import Plantilla


class EstadoEncuesta(StrEnum):
    BORRADOR = "Borrador"
    ABIERTA = "Abierta"
    CERRADA = "Cerrada"
    PUBLICADA = "Publicada"


class Encuesta(Base):
    """Instancia de una plantilla sobre un contexto academico de CELDA.

    PULSO no es dueno de Programa, Asignatura ni CursoAcademico: guarda su
    identificador en CELDA y una copia de la etiqueta legible en el momento
    de creacion (`*_nombre`), para que el contexto siga siendo legible si
    CELDA renombra o archiva el elemento."""

    __tablename__ = "encuestas"

    id: Mapped[int] = mapped_column(primary_key=True)
    plantilla_id: Mapped[int] = mapped_column(ForeignKey("plantillas.id"))

    celda_programa_id: Mapped[int] = mapped_column()
    celda_asignatura_id: Mapped[int] = mapped_column()
    celda_curso_academico_id: Mapped[int] = mapped_column()
    programa_nombre: Mapped[str] = mapped_column(String(200))
    asignatura_nombre: Mapped[str] = mapped_column(String(200))
    curso_academico_etiqueta: Mapped[str] = mapped_column(String(20))

    apertura: Mapped[datetime] = mapped_column(DateTimeUTC)
    cierre: Mapped[datetime] = mapped_column(DateTimeUTC)
    umbral_minimo: Mapped[int] = mapped_column()
    estado: Mapped[str] = mapped_column(String(20), default=EstadoEncuesta.BORRADOR)

    creada_por: Mapped[str] = mapped_column(String(200))
    creada_en: Mapped[datetime] = mapped_column(
        DateTimeUTC, default=lambda: datetime.now(UTC)
    )

    plantilla: Mapped[Plantilla] = relationship()

    def admite_respuestas(self, ahora: datetime) -> bool:
        return (
            self.estado == EstadoEncuesta.ABIERTA
            and self.apertura <= ahora < self.cierre
        )
