## Context

Actualmente la API de Redmine ya incluye `include: "attachments"` en `get_issues()` (linea 268 de `redmine_client.py`), pero los datos de adjuntos que devuelve la API se descartan al construir los objetos `RedmineIssue`. No existe dataclass para adjuntos ni se parsean en `get_issue_with_journals()`. El `TaskDialog` no tiene seccion de adjuntos, y no hay mecanismo de descarga de archivos en la aplicacion (salvo el auto-update que usa `httpx.stream`).

La API de Redmine devuelve los attachments en el JSON de cada issue bajo la clave `"attachments"`, con campos: `id`, `filename`, `filesize`, `content_type`, `content_url`, `description`, `author` (con `id` y `name`), `created_on`.

## Goals / Non-Goals

**Goals:**
- Parsear attachments de las respuestas de API y almacenarlos en una dataclass
- Mostrar lista de adjuntos en el `TaskDialog` al editar/ver una tarea
- Permitir descargar cada adjunto individualmente con un boton "Descargar"
- Usar `QFileDialog.getSaveFileName` para que el usuario elija donde guardar
- Descargar via `httpx.stream` (sin dependencias nuevas)

**Non-Goals:**
- Subida de adjuntos (crear nuevos adjuntos en tareas)
- Previsualizacion inline de imagenes o documentos
- Descarga multiple/masiva de adjuntos
- Cache local de adjuntos descargados
- Progreso de descarga con barra de progreso

## Decisions

### 1. Dataclass `RedmineAttachment` con campos planos

Campos: `id`, `filename`, `filesize`, `content_type`, `content_url`, `description`, `author_name`, `created_on`. Sin anidar objetos (ej. `author` se aplana a `author_name`), igual que el resto de dataclasses del cliente.

### 2. Parseo en `get_issues()` y `get_issue_with_journals()`

En `get_issues()`, se extrae `attachments` del JSON de cada issue y se parsea a `list[RedmineAttachment]`. Se anade campo `attachments` a `RedmineIssue`. En `get_issue_with_journals()`, se incluye `"include": "attachments"` en los parametros y se parsean igual.

### 3. Widget inline en `TaskDialog` (no widget separado)

**Alternativa considerada:** Crear `AttachmentsWidget` en `app/widgets/`. **Rechazada** porque el widget es simple (lista de frames con label + boton) y el `TaskDialog` ya tiene widgets inline similares (comments). Mantenerlo inline reduce la friccion de pasar datos y evita un nuevo archivo.

### 4. Boton "Descargar" por adjunto con `QFileDialog.getSaveFileName`

Cada adjunto tiene su propio boton. Al hacer clic:
1. Se abre `QFileDialog.getSaveFileName` con el `filename` original como sugerencia
2. Si el usuario acepta, se llama a `RedmineClient.download_attachment(url, path)`
3. La descarga usa `httpx.Client.stream("GET", url)` con el cliente HTTP ya configurado (cookies, proxy, headers)

**Alternativa considerada:** `QDesktopServices.openUrl(url)` para abrir en navegador. **Rechazada** porque requiere que el navegador tenga la sesion de Redmine activa, y no todos los entornos lo permiten (SSO, VPN).

### 5. Nuevo metodo `RedmineClient.download_attachment(url, dest_path)`

Usa `self._client.stream("GET", url)` (sin `self._base_url` porque `content_url` ya es absoluta). Escribe en chunks de 8 KB a `dest_path`. Lanza `RedmineError` si falla.

### 6. `attachments` en `task_data` del `main_window._editar_tarea()`

Se extrae de `data.get("attachments", [])` — la API de Redmine devuelve `"attachments"` en el JSON del issue cuando se usa `get_issue_with_journals()` con `include=attachments`.

## Risks / Trade-offs

- **[Riesgo] `content_url` requiere autenticacion**: La URL de descarga de Redmine (`/attachments/download/{id}/{filename}`) requiere la misma sesion/cookie/API key que el resto de llamadas. → **Mitigacion**: Se reutiliza el mismo `httpx.Client` con cookies y headers ya configurados.
- **[Riesgo] Archivos grandes bloquean la UI**: `httpx.stream` es sincrono y se ejecuta en el hilo principal. → **Mitigacion**: Para archivos tipicos de Redmine (<50 MB) el bloqueo es aceptable. Si fuera necesario, se puede migrar a `QThread` en el futuro.
- **[Trade-off] Sin barra de progreso**: No se muestra progreso de descarga. → Es aceptable para la mayoria de adjuntos de Redmine (capturas, PDFs, hojas de calculo).
