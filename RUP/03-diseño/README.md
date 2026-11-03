# Diseño

## Arquitectura

| Capa | Tecnología | Ubicación |
|---|---|---|
| API | FastAPI + SQLAlchemy 2 + Pydantic 2, Python >= 3.11, `uv` | `backend/app` |
| Persistencia | SQLite (mismo criterio que pyCelda) | `DATABASE_URL` |
| Cliente | React 19 + TypeScript + Vite + react-router | `frontend/src` |
| Catálogo CELDA | Puerto `CatalogoCelda`; v1 `StubCatalogoCelda` sobre JSON | `backend/app/celda` |

Estructura del backend, misma división que pyCelda: `models/` (entidades y reglas propias de la entidad), `services/` (casos de uso, transacciones), `schemas/` (contratos de la API), `routers/` (HTTP y autorización), `core/` (configuración, base de datos, autenticación, límites).

## Integración con CELDA

CELDA no expone hoy una API para satélites. El puerto `CatalogoCelda` (`app/celda/catalogo.py`) define exactamente lo que PULSO necesita: programas, asignaturas, cursos académicos, `imparte(email, asignatura, curso)` y `dirige(email, programa)`. La implementación real sustituirá al stub sin cambios en servicios ni routers.

`Encuesta` guarda el identificador CELDA y una copia de la etiqueta legible (`*_nombre`, `curso_academico_etiqueta`): el dato sigue teniendo un único dueño, y el histórico de resultados sigue siendo legible si CELDA renombra o archiva.

## Autenticación

| Quién | v1 | Pendiente |
|---|---|---|
| Personal | Cabecera `X-Dev-User`, solo con `PULSO_ENV=dev`; fuera de dev, 401 | Google OAuth institucional como pyCelda |
| Alumno | Código de invitación | v2: censo del ERP |

## Seguridad

| Control | Implementación |
|---|---|
| Fuerza bruta de códigos | 5 fallos / 15 min / IP -> 429 + `Retry-After` (`core/limites.py`). Solo cuentan fallos: un aula tras NAT comparte IP |
| Espacio de códigos | 10 caracteres de un alfabeto de 31 (~49 bits), `secrets` |
| Almacenamiento de códigos | HMAC-SHA256 con `CODIGO_PEPPER`; obligatorio fuera de dev (arranque falla sin él) |
| Tamaño de entrada | Límite de 256 KiB por `Content-Length`; límites de longitud en todos los esquemas Pydantic |
| Validación | Server-side completa de cada respuesta contra la plantilla |
| Cabeceras | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`; CORS restringido a `FRONTEND_URL` |
| Documentación OpenAPI | Solo en dev |
| Secretos | `.env` ignorado; `.env.example` sin valores |

Límites conocidos: el limitador vive en memoria de un proceso (con varios workers hay que moverlo a almacén compartido); el límite de tamaño no cubre peticiones `chunked` sin `Content-Length` (lo cubre el proxy en despliegue); CSP y HSTS corresponden al proxy (Caddy), aún no configurado.

## Configuración

Variables en [`backend/.env.example`](../../backend/.env.example):

| Variable | Uso |
|---|---|
| `PULSO_ENV` | `dev` habilita `X-Dev-User` y `/api/docs` |
| `DATABASE_URL` | URL SQLAlchemy |
| `CODIGO_PEPPER` | Secreto HMAC de los códigos. Cambiarlo invalida todos los códigos emitidos |
| `GESTORES_EMAILS` | Emails con rol Gestor de calidad, separados por comas |
| `FRONTEND_URL` | Origen permitido por CORS |
| `CELDA_STUB_PATH` | JSON del catálogo CELDA simulado |

## Modelo de datos

<div align=center>

|![](/images/RUP/03-diseño/modelo-datos/DER.svg)
|-:
|<sub>[Código fuente](modelo-datos/DER.puml)</sub>

</div>

Sin migraciones en v1 (`create_all` al arrancar). Antes de la primera instalación con datos reales hay que introducir Alembic.
