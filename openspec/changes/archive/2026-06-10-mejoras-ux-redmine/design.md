## Context

Actualmente la app tiene 7 columnas (ID, Título, Fecha inicio, Estado, Asignado a, Progreso, botón URL), un `FilterBar` con 6 filtros (proyecto, estado, prioridad, categoría, asignado, búsqueda texto) y campos de texto simples para descripción y comentarios. La API REST de Redmine expone `due_date` en los issues y soporta filtros por rango de fechas (`>=<`), pero el cliente no los aprovecha. El botón "Abrir en Redmine" construye la URL concatenando `settings.redmine_url + "/issues/" + id`, que falla cuando la URL base tiene barra final (doble slash) o carece de protocolo.

## Goals / Non-Goals

**Goals:**
- Corregir la URL del botón "Abrir en Redmine" normalizando la URL base al guardar en `SettingsManager`.
- Añadir columna "Fecha fin" mostrando `due_date` de Redmine, con edición inline (doble clic → `QDateEdit` en la celda).
- Añadir campo "Fecha fin" en los diálogos de nueva tarea y edición de tarea (`TaskDialog`).
- Añadir filtro por `due_date` con presets rápidos (Hoy, Ayer, Esta semana, Semana pasada, Este mes, Mes pasado) y opción de rango personalizado.
- Añadir autocompletado de `@usuario` en descripción y comentarios usando los miembros del proyecto actual.

**Non-Goals:**
- No se modifica la API de Redmine ni el servidor.
- No se renderiza formato wiki de Redmine (negritas, enlaces) en comentarios; solo se autocompletan menciones.

## Decisions

### 1. Normalización de URL

**Decisión**: Normalizar la URL en el setter de `SettingsManager.redmine_url` con `.rstrip("/")`. Además, al construir la URL en `_cargar_issues()`, usar `urljoin` o concatenación segura sin doble slash. Para el fallback en `_abrir_url_redmine()`, misma normalización.

**Alternativas**: Normalizar solo en el getter (no persistir la versión normalizada) → frágil, otros lugares que lean la URL cruda sufrirían el mismo bug.

### 2. Columna "Fecha fin" — ubicación y edición inline

**Decisión**: Insertar `COL_DUE_DATE = 3` entre "Fecha inicio" (2) y "Estado" (3 actual). Renumerar columnas existentes: Estado → 4, Asignado a → 5, Progreso → 6, URL → 7. La edición inline se implementa con un `QDateEdit` que reemplaza temporalmente el texto de la celda al hacer doble clic. Al confirmar (Enter o foco perdido), se llama a `RedmineClient.update_issue(issue_id, due_date=...)` para persistir en Redmine. El `QTableWidget` ya tiene soporte para `setCellWidget()` y `openPersistentEditor()`.

**Alternativas**: 
- Usar `QCalendarWidget` en popup → más complejo, requiere gestionar geometría del popup.
- Editar solo desde el diálogo de edición → rompe el flujo rápido; el usuario quiere cambiar la fecha sin abrir otro diálogo.

### 3. Filtro por fecha — presets

**Decisión**: Añadir un `QComboBox` con opciones: "Sin filtro", "Hoy", "Ayer", "Esta semana", "Semana pasada", "Este mes", "Mes pasado", "Rango personalizado". Al seleccionar "Rango personalizado", mostrar dos `QDateEdit` (desde/hasta). Los presets calculan rangos de fecha en Python (usando `datetime`/`date`) y los convierten a formato ISO para la API de Redmine (`YYYY-MM-DD`).

Cálculo de rangos:
- **Hoy**: `date.today()` → `date.today()`
- **Ayer**: `date.today() - 1 day` → ídem
- **Esta semana**: lunes de esta semana → domingo de esta semana
- **Semana pasada**: lunes de la semana pasada → domingo de la semana pasada
- **Este mes**: día 1 del mes actual → último día del mes actual
- **Mes pasado**: día 1 del mes pasado → último día del mes pasado

**Alternativas**: Usar `QCalendarWidget` → demasiado pesado para un filtro rápido. Usar solo `QDateEdit` sin presets → obliga al usuario a seleccionar fechas manualmente cada vez.

### 4. API de Redmine — filtro `due_date`

**Decisión**: Añadir parámetros `due_date_from: str | None` y `due_date_to: str | None` a `get_issues()`. Formatear el filtro como `>=<YYYY-MM-DD|YYYY-MM-DD` (sintaxis de Redmine para rangos). Si solo se especifica un extremo, usar `>=<YYYY-MM-DD` (desde) o `<=YYYY-MM-DD` (hasta). Si ambos, usar el formato de rango completo.

**Alternativas**: Usar múltiples parámetros de query string → Redmine REST API no soporta múltiples valores para el mismo key; usa el formato `>=<` en el valor.

### 5. Autocompletado @usuario

**Decisión**: Usar `QCompleter` con un modelo `QStringListModel`. Al detectar `@` en el texto, mostrar el popup con los miembros del proyecto. Implementar un `eventFilter` o sobrescribir `keyPressEvent` en un `QPlainTextEdit` personalizado para detectar `@` y activar el completer. El completer se filtra incrementalmente según el texto tras la `@`.

La lista de miembros se obtiene del método existente `get_project_memberships()` del `RedmineClient`. El `CommentsWidget` y el `TaskDialog` ya tienen acceso al cliente Redmine y al `project_id`.

**Alternativas**:
- Procesar el texto completo con regex → no ofrece UI de selección.
- `QTextEdit` con `QTextCursor` + menú contextual → complejo, el usuario espera un dropdown inline.
- `QCompleter` estándar de Qt → simple, nativo, bien integrado con `QPlainTextEdit`.

### 6. Menú contextual "Abrir en Redmine"

**Decisión**: Añadir al menú contextual de la tabla (clic derecho) una acción "Abrir en Redmine" que emita la misma señal `tarea_abrir_url`.

### 7. Campo due_date en TaskDialog

**Decisión**: Añadir un `QDateEdit` con checkbox de activación en el `TaskDialog`, en una nueva fila debajo de "Fecha inicio". El checkbox permite establecer o limpiar la fecha de fin: si está marcado, se usa el valor del `QDateEdit`; si no, se envía `due_date=""` (sin fecha). El campo debe aparecer tanto en modo creación como en modo edición, precargando el valor existente en este último caso. El `create_issue()` y `update_issue()` del `RedmineClient` ya soportan pasar `due_date` como parte de los kwargs genéricos.

**Alternativas**: 
- `QDateEdit` sin checkbox → obliga a tener siempre una fecha, no permite "sin fecha de fin".
- `QCalendarWidget` → ocupa demasiado espacio en el diálogo.

## Risks / Trade-offs

- **[Riesgo] La API de Redmine no tiene el campo `due_date` en todas las instancias**: Algunas versiones antiguas o configuraciones pueden no exponer `due_date`. → Mitigación: usar `.get("due_date", "")` con valor por defecto vacío.
- **[Riesgo] El autocompletado @ podría interferir con edición normal**: Si el usuario escribe `@` sin intención de mencionar. → Mitigación: el completer solo se muestra si hay al menos 1 miembro que coincida; se cierra con Escape.
- **[Trade-off] El filtro de fecha usa `due_date` como campo base**: No se filtra por `created_on` ni `updated_on`. → Aceptable para esta iteración; el usuario pidió específicamente filtro por fecha de fin.
- **[Riesgo] Los presets de semana asumen semana de lunes a domingo**: Usar `date.weekday()` donde lunes=0, domingo=6. Consistente con la convención europea.

## Open Questions

- ¿Debería persistir el filtro de fecha en QSettings? → Sí, para mantener coherencia con el resto de filtros.
