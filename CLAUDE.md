# CLAUDE.md

Convenciones de pyPULSO para cualquier sesión de agente en este repositorio.

## Idioma

Español en todo: código (identificadores de dominio), documentación, commits. Misma convención que pyCelda.

## Invariante de anonimato

Ninguna tabla de contenido (`respuestas`, `respuesta_items`) puede referenciar `codigos_invitacion` ni llevar marca temporal, IP o identificador secuencial; `codigos_invitacion` no lleva marca temporal de consumo. `backend/tests/test_anonimato.py` lo comprueba sobre el esquema. Un cambio que haga fallar esos tests es un cambio de la decisión D1 (`docs/DECISIONES.md`), no un ajuste de tests.

## Umbral

Ningún endpoint devuelve contenido de respuestas de una encuesta por debajo de su umbral, a ningún rol. Toda agregación nueva pasa por `services/resultados.py`.

## Datos de CELDA

PULSO no es dueño de programas, asignaturas, cursos ni profesores. Se acceden solo a través del puerto `app/celda/catalogo.py`; nunca se modelan como tablas propias.

## Estructura

- `backend/app/models`: entidades y reglas propias de la entidad.
- `backend/app/services`: casos de uso y transacciones; lanzan `ErrorDominio` y subclases, que `main.py` traduce a HTTP.
- `backend/app/routers`: HTTP y autorización; sin lógica de negocio.
- `RUP/`: documentación por disciplina. SVG en `images/RUP/<misma ruta>`.

## Diagramas

Al cambiar un `.puml`, regenerar su SVG (`plantuml -tsvg -o "$PWD/images/<dir>" <fichero>`) y verificar por contenido (`grep` del texto nuevo en el SVG), no por fecha ni hash.

## Verificación

```bash
cd backend && uv run pytest
cd frontend && npm run build
```

Declarar siempre qué se verificó de verdad y qué no.
