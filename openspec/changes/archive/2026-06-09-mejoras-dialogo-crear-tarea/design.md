## Context

La aplicación `pyIssuesTracker` es un cliente de escritorio PyQt6 para Redmine. El diálogo de creación/edición de tareas (`TaskDialog`) actualmente permite configurar proyecto, tracker, asunto, descripción, prioridad, categoría, fecha de inicio y progreso. En modo edición también muestra estado, checklist, comentarios y adjuntos existentes (solo lectura/descarga).

La barra de filtros (`FilterBar`) ya tiene un combo de proyecto, y el `MainWindow` ya obtiene los miembros del proyecto (`get_project_memberships`) para poblar el filtro de "Asignado a" y el diálogo `AssignDialog`. Sin embargo, esta información no se aprovecha en el diálogo de nueva tarea.

Redmine expone una API REST para subir archivos: `POST /uploads.json` con `Content-Type: application/octet-stream` (o `multipart/form-data`) que devuelve un token. Este token se incluye en el campo `uploads` del payload de creación/actualización de issues.

## Goals / Non-Goals

**Goals:**
- Preseleccionar el proyecto en el diálogo de nueva tarea según el filtro activo, con carga inmediata de categorías.
- Permitir elegir "Asignado a" en el diálogo de nueva tarea (y edición), con combo buscable poblado desde los miembros del proyecto.
- Permitir adjuntar archivos locales al crear una tarea, subiéndolos a Redmine y vinculándolos a la nueva issue.

**Non-Goals:**
- No se modifica el diálogo de edición para añadir/quitar adjuntos en tareas existentes (solo se implementa en creación). La gestión de adjuntos en edición se relega a una futura iteración.
- No se modifica el comportamiento del filtro de "Asignado a" en la barra de filtros.
- No se añade drag & drop para adjuntos (se usará el selector de archivos nativo).

## Decisions

### 1. Paso de proyecto por defecto mediante parámetro en constructor

**Decisión**: Añadir un parámetro `default_project_id: int = 0` al constructor de `TaskDialog`. Si es > 0, se invoca `_set_combo_data(self._project_combo, default_project_id)` dentro de `_populate_fields()` (incluso en modo creación, adaptando la condición actual que solo puebla en edición).

**Alternativa considerada**: Usar una señal o método setter post-construcción. Se descartó porque añade complejidad innecesaria; el parámetro en constructor es más directo y sigue el patrón existente de `initial_categories`.

### 2. Combo de "Asignado a" en TaskDialog

**Decisión**: Añadir un combo buscable (mismo patrón `_make_searchable_combo`) en el grupo "Detalles". Se añade un parámetro `members: list[tuple[int, str]]` al constructor. Cuando el proyecto cambia, se recargan los miembros mediante `_load_members_for_project()`. Se expone una propiedad `assigned_to_id`.

**Alternativa considerada**: Reutilizar el `AssignDialog` existente. Se descartó porque rompe el flujo inline del diálogo de creación y obliga a un paso extra.

### 3. Subida de adjuntos en creación

**Decisión**: 
- Añadir método `upload_file(file_path: str) -> dict` en `RedmineClient` que hace `POST /uploads.json` con el contenido binario del archivo y `Content-Type: application/octet-stream`.
- En `TaskDialog`, añadir una sección "Documentos adjuntos" visible también en modo creación (actualmente solo en edición). Incluye un botón "Añadir archivo" que abre `QFileDialog` y almacena los paths seleccionados.
- Los archivos se suben al hacer clic en "Aceptar" (dentro de `_validate_and_accept` o antes de `accept()`), almacenando los tokens en `self._pending_uploads`.
- Propiedad `upload_tokens` expone la lista de tokens para que `_nueva_tarea()` los pase a `create_issue`.

**Alternativa considerada**: Subir archivos uno a uno en tiempo real al seleccionarlos. Se descartó para evitar subidas innecesarias si el usuario cancela el diálogo.

### 4. Extensión de `create_issue` para soportar uploads

**Decisión**: Añadir un parámetro `uploads: list[dict] | None = None` al método `create_issue` de `RedmineClient`. Si se proporciona, se incluye en el payload como `"uploads": uploads`.

**Alternativa considerada**: Hacer una segunda llamada `update_issue` tras crear. Se descartó porque genera dos peticiones y la issue aparece momentáneamente sin adjuntos.

## Risks / Trade-offs

- **[Riesgo] Falla en la subida de archivos grandes**: La subida de archivos > 50 MB podría timeout. → **Mitigación**: Usar streaming con `httpx` y un timeout amplio (120s). Mostrar barra de progreso si se implementa en futuro.
- **[Riesgo] El plugin de uploads no está habilitado en el servidor Redmine**: Algunas instancias pueden tener deshabilitada la API de uploads. → **Mitigación**: Capturar error HTTP 404/405 en `upload_file` y mostrar mensaje descriptivo al usuario.
- **[Riesgo] Carga de miembros lenta en proyectos grandes**: `get_project_memberships` puede traer cientos de miembros. → **Mitigación**: El combo ya usa `QCompleter` con `MatchContains` para búsqueda rápida; la carga se hace bajo demanda al cambiar de proyecto.
- **[Trade-off] Adjuntos solo en creación**: No se implementa adjuntar en edición para limitar el alcance. El usuario puede usar la interfaz web para añadir adjuntos a tareas existentes.
