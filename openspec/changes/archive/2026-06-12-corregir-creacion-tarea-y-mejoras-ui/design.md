## Context

La aplicación PyIssuesTracker (v0.3.9) es un cliente de escritorio PyQt6 para Redmine. Actualmente la creación de tareas falla silenciosamente sin mostrar errores de la API, y existen carencias de usabilidad en la edición de trackers, visualización en el grid, límite de proyectos en el filtro y orden de asignación.

El proyecto usa:
- **httpx** como cliente HTTP con `follow_redirects=False` para detectar SSO
- **PyQt6** para la UI con widgets nativos (QComboBox, QTableWidget, QDateEdit)
- Jerarquía de excepciones propias: `RedmineError` → `RedmineAuthError`, `RedmineConnectionError`, `RedmineSSOError`
- Carga de datos bajo demanda (categorías y miembros se cargan al seleccionar proyecto)

## Goals / Non-Goals

**Goals:**
1. Capturar y mostrar errores de validación de la API de Redmine (HTTP 422, 500) al crear/editar tareas
2. Asegurar que el combo de tracker sea editable en modo edición de tarea
3. Añadir columna de tracker visible en la tabla de issues
4. Soportar más de 200 proyectos mediante paginación en la API
5. Ordenar la lista de asignación priorizando al usuario actual

**Non-Goals:**
- No se modificará el sistema de notificaciones ni el polling
- No se añadirá paginación a la tabla de issues (ya existe vía offset)
- No se cambiará el flujo de autenticación ni la detección de SSO
- No se modificará el sistema de adjuntos ni checklists

## Decisions

### D1: Jerarquía de errores de validación

**Decisión**: Crear una nueva excepción `RedmineValidationError(RedmineError)` que incluya los errores de validación devueltos por la API de Redmine en el cuerpo de la respuesta (HTTP 422).

**Alternativa considerada**: Usar `RedmineError` genérico y formatear el mensaje en `_post`/`_put`. Rechazada porque no permite al caller distinguir entre errores de red/autenticación y errores de validación de datos, lo que impide mostrar mensajes contextualizados.

**Implementación**: Modificar `_post()` y `_put()` en `redmine_client.py` para detectar HTTP 422, extraer los mensajes de error del JSON de respuesta y lanzar `RedmineValidationError` con un mensaje descriptivo formateado.

### D2: Columna tracker en el grid

**Decisión**: Insertar la columna de tracker en la posición 1 (después de ID), desplazando las columnas existentes una posición. La columna mostrará el nombre del tracker (Bug, Feature, Support, etc.).

**Alternativa considerada**: Colocar la columna al final del grid. Rechazada porque el tracker es información fundamental para identificar visualmente el tipo de tarea.

**Impacto en índices**: Todas las constantes `COL_*` a partir de `COL_TITLE` se incrementan en 1: `COL_TITLE=2`, `COL_START_DATE=3`, `COL_DUE_DATE=4`, `COL_STATUS=5`, `COL_ASSIGNED_TO=6`, `COL_PROGRESS=7`, `COL_URL=8`.

### D3: Paginación de proyectos

**Decisión**: Modificar `get_projects()` para aceptar un parámetro `offset` y usarlo junto con `limit`. Crear un método wrapper `get_all_projects()` que itere sobre las páginas hasta obtener todos los proyectos.

**Alternativa considerada**: Simplemente aumentar el límite a 500 o 1000. Rechazada porque no escala para instancias con miles de proyectos.

**Parámetros**: 
- `limit` por defecto: 100 (consistente con `REDMINE_PAGE_LIMIT`)
- `get_all_projects()` llamará internamente a `get_projects()` con offset incremental hasta recibir una página vacía
- Máximo 20 páginas (2000 proyectos) para evitar bucles infinitos

### D4: Orden de asignación

**Decisión**: En `_populate_members()`, colocar al usuario actual en primera posición (después de "(Sin asignar)"), seguido del resto de miembros ordenados alfabéticamente. El ID del usuario actual se obtendrá mediante `RedmineClient.get_current_user_id()` cacheado.

**Alternativa considerada**: Añadir opción "Asignado a mí" como item especial en el combo. Rechazada porque requiere manejar un valor especial (-2 como en el filtro) y añade complejidad innecesaria cuando se puede simplemente reordenar.

**Caché del user ID**: El `RedmineClient` ya dispone de `get_current_user_id()`. Se cacheará el resultado en `self._current_user_id` para evitar llamadas repetidas a la API.

### D5: Visibilidad de errores en creación/edición

**Decisión**: Ampliar los bloques `try/except` en `_nueva_tarea()` y `_editar_tarea()` para capturar tanto `RedmineError` como excepciones inesperadas, mostrando siempre un `QMessageBox` con el mensaje de error. Se añadirá `RedmineValidationError` a la cadena de captura.

**Implementación**: 
- `_post()` y `_put()` lanzarán `RedmineValidationError` con los errores del JSON de respuesta en HTTP 422
- `main_window.py` capturará `RedmineValidationError` y mostrará los errores específicos
- Se mantendrá la captura de `RedmineError` como fallback

## Risks / Trade-offs

- **[Riesgo] La paginación de proyectos puede ralentizar la carga inicial si hay cientos de proyectos**: Mitigación: mostrar un indicador de progreso o cargar solo la primera página y cargar el resto bajo demanda. La mayoría de instancias tienen <200 proyectos, así que el impacto será mínimo.
- **[Riesgo] La columna adicional del tracker reduce el espacio disponible para el título en pantallas pequeñas**: Mitigación: la columna de tracker usará `ResizeToContents` y tendrá un ancho máximo razonable; el título seguirá usando `Stretch`.
- **[Riesgo] El cambio de índices de columna puede romper referencias en menús contextuales y señales**: Mitigación: revisar todas las referencias a constantes `COL_*` en `task_table.py` y `main_window.py`, actualizándolas consistentemente.
- **[Trade-off] `get_all_projects()` puede aumentar el tiempo de la primera carga**: Aceptable porque solo ocurre al iniciar la aplicación o al refrescar manualmente; los proyectos se cachean en memoria.
