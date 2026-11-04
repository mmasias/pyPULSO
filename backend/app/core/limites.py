"""Limitacion de intentos fallidos de codigo de invitacion por IP.

Se cuentan solo los FALLOS, no todos los intentos: un aula entera sale a
internet por la misma IP (NAT del campus) y 30 alumnos validos no deben
bloquearse entre si. 5 fallos / 15 min / IP -> 429 con Retry-After.

En memoria de proceso: suficiente para un unico worker. Con varios workers
o replicas hay que moverlo a un almacen compartido.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

MAX_FALLOS = 5
VENTANA_SEGUNDOS = 15 * 60


class LimitadorFallos:
    def __init__(self, max_fallos: int = MAX_FALLOS, ventana: int = VENTANA_SEGUNDOS) -> None:
        self.max_fallos = max_fallos
        self.ventana = ventana
        self._fallos: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _purgar(self, clave: str, ahora: float) -> deque[float]:
        cola = self._fallos[clave]
        while cola and ahora - cola[0] >= self.ventana:
            cola.popleft()
        return cola

    def _olvidar_si_vacia(self, clave: str) -> None:
        if not self._fallos.get(clave):
            self._fallos.pop(clave, None)

    def comprobar(self, clave: str) -> None:
        ahora = time.monotonic()
        with self._lock:
            cola = self._purgar(clave, ahora)
            if len(cola) >= self.max_fallos:
                reintento = int(self.ventana - (ahora - cola[0])) + 1
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    "Demasiados intentos fallidos",
                    headers={"Retry-After": str(reintento)},
                )
            self._olvidar_si_vacia(clave)

    def reservar(self, clave: str) -> None:
        """Comprueba y cuenta el intento como fallo en un solo paso.

        Para verificaciones lentas (PBKDF2): si se comprobara antes y se
        contara despues, todas las peticiones concurrentes pasarian la
        comprobacion. Si el intento acierta, `liberar` retira la marca."""
        ahora = time.monotonic()
        with self._lock:
            cola = self._purgar(clave, ahora)
            if len(cola) >= self.max_fallos:
                reintento = int(self.ventana - (ahora - cola[0])) + 1
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    "Demasiados intentos fallidos",
                    headers={"Retry-After": str(reintento)},
                )
            cola.append(ahora)

    def liberar(self, clave: str) -> None:
        with self._lock:
            cola = self._fallos.get(clave)
            if cola:
                cola.pop()
            if not cola:
                self._fallos.pop(clave, None)

    def registrar_fallo(self, clave: str) -> None:
        with self._lock:
            self._fallos[clave].append(time.monotonic())

    def reiniciar(self) -> None:
        with self._lock:
            self._fallos.clear()


limitador_codigos = LimitadorFallos()
limitador_login = LimitadorFallos()


def ip_cliente(request: Request) -> str:
    # Detras de un proxy (Caddy) hay que configurar uvicorn con
    # --proxy-headers / forwarded-allow-ips para que esto sea la IP real.
    return request.client.host if request.client else "desconocida"
