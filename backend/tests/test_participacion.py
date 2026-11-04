from datetime import UTC, datetime, timedelta

from tests.conftest import GESTOR, crear_encuesta_abierta, crear_plantilla_publicada, responder


def test_flujo_completo(client):
    encuesta, codigos = crear_encuesta_abierta(client)
    form = client.post("/api/participacion/acceder", json={"codigo": codigos[0].lower()})
    assert form.status_code == 200
    assert form.json()["asignatura_nombre"] == "IS101 Ingenieria del Software I"
    assert responder(client, codigos[0], form.json()).status_code == 204
    p = client.get(f"/api/encuestas/{encuesta['id']}/participacion", headers=GESTOR).json()
    assert p["respuestas"] == 1 and p["codigos_emitidos"] == 5


def test_codigo_de_un_solo_uso(client):
    _, codigos = crear_encuesta_abierta(client)
    assert responder(client, codigos[0]).status_code == 204
    r = client.post("/api/participacion/acceder", json={"codigo": codigos[0]})
    assert r.status_code == 403
    assert r.json()["detail"] == "Codigo ya utilizado"


def test_codigo_inexistente(client):
    crear_encuesta_abierta(client)
    r = client.post("/api/participacion/acceder", json={"codigo": "ZZZZZZZZZZ"})
    assert r.status_code == 403


def test_fuera_de_ventana(client):
    plantilla = crear_plantilla_publicada(client)
    ahora = datetime.now(UTC)
    e = client.post(
        "/api/encuestas",
        json={
            "plantilla_id": plantilla["id"],
            "celda_programa_id": 10,
            "celda_asignatura_id": 101,
            "celda_curso_academico_id": 2,
            "apertura": (ahora + timedelta(days=1)).isoformat(),
            "cierre": (ahora + timedelta(days=2)).isoformat(),
            "umbral_minimo": 1,
        },
        headers=GESTOR,
    ).json()
    codigos = client.post(
        f"/api/encuestas/{e['id']}/codigos", json={"cantidad": 1}, headers=GESTOR
    ).json()["codigos"]
    client.post(f"/api/encuestas/{e['id']}/abrir", headers=GESTOR)
    r = client.post("/api/participacion/acceder", json={"codigo": codigos[0]})
    assert r.status_code == 409


def test_valores_fuera_de_rango(client):
    _, codigos = crear_encuesta_abierta(client)
    assert responder(client, codigos[0], likert=6).status_code == 422
    assert responder(client, codigos[0], likert=0).status_code == 422


def test_limite_de_fallos_por_ip(client):
    crear_encuesta_abierta(client)
    for _ in range(5):
        assert client.post("/api/participacion/acceder", json={"codigo": "AAAAAAAAAA"}).status_code == 403
    r = client.post("/api/participacion/acceder", json={"codigo": "AAAAAAAAAA"})
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0


def test_aciertos_no_cuentan_para_el_limite(client):
    # Aula detras de NAT: muchos alumnos validos desde la misma IP.
    _, codigos = crear_encuesta_abierta(client, umbral=1, codigos=8)
    for c in codigos:
        assert responder(client, c).status_code == 204


def test_cuerpo_demasiado_grande(client):
    r = client.post(
        "/api/participacion/acceder",
        content=b"x" * (300 * 1024),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 413
