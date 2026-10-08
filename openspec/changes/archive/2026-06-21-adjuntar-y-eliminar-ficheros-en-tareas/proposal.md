## Why

Actualmente, el diálogo de tareas solo permite adjuntar archivos en el modo de creación (`_upload_group` está oculto en edición). Además, no existe forma de eliminar adjuntos ya vinculados a una tarea, ni en creación ni en edición. Esto obliga al usuario a tener que abrir Redmine en el navegador para añadir o quitar documentos, rompiendo el flujo de trabajo desde la aplicación de escritorio.

## What Changes

- Mostrar la sección "Adjuntar archivos" también en el modo de edición, permitiendo añadir nuevos ficheros al modificar una tarea.
- Añadir soporte para `uploads` en el método `update_issue()` del cliente Redmine, enviando los tokens de archivo subidos al actualizar la tarea.
- Pasar los tokens de subida (`upload_tokens`) desde `MainWindow._editar_tarea()` al llamar a `update_issue()`, igual que ya se hace en `_nueva_tarea()`.
- Añadir un botón "Eliminar" (−) junto a cada adjunto existente en la sección "Documentos adjuntos", tanto en creación como en edición, que permita borrar el adjunto del servidor Redmine.
- Implementar el endpoint `DELETE /attachments/{id}.json` en `RedmineClient` para eliminar adjuntos.

## Capabilities

### New Capabilities
- `adjuntar-ficheros-edicion`: Subida de archivos durante la edición de una tarea existente, incluyendo el envío de tokens de subida en la llamada a `update_issue()`.
- `eliminar-adjuntos`: Eliminación de adjuntos existentes desde el diálogo de tarea mediante un botón "Eliminar" (−), usando el endpoint `DELETE /attachments/{id}.json` de la API de Redmine.

### Modified Capabilities
- `document-attachments-download`: Se añade la capacidad de eliminar adjuntos existentes (requisito nuevo: botón de eliminación, confirmación, llamada DELETE). La visualización de adjuntos no cambia, pero se extiende con la acción de eliminación.

## Impact

- `app/dialogs/task_dialog.py`: Desbloquear `_upload_group` en modo edición; añadir botón "Eliminar" en `_load_attachments()`; conectar la señal de eliminar.
- `app/services/redmine_client.py`: Añadir parámetro `uploads` a `update_issue()`; implementar `delete_attachment(attachment_id)`.
- `app/main_window.py`: Pasar `uploads=dlg.upload_tokens` en la llamada a `update_issue()` dentro de `_editar_tarea()`.
