from datetime import UTC, datetime, timedelta

from tests.conftest import (
    DIRECTORA_GII,
    GESTOR,
    PROFESOR_A,
    PROFESOR_B,
    crear_encuesta_abierta,
    crear_plantilla_publicada,
    responder,
)


def _cerrar(client, eid):
    assert client.post(f"/api/encuestas/{eid}/cerrar", headers=GESTOR).status_code == 200


def test_sin_identidad_401(client):
    assert client.get("/api/encuestas").status_code == 401


def test_solo_gestor_crea_plantillas(client):
    r = client.post("/api/plantillas", json={"nombre": "x"}, headers=PROFESOR_A)
    assert r.status_code == 403


def test_plantilla_publicada_inmutable_y_versionado(client):
    p = crear_plantilla_publicada(client)
    r = client.post(
        f"/api/plantillas/{p['id']}/preguntas",
        json={"enunciado": "nueva", "tipo": "likert5"},
        headers=GESTOR,
    )
    assert r.status_code == 409
    v2 = client.post(f"/api/plantillas/{p['id']}/nueva-version", headers=GESTOR).json()
    assert v2["version"] == 2 and v2["estado"] == "Borrador"
    assert v2["plantilla_origen_id"] == p["id"]
    assert len(v2["preguntas"]) == 3


def test_contexto_validado_contra_celda(client):
    p = crear_plantilla_publicada(client)
    ahora = datetime.now(UTC)
    base = {
        "plantilla_id": p["id"],
        "celda_programa_id": 20,  # GADE
        "celda_asignatura_id": 101,  # asignatura de GII
        "celda_curso_academico_id": 2,
        "apertura": ahora.isoformat(),
        "cierre": (ahora + timedelta(days=1)).isoformat(),
        "umbral_minimo": 1,
    }
    assert client.post("/api/encuestas", json=base, headers=GESTOR).status_code == 422
    base["celda_asignatura_id"] = 999
    assert client.post("/api/encuestas", json=base, headers=GESTOR).status_code == 422


def test_no_abre_sin_codigos_suficientes(client):
    p = crear_plantilla_publicada(client)
    ahora = datetime.now(UTC)
    e = client.post(
        "/api/encuestas",
        json={
            "plantilla_id": p["id"],
            "celda_programa_id": 10,
            "celda_asignatura_id": 101,
            "celda_curso_academico_id": 2,
            "apertura": ahora.isoformat(),
            "cierre": (ahora + timedelta(days=1)).isoformat(),
            "umbral_minimo": 5,
        },
        headers=GESTOR,
    ).json()
    client.post(f"/api/encuestas/{e['id']}/codigos", json={"cantidad": 2}, headers=GESTOR)
    assert client.post(f"/api/encuestas/{e['id']}/abrir", headers=GESTOR).status_code == 409


def test_umbral_oculta_resultados_incluso_al_gestor(client):
    e, codigos = crear_encuesta_abierta(client, umbral=3)
    responder(client, codigos[0])
    responder(client, codigos[1])
    _cerrar(client, e["id"])
    r = client.get(f"/api/encuestas/{e['id']}/resultados", headers=GESTOR).json()
    assert r["publicable"] is False and r["preguntas"] == [] and r["respuestas"] == 2
    assert client.post(f"/api/encuestas/{e['id']}/publicar", headers=GESTOR).status_code == 409


def test_sin_resultados_en_vivo_para_nadie(client):
    # Revision C1: con resultados en vivo, la diferencia entre dos consultas
    # aisla cada respuesta nueva aunque se haya superado el umbral.
    e, codigos = crear_encuesta_abierta(client, umbral=1)
    for c in codigos[:3]:
        responder(client, c)
    r = client.get(f"/api/encuestas/{e['id']}/resultados", headers=GESTOR)
    assert r.status_code == 409
    _cerrar(client, e["id"])
    assert client.get(f"/api/encuestas/{e['id']}/resultados", headers=GESTOR).status_code == 200


def test_opciones_repetidas_rechazadas(client):
    p = client.post("/api/plantillas", json={"nombre": "x"}, headers=GESTOR).json()
    r = client.post(
        f"/api/plantillas/{p['id']}/preguntas",
        json={"enunciado": "q", "tipo": "opcion_unica", "opciones": ["Si", "si", "No"]},
        headers=GESTOR,
    )
    assert r.status_code == 422


def test_encuesta_vencida_se_cierra_sola(client, db_session):
    from app.models import Encuesta

    e, codigos = crear_encuesta_abierta(client, umbral=1)
    responder(client, codigos[0])
    db = db_session()
    enc = db.get(Encuesta, e["id"])
    enc.cierre = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()
    db.close()
    assert client.get(f"/api/encuestas/{e['id']}", headers=GESTOR).json()["estado"] == "Cerrada"


def test_resultados_agregados_y_visibilidad(client):
    e, codigos = crear_encuesta_abierta(client, umbral=3)
    for c, v in zip(codigos[:3], (3, 4, 5)):
        assert responder(client, c, likert=v).status_code == 204

    # Antes de publicar: profesor sin acceso.
    assert client.get(f"/api/encuestas/{e['id']}/resultados", headers=PROFESOR_A).status_code == 403
    _cerrar(client, e["id"])
    assert client.post(f"/api/encuestas/{e['id']}/publicar", headers=GESTOR).status_code == 200

    r = client.get(f"/api/encuestas/{e['id']}/resultados", headers=PROFESOR_A).json()
    likert, opcion, texto = r["preguntas"]
    assert likert["media"] == 4.0
    assert likert["distribucion"] == {"1": 0, "2": 0, "3": 1, "4": 1, "5": 1}
    assert opcion["distribucion"] == {"Baja": 0, "Adecuada": 3, "Excesiva": 0}
    assert sorted(texto["textos"]) == ["comentario 3", "comentario 4", "comentario 5"]

    assert client.get(f"/api/encuestas/{e['id']}/resultados", headers=DIRECTORA_GII).status_code == 200
    assert client.get(f"/api/encuestas/{e['id']}/resultados", headers=PROFESOR_B).status_code == 403
    assert [x["id"] for x in client.get("/api/encuestas", headers=PROFESOR_A).json()] == [e["id"]]
    assert client.get("/api/encuestas", headers=PROFESOR_B).json() == []


def test_sin_pulso_env_no_se_acepta_identidad_por_cabecera(monkeypatch):
    # Revision I1: el valor por defecto es produccion.
    from app.core import config

    monkeypatch.delenv("PULSO_ENV", raising=False)
    monkeypatch.setenv("CODIGO_PEPPER", "x" * 64)
    monkeypatch.setenv("SESSION_SECRET", "y" * 64)
    config.get_settings.cache_clear()
    try:
        assert config.get_settings().es_dev is False
    finally:
        config.get_settings.cache_clear()


def test_fuera_de_dev_exige_secreto_de_sesion(monkeypatch):
    import pytest

    from app.core import config

    monkeypatch.setenv("PULSO_ENV", "prod")
    monkeypatch.setenv("CODIGO_PEPPER", "x" * 64)
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    config.get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError):
            config.get_settings()
    finally:
        monkeypatch.setenv("PULSO_ENV", "dev")
        config.get_settings.cache_clear()
