"""Propiedades de la separacion identidad/respuesta (RUP/02-analisis/anonimato.md)."""

from sqlalchemy import inspect, select

from app.models import CodigoInvitacion, Respuesta, RespuestaItem
from tests.conftest import crear_encuesta_abierta, responder


def test_esquema_sin_vinculo_entre_codigo_y_respuesta(db_session):
    insp = inspect(db_session().get_bind())
    for tabla in ("respuestas", "respuesta_items"):
        destinos = {fk["referred_table"] for fk in insp.get_foreign_keys(tabla)}
        assert "codigos_invitacion" not in destinos
        columnas = {c["name"] for c in insp.get_columns(tabla)}
        assert not columnas & {"codigo_id", "codigo_hash", "creada_en", "enviada_en", "ip"}
    destinos = {fk["referred_table"] for fk in insp.get_foreign_keys("codigos_invitacion")}
    assert destinos == {"encuestas"}
    columnas = {c["name"] for c in insp.get_columns("codigos_invitacion")}
    assert columnas == {"id", "encuesta_id", "codigo_hash", "consumido"}


def test_codigo_no_se_guarda_en_claro(client, db_session):
    _, codigos = crear_encuesta_abierta(client)
    db = db_session()
    hashes = set(db.scalars(select(CodigoInvitacion.codigo_hash)))
    assert not hashes & set(codigos)
    assert all(len(h) == 64 for h in hashes)


def test_identificador_de_respuesta_no_secuencial(client, db_session):
    _, codigos = crear_encuesta_abierta(client)
    for c in codigos[:3]:
        assert responder(client, c).status_code == 204
    db = db_session()
    ids = list(db.scalars(select(Respuesta.id)))
    assert all(len(i) == 32 and not i.isdigit() for i in ids)
    assert all(len(i) == 32 for i in db.scalars(select(RespuestaItem.id)))


def test_consumo_y_respuesta_en_misma_transaccion(client, db_session):
    _, codigos = crear_encuesta_abierta(client)
    db = db_session()
    # Envio invalido (falta obligatoria): ni se consume el codigo ni se guarda nada.
    form = client.post("/api/participacion/acceder", json={"codigo": codigos[0]}).json()
    r = client.post(
        "/api/participacion/enviar",
        json={"codigo": codigos[0], "items": [{"pregunta_id": form["preguntas"][0]["id"], "valor_entero": 3}]},
    )
    assert r.status_code == 422
    assert db.scalar(select(CodigoInvitacion).where(CodigoInvitacion.consumido)) is None
    assert db.scalars(select(Respuesta)).first() is None
    assert responder(client, codigos[0]).status_code == 204
