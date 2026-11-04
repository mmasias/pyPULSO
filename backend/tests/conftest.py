import os
from datetime import UTC, datetime, timedelta

os.environ["PULSO_ENV"] = "dev"
os.environ["GESTORES_EMAILS"] = "calidad@example.edu"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["ACCESO_USUARIO"] = "Cuenta Pruebas"
CLAVE_PRUEBAS = "clave-de-pruebas"
from app.core.claves import generar as _generar  # noqa: E402

os.environ["ACCESO_CLAVE_HASH"] = _generar(CLAVE_PRUEBAS, iteraciones=1000)
os.environ["CELDA_STUB_PATH"] = str(__import__("pathlib").Path(__file__).parent / "celda_test.json")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.limites import limitador_codigos, limitador_login
from app.main import app

GESTOR = {"X-Dev-User": "calidad@example.edu"}
PROFESOR_A = {"X-Dev-User": "profesor.a@example.edu"}  # imparte 101 en curso 2
PROFESOR_B = {"X-Dev-User": "profesor.b@example.edu"}  # imparte 102
DIRECTORA_GII = {"X-Dev-User": "directora.gii@example.edu"}  # dirige programa 10


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine, autoflush=False)
    yield Sesion
    engine.dispose()


@pytest.fixture
def client(db_session):
    def _get_db():
        db = db_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    limitador_codigos.reiniciar()
    limitador_login.reiniciar()
    yield TestClient(app)
    app.dependency_overrides.clear()


def crear_plantilla_publicada(client) -> dict:
    p = client.post("/api/plantillas", json={"nombre": "Satisfaccion docente"}, headers=GESTOR)
    pid = p.json()["id"]
    client.post(
        f"/api/plantillas/{pid}/preguntas",
        json={"enunciado": "Claridad de las explicaciones", "tipo": "likert5"},
        headers=GESTOR,
    )
    client.post(
        f"/api/plantillas/{pid}/preguntas",
        json={
            "enunciado": "Carga de trabajo",
            "tipo": "opcion_unica",
            "opciones": ["Baja", "Adecuada", "Excesiva"],
        },
        headers=GESTOR,
    )
    client.post(
        f"/api/plantillas/{pid}/preguntas",
        json={"enunciado": "Comentarios", "tipo": "texto_libre", "obligatoria": False},
        headers=GESTOR,
    )
    r = client.post(f"/api/plantillas/{pid}/publicar", headers=GESTOR)
    assert r.status_code == 200, r.text
    return r.json()


def crear_encuesta_abierta(client, umbral: int = 3, codigos: int = 5) -> tuple[dict, list[str]]:
    plantilla = crear_plantilla_publicada(client)
    ahora = datetime.now(UTC)
    r = client.post(
        "/api/encuestas",
        json={
            "plantilla_id": plantilla["id"],
            "celda_programa_id": 10,
            "celda_asignatura_id": 101,
            "celda_curso_academico_id": 2,
            "apertura": (ahora - timedelta(hours=1)).isoformat(),
            "cierre": (ahora + timedelta(days=7)).isoformat(),
            "umbral_minimo": umbral,
        },
        headers=GESTOR,
    )
    assert r.status_code == 201, r.text
    encuesta = r.json()
    r = client.post(
        f"/api/encuestas/{encuesta['id']}/codigos", json={"cantidad": codigos}, headers=GESTOR
    )
    lista = r.json()["codigos"]
    r = client.post(f"/api/encuestas/{encuesta['id']}/abrir", headers=GESTOR)
    assert r.status_code == 200, r.text
    return r.json(), lista


def responder(client, codigo: str, formulario: dict | None = None, likert: int = 4):
    if formulario is None:
        formulario = client.post("/api/participacion/acceder", json={"codigo": codigo}).json()
    pregs = formulario["preguntas"]
    items = [
        {"pregunta_id": pregs[0]["id"], "valor_entero": likert},
        {"pregunta_id": pregs[1]["id"], "valor_entero": 1},
        {"pregunta_id": pregs[2]["id"], "valor_texto": f"comentario {likert}"},
    ]
    return client.post("/api/participacion/enviar", json={"codigo": codigo, "items": items})
