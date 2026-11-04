import json
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, DateTimeUTC


class EstadoPlantilla(StrEnum):
    BORRADOR = "Borrador"
    PUBLICADA = "Publicada"
    ARCHIVADA = "Archivada"


class TipoPregunta(StrEnum):
    LIKERT5 = "likert5"
    LIKERT7 = "likert7"
    OPCION_UNICA = "opcion_unica"
    TEXTO_LIBRE = "texto_libre"


class Plantilla(Base):
    """Plantilla institucional de encuesta.

    Una plantilla Publicada es inmutable: cambiar una pregunta rompe la
    comparabilidad longitudinal de los resultados. Para modificarla se crea
    una nueva version (`plantilla_origen_id` apunta a la anterior)."""

    __tablename__ = "plantillas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(default=1)
    estado: Mapped[str] = mapped_column(String(20), default=EstadoPlantilla.BORRADOR)
    plantilla_origen_id: Mapped[int | None] = mapped_column(
        ForeignKey("plantillas.id"), nullable=True
    )
    creada_en: Mapped[datetime] = mapped_column(
        DateTimeUTC, default=lambda: datetime.now(UTC)
    )

    preguntas: Mapped[list["Pregunta"]] = relationship(
        back_populates="plantilla",
        order_by="Pregunta.orden",
        cascade="all, delete-orphan",
    )

    @property
    def editable(self) -> bool:
        return self.estado == EstadoPlantilla.BORRADOR


# Valor maximo de cada escala (el minimo es siempre 1).
ESCALAS = {TipoPregunta.LIKERT5: 5, TipoPregunta.LIKERT7: 7}


class Pregunta(Base):
    __tablename__ = "preguntas"

    id: Mapped[int] = mapped_column(primary_key=True)
    plantilla_id: Mapped[int] = mapped_column(ForeignKey("plantillas.id"))
    orden: Mapped[int] = mapped_column()
    enunciado: Mapped[str] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(String(20))
    obligatoria: Mapped[bool] = mapped_column(default=True)
    # Titulo del bloque al que pertenece (p. ej. "Atencion al estudiante").
    # Las preguntas consecutivas con la misma seccion forman un bloque.
    seccion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # Lista JSON de etiquetas; solo para opcion_unica.
    opciones_json: Mapped[str] = mapped_column(Text, default="[]")

    plantilla: Mapped[Plantilla] = relationship(back_populates="preguntas")

    @property
    def opciones(self) -> list[str]:
        return json.loads(self.opciones_json)

    @opciones.setter
    def opciones(self, valor: list[str]) -> None:
        self.opciones_json = json.dumps(valor, ensure_ascii=False)
