"""Puerto de acceso al catalogo de CELDA.

PULSO consume de CELDA, sin modificarlo: programas, asignaturas, cursos
academicos, quien imparte cada asignatura y quien dirige cada programa.
CELDA no expone hoy una API para satelites, asi que v1 trabaja contra un
JSON con la misma forma (`StubCatalogoCelda`). Cuando exista la API, se
sustituye la implementacion sin tocar servicios ni routers.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


@dataclass(frozen=True)
class Programa:
    id: int
    nombre: str


@dataclass(frozen=True)
class Asignatura:
    id: int
    programa_id: int
    nombre: str


@dataclass(frozen=True)
class CursoAcademico:
    id: int
    etiqueta: str
    activo: bool


class CatalogoCelda(Protocol):
    def programas(self) -> list[Programa]: ...
    def programa(self, programa_id: int) -> Programa | None: ...
    def asignaturas(self, programa_id: int) -> list[Asignatura]: ...
    def asignatura(self, asignatura_id: int) -> Asignatura | None: ...
    def cursos_academicos(self) -> list[CursoAcademico]: ...
    def curso_academico(self, curso_id: int) -> CursoAcademico | None: ...
    def imparte(self, email: str, asignatura_id: int, curso_id: int) -> bool: ...
    def dirige(self, email: str, programa_id: int) -> bool: ...
    def es_profesor(self, email: str) -> bool: ...
    def es_director(self, email: str) -> bool: ...


class StubCatalogoCelda:
    def __init__(self, ruta: Path) -> None:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        self._programas = {p["id"]: p for p in datos["programas"]}
        self._asignaturas = {a["id"]: a for a in datos["asignaturas"]}
        self._cursos = {c["id"]: c for c in datos["cursos_academicos"]}
        self._imparticiones = {
            (i["profesor_email"].lower(), i["asignatura_id"], i["curso_academico_id"])
            for i in datos["imparticiones"]
        }
        self._direcciones = {
            (email.lower(), p["id"])
            for p in datos["programas"]
            for email in p.get("directores", [])
        }

    def programas(self) -> list[Programa]:
        return [Programa(p["id"], p["nombre"]) for p in self._programas.values()]

    def programa(self, programa_id: int) -> Programa | None:
        p = self._programas.get(programa_id)
        return Programa(p["id"], p["nombre"]) if p else None

    def asignaturas(self, programa_id: int) -> list[Asignatura]:
        return [
            Asignatura(a["id"], a["programa_id"], a["nombre"])
            for a in self._asignaturas.values()
            if a["programa_id"] == programa_id
        ]

    def asignatura(self, asignatura_id: int) -> Asignatura | None:
        a = self._asignaturas.get(asignatura_id)
        return Asignatura(a["id"], a["programa_id"], a["nombre"]) if a else None

    def cursos_academicos(self) -> list[CursoAcademico]:
        return [CursoAcademico(c["id"], c["etiqueta"], c["activo"]) for c in self._cursos.values()]

    def curso_academico(self, curso_id: int) -> CursoAcademico | None:
        c = self._cursos.get(curso_id)
        return CursoAcademico(c["id"], c["etiqueta"], c["activo"]) if c else None

    def imparte(self, email: str, asignatura_id: int, curso_id: int) -> bool:
        return (email.lower(), asignatura_id, curso_id) in self._imparticiones

    def dirige(self, email: str, programa_id: int) -> bool:
        return (email.lower(), programa_id) in self._direcciones

    def es_profesor(self, email: str) -> bool:
        return any(i[0] == email.lower() for i in self._imparticiones)

    def es_director(self, email: str) -> bool:
        return any(d[0] == email.lower() for d in self._direcciones)


@lru_cache
def get_catalogo() -> CatalogoCelda:
    return StubCatalogoCelda(Path(get_settings().celda_stub_path))
