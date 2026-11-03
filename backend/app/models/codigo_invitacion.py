from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CodigoInvitacion(Base):
    """Lado IDENTIDAD de la separacion identidad/respuesta.

    Solo responde a la pregunta "este codigo ya se uso?". Restricciones
    deliberadas (ver RUP/02-analisis/anonimato.md):

    - Se guarda el HMAC del codigo, nunca el codigo en claro.
    - Sin marca temporal de consumo: un instante de consumo permitiria
      correlacionar con cualquier otro registro temporal.
    - Ninguna tabla de respuestas referencia a esta, ni esta a aquellas.
    """

    __tablename__ = "codigos_invitacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    encuesta_id: Mapped[int] = mapped_column(ForeignKey("encuestas.id"), index=True)
    codigo_hash: Mapped[str] = mapped_column(String(64), unique=True)
    consumido: Mapped[bool] = mapped_column(default=False)
