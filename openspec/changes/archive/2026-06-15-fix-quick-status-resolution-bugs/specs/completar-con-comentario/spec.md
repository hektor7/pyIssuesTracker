## MODIFIED Requirements

### Requirement: API de completar acepta comentario opcional
El sistema SHALL soportar un parámetro opcional `notes` en el método `complete_issue()` del `RedmineClient` que, cuando se proporciona, se incluye en la petición PUT a Redmine.

#### Scenario: Llamada a API de completar con comentario
- **WHEN** se invoca `complete_issue(issue_id=42, done_ratio=100, status_id=3, notes="Verificado en producción")`
- **THEN** se envía una petición PUT a `/issues/42.json` con `{"issue": {"done_ratio": 100, "status_id": 3, "notes": "Verificado en producción"}}`

### Requirement: Campo due_date con reintento automático al completar
El sistema SHALL intentar incluir `due_date` con la fecha actual en la petición de completar. Si Redmine rechaza la petición con HTTP 422 (`RedmineValidationError`), se DEBE reintentar automáticamente sin el campo `due_date`. Esto evita rechazos en instancias de Redmine que no soportan el campo en el tracker o el usuario no tiene permisos.

#### Scenario: Completar issue con due_date aceptado
- **WHEN** se completa un issue y Redmine acepta el campo `due_date`
- **THEN** el payload incluye `due_date` con la fecha actual y la operación se completa exitosamente

#### Scenario: Completar issue con due_date rechazado — reintento exitoso
- **WHEN** se completa un issue, Redmine rechaza el primer intento con `due_date` (HTTP 422), y el reintento sin `due_date` es aceptado
- **THEN** el payload del reintento NO incluye el campo `due_date` y la operación se completa exitosamente

### Requirement: Validación de estado resuelto antes de completar
El sistema SHALL verificar que existe un estado de tipo "Resuelta" antes de enviar la petición de completar. Si no se encuentra ningún estado resuelto, se DEBE mostrar una advertencia al usuario y NO enviar la petición.

#### Scenario: Estado resuelto no encontrado en el servidor
- **WHEN** el servidor Redmine no tiene un estado llamado "Resuelta", "Resolved" ni similar
- **THEN** se muestra un diálogo de advertencia: "No se encontró un estado 'Resuelta'. La tarea no se puede completar. Contacte con el administrador."
- **AND** no se envía ninguna petición a la API

### Requirement: Mensaje descriptivo cuando Redmine rechaza completar
El sistema SHALL capturar `RedmineValidationError` al completar una tarea y mostrar un mensaje descriptivo con las causas probables y los errores devueltos por la API.

#### Scenario: Redmine rechaza completar por workflow
- **WHEN** Redmine devuelve HTTP 422 al intentar completar una tarea
- **THEN** se muestra un diálogo con las causas probables (estado no válido para el tracker, transición no permitida, fecha no válida) y el detalle de errores de la API
