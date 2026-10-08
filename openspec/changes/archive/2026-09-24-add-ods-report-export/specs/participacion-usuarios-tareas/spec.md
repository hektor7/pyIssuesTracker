## ADDED Requirements

### Requirement: Parseo de journals con identificador de usuario
El `RedmineClient` SHALL parsear los journals del issue cuando la respuesta los incluya. La dataclass `RedmineJournal` SHALL exponer el `user_id` además del `user_name`, las notas y la fecha. Los journals sin notas SHALL conservarse (representan cambios), a diferencia del filtrado actual de `get_issue_with_journals`, que solo conserva los que tienen notas.

#### Scenario: Journal con notas
- **WHEN** la respuesta de un issue incluye un journal con `user: {id, name}` y `notes` no vacío
- **THEN** se crea un `RedmineJournal` con `user_id`, `user_name`, `notes` y `created_on`

#### Scenario: Journal solo de cambio
- **WHEN** la respuesta incluye un journal sin `notes` pero con `details`
- **THEN** se conserva el journal con su `user_id` y `notes` vacío

### Requirement: Identificación de usuarios implicados en un issue
El `RedmineIssue` SHALL exponer la lista de identificadores de usuarios implicados, compuesta por el autor, el asignado actual (si lo hay) y los autores de los journals. La lista SHALL estar sin duplicados.

#### Scenario: Autor, asignado y journals
- **WHEN** un issue tiene `author.id=1`, `assigned_to.id=2` y journals de los usuarios 2 y 3
- **THEN** los usuarios implicados son `{1, 2, 3}` sin duplicados

#### Scenario: Issue sin asignado ni journals
- **WHEN** un issue solo tiene autor
- **THEN** los usuarios implicados contienen únicamente al autor

### Requirement: Clasificación por rol de implicación
El sistema SHALL poder clasificar la implicación de un usuario en una tarea en tres roles: **Creador** (autor del issue), **Actualizador** (autor de cualquier journal que registre un cambio) y **Participante** (autor de un journal con notas o asignado actual del issue). Un mismo usuario SHALL poder cumplir varios roles en la misma tarea.

#### Scenario: Creador
- **WHEN** el usuario coincide con el autor del issue
- **THEN** cumple el rol "Creador"

#### Scenario: Actualizador
- **WHEN** el usuario es autor de al menos un journal con detalles de cambio
- **THEN** cumple el rol "Actualizador"

#### Scenario: Participante por comentario
- **WHEN** el usuario es autor de al menos un journal con notas
- **THEN** cumple el rol "Participante"

#### Scenario: Participante por asignación
- **WHEN** el usuario es el asignado actual del issue
- **THEN** cumple el rol "Participante"

#### Scenario: Varios roles a la vez
- **WHEN** el usuario es el autor del issue y además ha comentado
- **THEN** cumple los roles "Creador" y "Participante" simultáneamente

### Requirement: Consulta de tareas con journals para el informe
El `RedmineClient` SHALL poder obtener las tareas incluyendo sus journals en una sola petición por proyecto, sin requerir una petición adicional por tarea.

#### Scenario: Obtención en bloque
- **WHEN** se solicitan las tareas de un proyecto con `include_journals=True`
- **THEN** cada `RedmineIssue` devuelta ya incluye sus journals parseados
- **AND** no se realiza una petición GET por issue
