## MODIFIED Requirements

### Requirement: Menú contextual de cambio rápido de estado
El sistema SHALL mostrar un menú contextual al hacer clic derecho sobre la columna "Estado" de una tarea, listando todos los estados disponibles obtenidos del servidor Redmine. Al seleccionar cualquier estado, se mostrará un diálogo de confirmación antes de ejecutar el cambio.

#### Scenario: Cambiar estado a "Resuelta" con confirmación
- **WHEN** el usuario hace clic derecho en la celda de estado de la tarea #42, selecciona "Resuelta" y confirma en el diálogo
- **THEN** la tarea se actualiza al estado "Resuelta" y la tabla se refresca

#### Scenario: Cancelar cambio de estado
- **WHEN** el usuario hace clic derecho, selecciona "Cerrada" y pulsa "No" en el diálogo de confirmación
- **THEN** la tarea no se modifica

#### Scenario: Estado actual resaltado
- **WHEN** el menú contextual de estado se abre para una tarea cuyo estado actual es "En progreso"
- **THEN** la opción "En progreso" aparece marcada o resaltada visualmente

#### Scenario: Menú con múltiples estados
- **WHEN** el servidor Redmine tiene 7 estados configurados
- **THEN** el menú contextual muestra los 7 estados como opciones seleccionables

### Requirement: Actualización vía API al cambiar estado
El sistema SHALL llamar a `update_issue(issue_id, status_id=N)` al seleccionar un nuevo estado, y refrescar la tabla tras la actualización exitosa.

#### Scenario: Estado actualizado correctamente
- **WHEN** el usuario selecciona "Cerrada" del menú contextual de estado
- **THEN** la tabla se refresca y la columna de estado muestra "Cerrada"

### Requirement: Mensaje descriptivo cuando Redmine rechaza cambio de estado
El sistema SHALL capturar `RedmineValidationError` al cambiar el estado desde el menú contextual y mostrar un mensaje descriptivo indicando que el estado seleccionado puede no ser válido para el workflow del tracker de la tarea, incluyendo los errores devueltos por la API.

#### Scenario: Estado rechazado por workflow
- **WHEN** el usuario selecciona un estado que no está permitido en el workflow del tracker
- **THEN** se muestra un diálogo con el mensaje "Redmine rechazó el cambio de estado. Esto suele ocurrir porque el estado seleccionado no está permitido en el workflow de esta tarea." seguido del detalle de errores de la API
