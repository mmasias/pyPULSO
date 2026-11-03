# Análisis

| Documento | Contenido |
|---|---|
| [anonimato.md](anonimato.md) | Separación identidad/respuesta: mecanismo v1, propiedades, riesgos residuales, evolución a v2 |

## Reglas institucionales modeladas

| Regla | Dónde vive |
|---|---|
| Ventana temporal ligada al calendario académico | `Encuesta.apertura` / `cierre`; `Encuesta.admite_respuestas()` |
| Umbral mínimo de participación | `Encuesta.umbral_minimo`; `services/resultados.py` no devuelve contenido por debajo |
| Comparabilidad longitudinal | `Plantilla` publicada inmutable; cambios = nueva versión con `plantilla_origen_id` |
| Contexto académico | `Encuesta` referencia programa, asignatura y curso de CELDA, validados al crear |
