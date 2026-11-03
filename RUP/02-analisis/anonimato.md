# Anonimato: separación identidad / respuesta

Decisión crítica del proyecto según el [documento de PULSO en el ecosistema CELDA](https://github.com/mmasias/_ECOSISTEMA_CELDA/blob/main/docs/PULSO/README.md). Estado: **propuesta técnica adoptada para v1, pendiente de ratificación institucional** (ver [docs/DECISIONES.md](../../docs/DECISIONES.md), D1).

## Requisito

- Anónima para el profesor evaluado, para el gabinete de calidad y para quien tenga acceso a la base de datos.
- Contextualizada: cada respuesta pertenece a una asignatura, un programa y un curso académico concretos.
- Un solo envío por participante.

## Mecanismo v1: código de un solo uso sin vínculo

| Elemento | Qué guarda | Qué no guarda, a propósito |
|---|---|---|
| `codigos_invitacion` | encuesta, HMAC-SHA256 del código, `consumido` | código en claro, instante de consumo, IP, referencia a la respuesta |
| `respuestas` | encuesta (de ahí el contexto académico) | código, instante de envío, IP, identificador secuencial |
| `respuesta_items` | pregunta, valor | ídem |

Flujo de envío (`app/services/participacion.py`), en una única transacción:

1. Localizar el código por su HMAC; rechazar si no existe, está consumido o la encuesta no admite respuestas.
2. Validar los ítems contra la plantilla.
3. `UPDATE codigos_invitacion SET consumido = 1 WHERE id = ? AND consumido = 0`; si no afecta exactamente a una fila (envío concurrente con el mismo código), abortar.
4. Insertar `Respuesta` + `RespuestaItem` con identificadores `uuid4`.
5. Commit: consumo y respuesta existen juntos o no existen.

Propiedad resultante: aunque el gestor anote a qué alumno entregó cada código y además lea la base de datos completa, solo puede saber **qué alumnos participaron**, nunca **qué contestó cada uno**. No hay columna, clave ni orden que permita la unión.

Los tests de `backend/tests/test_anonimato.py` fijan la propiedad sobre el esquema: si alguien añade una FK o una marca temporal a las tablas de contenido, fallan.

## Riesgos residuales (no los resuelve el esquema)

| Riesgo | Mecanismo | Mitigación |
|---|---|---|
| Grupos pequeños | Con 2-3 respuestas, el agregado identifica | Umbral mínimo por encuesta: por debajo no se devuelve contenido a nadie, gestor incluido; no se puede abrir una encuesta con menos códigos que el umbral |
| Texto libre | Estilo, datos personales mencionados | Aviso en el formulario; textos devueltos en orden aleatorio; se publican solo sobre el umbral. Moderación previa: decisión pendiente (D5) |
| Logs de acceso | El proxy registra IP y hora de cada `POST /enviar` | No vinculan con el contenido (la respuesta no tiene hora con la que cruzarlos), pero revelan quién participó si la IP es atribuible. No registrar cuerpos de petición; rotación corta de logs |
| Orden físico en SQLite | El `rowid` interno de las filas refleja orden de inserción | Sin marca temporal externa con que cruzarlo, no vincula código y respuesta (el código no guarda orden de consumo). Mitigable en v2 con inserción por lotes al cierre si se considera necesario |
| Encuesta con un solo profesor | El profesor sabe a quién entregó códigos | No afecta a la desvinculación; solo revela participación, igual que en cualquier sistema con control de participación |
| Distribución del código | Quien recibe un código puede cederlo | Aceptado en v1 (sin censo). En v2 el censo del ERP limita a matriculados |

## v2: censo del ERP

El censo del ERP sustituye al código como prueba de pertenencia, pero el principio es el mismo: tabla de participación (`alumno`, `encuesta`, `participó`) sin vínculo con la tabla de respuestas. El código de un solo uso puede mantenerse como credencial derivada del censo o sustituirse por autenticación institucional; en ambos casos la separación de tablas es la que garantiza el anonimato.
