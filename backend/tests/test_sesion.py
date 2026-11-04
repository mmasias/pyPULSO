import base64

from fastapi import Response

from app.core import claves, sesion
from app.core.limites import limitador_login
from tests.conftest import CLAVE_PRUEBAS


def _login(client, usuario="Cuenta Pruebas", clave=CLAVE_PRUEBAS):
    return client.post("/api/auth/login", json={"usuario": usuario, "clave": clave})


def test_login_emite_cookie_httponly_y_da_acceso_de_gestor(client):
    r = _login(client)
    assert r.status_code == 204
    cookie = r.headers["set-cookie"]
    assert "pulso_sesion=" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie
    yo = client.get("/api/yo").json()
    assert yo["email"] == "Cuenta Pruebas" and yo["es_gestor"] is True
    assert client.get("/api/plantillas").status_code == 200


def test_usuario_sin_distinguir_mayusculas(client):
    assert _login(client, usuario="  cuenta pruebas ").status_code == 204


def test_clave_incorrecta_y_usuario_inexistente_mismo_error(client):
    a = _login(client, clave="mala")
    b = _login(client, usuario="otro", clave=CLAVE_PRUEBAS)
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()
    assert "set-cookie" not in a.headers and "set-cookie" not in b.headers


def test_el_login_sin_clave_ya_no_existe(client):
    r = client.post("/api/auth/login", json={"email": "calidad@example.edu"})
    assert r.status_code == 422


def test_logout_cierra_la_sesion(client):
    _login(client)
    assert client.get("/api/yo").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/yo").status_code == 401


def test_cookie_manipulada_rechazada(client):
    _login(client)
    _, firma = client.cookies.get("pulso_sesion").rsplit(".", 1)
    falsa = base64.urlsafe_b64encode(b"otro@example.edu|9999999999").decode() + "." + firma
    client.cookies.set("pulso_sesion", falsa)
    assert client.get("/api/yo").status_code == 401


def test_cookie_caducada_rechazada(monkeypatch):
    monkeypatch.setattr(sesion, "DURACION", -10)
    r = Response()
    sesion.emitir(r, "Cuenta Pruebas")
    valor = r.headers["set-cookie"].split("pulso_sesion=")[1].split(";")[0].strip('"')
    assert sesion.leer(valor) is None


def test_hash_de_clave():
    h = claves.generar("secreta", iteraciones=1000)
    assert h.startswith("pbkdf2_sha256$1000$") and "secreta" not in h
    assert claves.verificar("secreta", h) and not claves.verificar("otra", h)
    assert not claves.verificar("secreta", "basura")


def test_limite_de_intentos_de_login(client):
    limitador_login.reiniciar()
    for _ in range(5):
        assert _login(client, clave="mala").status_code == 401
    r = _login(client)
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0
    limitador_login.reiniciar()


def test_cabecera_dev_no_suplanta_a_la_cuenta_de_acceso(client):
    # Revision I2: la cuenta solo se obtiene con contrasena.
    yo = client.get("/api/yo", headers={"X-Dev-User": "cuenta pruebas"}).json()
    assert yo["es_gestor"] is False
    r = client.post("/api/plantillas", json={"nombre": "x"}, headers={"X-Dev-User": "Cuenta Pruebas"})
    assert r.status_code == 403


def test_rafaga_concurrente_no_elude_el_limite(client, monkeypatch):
    # Revision I3: el intento se reserva antes de la verificacion lenta.
    import threading
    import time

    real = claves.verificar
    monkeypatch.setattr(claves, "verificar", lambda c, h: (time.sleep(0.2), real(c, h))[1])
    limitador_login.reiniciar()
    codigos = []
    barrera = threading.Barrier(20)

    def intento():
        barrera.wait()
        codigos.append(_login(client, clave="mala").status_code)

    hilos = [threading.Thread(target=intento) for _ in range(20)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert codigos.count(401) == 5 and codigos.count(429) == 15
    limitador_login.reiniciar()


def test_acierto_no_consume_intentos(client):
    limitador_login.reiniciar()
    for _ in range(10):
        assert _login(client).status_code == 204
    assert _login(client, clave="mala").status_code == 401


def test_escritura_desde_otro_sitio_rechazada(client):
    _login(client)
    r = client.post("/api/plantillas", json={"nombre": "x"}, headers={"Sec-Fetch-Site": "same-site"})
    assert r.status_code == 403
    r = client.post("/api/plantillas", json={"nombre": "x"}, headers={"Sec-Fetch-Site": "same-origin"})
    assert r.status_code == 201
