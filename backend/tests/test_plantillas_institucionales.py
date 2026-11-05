from collections import Counter

from sqlalchemy import select

from app import cargar_plantillas
from app.models import Plantilla
from tests.conftest import GESTOR


def test_ficheros_validos_y_contenido_de_estudiantes():
    cabecera, preguntas = cargar_plantillas.leer(cargar_plantillas.DIRECTORIO / "01-estudiantes.json")
    assert cabecera.nombre == "Encuesta de satisfacción de estudiantes"
    assert len(preguntas) == 29
    assert Counter(p.tipo for p in preguntas) == {"likert7": 25, "opcion_unica": 2, "texto_libre": 2}
    tfm = [p for p in preguntas if p.seccion and p.seccion.startswith("Trabajo de Fin de Máster")]
    assert len(tfm) == 3 and not any(p.obligatoria for p in tfm)
    assert [p.seccion for p in preguntas[:3]] == ["Datos generales"] * 3
    assert not any(p.obligatoria for p in preguntas[:3])


def test_carga_idempotente(client, db_session, monkeypatch, capsys):
    engine = db_session().get_bind()
    monkeypatch.setattr(cargar_plantillas, "engine", engine)
    monkeypatch.setattr(cargar_plantillas, "SessionLocal", db_session)
    assert cargar_plantillas.main([]) == 0
    assert cargar_plantillas.main([]) == 0
    nombres = list(db_session().scalars(select(Plantilla.nombre)))
    assert nombres.count("Encuesta de satisfacción de estudiantes") == 1
    p = [x for x in client.get("/api/plantillas", headers=GESTOR).json()][0]
    assert p["estado"] == "Publicada" and p["preguntas"][3]["seccion"] == "Atención al estudiante"


def test_likert7_rango_y_resultados(client):
    from tests.conftest import crear_encuesta_abierta

    p = client.post("/api/plantillas", json={"nombre": "Siete"}, headers=GESTOR).json()
    client.post(f"/api/plantillas/{p['id']}/preguntas",
                json={"enunciado": "q", "tipo": "likert7", "seccion": "Bloque"}, headers=GESTOR)
    pub = client.post(f"/api/plantillas/{p['id']}/publicar", headers=GESTOR).json()
    assert pub["preguntas"][0]["seccion"] == "Bloque"
    # crear_encuesta_abierta usa su propia plantilla; aqui basta validar el rango
    from datetime import UTC, datetime, timedelta

    ahora = datetime.now(UTC)
    e = client.post("/api/encuestas", json={
        "plantilla_id": p["id"], "celda_programa_id": 10, "celda_asignatura_id": 101,
        "celda_curso_academico_id": 2, "apertura": (ahora - timedelta(hours=1)).isoformat(),
        "cierre": (ahora + timedelta(days=1)).isoformat(), "umbral_minimo": 1}, headers=GESTOR).json()
    codigos = client.post(f"/api/encuestas/{e['id']}/codigos", json={"cantidad": 3}, headers=GESTOR).json()["codigos"]
    client.post(f"/api/encuestas/{e['id']}/abrir", headers=GESTOR)
    pid = pub["preguntas"][0]["id"]
    enviar = lambda c, v: client.post("/api/participacion/enviar", json={"codigo": c, "items": [{"pregunta_id": pid, "valor_entero": v}]})
    assert enviar(codigos[0], 8).status_code == 422
    assert enviar(codigos[0], 7).status_code == 204
    assert enviar(codigos[1], 1).status_code == 204
    client.post(f"/api/encuestas/{e['id']}/cerrar", headers=GESTOR)
    r = client.get(f"/api/encuestas/{e['id']}/resultados", headers=GESTOR).json()["preguntas"][0]
    assert r["distribucion"] == {"1": 1, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 1}
    assert r["media"] == 4.0 and r["seccion"] == "Bloque"


def test_programas_internos_sin_profesores_ni_director():
    # Encuestas de personal administrativo y de facultad: resultados solo
    # para gestores. Nadie imparte ni dirige PAS ni FACULTAD.
    import json
    from pathlib import Path

    datos = json.loads((Path(__file__).parents[1] / "app/data/celda_stub.json").read_text())
    for nombre in ("PAS", "FACULTAD"):
        prog = [p for p in datos["programas"] if p["nombre"] == nombre]
        assert len(prog) == 1 and prog[0]["directores"] == [], nombre
        asignaturas = {a["id"] for a in datos["asignaturas"] if a["programa_id"] == prog[0]["id"]}
        assert len(asignaturas) == 1, nombre
        assert not [i for i in datos["imparticiones"] if i["asignatura_id"] in asignaturas], nombre


def test_plantilla_personal_administrativo():
    cabecera, preguntas = cargar_plantillas.leer(cargar_plantillas.DIRECTORIO / "02-personal-administrativo.json")
    assert cabecera.nombre == "Encuesta de satisfacción del personal administrativo"
    assert len(preguntas) == 18
    assert Counter(p.tipo for p in preguntas) == {"likert7": 17, "texto_libre": 1}
    assert Counter(p.seccion for p in preguntas) == {
        "Información y transparencia": 6, "Instalaciones e infraestructuras": 6,
        "Motivación y satisfacción": 5, "Observaciones": 1}


def test_cada_programa_tiene_su_asignatura_encuesta():
    # Las encuestas de programa (estudiantes) y las institucionales (en los
    # programas internos PAS y FACULTAD) cuelgan de ENC ENCUESTA: id fijo y
    # sin profesores asignados.
    import json
    from pathlib import Path

    datos = json.loads((Path(__file__).parents[1] / "app/data/celda_stub.json").read_text())
    enc = [a for a in datos["asignaturas"] if a["codigo"] == "ENC"]
    assert sorted(a["programa_id"] for a in enc) == sorted(p["id"] for p in datos["programas"])
    assert all(a["nombre"] == "ENCUESTA" and a["id"] == a["programa_id"] * 1000 + 999 for a in enc)
    ids_enc = {a["id"] for a in enc}
    assert not [i for i in datos["imparticiones"] if i["asignatura_id"] in ids_enc]


def test_plantilla_facultad():
    cabecera, preguntas = cargar_plantillas.leer(cargar_plantillas.DIRECTORIO / "03-facultad.json")
    assert cabecera.nombre == "Encuesta de satisfacción de la facultad"
    assert len(preguntas) == 38
    assert Counter(p.tipo for p in preguntas) == {"likert7": 35, "opcion_unica": 2, "texto_libre": 1}
    assert Counter(p.seccion for p in preguntas) == {
        "Datos generales": 2, "Estructura y calidad del programa": 12,
        "Gestión y resultados de la docencia": 10, "Instalaciones, infraestructuras y servicios": 5,
        "Soporte a la docencia": 4, "Motivación y satisfacción": 4, "Observaciones": 1}
    assert preguntas[-2].enunciado == "Me siento satisfecho de manera general con la universidad."


def test_plantillas_sin_nombre_de_institucion():
    # Plantillas agnosticas: ninguna nombra a una universidad concreta.
    for fichero in sorted(cargar_plantillas.DIRECTORIO.glob("*.json")):
        texto = fichero.read_text(encoding="utf-8")
        assert "Universidad " not in texto and "UNIB" not in texto, fichero.name


def test_ids_fijos_de_programas_internos():
    # Revision I1: si se desplazaran, una encuesta de PAS pasaria a un
    # programa real con director.
    import json
    from pathlib import Path

    datos = json.loads((Path(__file__).parents[1] / "app/data/celda_stub.json").read_text())
    ids = {p["nombre"]: p["id"] for p in datos["programas"] if p["nivel"] == "Institucional"}
    assert ids == {"PAS": 9001, "FACULTAD": 9002}


def test_carga_fallida_no_deja_borradores(client, db_session, monkeypatch):
    # Revision I3: una excepcion a mitad no deja una plantilla a medias.
    import pytest

    engine = db_session().get_bind()
    monkeypatch.setattr(cargar_plantillas, "engine", engine)
    monkeypatch.setattr(cargar_plantillas, "SessionLocal", db_session)
    real = cargar_plantillas.Pregunta
    cuenta = {"n": 0}

    def falla_en_la_quinta(**kw):
        cuenta["n"] += 1
        if cuenta["n"] == 5:
            raise RuntimeError("fallo provocado")
        return real(**kw)

    monkeypatch.setattr(cargar_plantillas, "Pregunta", falla_en_la_quinta)
    with pytest.raises(RuntimeError):
        cargar_plantillas.main([])
    assert list(db_session().scalars(select(Plantilla.nombre))) == []
    monkeypatch.setattr(cargar_plantillas, "Pregunta", real)
    assert cargar_plantillas.main([]) == 0
    assert len(list(db_session().scalars(select(Plantilla)))) == 3


def test_borrador_con_el_mismo_nombre_se_avisa(client, db_session, monkeypatch):
    engine = db_session().get_bind()
    monkeypatch.setattr(cargar_plantillas, "engine", engine)
    monkeypatch.setattr(cargar_plantillas, "SessionLocal", db_session)
    client.post("/api/plantillas", json={"nombre": "Encuesta de satisfacción de estudiantes"}, headers=GESTOR)
    assert cargar_plantillas.main([]) == 1


def test_nueva_version_conserva_secciones(client):
    p = client.post("/api/plantillas", json={"nombre": "Con secciones"}, headers=GESTOR).json()
    client.post(f"/api/plantillas/{p['id']}/preguntas",
                json={"enunciado": "q", "tipo": "likert7", "seccion": "Bloque A"}, headers=GESTOR)
    client.post(f"/api/plantillas/{p['id']}/publicar", headers=GESTOR)
    v2 = client.post(f"/api/plantillas/{p['id']}/nueva-version", headers=GESTOR).json()
    assert v2["preguntas"][0]["seccion"] == "Bloque A" and v2["preguntas"][0]["tipo"] == "likert7"
