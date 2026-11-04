"""Carga las plantillas institucionales de app/data/plantillas/*.json.

Uso (desde backend/, con el .env cargado):
    python -m app.cargar_plantillas --simular   # que haria, sin escribir
    python -m app.cargar_plantillas             # crea y publica las que falten
    python -m app.cargar_plantillas --migrar    # ademas, anade columnas nuevas

Idempotente: una plantilla cuyo nombre ya existe (en cualquier version) no
se toca. Para cambiar una plantilla ya cargada se versiona desde la
aplicacion, no desde aqui: publicada = inmutable.

--migrar: v1 no tiene migraciones (create_all no altera tablas existentes).
Anade, solo si faltan, columnas nuevas y anulables (preguntas.seccion) con
ALTER TABLE ADD COLUMN, que no toca los datos existentes.
"""

import json
import sys
from pathlib import Path

from sqlalchemy import inspect, select, text

from app import models  # noqa: F401 -- registra las clases
from app.core.database import Base, SessionLocal, engine
from app.models import EstadoPlantilla, Plantilla, Pregunta
from app.schemas.plantilla import PlantillaIn, PreguntaIn

DIRECTORIO = Path(__file__).parent / "data" / "plantillas"
COLUMNAS_NUEVAS = {"preguntas": {"seccion": "VARCHAR(300)"}}


def columnas_que_faltan() -> list[tuple[str, str, str]]:
    insp = inspect(engine)
    faltan = []
    for tabla, columnas in COLUMNAS_NUEVAS.items():
        if not insp.has_table(tabla):
            continue
        existentes = {c["name"] for c in insp.get_columns(tabla)}
        faltan += [(tabla, c, tipo) for c, tipo in columnas.items() if c not in existentes]
    return faltan


def leer(ruta: Path) -> tuple[PlantillaIn, list[PreguntaIn]]:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    cabecera = PlantillaIn(nombre=datos["nombre"], descripcion=datos.get("descripcion", ""))
    return cabecera, [PreguntaIn(**p) for p in datos["preguntas"]]


def main(argv: list[str]) -> int:
    simular, migrar = "--simular" in argv, "--migrar" in argv
    faltan = columnas_que_faltan()
    if faltan:
        lista = ", ".join(f"{t}.{c}" for t, c, _ in faltan)
        if simular or not migrar:
            print(f"Faltan columnas: {lista}. Ejecutar con --migrar para anadirlas.")
            if not simular:
                return 1
        else:
            with engine.begin() as conexion:
                for tabla, columna, tipo in faltan:
                    conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}"))
            print(f"Columnas anadidas: {lista}")
    if not simular:
        Base.metadata.create_all(bind=engine)

    ficheros = sorted(DIRECTORIO.glob("*.json"))
    resultado = 0
    with SessionLocal() as db:
        estados: dict[str, set[str]] = {}
        if not (simular and faltan):
            for nombre, estado in db.execute(select(Plantilla.nombre, Plantilla.estado)):
                estados.setdefault(nombre, set()).add(estado)
        for ruta in ficheros:
            cabecera, preguntas = leer(ruta)
            previas = estados.get(cabecera.nombre, set())
            if previas - {EstadoPlantilla.BORRADOR}:
                print(f"= {ruta.name}: '{cabecera.nombre}' ya existe, sin cambios")
                continue
            if previas:
                # Un borrador con el mismo nombre (creado a mano o resto de
                # una carga antigua): no se adivina cual es la buena.
                print(f"! {ruta.name}: hay un borrador '{cabecera.nombre}'; revisarlo o borrarlo")
                resultado = 1
                continue
            if simular:
                print(f"+ {ruta.name}: crearia y publicaria '{cabecera.nombre}' ({len(preguntas)} preguntas)")
                continue
            # Toda la plantilla en una transaccion: o queda publicada entera o
            # no queda nada (una carga a medias no se confunde con una hecha).
            plantilla = Plantilla(
                nombre=cabecera.nombre,
                descripcion=cabecera.descripcion,
                estado=EstadoPlantilla.PUBLICADA,
            )
            for orden, p in enumerate(preguntas, start=1):
                pregunta = Pregunta(
                    orden=orden,
                    enunciado=p.enunciado,
                    tipo=p.tipo,
                    obligatoria=p.obligatoria,
                    seccion=(p.seccion or "").strip() or None,
                )
                pregunta.opciones = p.opciones
                plantilla.preguntas.append(pregunta)
            db.add(plantilla)
            db.commit()
            print(f"+ {ruta.name}: '{cabecera.nombre}' publicada (id {plantilla.id}, {len(preguntas)} preguntas)")
    return resultado


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
