class ErrorDominio(Exception):
    """Regla de negocio incumplida. main.py la traduce a HTTP."""

    estado_http = 409

    def __init__(self, detalle: str) -> None:
        super().__init__(detalle)
        self.detalle = detalle


class NoEncontrado(ErrorDominio):
    estado_http = 404


class Prohibido(ErrorDominio):
    estado_http = 403


class Invalido(ErrorDominio):
    estado_http = 422
