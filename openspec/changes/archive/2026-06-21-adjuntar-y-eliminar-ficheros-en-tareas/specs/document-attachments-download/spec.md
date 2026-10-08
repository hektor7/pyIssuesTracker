## ADDED Requirements

### Requirement: Eliminacion de adjuntos desde el dialogo de tarea
El sistema DEBE permitir al usuario eliminar un adjunto existente desde la seccion "Documentos adjuntos" del `TaskDialog`, mediante un boton "Eliminar" que usa el endpoint `DELETE /attachments/{id}.json` de la API de Redmine.

#### Scenario: Usuario elimina un adjunto con exito
- **WHEN** el usuario hace clic en el boton "Eliminar" de un adjunto en la seccion "Documentos adjuntos"
- **THEN** se muestra un dialogo de confirmacion `QMessageBox.question`
- **AND** si el usuario confirma, se llama a `redmine.delete_attachment(attachment_id)`
- **AND** si la API retorna exito, el adjunto se elimina de la interfaz inmediatamente

#### Scenario: Error al eliminar adjunto
- **WHEN** el usuario confirma la eliminacion pero la API devuelve error
- **THEN** se muestra `QMessageBox.warning` informando del fallo
- **AND** el adjunto permanece visible en la lista
