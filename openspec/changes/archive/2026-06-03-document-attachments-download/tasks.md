## 1. Modelo de datos y parseo en RedmineClient

- [x] 1.1 Crear dataclass `RedmineAttachment` en `app/services/redmine_client.py` con campos: id, filename, filesize, content_type, content_url, description, author_name, created_on
- [x] 1.2 Anadir campo `attachments: list[RedmineAttachment]` a la dataclass `RedmineIssue` con default `field(default_factory=list)`
- [x] 1.3 Parsear attachments en `get_issues()`: extraer del JSON de cada issue el array `attachments` y convertirlo a `list[RedmineAttachment]`
- [x] 1.4 Modificar `get_issue_with_journals()` para incluir `attachments` en los parametros y parsearlos en el resultado
- [x] 1.5 Implementar `download_attachment(url, dest_path)` en `RedmineClient` usando `httpx.Client.stream` con chunks de 8 KB

## 2. Visualizacion en TaskDialog

- [x] 2.1 Anadir seccion "Documentos adjuntos" en `TaskDialog._setup_ui()` con un `QGroupBox` que contenga un layout vertical para los items de adjuntos
- [x] 2.2 Implementar metodo `_load_attachments()` que recorra la lista de adjuntos del `task_data` y cree un frame por cada uno con: QLabel con nombre, tamano (formateado KB/MB) y fecha, y QPushButton "Descargar"
- [x] 2.3 Conectar el boton "Descargar" de cada adjunto a un slot `_on_download_attachment(attachment)` que: (a) abra `QFileDialog.getSaveFileName`, (b) llame a `self._redmine.download_attachment(url, path)`, (c) muestre error si falla
- [x] 2.4 Si no hay adjuntos, ocultar la seccion o mostrar texto "(Sin adjuntos)"

## 3. Integracion en MainWindow

- [x] 3.1 En `main_window._editar_tarea()`, extraer `attachments` de `data.get("_attachments", [])` y anadirlo al `task_data` que se pasa al `TaskDialog`

## 4. Tests

- [x] 4.1 Test unitario para parseo de attachments en `RedmineClient`: mockear respuesta JSON con attachments y verificar que `RedmineIssue.attachments` se rellena correctamente
- [x] 4.2 Test unitario para `download_attachment`: mockear `httpx.Client.stream` y verificar que los chunks se escriben al archivo destino
- [x] 4.3 Test de integracion: verificar que una issue sin attachments devuelve lista vacia
