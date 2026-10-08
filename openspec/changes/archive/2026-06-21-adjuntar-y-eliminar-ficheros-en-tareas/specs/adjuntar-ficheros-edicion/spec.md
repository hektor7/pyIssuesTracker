## ADDED Requirements

### Requirement: Seccion de adjuntar archivos visible en edicion
El sistema DEBE mostrar la seccion "Adjuntar archivos" del `TaskDialog` tanto en modo creacion como en modo edicion. El grupo `_upload_group` NO DEBE ocultarse cuando `_is_edit` es `True`.

#### Scenario: Usuario abre tarea en modo edicion y ve la seccion de adjuntar
- **WHEN** se abre el `TaskDialog` en modo edicion (`_is_edit = True`)
- **THEN** la seccion "Adjuntar archivos" es visible
- **AND** el boton "Anadir archivo..." esta habilitado
- **AND** la lista de archivos pendientes de subir se muestra (vacia inicialmente)

#### Scenario: Usuario anade archivos en modo edicion
- **WHEN** el usuario hace clic en "Anadir archivo..." en modo edicion
- **THEN** se abre `QFileDialog.getOpenFileNames` para seleccionar archivos
- **AND** los archivos seleccionados se agregan a `_pending_files`
- **AND** cada archivo se muestra en la lista con nombre, tamano y boton "Eliminar" (de la lista pendiente)

### Requirement: Envio de uploads en update_issue
El metodo `update_issue()` del `RedmineClient` DEBE aceptar un parametro opcional `uploads` con la lista de tokens de archivos subidos, y DEBE incluirlos en el payload de la peticion PUT.

#### Scenario: Update de issue con archivos adjuntos
- **WHEN** se llama a `update_issue(issue_id=123, subject="Nuevo titulo", uploads=[{"token": "abc123", "filename": "doc.pdf", "content_type": "application/pdf"}])`
- **THEN** el payload enviado a `PUT /issues/123.json` incluye `"uploads": [{"token": "abc123", ...}]`

#### Scenario: Update de issue sin archivos adjuntos
- **WHEN** se llama a `update_issue(issue_id=123, subject="Nuevo titulo")` sin el parametro `uploads`
- **THEN** el payload enviado NO incluye el campo `uploads`

### Requirement: MainWindow pasa upload_tokens al editar
Al aceptar el `TaskDialog` en modo edicion, `MainWindow._editar_tarea()` DEBE pasar `uploads=dlg.upload_tokens or None` al llamar a `redmine.update_issue()`, igual que ya se hace en `_nueva_tarea()` para `create_issue()`.

#### Scenario: Edicion con nuevos archivos adjuntos
- **WHEN** el usuario edita una tarea, anade archivos y acepta el dialogo
- **THEN** `_editar_tarea()` llama a `update_issue()` con `uploads=dlg.upload_tokens`
- **AND** los archivos quedan vinculados a la tarea en Redmine

#### Scenario: Edicion sin nuevos archivos adjuntos
- **WHEN** el usuario edita una tarea sin anadir archivos y acepta el dialogo
- **THEN** `_editar_tarea()` llama a `update_issue()` con `uploads=None`
- **AND** el comportamiento de la edicion es identico al actual
