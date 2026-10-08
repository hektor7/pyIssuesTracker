## ADDED Requirements

### Requirement: Autocompletado de @usuario en campo de descripcion
El sistema DEBE proporcionar autocompletado de nombres de usuario al escribir `@` seguido de texto en el campo de descripcion del `TaskDialog`. Al detectar `@`, el sistema DEBE mostrar un popup con los miembros del proyecto actual, filtrados incrementalmente segun el texto tras la `@`.

#### Scenario: Usuario escribe @ y aparece autocompletado
- **WHEN** el usuario escribe `@` en el campo de descripcion en un dialogo de tarea con proyecto seleccionado
- **THEN** aparece un popup con la lista de miembros del proyecto
- **AND** los miembros se filtran a medida que el usuario escribe mas caracteres

#### Scenario: Usuario selecciona un miembro del autocompletado
- **WHEN** el usuario escribe `@mar` y el popup muestra "Maria Garcia" y "Martin Lopez"
- **THEN** al seleccionar "Maria Garcia" (con Enter o click), se reemplaza `@mar` por `@Maria Garcia` en el texto

#### Scenario: Usuario cierra el autocompletado con Escape
- **WHEN** el popup de autocompletado esta visible
- **THEN** al pulsar Escape, el popup se cierra y el texto `@` queda sin cambios

#### Scenario: Sin miembros que coincidan
- **WHEN** el usuario escribe `@xyz` y ningun miembro del proyecto contiene "xyz"
- **THEN** el popup no se muestra (o se muestra vacio y se cierra)

### Requirement: Autocompletado de @usuario en campo de comentarios
El sistema DEBE proporcionar el mismo autocompletado de `@usuario` en el campo de comentarios del `CommentsWidget`, usando la lista de miembros del proyecto de la tarea actual.

#### Scenario: Usuario escribe @ en un comentario
- **WHEN** el usuario escribe `@` en el campo de comentario del `CommentsWidget`
- **THEN** se muestra el mismo popup de autocompletado con los miembros del proyecto

#### Scenario: Proyecto sin miembros cargados
- **WHEN** el usuario escribe `@` en un comentario pero el proyecto no tiene miembros disponibles (no se han cargado)
- **THEN** no se muestra ningun popup de autocompletado

### Requirement: Integracion del autocompletado con RedmineClient
El sistema DEBE obtener la lista de miembros del proyecto desde `RedmineClient.get_project_memberships()`. El `CommentsWidget` y el `TaskDialog` DEBEN recibir la lista de miembros (o el `RedmineClient` y `project_id`) para poder construir el modelo del `QCompleter`.

#### Scenario: TaskDialog recibe miembros del proyecto
- **WHEN** se abre el `TaskDialog` para crear/editar una tarea
- **THEN** el dialogo tiene acceso a la lista de miembros del proyecto actual
- **AND** el `QCompleter` de la descripcion se inicializa con esos nombres

#### Scenario: CommentsWidget recibe miembros del proyecto
- **WHEN** se carga un `CommentsWidget` en el `TaskDialog`
- **THEN** el widget recibe la lista de miembros (o la referencia al cliente y project_id)
- **AND** el `QCompleter` del campo de comentario se inicializa con esos nombres

### Requirement: Comportamiento no intrusivo del autocompletado
El autocompletado NO DEBE interferir con la escritura normal. Solo DEBE activarse cuando el caracter inmediatamente anterior es `@` (o cuando el cursor esta justo despues de `@` seguido de texto sin espacios). El popup DEBE ocupar un espacio reducido (maximo 5 elementos visibles, con scroll para el resto).

#### Scenario: Usuario escribe @ sin intencion de mencionar
- **WHEN** el usuario escribe `@` en un contexto donde no es una mencion (ej. "@" como texto literal)
- **THEN** si no hay miembros coincidentes, el popup no se muestra y la escritura continua normalmente

#### Scenario: Usuario escribe texto normal sin @
- **WHEN** el usuario escribe texto sin el caracter `@`
- **THEN** el autocompletado no se activa en ningun momento
