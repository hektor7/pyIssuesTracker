## Why

El diálogo actual de creación de tareas no ofrece las mismas capacidades que la interfaz web de Redmine: preseleccionar el proyecto activo en el filtro, elegir a quién asignar la tarea directamente, y adjuntar documentos en el momento de creación. Estas carencias obligan al usuario a realizar pasos adicionales tras crear la tarea (editar para asignar, abrir Redmine web para adjuntar archivos), lo que interrumpe el flujo de trabajo y reduce la productividad.

## What Changes

- **Preselección del proyecto según filtro activo**: Al abrir el diálogo de nueva tarea, el combo de proyecto se inicializa automáticamente con el proyecto seleccionado en la barra de filtros (si hay uno), evitando que el usuario tenga que buscarlo manualmente cada vez.
- **Selector de "Asignado a" en el diálogo de crear tarea**: Se añade un combo editable con búsqueda que lista los miembros del proyecto para permitir elegir el asignado directamente al crear la tarea, igual que en la interfaz web de Redmine.
- **Adjuntar documentos al crear tarea**: Se añade una sección en el diálogo de nueva tarea para seleccionar y adjuntar archivos locales, usando la API de subida de archivos de Redmine (`POST /uploads.json`) para obtener tokens e incluirlos en la creación de la issue.

## Capabilities

### New Capabilities
- `preseleccion-proyecto-crear-tarea`: El diálogo de nueva tarea recibe y aplica automáticamente el ID del proyecto seleccionado en el filtro, con carga dinámica de categorías asociada.
- `selector-asignado-crear-tarea`: El diálogo de nueva tarea incluye un combo buscable de "Asignado a" poblado con los miembros del proyecto, y el valor seleccionado se envía en la petición de creación.
- `adjuntar-documentos-crear-tarea`: El diálogo de nueva tarea permite seleccionar archivos locales, subirlos a Redmine mediante la API de uploads, e incluir los tokens resultantes en el payload de creación de la issue.

### Modified Capabilities
- `document-attachments-download`: El cliente Redmine existente (`RedmineClient`) se amplía con un nuevo método `upload_file()` para soportar la subida de archivos. La sección de adjuntos del `TaskDialog` se extiende para funcionar también en modo creación (no solo edición).

## Impact

- **`app/dialogs/task_dialog.py`**: Cambios principales — nuevo parámetro `default_project_id`, nuevo combo "Asignado a", nueva sección de adjuntos para modo creación, nuevo método `_upload_file()` de apoyo, nueva propiedad `assigned_to_id`, nueva propiedad `upload_tokens`.
- **`app/services/redmine_client.py`**: Nuevo método `upload_file()` que hace `POST /uploads.json` con `multipart/form-data`.
- **`app/main_window.py`**: En `_nueva_tarea()` — pasar `default_project_id` y miembros del proyecto al diálogo, y pasar `assigned_to_id` y `uploads` en la llamada a `create_issue`. En `_editar_tarea()` — opcionalmente pasar miembros para el combo de asignado.
