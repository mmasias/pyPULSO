# Modelo del dominio

<div align=center>

|![](/images/RUP/00-modelo-del-dominio/modeloDominio.svg)
|-:
|<sub>[Código fuente](modeloDominio.puml)</sub>

</div>

| Concepto | Dueño | Descripción |
|---|---|---|
| Programa, Asignatura, CursoAcademico, Profesor | CELDA | PULSO los referencia por identificador y no los modifica |
| Plantilla | PULSO | Conjunto ordenado de preguntas. Publicada = inmutable; se versiona |
| Pregunta | PULSO | `likert5` (1-5), `likert7` (1-7), `opcion_unica` (lista de opciones) o `texto_libre`; sección opcional (las consecutivas con la misma sección forman un bloque) |
| Encuesta | PULSO | Plantilla aplicada a una asignatura de un programa en un curso académico, con ventana temporal y umbral |
| CodigoInvitacion | PULSO | Credencial de un solo uso. Lado identidad: solo dice si ya se usó |
| Respuesta, RespuestaItem | PULSO | Lado contenido: qué se contestó, sin vínculo con el código |

## Estados

| Encuesta | Plantilla |
|:-:|:-:|
|![](/images/RUP/00-modelo-del-dominio/estados-entidades/encuesta.svg)|![](/images/RUP/00-modelo-del-dominio/estados-entidades/plantilla.svg)|
|<sub>[Código fuente](estados-entidades/encuesta.puml)</sub>|<sub>[Código fuente](estados-entidades/plantilla.puml)</sub>|
