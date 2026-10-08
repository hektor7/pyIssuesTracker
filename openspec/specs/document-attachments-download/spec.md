## Purpose

Definir el manejo de adjuntos de las tareas: parseo desde la API, visualización en el diálogo, descarga reutilizando la sesión y eliminación desde el diálogo.

## Requirements

### Requirement: Parseo de attachments desde la API
El sistema SHALL parsear los datos de adjuntos desde las respuestas JSON de la API de Redmine y almacenarlos en objetos `RedmineAttachment`. Los attachments SHALL incluirse tanto en el listado de issues (`get_issues`) como en el detalle de issue (`get_issue_with_journals`).

#### Scenario: Listado de issues incluye attachments
- **WHEN** se obtiene la lista de issues via `get_issues()`
- **THEN** cada `RedmineIssue` incluye una lista `attachments` con los adjuntos parseados
- **AND** los campos de cada `RedmineAttachment` son: id, filename, filesize, content_type, content_url, description, author_name, created_on

#### Scenario: Issue sin adjuntos
- **WHEN** una issue no tiene adjuntos en la respuesta de la API
- **THEN** el campo `attachments` es una lista vacia

### Requirement: Visualizacion de adjuntos en el dialogo de tarea
El sistema SHALL mostrar una seccion de "Documentos adjuntos" en el `TaskDialog` cuando se abre una tarea que tiene adjuntos. Cada adjunto SHALL mostrar su nombre de archivo, tamano y fecha de creacion, junto con un boton para descargarlo.

#### Scenario: Tarea con adjuntos muestra la seccion
- **WHEN** se abre el `TaskDialog` para una tarea que tiene uno o mas adjuntos
- **THEN** se muestra la seccion "Documentos adjuntos" con la lista de adjuntos
- **AND** cada adjunto muestra: nombre de archivo, tamano en KB/MB, fecha de creacion, y un boton "Descargar"

#### Scenario: Tarea sin adjuntos no muestra la seccion
- **WHEN** se abre el `TaskDialog` para una tarea que no tiene adjuntos
- **THEN** la seccion "Documentos adjuntos" no se muestra o aparece vacia con el texto "(Sin adjuntos)"

### Requirement: Descarga de adjuntos
El sistema SHALL permitir al usuario descargar un adjunto seleccionando la ubicacion de destino mediante un dialogo "Guardar como" nativo del sistema operativo.

#### Scenario: Usuario descarga un adjunto
- **WHEN** el usuario hace clic en el boton "Descargar" de un adjunto
- **THEN** se abre un dialogo `QFileDialog.getSaveFileName` con el nombre original del archivo como sugerencia
- **AND** si el usuario confirma la ubicacion, el archivo se descarga mediante `httpx.stream` a la ruta elegida

#### Scenario: Usuario cancela la descarga
- **WHEN** el usuario hace clic en "Descargar" pero cancela el dialogo "Guardar como"
- **THEN** no se realiza ninguna descarga ni se muestra error

#### Scenario: Error durante la descarga
- **WHEN** ocurre un error durante la descarga (red, permisos, API)
- **THEN** se muestra un mensaje de error `QMessageBox.warning` indicando que la descarga fallo

### Requirement: Cliente de descarga reutiliza la sesion
El metodo de descarga SHALL usar el mismo `httpx.Client` configurado con cookies, proxy y headers de la sesion actual de Redmine para garantizar que la autenticacion funcione correctamente.

#### Scenario: Descarga con sesion autenticada
- **WHEN** se solicita la descarga de un adjunto
- **THEN** la peticion HTTP usa el mismo `httpx.Client` que el resto de llamadas a la API
- **AND** la URL de descarga es la `content_url` proporcionada por la API de Redmine

### Requirement: Eliminacion de adjuntos desde el dialogo de tarea
El sistema SHALL permitir al usuario eliminar un adjunto existente desde la seccion "Documentos adjuntos" del `TaskDialog`, mediante un boton "Eliminar" que usa el endpoint `DELETE /attachments/{id}.json` de la API de Redmine.

#### Scenario: Usuario elimina un adjunto con exito
- **WHEN** el usuario hace clic en el boton "Eliminar" de un adjunto en la seccion "Documentos adjuntos"
- **THEN** se muestra un dialogo de confirmacion `QMessageBox.question`
- **AND** si el usuario confirma, se llama a `redmine.delete_attachment(attachment_id)`
- **AND** si la API retorna exito, el adjunto se elimina de la interfaz inmediatamente

#### Scenario: Error al eliminar adjunto
- **WHEN** el usuario confirma la eliminacion pero la API devuelve error
- **THEN** se muestra `QMessageBox.warning` informando del fallo
- **AND** el adjunto permanece visible en la lista
