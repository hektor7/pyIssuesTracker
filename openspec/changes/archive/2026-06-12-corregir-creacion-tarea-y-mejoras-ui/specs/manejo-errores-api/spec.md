## ADDED Requirements

### Requirement: Visualizar errores de validación de la API
El sistema SHALL capturar y mostrar al usuario los errores de validación devueltos por la API REST de Redmine al crear o editar tareas, incluyendo el detalle de los campos que fallaron la validación.

#### Scenario: Error de validación al crear tarea sin campos obligatorios
- **WHEN** el usuario envía una tarea con datos que Redmine rechaza (HTTP 422)
- **THEN** el sistema muestra un diálogo de error con los mensajes de validación devueltos por la API (ej. "Subject cannot be blank")

#### Scenario: Error de red al crear tarea
- **WHEN** ocurre un error de conexión (timeout, desconexión) al enviar la tarea
- **THEN** el sistema muestra un diálogo de error indicando el problema de conexión

#### Scenario: Éxito en la creación muestra confirmación
- **WHEN** la tarea se crea correctamente en Redmine (HTTP 201)
- **THEN** el sistema recarga la lista de issues y no muestra ningún mensaje de error

### Requirement: Errores de validación en edición de tareas
El sistema SHALL capturar y mostrar errores de validación también al actualizar tareas existentes (HTTP 422 en PUT).

#### Scenario: Error de validación al editar tarea
- **WHEN** el usuario modifica una tarea y Redmine rechaza la actualización (HTTP 422)
- **THEN** el sistema muestra un diálogo de error con los mensajes de validación de la API

### Requirement: Tracker modificable en edición
El sistema SHALL permitir al usuario modificar el campo tracker (tipo de tarea) desde el diálogo de edición de una tarea existente, con el mismo comportamiento de búsqueda que en creación.

#### Scenario: Cambiar tracker en modo edición
- **WHEN** el usuario abre una tarea existente en modo edición
- **THEN** el combo de tracker es editable y permite seleccionar cualquier tracker disponible
- **AND** el tracker actual de la tarea aparece preseleccionado

#### Scenario: Guardar cambio de tracker
- **WHEN** el usuario cambia el tracker y presiona OK
- **THEN** la tarea se actualiza en Redmine con el nuevo tracker
