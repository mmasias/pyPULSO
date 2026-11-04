# pyPULSO - Plataforma Unificada de Levantamiento y Seguimiento de Opiniones

<div align=right>

<sub>[**RUP:**](RUP/README.md) [Modelo del dominio](RUP/00-modelo-del-dominio/README.md) / [Actores y casos de uso](RUP/01-requisitos/01-actores-casos-uso/README.md) / [Análisis: anonimato](RUP/02-analisis/anonimato.md) / [Diseño](RUP/03-diseño/README.md)<br>**[Decisiones](docs/DECISIONES.md)** · Satélite del [ecosistema CELDA](https://github.com/mmasias/_ECOSISTEMA_CELDA/blob/main/docs/PULSO/README.md)</sub>

</div>

<div align=center>

|![](images/RUP/00-modelo-del-dominio/modeloDominio.svg)
|-:
|<sub>[Código fuente](RUP/00-modelo-del-dominio/modeloDominio.puml)</sub>

</div>

## ¿Por qué?

La opinión del alumnado sobre la docencia se recoge hoy con formularios genéricos desconectados del catálogo académico. Cada respuesta hay que cruzarla a mano con la asignatura, el profesor y el curso académico, normalmente en una hoja de cálculo.

## ¿Qué?

Un gestor de encuestas docentes construido sobre el catálogo de [CELDA](https://github.com/mmasias/pyCelda): cada encuesta nace vinculada a un programa, una asignatura y un curso académico. Las respuestas son anónimas y llegan ya contextualizadas.

| Problema | Mecanismo |
|---|---|
| Datos sin contexto | La encuesta referencia programa, asignatura y curso de CELDA, validados al crearla |
| Anonimato frente a "un alumno, una respuesta" | Código de invitación de un solo uso, sin ningún vínculo almacenado con la respuesta; sin resultados hasta el cierre; orden de llegada borrado al cerrar ([detalle](RUP/02-analisis/anonimato.md)) |
| Resultados no representativos o identificables | Umbral mínimo por encuesta: por debajo no se muestra nada a nadie |
| Comparabilidad entre cursos | Plantillas versionadas; una plantilla publicada no cambia |
| Ventanas del calendario | Apertura y cierre por encuesta; fuera de ventana no se admiten respuestas |

## ¿Para qué?

| Audiencia | Qué obtiene |
|---|---|
| Gabinete de calidad | Encuestas sobre el catálogo real, participación en tiempo real, publicación controlada por umbral |
| Dirección de programa | Resultados publicados de las asignaturas de su programa |
| Profesorado | Resultados publicados de sus asignaturas, por curso |
| PRISMA | Agregados por encuesta listos para consumir |

## ¿Cómo?

### Gestor de calidad

1. Inicia sesión en la página de entrada.
1. Usa una plantilla institucional (cargadas desde `backend/app/data/plantillas/` con `python -m app.cargar_plantillas`) o crea una: preguntas de escala 1-5 o 1-7, opción única o texto libre, agrupadas por sección.
1. Crea una encuesta: plantilla, programa, asignatura, curso académico, ventana y umbral. Las encuestas del programa entero (p. ej. satisfacción de estudiantes) se crean sobre la asignatura `ENC · ENCUESTA` que tiene cada programa; las del personal administrativo y de la facultad, sobre los programas internos `PAS` y `FACULTAD` (resultados solo para el gestor).
1. Emite tantos códigos como alumnos y los descarga (se muestran una sola vez).
1. Abre la encuesta y sigue la participación (solo recuento: el contenido no se ve hasta el cierre).
1. La cierra (o vence la ventana) y la publica si alcanza el umbral.

### Alumno

1. Desde la página de entrada, "Responder encuesta": introduce su código, sin cuenta ni login.
1. Responde y envía. El código queda inutilizado; la respuesta no guarda nada que la relacione con él.

### Profesor / Director de programa

1. Consulta los resultados publicados de sus asignaturas o de su programa.

### Puesta en marcha (desarrollo)

```bash
# Backend
cd backend
cp .env.example .env          # cambiar a PULSO_ENV=dev; ACCESO_USUARIO y ACCESO_CLAVE_HASH (uv run python -m app.core.claves)
uv venv && uv pip install -e ".[dev]"
uv run pytest
set -a; . ./.env; set +a
uv run uvicorn app.main:app --reload    # http://localhost:8000/api/docs

# Frontend
cd frontend
npm install
npm run dev                   # http://localhost:5173 (proxy /api -> :8000)
```

La página de entrada (`/`) tiene el login del personal (usuario y contraseña) y el acceso del alumno (`/participar`); el resto de la aplicación (`/app`) exige sesión. La cuenta de acceso se configura en `backend/.env` (`ACCESO_USUARIO` y `ACCESO_CLAVE_HASH`, generado con `python3 -m app.core.claves`) y tiene rol Gestor de calidad. El catálogo es el de UNIB (20 programas y 783 asignaturas extraídos de unib.org por `backend/scripts/generar_catalogo_unib.py`, más los programas internos PAS y FACULTAD y una asignatura `ENC · ENCUESTA` por programa: 22 programas y 805 asignaturas); profesores y director, sin cuenta con contraseña todavía, son identidades ficticias que solo se usan en desarrollo por la cabecera `X-Dev-User` (tests y `curl`):

| Identidad | Rol |
|---|---|
| El email de `GESTORES_EMAILS` | Gestor de calidad |
| `director.programa@example.edu` | Director de la Maestría en Dirección Estratégica con Especialidad en Tecnologías de la Información |
| `profesor.a@example.edu` | Imparte TI041 y TI043 de esa maestría en 2026-2027 |
| `profesor.b@example.edu` | Imparte DD014 de esa maestría en 2026-2027 |

### Stack

| Capa | Tecnología | Versión | Dónde corre |
|---|---|---|---|
| API | FastAPI + Uvicorn | FastAPI >= 0.115, Uvicorn >= 0.32 | Servidor, un proceso |
| Lenguaje backend | Python | >= 3.11 (`StrEnum`, `datetime.UTC`); probado con 3.12 | Servidor |
| Dependencias backend | uv, con `backend/uv.lock` | uv 0.13 | Servidor |
| ORM / validación | SQLAlchemy 2, Pydantic 2 | | |
| Base de datos | SQLite, un fichero (`DATABASE_URL`) | La de Python | Disco local del servidor |
| Frontend | React 19 + TypeScript 7 + Vite 8 + react-router 7 | | Ficheros estáticos (`frontend/dist`) |
| Compilación del frontend | Node.js + npm | >= 20.19 o >= 22.12 (lo exige Vite 8); probado con 24 | Solo para compilar |
| Proxy inverso / TLS | Caddy (como pyCelda) | 2.x | Servidor |

Dependencias externas en ejecución: solo Google Fonts (Roboto y Open Sans, desde `fonts.googleapis.com` y `fonts.gstatic.com`). Sin correo, colas ni servicios de terceros; el catálogo de UNIB va dentro del repositorio (`backend/app/data/celda_stub.json`).

### Despliegue en servidor

#### Servidor

| Recurso | Mínimo razonable |
|---|---|
| Sistema | Ubuntu 24.04 LTS o Debian 12/13 (Python 3.12 / 3.11 de serie) |
| CPU / RAM | 1 vCPU, 1 GB. El único coste apreciable es el hash de la contraseña en el login (~0,3 s) |
| Disco | < 1 GB para la aplicación; la base de datos crece del orden de KB por respuesta |
| Red | 80 y 443 abiertos; Uvicorn solo en `127.0.0.1:8000` |
| Dominio | Nombre DNS apuntando al servidor. **HTTPS obligatorio**: fuera de dev la cookie de sesión lleva `Secure` y sin TLS no se puede iniciar sesión |

#### Arquitectura

```
Internet --443--> Caddy --+-- /api/*  --> uvicorn 127.0.0.1:8000 (1 worker) --> pulso.db
                          +-- resto   --> frontend/dist (estático, fallback a index.html)
```

El frontend llama a `/api` en el mismo origen: no hace falta CORS en producción.

#### Variables de entorno (`backend/.env`, permisos 600)

| Variable | Producción |
|---|---|
| `PULSO_ENV` | `prod` (si falta también se asume `prod`; mejor explícita) |
| `DATABASE_URL` | `sqlite:////var/lib/pulso/pulso.db`, ruta absoluta fuera del código |
| `CODIGO_PEPPER` | `openssl rand -hex 32`. Obligatorio. Cambiarlo invalida los códigos emitidos |
| `SESSION_SECRET` | `openssl rand -hex 32`. Obligatorio (>= 32 caracteres). Cambiarlo cierra todas las sesiones |
| `ACCESO_USUARIO` / `ACCESO_CLAVE_HASH` | Cuenta de acceso; el hash con `python3 -m app.core.claves`. La contraseña no se guarda en ningún fichero |
| `FRONTEND_URL` | `https://pulso.<dominio>` (el mismo sitio que sirve Caddy) |
| `CELDA_STUB_PATH` | `app/data/celda_stub.json` |
| `GESTORES_EMAILS` | Vacío: en `prod` la cabecera `X-Dev-User` se ignora |

El hash contiene `$`: escribirlo siempre entre comillas simples (`ACCESO_CLAVE_HASH='pbkdf2_sha256$...'`). systemd retira las comillas y `source` no expande dentro de ellas, así que la misma línea sirve para los dos. Con comillas dobles, `source` expande los `$` y el login falla sin más aviso.

#### Restricciones que condicionan el servidor

1. **Un solo proceso de Uvicorn.** El límite de intentos fallidos (login y códigos) vive en memoria del proceso, y SQLite no admite escritores concurrentes.
2. **IP real del cliente.** Uvicorn con `--proxy-headers --forwarded-allow-ips 127.0.0.1`. Sin ello todos los clientes son la IP del proxy y 5 fallos de cualquiera bloquean a todos; con `*`, `X-Forwarded-For` se falsifica y el límite se elude.
3. **CSP y HSTS en Caddy.** La aplicación solo añade `nosniff`, `X-Frame-Options`, `Referrer-Policy` y `no-store`. La CSP debe permitir Google Fonts.
4. **Tamaño de petición también en Caddy** (`max_size 256KB`): el backend solo lo controla cuando hay `Content-Length`.
5. **Logs de acceso.** Revelan quién participó (IP + hora de `POST /api/participacion/enviar`): sin cuerpos de petición y con rotación corta ([anonimato](RUP/02-analisis/anonimato.md)).
6. **Copias de seguridad** en caliente con `sqlite3 pulso.db ".backup <destino>"`, no con `cp`. La copia contiene datos sensibles: mismos permisos.
7. **Cierre de encuestas vencidas.** Una encuesta vencida se cierra al consultarla; para las que nadie consulta (que conservarían el orden de llegada), un timer de systemd ejecuta `python -m app.tareas` cada hora.
8. **Copias y snapshots** contienen el orden de llegada de las encuestas abiertas en ese momento: mismo control de acceso que la base de datos ([anonimato](RUP/02-analisis/anonimato.md)).

#### `/etc/systemd/system/pulso.service`

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

#### `/etc/systemd/system/pulso-tareas.service` y `.timer`

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

#### `/etc/caddy/Caddyfile`

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
        Content-Security-Policy "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    }
    log {
        output file /var/log/caddy/pulso.log {
            roll_keep_for 168h
        }
    }
}
```

#### Instalación

Todo lo que escribe en `/opt/pulso` se ejecuta como el usuario `pulso` (`sudo -u pulso -H`); el administrador solo instala paquetes y servicios.

```bash
# 1. Requisitos del sistema: Python >= 3.11 (de serie en Ubuntu 24.04 / Debian 12),
#    Caddy 2, Node.js >= 20.19 o >= 22.12 (solo para compilar) y uv instalado para todos
sudo apt install -y python3 python3-venv git sqlite3 caddy
curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin sh

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

#### Actualización

```bash
cd /opt/pulso && sudo -u pulso -H git pull
cd backend && sudo -u pulso -H env UV_PYTHON_PREFERENCE=only-system uv sync --frozen --no-dev
# Antes de reiniciar: columnas nuevas y plantillas nuevas (create_all no altera tablas existentes)
sudo -u pulso -H sh -c 'set -a; . ./.env; set +a; .venv/bin/python -m app.cargar_plantillas --migrar'
cd ../frontend && sudo -u pulso -H npm ci && sudo -u pulso -H npm run build
sudo systemctl restart pulso
```

#### Límites conocidos del despliegue

- Sin migraciones completas: las tablas se crean al arrancar y `python -m app.cargar_plantillas --migrar` solo añade columnas nuevas anulables. Cambios de modelo de mayor calado con datos reales requieren Alembic.
- Sin Dockerfile ni `DEPLOY.md` al estilo pyCelda.
- Una sola cuenta de acceso (Gestor de calidad); profesores y directores, pendientes del login institucional.

## ¿Y ahora qué?

| Pendiente | Referencia |
|---|---|
| Ratificar política de anonimato y valor del umbral con la institución | [D1, D3](docs/DECISIONES.md) |
| Login institucional (OAuth) para el personal | [Diseño](RUP/03-diseño/README.md#autenticación) |
| Adaptador real de CELDA cuando exista API | `backend/app/celda/catalogo.py` |
| Detalle de casos de uso y wireframes | [Requisitos](RUP/01-requisitos/01-actores-casos-uso/README.md) |
| Migraciones (Alembic), imagen Docker | [Despliegue en servidor](#despliegue-en-servidor) |
| v2: censo del ERP, distribución vía PANAL | [Decisiones D2, D3](docs/DECISIONES.md) |
