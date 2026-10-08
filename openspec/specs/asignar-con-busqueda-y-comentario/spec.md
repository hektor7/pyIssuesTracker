## Purpose

Definir el diálogo de asignación de tareas: búsqueda por teclado en el combo de usuarios y comentario opcional que se guarda en la issue al confirmar.

## Requirements

### Requirement: Búsqueda por teclado en combo de usuarios del diálogo de asignación
El sistema SHALL permitir al usuario escribir en el combo de selección de usuario del `AssignDialog` para filtrar dinámicamente los miembros del proyecto, buscando coincidencias en cualquier parte del nombre.

#### Scenario: Búsqueda parcial de usuario
- **WHEN** el usuario desmarca "Asignarme a mí" y escribe "gar" en el combo de usuarios
- **THEN** el dropdown muestra solo los miembros cuyo nombre contenga "gar" (ej. "Edgar", "Margarita"), ignorando mayúsculas/minúsculas

#### Scenario: Combo inhabilitado con checkbox marcado
- **WHEN** el checkbox "Asignarme a mí" está marcado
- **THEN** el combo de usuarios permanece deshabilitado y no acepta entrada de teclado

### Requirement: Campo de comentario en el diálogo de asignación
El sistema SHALL incluir un campo de texto multilínea en el `AssignDialog` para que el usuario pueda añadir una nota opcional que se guardará como comentario en la issue de Redmine al confirmar la asignación.

#### Scenario: Asignar con comentario
- **WHEN** el usuario selecciona un destinatario, escribe "Asignado por urgencia del cliente" en el campo de comentario y pulsa Aceptar
- **THEN** la issue se asigna al usuario seleccionado y se añade la nota "Asignado por urgencia del cliente" en el historial

#### Scenario: Asignar sin comentario
- **WHEN** el usuario selecciona un destinatario, deja el campo de comentario vacío y pulsa Aceptar
- **THEN** la issue se asigna al usuario seleccionado sin añadir ninguna nota

### Requirement: API de asignación acepta comentario opcional
El sistema SHALL soportar un parámetro opcional `notes` en el método `assign_issue()` del `RedmineClient` que, cuando se proporciona, se incluye en la petición PUT a Redmine.

#### Scenario: Llamada a API con comentario
- **WHEN** se invoca `assign_issue(issue_id=42, assigned_to_id=5, notes="Reasignado por prioridad")`
- **THEN** se envía una petición PUT a `/issues/42.json` con `{"issue": {"assigned_to_id": 5, "notes": "Reasignado por prioridad"}}`
