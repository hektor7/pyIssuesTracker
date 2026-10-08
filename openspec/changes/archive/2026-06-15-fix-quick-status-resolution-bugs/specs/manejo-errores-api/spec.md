## MODIFIED Requirements

### Requirement: Errores de validación en edición de tareas
El sistema SHALL capturar y mostrar errores de validación también al actualizar tareas existentes (HTTP 422 en PUT).

#### Scenario: Error de validación al editar tarea
- **WHEN** el usuario modifica una tarea y Redmine rechaza la actualización (HTTP 422)
- **THEN** el sistema muestra un diálogo de error con los mensajes de validación de la API

### Requirement: Errores de validación en cambios rápidos
El sistema SHALL capturar `RedmineValidationError` en las operaciones de cambio rápido (menú contextual de progreso, estado y asignación) y mostrar un diálogo con los mensajes de validación devueltos por la API. El mensaje DEBE ser descriptivo e indicar la causa probable del rechazo.

#### Scenario: Error de validación al cambiar estado desde menú contextual
- **WHEN** el usuario intenta cambiar el estado de una tarea a uno no permitido por el workflow y Redmine devuelve HTTP 422
- **THEN** el sistema muestra un mensaje explicativo: "Redmine rechazó el cambio de estado. Esto suele ocurrir porque el estado seleccionado no está permitido en el workflow de esta tarea." seguido del detalle de errores

#### Scenario: Error de validación al completar tarea
- **WHEN** el usuario pulsa "Completada" y Redmine devuelve HTTP 422
- **THEN** el sistema muestra un mensaje explicativo con las causas probables (estado no válido para el tracker, transición no permitida, fecha no válida) y el detalle de errores

#### Scenario: Error de validación al cambiar progreso
- **WHEN** el usuario cambia el progreso desde el menú contextual y Redmine devuelve HTTP 422
- **THEN** el sistema muestra un diálogo con los mensajes de validación de la API
