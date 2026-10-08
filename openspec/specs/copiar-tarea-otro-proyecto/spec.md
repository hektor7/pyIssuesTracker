## Purpose

Definir la acción de copiar una tarea a otro proyecto: selección del destino, preselección y atributos dependientes, asunto y descripción compuesta, propuesta de adjuntos no destructiva y creación sin modificar el origen.

## Requirements

### Requirement: Acción "Mover a otro proyecto" en el menú contextual
El sistema SHALL ofrecer una acción "Mover a otro proyecto..." en el menú contextual genérico de una fila de `TaskTable` (el que se muestra en las columnas que no son Progreso, Asignado a, Estado ni Fecha fin).

#### Scenario: Acción presente en el menú genérico
- **WHEN** el usuario hace clic derecho sobre una fila en la columna "Título"
- **THEN** el menú contextual contiene "Copiar URL", un separador, la acción "Mover a otro proyecto..." y la acción "Abrir en Redmine"

#### Scenario: Emisión de la señal con la tarea correcta
- **WHEN** el usuario selecciona "Mover a otro proyecto..." en una fila
- **THEN** se emite `tarea_mover_proyecto` con el `id` de la issue mostrada en esa fila, resuelto por el rol de ID de la fila y no por el índice

#### Scenario: Clic derecho fuera de una fila
- **WHEN** el usuario hace clic derecho sobre una zona vacía de la tabla
- **THEN** no se muestra ningún menú contextual

### Requirement: Selección del proyecto destino
El sistema SHALL permitir al usuario elegir el proyecto destino mediante un diálogo con un combo buscable que liste todos los proyectos disponibles.

#### Scenario: Selección de proyecto destino
- **WHEN** el usuario elige un proyecto destino y confirma el diálogo
- **THEN** se abre el `TaskDialog` en modo creación con el proyecto destino preseleccionado

#### Scenario: Cancelación de la selección
- **WHEN** el usuario cancela el diálogo de selección de proyecto
- **THEN** no se abre el `TaskDialog` y no se modifica ninguna tarea

### Requirement: Preselección y atributos dependientes del proyecto destino
En modo copia, el sistema SHALL dejar seleccionado el proyecto destino, SHALL recargar las categorías, los miembros y los campos personalizados de ese proyecto, y SHALL dejar vacíos los atributos (tracker, prioridad, categoría, estado) que no existan en el destino sin que la operación falle.

#### Scenario: Atributos sin correspondencia en el destino
- **WHEN** el proyecto destino no tiene el tracker, la prioridad o la categoría de la tarea origen
- **THEN** el atributo correspondiente queda vacío o sin selección
- **AND** no se lanza ningún error y el usuario puede continuar

#### Scenario: Recarga de datos del destino
- **WHEN** se abre el `TaskDialog` en modo copia con un proyecto destino
- **THEN** las categorías, los miembros y los campos personalizados mostrados corresponden al proyecto destino

### Requirement: Asunto copiado y editable
El sistema SHALL copiar el asunto de la tarea origen al campo de asunto del `TaskDialog` en modo copia, y ese campo SHALL ser editable antes de crear la tarea.

#### Scenario: Asunto copiado
- **WHEN** se abre el `TaskDialog` en modo copia para una tarea origen con asunto "Revisar despliegue"
- **THEN** el campo "Asunto" contiene "Revisar despliegue"
- **AND** el usuario puede modificar el texto antes de guardar

### Requirement: Descripción compuesta con cita de la tarea origen
El sistema SHALL componer la descripción de la nueva tarea con el texto literal `Tarea creada partiendo de la tarea #<id_origen>` seguido del contenido de la descripción de la tarea origen citado como blockquote, prefijando cada línea con `> `. El texto resultante SHALL ser editable y lo que se envíe será el contenido final editado.

#### Scenario: Descripción origen multilínea
- **WHEN** la tarea origen #42 tiene la descripción "Primera línea\nSegunda línea"
- **THEN** la descripción propuesta es "Tarea creada partiendo de la tarea #42" seguida de una línea en blanco y de "> Primera línea" y "> Segunda línea" en líneas separadas

#### Scenario: Descripción origen vacía
- **WHEN** la tarea origen no tiene descripción
- **THEN** la descripción propuesta contiene únicamente el texto "Tarea creada partiendo de la tarea #<id_origen>"

#### Scenario: Descripción editable
- **WHEN** el usuario modifica la descripción propuesta y guarda la tarea
- **THEN** la tarea creada en el proyecto destino contiene exactamente el texto editado por el usuario

### Requirement: Propuesta de adjuntos no destructiva
En modo copia, el sistema SHALL mostrar los adjuntos de la tarea origen como una propuesta de copia, con un botón de eliminar por adjunto que SOLO lo quita de la propuesta. En este modo el sistema SHALL NOT llamar a `delete_attachment` ni eliminar el adjunto en el servidor Redmine.

#### Scenario: Adjuntos origen propuestos
- **WHEN** se abre el `TaskDialog` en modo copia para una tarea origen con dos adjuntos
- **THEN** la sección de adjuntos muestra los dos adjuntos de la tarea origen
- **AND** cada adjunto muestra un botón "−" para quitarlo de la propuesta

#### Scenario: Eliminar un adjunto de la propuesta
- **WHEN** el usuario pulsa el botón "−" de un adjunto en modo copia
- **THEN** el adjunto desaparece de la lista de propuesta
- **AND** no se invoca `delete_attachment` y el adjunto permanece intacto en la tarea origen del servidor

#### Scenario: No confundir con el borrado del modo edición
- **WHEN** el `TaskDialog` se abre en modo edición normal
- **THEN** el botón "−" mantiene su comportamiento de eliminación en el servidor descrito en la capacidad `document-attachments-download`

### Requirement: Copia real de adjuntos mediante descarga y resubida
Debido a que la API de Redmine no permite adjuntar un `attachment_id` existente a un issue nuevo, el sistema SHALL descargar cada adjunto propuesto a un fichero temporal, resubirlo con `upload_file` y usar los tokens obtenidos en el parámetro `uploads` del alta.

#### Scenario: Adjuntos propuestos copiados al crear
- **WHEN** el usuario acepta el `TaskDialog` en modo copia conservando dos adjuntos en la propuesta
- **THEN** cada adjunto se descarga a un fichero temporal y se resube mediante `upload_file`
- **AND** los tokens resultantes se incluyen en `uploads` de la llamada a `create_issue`
- **AND** los ficheros temporales se eliminan al finalizar

#### Scenario: Error al copiar un adjunto
- **WHEN** falla la descarga o la resubida de un adjunto propuesto
- **THEN** se muestra un mensaje de error al usuario y no se crea la tarea con datos incompletos

### Requirement: Creación en el proyecto destino sin modificar el origen
El sistema SHALL crear la nueva tarea mediante `create_issue` en el proyecto destino y SHALL NOT modificar la tarea origen.

#### Scenario: Creación efectiva en el destino
- **WHEN** el usuario confirma el `TaskDialog` en modo copia
- **THEN** se llama a `create_issue` con el `project_id` del proyecto destino, el asunto, la descripción compuesta, los campos personalizados y los `uploads` de los adjuntos copiados
- **AND** la tabla de tareas se refresca tras la creación

#### Scenario: Tarea origen intacta
- **WHEN** finaliza la copia de la tarea #42 a otro proyecto
- **THEN** el asunto, la descripción y los adjuntos de la tarea #42 permanecen sin cambios
- **AND** no se llama a `update_issue` sobre el id de la tarea origen

#### Scenario: Copia al mismo proyecto
- **WHEN** el usuario elige como destino el mismo proyecto de la tarea origen
- **THEN** se crea una tarea nueva en ese proyecto con los datos copiados
- **AND** la tarea origen permanece sin cambios
