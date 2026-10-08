## Why

Actualmente la API de Redmine solicita los adjuntos (`include: "attachments"`) al listar issues, pero los datos se descartan completamente: no se parsean, no se almacenan en ninguna dataclass, y el `TaskDialog` no muestra ninguna seccion de adjuntos. Los usuarios no tienen forma de saber si una tarea tiene documentos adjuntos ni de descargarlos desde la aplicacion, teniendo que abrir el navegador para acceder a ellos.

## What Changes

- Nueva dataclass `RedmineAttachment` con campos: `id`, `filename`, `filesize`, `content_type`, `content_url`, `description`, `author_name`, `created_on`
- Parseo de attachments en `get_issues()` y `get_issue_with_journals()` desde las respuestas de la API
- Nueva seccion "Documentos adjuntos" en el `TaskDialog` que muestra cada adjunto con:
  - Nombre del archivo, tamaño y fecha
  - Boton "Descargar" para cada adjunto
- Mecanismo de descarga usando `QFileDialog.getSaveFileName` + `httpx` streaming
- Extraccion de attachments en `main_window._editar_tarea()` para pasarlos al `TaskDialog`

## Capabilities

### New Capabilities
- `document-attachments-download`: Visualizacion y descarga de documentos adjuntos desde el dialogo de detalle de tarea. Muestra lista de adjuntos con nombre, tamano y boton de descarga individual.

### Modified Capabilities
<!-- Ninguno - los cambios son puramente aditivos -->

## Impact

- `app/services/redmine_client.py`: Nueva dataclass `RedmineAttachment`, parseo en `get_issues()` y `get_issue_with_journals()`, nuevo metodo `download_attachment()`
- `app/dialogs/task_dialog.py`: Nueva seccion de adjuntos con widgets de lista y botones de descarga
- `app/main_window.py`: Extraer `attachments` del `task_data` en `_editar_tarea()`
- `app/widgets/`: Posible nuevo `attachments_widget.py` (o integrado en `task_dialog.py`)
- No se requieren nuevas dependencias (httpx ya esta en uso)
