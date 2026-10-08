## Context

La aplicación PyIssuesTracker (PyQt6) permite visualizar, filtrar y gestionar tareas de Redmine. Actualmente:
- **Tabla de issues**: muestra 9 columnas (ID, Tracker, Título, Fecha inicio, Fecha fin, Estado, Asignado a, Progreso %, URL) pero no muestra `created_on` ni `updated_on`, aunque la API de Redmine ya devuelve esos campos y el `RedmineClient` ya los parsea en el dataclass `RedmineIssue`.
- **Filtros**: el `FilterBar` emite señales individuales por cada filtro. `MainWindow._cargar_issues()` recolecta los filtros de estado, prioridad, categoría y asignado directamente del `FilterBar`, pero las fechas (`due_date_from`, `due_date_to`) se pasan como parámetros solo cuando el manejador `_on_filter_date_changed` los incluye. Si cualquier otro filtro dispara la recarga (estado, prioridad, categoría, asignado, búsqueda), los parámetros de fecha se omiten y el filtro de fecha se pierde.
- **Asignado a**: es un `QComboBox` de selección única con opciones "Todos", "Sin asignar", "Asignado a mí" y la lista de miembros del proyecto. Solo permite elegir un valor.
- **Checklist**: en el `TaskDialog`, el `ChecklistWidget` se crea en el UI pero permanece oculto (`setVisible(False)`) en modo creación. Solo se carga y muestra en modo edición mediante `_load_checklists()`.

## Goals / Non-Goals

**Goals:**
1. Añadir columnas "Creado" y "Modificado" en la tabla con formato `DD/MM/YY HH:MM`, ordenables
2. Unificar la recolección de filtros para que todos (incluyendo fecha) se lean siempre del `FilterBar`, garantizando AND entre ellos
3. Convertir el filtro "Asignado a" en multiselección con checkboxes
4. Mostrar el checklist en modo creación de tarea (alta), permitiendo añadir items antes de guardar

**Non-Goals:**
- No se modifica el comportamiento de otros filtros (prioridad, categoría, proyecto)
- No se cambia la API de Redmine (los filtros se siguen enviando como query params estándar)
- No se modifica la persistencia individual de filtros (fuera del cambio de `assigned_to_id` único a lista)
- No se añaden nuevas dependencias externas

## Decisions

### D1: Unificar recolección de filtros en `_cargar_issues()`

**Decisión**: Eliminar los parámetros `due_date_from`/`due_date_to` de `_cargar_issues()` y leer siempre las fechas directamente del `FilterBar` mediante nuevas propiedades `selected_date_from` y `selected_date_to`. Todos los manejadores de cambio de filtro llamarán a `_cargar_issues()` sin argumentos.

**Alternativa considerada**: Pasar todos los filtros como parámetros en cada handler. Se descartó porque es propenso a errores (olvidar un filtro) y duplica la lógica de recolección.

**Cambios**:
- Añadir `selected_date_from: str | None` y `selected_date_to: str | None` como propiedades en `FilterBar`
- `FilterBar._on_date_preset_changed` y los handlers de rango personalizado almacenan las fechas en atributos internos (`_current_date_from`, `_current_date_to`)
- `MainWindow._cargar_issues()` lee todas las propiedades del `FilterBar` sin parámetros externos
- `MainWindow._on_filter_date_changed` solo llama a `_cargar_issues()` sin argumentos

### D2: Multiselección en "Asignado a" con `QListWidget` + checkboxes

**Decisión**: Reemplazar el `QComboBox` de asignado por un popup/dropdown con `QListWidget` que contenga checkboxes, emulando un combo multiselección. Se usará un `QPushButton` que muestre el texto "N seleccionados" y al hacer clic despliegue un menú con la lista de miembros con checkboxes.

**Alternativa considerada**: `QComboBox` con `setItemData` y check state. Se descartó porque `QComboBox` no soporta nativamente checkboxes visibles en el dropdown sin subclasificar el delegate, y la experiencia de usuario sería confusa (el texto del combo muestra solo el primer seleccionado).

**Cambios**:
- Nuevo widget helper `MultiSelectCombo` (o integrado en `FilterBar`) que encapsula el botón + popup con checkboxes
- La señal `asignado_cambiado` cambia de `pyqtSignal(int)` a `pyqtSignal(list)` — emite una lista de IDs
- `MainWindow` adapta el handler para aceptar `list[int]`
- `RedmineClient.get_issues()` acepta `assigned_to_id: list[int] | None` y si tiene múltiples valores, los envía como filtro OR (varios query params `assigned_to_id=1&assigned_to_id=2` o filtro client-side)
- Para "Sin asignar" (`!*`) y "me", se tratan como flags excluyentes: si están marcados, se ignora la selección de miembros concretos
- Persistencia: se guarda la lista de IDs seleccionados en `QSettings`

### D3: Columnas de fecha/hora en tabla

**Decisión**: Añadir `COL_CREATED = 9` y `COL_UPDATED = 10` después de la columna URL. El formato será `DD/MM/YY HH:MM` usando una nueva función `iso_datetime_to_display()` en `app/utils/dates.py` que convierta el timestamp ISO 8601 (ej. `2026-06-26T10:30:00Z`) al formato deseado.

**Alternativa considerada**: Formato `DD/MM/YYYY HH:MM`. Se descartó porque ocupa demasiado espacio horizontal. El año con 2 dígitos (`YY`) es suficiente para el contexto de uso.

**Cambios**:
- Nueva función `iso_datetime_to_display(iso_str: str) -> str` en `app/utils/dates.py`
- Añadir constantes `COL_CREATED`, `COL_UPDATED` y cabeceras "Creado", "Modificado" en `TaskTable`
- Incluir `created_on` y `updated_on` en el diccionario de issues en `MainWindow._cargar_issues()`
- Añadir celdas correspondientes en `TaskTable.set_issues()`
- Configurar `ResizeToContents` para ambas columnas

### D4: Checklist en modo creación

**Decisión**: En el `TaskDialog`, mostrar siempre el grupo de checklist (`_checklist_group.setVisible(True)`) independientemente del modo. En modo creación, los items añadidos se almacenan en una lista temporal (`_pending_checklist_items`) y se crean en Redmine después de guardar la tarea (cuando ya se tiene el `issue_id`).

**Alternativa considerada**: Crear la tarea sin checklist y luego añadir items. Se descartó porque requiere dos pasos y el usuario perdería los items si cierra el diálogo antes de guardar.

**Cambios**:
- `_setup_ui()`: No ocultar el checklist (`setVisible(True)` por defecto)
- Añadir `_pending_checklist_items: list[str]` como atributo
- `_on_checklist_item_added`: si `_es_nueva`, guardar en `_pending_checklist_items`; si edición, comportamiento actual
- `_guardar_tarea()`: después de crear la tarea, iterar `_pending_checklist_items` y crear cada item vía API
- `_load_checklists()`: solo se ejecuta en modo edición (sin cambios)

## Risks / Trade-offs

- **[Riesgo] Múltiples asignados en API**: La API de Redmine solo acepta un `assigned_to_id` por request. → **Mitigación**: Usar múltiples parámetros `assigned_to_id[]` si la API los soporta, o hacer múltiples requests y combinar resultados (con deduplicación por issue ID). Si la API no soporta array, se hará una request sin filtro de asignado y se filtrará client-side.
- **[Riesgo] Checklist en alta sin issue_id**: Si falla la creación de la tarea, los items del checklist se pierden. → **Mitigación**: Los items se crean después de confirmar que la tarea se guardó correctamente. Si algún item falla, se muestra un warning pero la tarea ya está creada.
- **[Riesgo] Formato de timestamp**: Redmine puede devolver `created_on` en formatos variables (con/sin timezone, con/sin hora). → **Mitigación**: La función `iso_datetime_to_display()` manejará `YYYY-MM-DDTHH:MM:SSZ`, `YYYY-MM-DDTHH:MM:SS+XX:XX` y `YYYY-MM-DD`. Si no tiene hora, mostrará solo fecha.
- **[Trade-off] Espacio en tabla**: Dos columnas adicionales reducen el espacio para el título. → Las columnas de fecha/hora usan `ResizeToContents` y se colocan al final; el título sigue usando `Stretch`.
