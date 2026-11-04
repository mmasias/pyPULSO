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

El esquema por sí solo no basta: la revisión adversarial previa al primer commit encontró dos formas de vincular código y respuesta observando el sistema **en el tiempo**, y v1 las cierra con dos medidas más:

| Ataque | Mecanismo | Medida |
|---|---|---|
| Diferencial sobre resultados en vivo | El gestor consulta los agregados antes y después de que se consuma un código concreto (sabe cuál sondeando `/participacion/acceder`); la diferencia es exactamente esa respuesta, texto libre incluido | **Sin resultados mientras la encuesta está en Borrador o Abierta, para ningún rol** (`services/encuestas.py::comprobar_resultados`). Cerrada, el conjunto ya no cambia |
| Orden físico de las filas | El `rowid` de SQLite refleja el orden de envío; cruzado con el log del proxy o con observaciones de `consumido`, la k-ésima respuesta es la del k-ésimo envío | **Al cerrar, las respuestas se reinsertan barajadas** (`SystemRandom`) con identificadores nuevos, y `PRAGMA secure_delete = ON` sobrescribe las filas originales (`_barajar_respuestas`). El cierre es atómico (`UPDATE` condicional bajo cerrojo de escritura): dos cierres no barajan dos veces y ningún envío entra después del barajado con su orden de llegada |

Propiedad resultante, una vez **cerrada** la encuesta, sobre la base de datos en uso: aunque el gestor anote a qué alumno entregó cada código, haya observado la API durante toda la ventana y lea la base de datos completa, solo puede saber **qué alumnos participaron**, nunca **qué contestó cada uno**.

Límite explícito: quien tenga acceso de lectura **continuo** a la base de datos **mientras la encuesta está abierta** puede ver aparecer cada respuesta junto con el código consumido. Ningún diseño que guarde la respuesta en el momento del envío lo evita; la alternativa (retener respuestas en memoria y escribirlas por lotes) pierde datos ante un reinicio. v1 lo trata como control de acceso a la base de datos, no como propiedad del esquema: decisión D1 en [DECISIONES.md](../../docs/DECISIONES.md).

Tests que fijan estas propiedades (`backend/tests/`):

- `test_anonimato.py`: sin FK, marca temporal ni identificador secuencial entre las tablas de identidad y de contenido; el cierre invierte el orden de llegada (barajado determinista en el test), renueva todos los identificadores y activa `secure_delete`.
- `test_encuestas.py::test_sin_resultados_en_vivo_para_nadie`: 409 en resultados con la encuesta abierta, también para el gestor.

## Riesgos residuales (no los resuelve el esquema)

| Riesgo | Mecanismo | Mitigación |
|---|---|---|
| Grupos pequeños | Con 2-3 respuestas, el agregado identifica | Umbral mínimo por encuesta: por debajo no se devuelve contenido a nadie, gestor incluido; no se puede abrir una encuesta con menos códigos que el umbral. Sin suelo técnico todavía: un umbral 1 publica una respuesta individual (D3) |
| Texto libre | Estilo, datos personales mencionados | Aviso en el formulario; textos devueltos en orden aleatorio; se publican solo sobre el umbral. Moderación previa: decisión pendiente (D5) |
| Logs de acceso | El proxy registra IP y hora de cada `POST /enviar` | No vinculan con el contenido (la respuesta no tiene hora con la que cruzarlos), pero revelan quién participó si la IP es atribuible. No registrar cuerpos de petición; rotación corta de logs |
| Copias fuera del fichero | `secure_delete` limpia las páginas del fichero, no el journal de rollback (`pulso.db-journal`, borrado con `unlink` tras el commit: su contenido puede quedar en bloques libres del disco) ni copias de seguridad o snapshots tomados con la encuesta abierta | Copias de seguridad y snapshots con el mismo control de acceso que la base de datos; cifrado del disco si el modelo de amenaza incluye acceso físico |
| Encuesta vencida que nadie consulta | Sigue Abierta y conserva el orden de llegada hasta la primera consulta | Tarea periódica `python -m app.tareas` (timer de systemd en el README) |
| Lectura continua de la BD con la encuesta abierta | Ver la fila nueva junto al código consumido | Control de acceso a la base de datos (ver límite explícito arriba) |
| Encuesta con un solo profesor | El profesor sabe a quién entregó códigos | No afecta a la desvinculación; solo revela participación, igual que en cualquier sistema con control de participación |
| Distribución del código | Quien recibe un código puede cederlo | Aceptado en v1 (sin censo). En v2 el censo del ERP limita a matriculados |

## v2: censo del ERP

El censo del ERP sustituye al código como prueba de pertenencia, pero el principio es el mismo: tabla de participación (`alumno`, `encuesta`, `participó`) sin vínculo con la tabla de respuestas. El código de un solo uso puede mantenerse como credencial derivada del censo o sustituirse por autenticación institucional; en ambos casos la separación de tablas es la que garantiza el anonimato.
