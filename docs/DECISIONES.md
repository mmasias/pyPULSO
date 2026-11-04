# Decisiones

Decisiones de diseño previas a la construcción que enumera el [documento de PULSO](https://github.com/mmasias/_ECOSISTEMA_CELDA/blob/main/docs/PULSO/README.md). "Adoptada (técnica)" significa que v1 la implementa como propuesta y que la institución puede revocarla; las políticas son institucionales, no técnicas.

| Id | Decisión | Estado | v1 implementa | Abierto |
|---|---|---|---|---|
| D1 | Garantía de anonimato | Adoptada (técnica), pendiente de ratificación | Código de un solo uso sin vínculo con la respuesta; sin resultados hasta el cierre; respuestas barajadas al cerrar ([anonimato.md](../RUP/02-analisis/anonimato.md)) | Política institucional escrita; quién puede leer la base de datos mientras hay encuestas abiertas |
| D2 | Distribución | Adoptada v1 | El gestor emite N códigos por encuesta y los descarga; el profesor o el gabinete los reparte (aula, email, LMS manual) | Canal LMS vía PANAL; censo del ERP (v2) |
| D3 | Umbral mínimo de participación | Mecanismo adoptado; valor pendiente | Umbral por encuesta, fijado por el gestor (mínimo técnico actual: 1). Sin umbral no hay resultados para nadie | Valor institucional y suelo técnico (absoluto, porcentual sobre matriculados, o ambos). El porcentual requiere censo (v2) |
| D4 | Plantillas reutilizables | Adoptada | Catálogo de plantillas versionadas; publicada = inmutable | Catálogo institucional inicial |
| D5 | Texto libre | Pendiente | Se admite, opcional; aviso al alumno; orden aleatorio; sujeto al umbral | Moderación previa a la publicación, o supresión del texto libre en encuestas de grupos pequeños |
| D6 | Granularidad de la encuesta | Adoptada v1 | Una encuesta = asignatura + programa + curso académico. Todos los profesores que la imparten ven el resultado | Encuesta por profesor cuando hay varios (requiere decidir si un alumno evalúa a cada uno por separado) |
| D7 | Destinatarios distintos de alumnos | Pendiente | Solo alumnos | Encuestas a profesores y directores (el documento de PULSO las contempla) |
| D8 | Exportación a PRISMA | Pendiente | Agregados vía `GET /api/encuestas/{id}/resultados` | Contrato de indicadores para PRISMA |
| D9 | Catálogo académico de desarrollo | Adoptada | 20 programas y 783 asignaturas de UNIB extraídos de los planes de estudio publicados en unib.org (`backend/scripts/generar_catalogo_unib.py`). Una asignatura compartida por varios programas aparece una vez por programa (como `AsignaturaPrograma` en CELDA) | Sustituir por el adaptador real de CELDA; profesores y directores reales |
