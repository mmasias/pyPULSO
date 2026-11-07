<div align=right>

<sub>**Documentación técnica:** [Desarrollo](docs/DESARROLLO.md) / [Despliegue](docs/DESPLIEGUE.md) / [Decisiones](docs/DECISIONES.md) / [Anonimato](RUP/02-analisis/anonimato.md)<br>[**RUP:**](RUP/README.md) [Modelo del dominio](RUP/00-modelo-del-dominio/README.md) / [Actores y casos de uso](RUP/01-requisitos/01-actores-casos-uso/README.md) / [Diseño](RUP/03-diseño/README.md)</sub>

</div>

# PULSO - Plataforma Unificada de Levantamiento y Seguimiento de Opiniones

Encuestas de satisfacción anónimas sobre el catálogo académico: cada respuesta llega con su programa, asignatura y curso, y nadie puede saber quién la dio.

## ¿Por qué?

Las encuestas de satisfacción se hacen hoy con formularios genéricos: Google Forms, Microsoft Forms u otros similares. Funcionan para recoger respuestas, pero no para lo que viene antes y después.

<div align=center>

|Quien responde|Quien organiza la encuesta|Quien recibe los resultados|
|-|-|-|
|No sabe si su opinión llegará con su nombre: el formulario pide identificarse o no explica qué guarda.|Prepara un formulario por asignatura y después cruza a mano cada respuesta con programa, asignatura y curso, normalmente en una hoja de cálculo.|Recibe los datos tarde y en el formato que haya usado cada campaña.|
|Si desconfía, responde con cautela o no responde.|Tiene que elegir: enlace abierto (alguien puede responder varias veces) o identificación (se pierde el anonimato).|En un grupo de tres personas, un resultado "anónimo" señala a quien lo dio.|
| |Las preguntas cambian de un año a otro y los cursos dejan de ser comparables.|Comparar con el curso anterior exige rehacer los números a mano.|

</div>

## ¿Qué?

PULSO es el sitio donde se preparan, se lanzan y se consultan las encuestas de satisfacción de una institución académica. Cada encuesta nace ligada al catálogo: programa, asignatura y curso académico. Sobre esa base, cinco garantías:

| Garantía | En la práctica |
|---|---|
| **Anónima, también frente a quien administra el sistema** | Cada participante recibe un código de un solo uso. El código sirve para entrar y deja de servir, pero la respuesta no guarda nada que permita volver a él. Cerrada la encuesta, ni el departamento de calidad, ni el profesorado, ni quien tenga acceso a la base de datos puede saber qué respondió cada persona ([cómo se garantiza](RUP/02-analisis/anonimato.md)) |
| **Una persona, una respuesta** | El código se consume al enviar: no admite un segundo envío |
| **Resultados solo cuando son fiables** | Mientras la encuesta está abierta no se ve ningún resultado, solo cuántos han respondido. Al cerrarla, si no se alcanza el mínimo de participación fijado al crearla, no se muestra nada a nadie |
| **Con contexto desde el origen** | No hay nada que cruzar: cada respuesta pertenece ya a su programa, asignatura y curso |
| **Comparable entre cursos** | Las plantillas se versionan: una plantilla publicada no cambia, y las mejoras crean una versión nueva |

## ¿Para qué?

<div align=center>

| |Qué obtiene|Estado actual|
|-|-|-|
|**Quien responde**<br>(alumnado, personal, profesorado)|Un código, sin cuenta ni contraseña. Un formulario breve, agrupado por secciones. La seguridad de que su respuesta no se le puede atribuir.|Disponible.|
|**Departamento de calidad**|Una vista de todas las encuestas. Plantillas institucionales comunes. La decisión de qué se publica y con qué umbral.|Disponible, con una cuenta de gestión.|
|**Departamentos que preparan encuestas**|Sus propias encuestas sobre el catálogo, siempre bajo la supervisión de calidad.|Hoy trabajan con la cuenta de gestión. Cuentas propias con permisos por departamento: pendiente.|
|**Dirección de programa**|Los resultados publicados de su programa, curso a curso.|Implementado y probado. Pendiente del inicio de sesión institucional para que puedan entrar.|
|**Profesorado**|Los resultados publicados de sus asignaturas.|Implementado y probado. Pendiente del inicio de sesión institucional.|
|**La institución**|Evidencia para los procesos de calidad y acreditación. Datos agregados por encuesta para otros sistemas.|Agregados disponibles. Conexión con el sistema de indicadores (PRISMA): pendiente.|

</div>

## ¿Cómo?

El recorrido de una encuesta, de principio a fin.

### Quien organiza la encuesta

1. **Prepara el cuestionario.** Parte de una plantilla institucional (satisfacción de estudiantes, de personal administrativo, de facultad) o crea una propia: preguntas de escala 1-5 o 1-7, de opción única o de texto libre, agrupadas por secciones.
1. **Crea la encuesta.** Elige plantilla, programa, asignatura, curso académico, fechas de apertura y cierre, y el mínimo de participación por debajo del cual no se publica nada. Una encuesta puede ser de una asignatura, del programa entero o institucional (personal administrativo, facultad).
1. **Emite los códigos.** Tantos como participantes. Se descargan una sola vez y se reparten por el canal habitual: en el aula, por correo, en el campus virtual. PULSO no sabe a quién se entrega cada código.
1. **Abre la encuesta y sigue la participación.** Ve en todo momento cuántos códigos se han usado, pero no qué se ha respondido.
1. **Cierra la encuesta,** a mano o al llegar la fecha de cierre. El cierre es definitivo: desde ese momento las respuestas quedan mezcladas y ya no admite más.
1. **Publica los resultados** si se alcanzó el mínimo de participación.

### Quien responde

1. Entra en "Responder encuesta" e introduce su código. Sin cuenta ni contraseña.
1. Responde y envía. El código deja de servir, y la respuesta no conserva nada que la relacione con él.

### Quien consulta los resultados

1. Ve, por pregunta, cuántas personas eligieron cada valor y la media; los comentarios de texto libre aparecen en orden aleatorio.
1. La dirección ve lo de su programa; el profesorado, lo de sus asignaturas. El departamento de calidad lo ve todo.

### Qué garantiza y qué no

- **Garantiza** que, cerrada la encuesta, nadie puede saber qué respondió cada persona.
- **No oculta quién participó.** Quien reparte los códigos sabe a quién los dio, y el sistema sabe qué códigos se usaron. Es lo mismo que ocurre con cualquier encuesta que controle la participación.
- **Las preguntas personales restan anonimato.** Sexo, edad o país, combinados en un grupo pequeño, pueden señalar a una persona. Por eso lo habitual es no preguntarlos.
- **El texto libre es del participante.** Lo que alguien escribe puede delatarle. El formulario lo advierte, y los comentarios solo se muestran por encima del mínimo de participación y en orden aleatorio.
- **Mientras la encuesta está abierta,** quien tenga acceso directo a la base de datos del servidor podría ver llegar cada respuesta. Lo cubre el control de acceso al servidor, no la aplicación ([detalle](RUP/02-analisis/anonimato.md)).

## ¿Y ahora, qué?

PULSO cubre hoy el ciclo completo de una encuesta: plantilla, lanzamiento, participación, cierre y publicación. Lo que falta está identificado, y su orden depende del uso real: las prioridades salen de las campañas que se lancen y de lo que pidan quienes las organizan.

| Pendiente | Para quién | Situación |
|---|---|---|
| Inicio de sesión institucional | Dirección de programa y profesorado: consultar sus resultados | Resuelto en [pyCelda](https://github.com/mmasias/pyCelda); falta incorporarlo a PULSO |
| Cuentas por departamento, bajo la supervisión de calidad | Departamentos que preparan encuestas | Por hacer en PULSO |
| Retirar las preguntas personales (sexo, edad, país) de las plantillas incluidas, que las traen del instrumento original | Quien responde: más anonimato | Cambio menor en las plantillas ([D14](docs/DECISIONES.md)) |
| Mínimo de participación institucional, común a todas las encuestas | Departamento de calidad | Decisión institucional; el mecanismo ya existe por encuesta ([D3](docs/DECISIONES.md)) |
| Conexión con el catálogo de CELDA | Quien organiza: programas y asignaturas sin mantener un fichero aparte | Depende de que CELDA exponga su catálogo a otras aplicaciones |
| Conexión con PRISMA | La institución: indicadores sin pasos manuales | Los agregados ya existen; falta acordar el formato con PRISMA ([D8](docs/DECISIONES.md)) |
| Participación limitada a los matriculados | Departamento de calidad: el código deja de poder cederse | Depende de conectarse con los sistemas de gestión académica (GUIAA, AGORA, SG...) |
| Mockups de navegación por perfil | Validar el recorrido con quien va a usarlo | Al completar el RUP, como en pyCelda |

PULSO forma parte del [ecosistema CELDA](https://github.com/mmasias/_ECOSISTEMA_CELDA/blob/main/docs/PULSO/README.md). Para instalarlo o contribuir: [Desarrollo](docs/DESARROLLO.md), [Despliegue](docs/DESPLIEGUE.md), [Decisiones](docs/DECISIONES.md) y [RUP](RUP/README.md).
