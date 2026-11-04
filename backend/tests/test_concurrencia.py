"""Carreras en el cierre (revision previa al segundo commit: C1, I1, I5).

SQLite en fichero y sesiones independientes, como en produccion: cada
peticion tiene su propia conexion."""

import threading
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models import Encuesta, EstadoEncuesta, Respuesta
from app.schemas.participacion import EnviarIn
from app.services import encuestas, participacion
from tests.conftest import crear_encuesta_abierta, responder


@pytest.fixture
def fichero(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'pulso.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine, autoflush=False)

    def _get_db():
        db = Sesion()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    yield Sesion, TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


def _respuestas(Sesion) -> int:
    with Sesion() as db:
        return db.scalar(select(func.count()).select_from(Respuesta))


def test_cierre_perdedor_no_vuelve_a_barajar(fichero):
    Sesion, client = fichero
    e, codigos = crear_encuesta_abierta(client, umbral=1, codigos=3)
    for c in codigos:
        assert responder(client, c).status_code == 204
    a, b = Sesion(), Sesion()
    assert encuestas.obtener(b, e["id"]).estado == EstadoEncuesta.ABIERTA  # B la ve abierta
    encuestas.cerrar(a, e["id"])  # A gana y comitea
    assert encuestas._pasar_a_cerrada(b, e["id"]) is False
    b.commit()
    assert _respuestas(Sesion) == 3


def test_cierres_simultaneos_en_hilos(fichero):
    Sesion, client = fichero
    e, codigos = crear_encuesta_abierta(client, umbral=1, codigos=5)
    for c in codigos:
        assert responder(client, c).status_code == 204
    salida = threading.Barrier(4)
    estados = []

    def cerrar():
        salida.wait()
        estados.append(client.post(f"/api/encuestas/{e['id']}/cerrar",
                                   headers={"X-Dev-User": "calidad@example.edu"}).status_code)

    hilos = [threading.Thread(target=cerrar) for _ in range(4)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert sorted(estados) == [200, 409, 409, 409]
    assert _respuestas(Sesion) == 5


def test_envio_que_pierde_contra_el_cierre_se_rechaza(fichero):
    Sesion, client = fichero
    e, codigos = crear_encuesta_abierta(client, umbral=1, codigos=2)
    form = client.post("/api/participacion/acceder", json={"codigo": codigos[1]}).json()
    assert responder(client, codigos[0], form).status_code == 204
    pregs = form["preguntas"]
    datos = EnviarIn(codigo=codigos[1], items=[
        {"pregunta_id": pregs[0]["id"], "valor_entero": 3},
        {"pregunta_id": pregs[1]["id"], "valor_entero": 0},
    ])
    b = Sesion()
    registro, encuesta = participacion._localizar(b, datos.codigo)  # B la ve abierta
    with Sesion() as a:
        encuestas.cerrar(a, e["id"])
    original = participacion._localizar
    participacion._localizar = lambda db, codigo: (registro, encuesta)
    try:
        with pytest.raises(participacion.ErrorDominio):
            participacion.enviar(b, datos)
    finally:
        participacion._localizar = original
    assert _respuestas(Sesion) == 1


def test_cerrar_vencidas_cierra_todas(fichero):
    Sesion, client = fichero
    ids = []
    for _ in range(3):
        e, codigos = crear_encuesta_abierta(client, umbral=1, codigos=1)
        responder(client, codigos[0])
        ids.append(e["id"])
    with Sesion() as db:
        for i in ids:
            db.get(Encuesta, i).cierre = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()
    with Sesion() as db:
        assert encuestas.cerrar_vencidas(db) == 3
    with Sesion() as db:
        assert [db.get(Encuesta, i).estado for i in ids] == ["Cerrada"] * 3
    assert _respuestas(Sesion) == 3
