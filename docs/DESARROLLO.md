<div align=right>

<sub>[Inicio](../README.md) · [Desarrollo](DESARROLLO.md) · [Despliegue](DESPLIEGUE.md) · [Decisiones](DECISIONES.md) · [RUP](../RUP/README.md)</sub>

</div>

# PULSO > Desarrollo

Puesta en marcha local, identidades de desarrollo y stack. El despliegue en un servidor está en [DESPLIEGUE.md](DESPLIEGUE.md).

## Puesta en marcha

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

La página de entrada (`/`) tiene el login del personal (usuario y contraseña) y el acceso del alumno (`/participar`); el resto de la aplicación (`/app`) exige sesión. La cuenta de acceso se configura en `backend/.env` (`ACCESO_USUARIO` y `ACCESO_CLAVE_HASH`, generado con `python3 -m app.core.claves`) y tiene rol Gestor de calidad. El catálogo es un ejemplo ficticio (`backend/app/data/celda_stub.json`: 5 programas de grado, máster y doctorado, más los programas internos PAS y FACULTAD y una asignatura `ENC · ENCUESTA` por programa: 7 programas y 30 asignaturas). Para usar el de una institución, `CELDA_STUB_PATH` apunta a un JSON con la misma estructura (ver [Diseño](../RUP/03-diseño/README.md#integración-con-celda)); profesores y director, sin cuenta con contraseña todavía, son identidades ficticias que solo se usan en desarrollo por la cabecera `X-Dev-User` (tests y `curl`):

| Identidad | Rol |
|---|---|
| El email de `GESTORES_EMAILS` | Gestor de calidad |
| `director.programa@example.edu` | Director del Máster en Dirección de Proyectos |
| `profesor.a@example.edu` | Imparte DP01 y DP02 de ese máster en 2026-2027 |
| `profesor.b@example.edu` | Imparte DP04 de ese máster en 2026-2027 |

## Stack

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

Dependencias externas en ejecución: ninguna. Tipografías del sistema, sin correo, colas ni servicios de terceros; el catálogo va en un fichero JSON local (`CELDA_STUB_PATH`).
