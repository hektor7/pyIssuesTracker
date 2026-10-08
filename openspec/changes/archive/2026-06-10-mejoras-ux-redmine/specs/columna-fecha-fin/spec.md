## ADDED Requirements

### Requirement: Mostrar fecha de fin en la tabla de tareas
El sistema DEBE mostrar la fecha de fin (`due_date`) de cada tarea en una columna dedicada de la tabla de tareas (`TaskTable`). La columna DEBE ubicarse entre "Fecha inicio" y "Estado". Si la tarea no tiene fecha de fin definida, la celda DEBE mostrarse vacia.

#### Scenario: Tarea con fecha de fin definida
- **WHEN** se cargan las tareas y una tarea tiene `due_date` = `"2026-06-15"`
- **THEN** la columna "Fecha fin" muestra `"2026-06-15"` para esa tarea

#### Scenario: Tarea sin fecha de fin
- **WHEN** se cargan las tareas y una tarea no tiene `due_date` (valor nulo o vacio)
- **THEN** la columna "Fecha fin" muestra una celda vacia para esa tarea

### Requirement: Extraer due_date de la API de Redmine
El `RedmineClient` DEBE incluir el campo `due_date` en el dataclass `RedmineIssue` y parsearlo desde la respuesta JSON de la API REST de Redmine en `get_issues()`.

#### Scenario: La API devuelve due_date
- **WHEN** la API REST de Redmine devuelve `{"issue": {"due_date": "2026-12-31", ...}}`
- **THEN** `RedmineIssue.due_date` contiene `"2026-12-31"`

#### Scenario: La API no incluye due_date
- **WHEN** la API REST devuelve un issue sin el campo `due_date`
- **THEN** `RedmineIssue.due_date` es una cadena vacia `""`

### Requirement: Persistencia del campo due_date en los datos de la tabla
El diccionario de datos construido en `_cargar_issues()` DEBE incluir el campo `due_date` para que la tabla pueda acceder a el.

#### Scenario: Datos incluyen due_date
- **WHEN** `_cargar_issues()` construye el diccionario para la tabla
- **THEN** cada diccionario incluye la clave `"due_date"` con el valor correspondiente

### Requirement: Edicion inline de fecha de fin en la tabla
El sistema DEBE permitir editar la fecha de fin directamente en la celda de la tabla mediante doble clic. Al hacer doble clic en una celda de la columna "Fecha fin", DEBE aparecer un `QDateEdit` inline. Al confirmar el cambio (Enter o cambio de foco), el sistema DEBE persistir la nueva fecha en Redmine via `update_issue(issue_id, due_date=...)` y refrescar la tabla.

#### Scenario: Usuario edita fecha de fin inline
- **WHEN** el usuario hace doble clic en la celda "Fecha fin" de la tarea #123 que muestra "2026-06-15"
- **THEN** aparece un `QDateEdit` con la fecha "2026-06-15" seleccionada
- **AND** al cambiar la fecha a "2026-06-20" y pulsar Enter, se llama a `update_issue(123, due_date="2026-06-20")`
- **AND** la tabla se refresca mostrando la nueva fecha

#### Scenario: Usuario limpia la fecha de fin inline
- **WHEN** el usuario hace doble clic en una celda "Fecha fin" con fecha y borra el valor
- **THEN** el sistema llama a `update_issue(issue_id, due_date="")` para eliminar la fecha de fin
- **AND** la celda queda vacia

#### Scenario: Celda vacia — usuario establece fecha
- **WHEN** el usuario hace doble clic en una celda "Fecha fin" vacia
- **THEN** aparece un `QDateEdit` con la fecha actual
- **AND** al seleccionar una fecha y confirmar, se persiste en Redmine

### Requirement: Campo fecha de fin en dialogo de nueva tarea
El `TaskDialog` en modo creacion DEBE incluir un campo `QDateEdit` con checkbox de activacion para la fecha de fin (`due_date`). El campo DEBE ubicarse debajo de "Fecha inicio". Al crear la tarea, si el checkbox esta marcado, se DEBE enviar `due_date` a `create_issue()`; si no, se DEBE enviar `due_date=""`.

#### Scenario: Usuario establece fecha de fin al crear tarea
- **WHEN** el usuario crea una nueva tarea, marca el checkbox "Fecha fin" y selecciona "2026-12-31"
- **THEN** `create_issue()` recibe `due_date="2026-12-31"`

#### Scenario: Usuario no establece fecha de fin al crear tarea
- **WHEN** el usuario crea una nueva tarea sin marcar el checkbox "Fecha fin"
- **THEN** `create_issue()` recibe `due_date=""` o no incluye el campo

### Requirement: Campo fecha de fin en dialogo de editar tarea
El `TaskDialog` en modo edicion DEBE mostrar el campo "Fecha fin" precargado con el valor actual de `due_date` de la tarea. El usuario DEBE poder modificar o limpiar la fecha.

#### Scenario: Editar tarea con fecha de fin existente
- **WHEN** el usuario abre el dialogo de edicion para una tarea con `due_date="2026-06-15"`
- **THEN** el campo "Fecha fin" muestra "2026-06-15" y el checkbox esta marcado

#### Scenario: Editar tarea sin fecha de fin
- **WHEN** el usuario abre el dialogo de edicion para una tarea sin `due_date`
- **THEN** el campo "Fecha fin" muestra la fecha actual pero el checkbox esta desmarcado
