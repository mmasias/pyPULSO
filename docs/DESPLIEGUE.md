<div align=right>

<sub>[Inicio](../README.md) · [Desarrollo](DESARROLLO.md) · [Despliegue](DESPLIEGUE.md) · [Decisiones](DECISIONES.md) · [RUP](../RUP/README.md)</sub>

</div>

# PULSO > Despliegue en servidor

Instalación y actualización en un servidor propio. Stack y versiones en [DESARROLLO.md](DESARROLLO.md#stack).

## Servidor

| Recurso | Mínimo razonable |
|---|---|
| Sistema | Ubuntu 24.04 LTS o Debian 12/13 (Python 3.12 / 3.11 de serie) |
| CPU / RAM | 1 vCPU, 1 GB. El único coste apreciable es el hash de la contraseña en el login (~0,3 s) |
| Disco | < 1 GB para la aplicación; la base de datos crece del orden de KB por respuesta |
| Red | 80 y 443 abiertos; Uvicorn solo en `127.0.0.1:8000` |
| Dominio | Nombre DNS apuntando al servidor. **HTTPS obligatorio**: fuera de dev la cookie de sesión lleva `Secure` y sin TLS no se puede iniciar sesión |

## Arquitectura

```
Internet --443--> Caddy --+-- /api/*  --> uvicorn 127.0.0.1:8000 (1 worker) --> pulso.db
                          +-- resto   --> frontend/dist (estático, fallback a index.html)
```

El frontend llama a `/api` en el mismo origen: no hace falta CORS en producción.

## Variables de entorno (`backend/.env`, permisos 600)

| Variable | Producción |
|---|---|
| `PULSO_ENV` | `prod` (si falta también se asume `prod`; mejor explícita) |
| `DATABASE_URL` | `sqlite:////var/lib/pulso/pulso.db`, ruta absoluta fuera del código |
| `CODIGO_PEPPER` | `openssl rand -hex 32`. Obligatorio. Cambiarlo invalida los códigos emitidos |
| `SESSION_SECRET` | `openssl rand -hex 32`. Obligatorio (>= 32 caracteres). Cambiarlo cierra todas las sesiones |
| `ACCESO_USUARIO` / `ACCESO_CLAVE_HASH` | Cuenta de acceso; el hash con `python3 -m app.core.claves`. La contraseña no se guarda en ningún fichero |
| `FRONTEND_URL` | `https://pulso.<dominio>` (el mismo sitio que sirve Caddy) |
| `CELDA_STUB_PATH` | `/var/lib/pulso/catalogo.json`: catálogo de la institución, fuera del código (ver [Catálogo académico](#catálogo-académico)). Con el valor por defecto, `app/data/celda_stub.json`, se usa el catálogo de ejemplo del repositorio |
| `GESTORES_EMAILS` | Vacío: en `prod` la cabecera `X-Dev-User` se ignora |

El hash contiene `$`: escribirlo siempre entre comillas simples (`ACCESO_CLAVE_HASH='pbkdf2_sha256$...'`). systemd retira las comillas y `source` no expande dentro de ellas, así que la misma línea sirve para los dos. Con comillas dobles, `source` expande los `$` y el login falla sin más aviso.

## Restricciones que condicionan el servidor

1. **Un solo proceso de Uvicorn.** El límite de intentos fallidos (login y códigos) vive en memoria del proceso, y SQLite no admite escritores concurrentes.
2. **IP real del cliente.** Uvicorn con `--proxy-headers --forwarded-allow-ips 127.0.0.1`. Sin ello todos los clientes son la IP del proxy y 5 fallos de cualquiera bloquean a todos; con `*`, `X-Forwarded-For` se falsifica y el límite se elude.
3. **CSP y HSTS en Caddy.** La aplicación solo añade `nosniff`, `X-Frame-Options`, `Referrer-Policy` y `no-store`. La aplicación no carga recursos de terceros: la CSP admite solo el propio origen.
4. **Tamaño de petición también en Caddy** (`max_size 256KB`): el backend solo lo controla cuando hay `Content-Length`.
5. **Logs de acceso.** Revelan quién participó (IP + hora de `POST /api/participacion/enviar`): sin cuerpos de petición y con rotación corta ([anonimato](../RUP/02-analisis/anonimato.md)).
6. **Copias de seguridad** en caliente con `sqlite3 pulso.db ".backup <destino>"`, no con `cp`. La copia contiene datos sensibles: mismos permisos.
7. **Cierre de encuestas vencidas.** Una encuesta vencida se cierra al consultarla; para las que nadie consulta (que conservarían el orden de llegada), un timer de systemd ejecuta `python -m app.tareas` cada hora.
8. **Copias y snapshots** contienen el orden de llegada de las encuestas abiertas en ese momento: mismo control de acceso que la base de datos ([anonimato](../RUP/02-analisis/anonimato.md)).

## Catálogo académico

Mientras no haya integración real con CELDA, programas, asignaturas, cursos y profesores salen de un JSON (`CELDA_STUB_PATH`). El del repositorio (`backend/app/data/celda_stub.json`) es un ejemplo ficticio: sirve para probar, no para una institución. El de producción va en `/var/lib/pulso/catalogo.json`, fuera del código, para que `git pull` no lo sustituya, y debe estar en su sitio **antes de crear la primera encuesta**: cada encuesta guarda los ids de programa y asignatura, y cambiarlos después las deja apuntando a otros.

| Clave | Contenido |
|---|---|
| `cursos_academicos` | `id`, `etiqueta` (`"2026-2027"`), `activo` |
| `programas` | `id`, `nombre`; opcionales: `nivel` (agrupa los programas en el formulario de nueva encuesta), `departamento`, `directores` (emails) |
| `asignaturas` | `id`, `programa_id`, `codigo`, `nombre`; opcional: `creditos` |
| `imparticiones` | `profesor_email`, `asignatura_id`, `curso_academico_id` |

Reglas que dan por hechas las decisiones [D11-D13](DECISIONES.md). Los tests las comprueban solo sobre el catálogo de ejemplo: el de la institución hay que revisarlo a mano.

- Ids estables: un id no se reutiliza para otro programa o asignatura.
- Cada programa tiene una asignatura `ENC` / `ENCUESTA` con id `programa * 1000 + 999`, sin profesores, para las encuestas del programa entero.
- Programas internos `PAS` (id 9001) y `FACULTAD` (id 9002), con `nivel` `Institucional`, cada uno solo con su `ENC`, sin directores ni profesores: los resultados de sus encuestas solo los ve el gestor. El formulario de nueva encuesta usa ese `nivel` para avisar de quién verá los resultados; sin él, avisa de que los ve la dirección del programa.

`backend/app/data/celda_stub.json` sirve de plantilla del formato.

## `/etc/systemd/system/pulso.service`

```ini
[Unit]
Description=pyPULSO API
After=network.target

[Service]
User=pulso
WorkingDirectory=/opt/pulso/backend
EnvironmentFile=/opt/pulso/backend/.env
ExecStart=/opt/pulso/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log
Restart=on-failure
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/var/lib/pulso

[Install]
WantedBy=multi-user.target
```

## `/etc/systemd/system/pulso-tareas.service` y `.timer`

```ini
# pulso-tareas.service
[Unit]
Description=pyPULSO: cierre de encuestas vencidas

[Service]
Type=oneshot
User=pulso
WorkingDirectory=/opt/pulso/backend
EnvironmentFile=/opt/pulso/backend/.env
ExecStart=/opt/pulso/backend/.venv/bin/python -m app.tareas
```

```ini
# pulso-tareas.timer
[Unit]
Description=pyPULSO: cierre de encuestas vencidas, cada hora

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

## `/etc/caddy/Caddyfile`

```
pulso.<dominio> {
    encode gzip
    request_body {
        max_size 256KB
    }
    handle /api/* {
        reverse_proxy 127.0.0.1:8000
    }
    handle {
        root * /opt/pulso/frontend/dist
        try_files {path} /index.html
        file_server
    }
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        Content-Security-Policy "default-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    }
    log {
        output file /var/log/caddy/pulso.log {
            roll_keep_for 168h
        }
    }
}
```

## Instalación

Todo lo que escribe en `/opt/pulso` se ejecuta como el usuario `pulso` (`sudo -u pulso -H`); el administrador solo instala paquetes y servicios.

```bash
# 1. Requisitos del sistema: Python >= 3.11 (de serie en Ubuntu 24.04 / Debian 12),
#    Caddy 2, Node.js >= 20.19 o >= 22.12 (solo para compilar) y uv instalado para todos
sudo apt install -y python3 python3-venv git sqlite3 caddy
curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin sh
# Node.js: el paquete nodejs de Ubuntu 24.04 / Debian 12 es la 18, insuficiente para Vite 8.
# Instalar Node 22 (p. ej. desde NodeSource) o compilar frontend/dist en otra máquina (paso 5)

# 2. Usuario de sistema (home en /var/lib/pulso: caches de uv y npm) y directorios
sudo useradd --system --create-home --home-dir /var/lib/pulso --shell /usr/sbin/nologin pulso
sudo install -d -o pulso -g pulso -m 750 /opt/pulso

# 3. Código
sudo -u pulso -H git clone https://github.com/mmasias/pyPULSO.git /opt/pulso

# 4. Backend: Python del sistema (no uno descargado en el home del administrador)
cd /opt/pulso/backend
sudo -u pulso -H env UV_PYTHON_PREFERENCE=only-system uv sync --frozen --no-dev
sudo -u pulso -H install -m 600 .env.example .env      # rellenar según la tabla de variables
sudo -u pulso -H .venv/bin/python -m app.core.claves    # hash para ACCESO_CLAVE_HASH, entre comillas simples
# Catálogo de la institución, aportado por el administrador (ver Catálogo académico), antes de crear encuestas
sudo install -o pulso -g pulso -m 640 <ruta>/catalogo.json /var/lib/pulso/catalogo.json
# Plantillas institucionales (app/data/plantillas); --migrar añade columnas nuevas a una BD existente
sudo -u pulso -H sh -c 'set -a; . ./.env; set +a; .venv/bin/python -m app.cargar_plantillas --migrar'

# 5. Frontend (aquí o en otra máquina; al servidor solo hace falta dist/)
cd /opt/pulso/frontend
sudo -u pulso -H npm ci && sudo -u pulso -H npm run build

# 6. Servicios (ficheros de las secciones anteriores)
sudo systemctl daemon-reload
sudo systemctl enable --now pulso pulso-tareas.timer
sudo systemctl reload caddy
curl -s https://pulso.<dominio>/api/health   # {"status":"ok"}
```

Caddy necesita leer `frontend/dist`: o se añade su usuario al grupo `pulso` (`sudo usermod -aG pulso caddy` y reinicio de Caddy), o se copia `dist/` a un directorio propio de Caddy (p. ej. `/srv/pulso`) y se ajusta `root` en el Caddyfile.

## Actualización

```bash
cd /opt/pulso && sudo -u pulso -H git pull
cd backend && sudo -u pulso -H env UV_PYTHON_PREFERENCE=only-system uv sync --frozen --no-dev
# Antes de reiniciar: columnas nuevas y plantillas nuevas (create_all no altera tablas existentes)
sudo -u pulso -H sh -c 'set -a; . ./.env; set +a; .venv/bin/python -m app.cargar_plantillas --migrar'
cd ../frontend && sudo -u pulso -H npm ci && sudo -u pulso -H npm run build
sudo systemctl restart pulso
```

Catálogo propio: si `CELDA_STUB_PATH` apunta al fichero del repositorio (`app/data/celda_stub.json`), `git pull` lo sustituye por la versión del repositorio, y las encuestas existentes quedan apuntando a ids de programa y asignatura que pueden haber cambiado. El catálogo de una institución va fuera del repositorio (`/var/lib/pulso/catalogo.json`) con `CELDA_STUB_PATH` apuntando a él.

## Límites conocidos del despliegue

- Sin migraciones completas: las tablas se crean al arrancar y `python -m app.cargar_plantillas --migrar` solo añade columnas nuevas anulables. Cambios de modelo de mayor calado con datos reales requieren Alembic.
- Sin Dockerfile.
- Una sola cuenta de acceso (Gestor de calidad); profesores y directores, pendientes del login institucional.
