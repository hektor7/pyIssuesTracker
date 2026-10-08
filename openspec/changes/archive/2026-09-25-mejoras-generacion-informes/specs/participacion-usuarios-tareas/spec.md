## MODIFIED Requirements

### Requirement: Parseo de journals con identificador de usuario
El `RedmineClient` SHALL parsear los journals del issue cuando la respuesta los incluya. La dataclass `RedmineJournal` SHALL exponer el `user_id` además del `user_name`, las notas, la fecha y los `details` (lista de cambios de atributo del journal). Los journals sin notas SHALL conservarse (representan cambios), a diferencia del filtrado actual de `get_issue_with_journals`, que solo conserva los que tienen notas. Cada detalle SHALL conservar al menos el nombre de la propiedad modificada, el valor anterior y el valor nuevo.

#### Scenario: Journal con notas
- **WHEN** la respuesta de un issue incluye un journal con `user: {id, name}` y `notes` no vacío
- **THEN** se crea un `RedmineJournal` con `user_id`, `user_name`, `notes` y `created_on`

#### Scenario: Journal solo de cambio
- **WHEN** la respuesta incluye un journal sin `notes` pero con `details`
- **THEN** se conserva el journal con su `user_id`, `notes` vacío y la lista de `details`

#### Scenario: Cambio de asignado en los details
- **WHEN** un journal incluye un detalle con propiedad `assigned_to_id`, valor anterior `2` y valor nuevo `3`
- **THEN** el `RedmineJournal` expone ese detalle con su propiedad y ambos valores

#### Scenario: Journal sin details
- **WHEN** un journal no incluye la clave `details`
- **THEN** su lista de `details` queda vacía

### Requirement: Identificación de usuarios implicados en un issue
El `RedmineIssue` SHALL exponer la lista de identificadores de usuarios implicados, compuesta por el autor, el asignado actual (si lo hay), los autores de los journals y los **asignados históricos** detectados en los `details` de los journals (valores anterior y nuevo de los cambios de `assigned_to_id`/`assigned_to`). La lista SHALL estar sin duplicados y en orden determinista.

#### Scenario: Autor, asignado y journals
- **WHEN** un issue tiene `author.id=1`, `assigned_to.id=2` y journals de los usuarios 2 y 3
- **THEN** los usuarios implicados son `{1, 2, 3}` sin duplicados

#### Scenario: Issue sin asignado ni journals
- **WHEN** un issue solo tiene autor
- **THEN** los usuarios implicados contienen únicamente al autor

#### Scenario: Asignado histórico por valor anterior
- **WHEN** un journal registra un cambio de `assigned_to_id` con `old_value=2` y el usuario 2 ya no es el asignado actual
- **THEN** el usuario 2 aparece en la lista de usuarios implicados

#### Scenario: Asignado histórico por valor nuevo
- **WHEN** un journal registra un cambio de `assigned_to_id` con `new_value=3`
- **THEN** el usuario 3 aparece en la lista de usuarios implicados

#### Scenario: Asignado histórico sin duplicados
- **WHEN** el usuario 2 es a la vez asignado histórico y autor de un journal
- **THEN** el usuario 2 aparece una sola vez en la lista de usuarios implicados

### Requirement: Clasificación por rol de implicación
El sistema SHALL poder clasificar la implicación de un usuario en una tarea en tres roles: **Creador** (autor del issue), **Actualizador** (autor de cualquier journal, con o sin notas) y **Participante** (autor de un journal con notas, asignado actual del issue, o usuario que haya tenido la tarea asignada en algún cambio de `assigned_to_id` registrado en los `details` de los journals). Un mismo usuario SHALL poder cumplir varios roles en la misma tarea.

#### Scenario: Creador
- **WHEN** el usuario coincide con el autor del issue
- **THEN** cumple el rol "Creador"

#### Scenario: Actualizador
- **WHEN** el usuario es autor de al menos un journal, con o sin notas
- **THEN** cumple el rol "Actualizador"

#### Scenario: Participante por comentario
- **WHEN** el usuario es autor de al menos un journal con notas
- **THEN** cumple el rol "Participante"

#### Scenario: Participante por asignación actual
- **WHEN** el usuario es el asignado actual del issue
- **THEN** cumple el rol "Participante"

#### Scenario: Participante por asignación histórica
- **WHEN** el usuario fue el valor anterior de un cambio de `assigned_to_id` y ya no es el asignado actual
- **THEN** cumple el rol "Participante"

#### Scenario: Participante histórico que además comentó
- **WHEN** un usuario tuvo la tarea asignada en el pasado y además firmó journals con notas
- **THEN** cumple el rol "Participante"
- **AND** la tarea aparece en el informe al filtrar por ese usuario con el rol "Participante"

#### Scenario: Asignación histórica coincide con el valor nuevo
- **WHEN** el usuario aparece como valor nuevo de un cambio de `assigned_to_id`
- **THEN** cumple el rol "Participante"

#### Scenario: Varios roles a la vez
- **WHEN** el usuario es el autor del issue y además ha comentado
- **THEN** cumple los roles "Creador" y "Participante" simultáneamente