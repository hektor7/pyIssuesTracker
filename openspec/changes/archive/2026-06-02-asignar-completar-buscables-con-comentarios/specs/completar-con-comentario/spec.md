## ADDED Requirements

### Requirement: Diálogo propio para completar tarea
El sistema SHALL reemplazar el `QMessageBox.question` actual por un diálogo `CompleteDialog` que muestre un campo de texto multilínea para un comentario opcional y botones Aceptar/Cancelar.

#### Scenario: Completar tarea con comentario
- **WHEN** el usuario pulsa el botón "Completar" en la toolbar, escribe "Cerrada tras verificación en staging" en el campo de comentario y pulsa Aceptar
- **THEN** la tarea se marca como completada (100% progreso, estado "Resuelta") y se añade la nota en el historial

#### Scenario: Completar tarea sin comentario
- **WHEN** el usuario pulsa el botón "Completar", deja el campo vacío y pulsa Aceptar
- **THEN** la tarea se marca como completada sin añadir ninguna nota

#### Scenario: Cancelar acción de completar
- **WHEN** el usuario pulsa el botón "Completar" y luego pulsa Cancelar en el diálogo
- **THEN** la tarea no se modifica y no se realiza ninguna llamada a la API

### Requirement: API de completar acepta comentario opcional
El sistema SHALL soportar un parámetro opcional `notes` en el método `complete_issue()` del `RedmineClient` que, cuando se proporciona, se incluye en la petición PUT a Redmine.

#### Scenario: Llamada a API de completar con comentario
- **WHEN** se invoca `complete_issue(issue_id=42, done_ratio=100, status_id=3, notes="Verificado en producción")`
- **THEN** se envía una petición PUT a `/issues/42.json` con `{"issue": {"done_ratio": 100, "status_id": 3, "notes": "Verificado en producción"}}`
