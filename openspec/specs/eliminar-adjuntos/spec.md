## Purpose

Definir la eliminación de adjuntos: método `delete_attachment()` en el cliente y botón 'Eliminar' en cada adjunto del diálogo de tarea, visible en modo creación y edición.

## Requirements

### Requirement: Eliminacion de adjuntos via API
El `RedmineClient` SHALL exponer un metodo `delete_attachment(attachment_id: int) -> bool` que realice una peticion `DELETE /attachments/{id}.json` a la API de Redmine.

#### Scenario: Eliminacion exitosa de un adjunto
- **WHEN** se llama a `delete_attachment(42)` y el servidor responde con codigo 2xx
- **THEN** el metodo retorna `True`
- **AND** el adjunto desaparece del servidor Redmine

#### Scenario: Error al eliminar un adjunto
- **WHEN** se llama a `delete_attachment(42)` y el servidor responde con codigo 4xx o 5xx
- **THEN** el metodo retorna `False`
- **AND** no se lanza excepcion

### Requirement: Boton Eliminar en cada adjunto
En la seccion "Documentos adjuntos" del `TaskDialog`, cada adjunto existente SHALL mostrar un boton "Eliminar" (−) junto al boton "Descargar" existente.

#### Scenario: Adjunto muestra boton Eliminar
- **WHEN** se cargan los adjuntos de una tarea en `_load_attachments()`
- **THEN** cada fila de adjunto incluye un `QPushButton("−")` con tooltip "Eliminar adjunto"

#### Scenario: Usuario hace clic en Eliminar y confirma
- **WHEN** el usuario hace clic en el boton "Eliminar" de un adjunto
- **THEN** se muestra un `QMessageBox.question` preguntando "¿Eliminar permanentemente <filename>?"
- **AND** si el usuario confirma, se llama a `redmine.delete_attachment(attachment_id)`
- **AND** si la eliminacion es exitosa, el adjunto desaparece de la lista visual
- **AND** si la eliminacion falla, se muestra `QMessageBox.warning` con el error

#### Scenario: Usuario cancela la eliminacion
- **WHEN** el usuario hace clic en "Eliminar" pero cancela el dialogo de confirmacion
- **THEN** no se realiza ninguna accion y el adjunto permanece en la lista

### Requirement: Boton Eliminar visible en ambos modos
El boton "Eliminar" SHALL estar presente y funcional tanto cuando el `TaskDialog` se abre en modo creacion como en modo edicion.

#### Scenario: Eliminar adjunto en modo edicion
- **WHEN** se abre el `TaskDialog` en modo edicion y la tarea tiene adjuntos
- **THEN** cada adjunto muestra el boton "Eliminar" funcional

#### Scenario: Eliminar adjunto en modo creacion
- **WHEN** se abre el `TaskDialog` en modo creacion y la tarea tiene adjuntos (caso raro pero posible)
- **THEN** cada adjunto muestra el boton "Eliminar" funcional
