"""Genera app/data/celda_stub.json con el catalogo publico de UNIB.

Fuente: planes de estudio publicados en https://www.unib.org/ (una pagina
por programa). Solo programas y asignaturas: profesores y directores son
identidades de desarrollo ficticias (UNIB no publica quien imparte que).

Uso (desde backend/):
    python3 -I scripts/generar_catalogo_unib.py > app/data/celda_stub.json
    python3 -I scripts/generar_catalogo_unib.py --html DIR > ...   # sin red, HTML ya descargado
"""

import json
import re
import sys
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://www.unib.org/a/"

# (ruta, nivel, departamento publicado; None si la pagina no lo muestra)
PROGRAMAS = [
    ("bachilleratos/bachillerato-artes-concentracion-psicologia", "Bachillerato", None),
    ("bachilleratos/bachillerato-ciencias-nutricion-dietetica", "Bachillerato", None),
    ("maestrias/maestria-gestion-y-auditorias-ambientales", "Maestría", "Medio Ambiente y Sostenibilidad"),
    ("maestrias/maestria-en-direccion-estrategica-con-especialidad-en-gerencia", "Maestría", "Innovación, Negocios y Nuevas Tecnologías"),
    ("maestrias/maestria-direccion-estrategica-tecnologias-informacion", "Maestría", "Innovación, Negocios y Nuevas Tecnologías"),
    ("maestrias/maestria-en-direccion-estrategica-con-especialidad-en-telecomunicaciones", "Maestría", "Innovación, Negocios y Nuevas Tecnologías"),
    ("maestrias/maestria-formacion-profesores-espanol-como-lengua-extranjera", "Maestría", "Ciencias de Lenguaje, Educación y Comunicaciones"),
    ("maestrias/master-teaching-english-foreign-language", "Maestría", "Ciencias de Lenguaje, Educación y Comunicaciones"),
    ("maestrias/maestria-en-educacion-con-especialidad-en-educacion-superior", "Maestría", "Ciencias de Lenguaje, Educación y Comunicaciones"),
    ("maestrias/maestria-en-educacion-con-especialidad-en-organizacion-y-gestion-de-centros-educativos", "Maestría", "Ciencias de Lenguaje, Educación y Comunicaciones"),
    ("maestrias/maestria-en-educacion-con-especialidad-en-las-tic-en-la-eduacion", "Maestría", "Ciencias de Lenguaje, Educación y Comunicaciones"),
    ("maestrias/maestria-en-educacion-con-especialidad-en-formacion-del-profesorado", "Maestría", "Ciencias de Lenguaje, Educación y Comunicaciones"),
    ("maestrias/maestria-actividad-fisica-entrenamiento-gestion-deportiva", "Maestría", "Ciencias de la Salud"),
    ("maestrias/maestria-en-ciencias-naturopaticas", "Maestría", "Ciencias de la Salud"),
    ("maestrias/maestria-en-salud-publica", "Maestría", "Ciencias de la Salud"),
    ("maestrias/maestria-en-diseno-gestion-y-direccion-proyectos", "Maestría", "Proyectos"),
    ("maestrias/maestria-en-diseno-gestion-y-direccion-de-proyectos-con-especialidad-en-innovacion-y-producto", "Maestría", "Proyectos"),
    ("maestrias/maestria-en-diseno-gestion-y-direccion-de-proyectos-con-especialidad-en-arquitectura-y-urbanismo", "Maestría", "Proyectos"),
    ("doctorados/doctorado-en-educacion-con-especialidad-en-investigacion", "Doctorado", None),
    ("doctorados/doctorado-en-proyectos-con-especialidad-en-investigacion", "Doctorado", None),
]

CODIGO = re.compile(r"^[A-Z][A-Z0-9_/\-]{1,24}$")


class _Tablas(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.filas: list[list[str]] = []
        self._fila: list[str] | None = None
        self._celda: list[str] = []
        self._en_celda = False
        self._en_h1 = False
        self._en_sup = 0  # llamadas a nota al pie: no forman parte del texto
        self.titulo = ""

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._fila = []
        elif tag in ("td", "th") and self._fila is not None:
            self._en_celda, self._celda = True, []
        elif tag == "h1":
            self._en_h1 = True
        elif tag == "sup":
            self._en_sup += 1

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._en_celda:
            self._fila.append(re.sub(r"\s+", " ", "".join(self._celda)).strip())
            self._en_celda = False
        elif tag == "tr" and self._fila is not None:
            self.filas.append(self._fila)
            self._fila = None
        elif tag == "h1":
            self._en_h1 = False
        elif tag == "sup" and self._en_sup:
            self._en_sup -= 1

    def handle_data(self, data):
        if self._en_celda and not self._en_sup:
            self._celda.append(data)
        if self._en_h1:
            self.titulo += data


def _numero(texto: str) -> float | None:
    texto = texto.replace(",", ".")
    return float(texto) if re.fullmatch(r"\d+(\.\d+)?", texto) else None


def _es_codigo(texto: str) -> bool:
    texto = texto.replace(" ", "")
    return bool(CODIGO.match(texto)) and (bool(re.search(r"\d", texto)) or "_" in texto)


def extraer(html: str) -> tuple[str, list[dict]]:
    p = _Tablas()
    p.feed(html)
    vistos: set[str] = set()
    asignaturas: list[dict] = []
    for fila in p.filas:
        # Maestrias: codigo en la 1a celda; bachilleratos: 1a celda = tipo de curso.
        i = next((j for j in range(min(2, len(fila) - 1)) if _es_codigo(fila[j])), None)
        if i is None:
            continue
        codigo, nombre = fila[i].replace(" ", ""), fila[i + 1]
        if not nombre or _numero(nombre) is not None or codigo in vistos:
            continue
        vistos.add(codigo)
        creditos = next((_numero(c) for c in fila[i + 2:] if _numero(c) is not None), None)
        asignaturas.append({"codigo": codigo, "nombre": nombre, "creditos": creditos})
    return re.sub(r"\s+", " ", p.titulo).strip(), asignaturas


def _html(ruta: str, directorio: Path | None) -> str:
    if directorio is not None:
        return (directorio / (ruta.rsplit("/", 1)[1] + ".html")).read_text(encoding="utf-8")
    peticion = urllib.request.Request(BASE + ruta, headers={"User-Agent": "pyPULSO catalogo"})
    with urllib.request.urlopen(peticion, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def main() -> None:
    directorio = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--html" else None
    programas, asignaturas = [], []
    for n, (ruta, nivel, departamento) in enumerate(PROGRAMAS, start=1):
        titulo, asigs = extraer(_html(ruta, directorio))
        if not asigs:
            raise SystemExit(f"Sin asignaturas extraidas: {ruta}")
        programas.append({
            "id": n,
            "nombre": titulo,
            "nivel": nivel,
            "departamento": departamento,
            "url": BASE + ruta,
            "directores": [],
        })
        for k, a in enumerate(asigs, start=1):
            asignaturas.append({"id": n * 1000 + k, "programa_id": n, **a})

    # Identidades de desarrollo, ficticias: permiten probar los roles.
    mdeti = next(p for p in programas if "Tecnologías de la Información" in p["nombre"])
    mdeti["directores"] = ["director.programa@example.edu"]
    por_codigo = {(a["programa_id"], a["codigo"]): a["id"] for a in asignaturas}
    imparticiones = [
        {"profesor_email": "profesor.a@example.edu", "asignatura_id": por_codigo[(mdeti["id"], "TI041")], "curso_academico_id": 2},
        {"profesor_email": "profesor.a@example.edu", "asignatura_id": por_codigo[(mdeti["id"], "TI043")], "curso_academico_id": 2},
        {"profesor_email": "profesor.b@example.edu", "asignatura_id": por_codigo[(mdeti["id"], "DD014")], "curso_academico_id": 2},
    ]

    salida = {
        "_nota": (
            f"Catalogo de UNIB extraido de los planes de estudio publicados en https://www.unib.org/ "
            f"el {date.today().isoformat()} por scripts/generar_catalogo_unib.py. "
            "Profesores y directores: identidades de desarrollo ficticias (@example.edu)."
        ),
        "cursos_academicos": [
            {"id": 1, "etiqueta": "2025-2026", "activo": False},
            {"id": 2, "etiqueta": "2026-2027", "activo": True},
        ],
        "programas": programas,
        "asignaturas": asignaturas,
        "imparticiones": imparticiones,
    }
    json.dump(salida, sys.stdout, ensure_ascii=False, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
