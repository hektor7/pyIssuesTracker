## 1. Mejora del manejo de errores en el cliente Redmine

- [x] 1.1 Crear excepción `RedmineValidationError(RedmineError)` en `app/services/redmine_client.py` que incluya los errores de validación del cuerpo JSON de respuestas HTTP 422
- [x] 1.2 Modificar `_post()` en `redmine_client.py` para detectar HTTP 422, extraer los errores del JSON (`response.json().get("errors", [])`) y lanzar `RedmineValidationError` con un mensaje descriptivo formateado
- [x] 1.3 Modificar `_put()` en `redmine_client.py` con el mismo tratamiento de HTTP 422 que `_post()`
- [x] 1.4 Modificar `_get()` en `redmine_client.py` para incluir el cuerpo de la respuesta en el mensaje de error cuando la API devuelve códigos de error no manejados (HTTP >= 400)

## 2. Corrección de tracker editable en edición y errores en main_window

- [x] 2.1 Verificar y corregir el combo de tracker en `task_dialog.py` para asegurar que en modo edición (`_is_edit = True`) el combo no tenga restricciones que impidan modificarlo (asegurar `setEnabled(True)`, verificar que `_update_completer_model` no bloquee la selección)
- [x] 2.2 Modificar `_nueva_tarea()` en `app/main_window.py` para capturar `RedmineValidationError` y mostrar los errores específicos de validación en el diálogo de error
- [x] 2.3 Modificar `_editar_tarea()` en `app/main_window.py` con el mismo tratamiento de errores que `_nueva_tarea()`, capturando `RedmineValidationError` para mostrar errores de validación al editar
- [x] 2.4 Añadir bloque `except Exception` como fallback en `_nueva_tarea()` y `_editar_tarea()` para capturar cualquier excepción inesperada y mostrar mensaje genérico al usuario, evitando fallos silenciosos
- [x] 2.5 Exportar `RedmineValidationError` en `app/services/__init__.py` (si existe) o añadir el import en `app/main_window.py`

## 3. Columna de tracker en el grid de tareas

- [x] 3.1 Añadir constante `COL_TRACKER = 1` en `app/widgets/task_table.py` y desplazar todas las constantes de columna existentes (`COL_TITLE = 2`, `COL_START_DATE = 3`, `COL_DUE_DATE = 4`, `COL_STATUS = 5`, `COL_ASSIGNED_TO = 6`, `COL_PROGRESS = 7`, `COL_URL = 8`)
- [x] 3.2 Actualizar la cabecera de columnas en el constructor de `TaskTable` para incluir "Tipo" o "Tracker" en la posición 1
- [x] 3.3 Actualizar los modos de redimensionado de columna en el constructor para incluir `COL_TRACKER` con `ResizeToContents`
- [x] 3.4 Modificar `set_issues()` para crear y poblar la celda del tracker con `QTableWidgetItem` usando `tracker_name` del dict de issue
- [x] 3.5 Asegurar que el resaltado de prioridad alta (fondo rojo) se aplique también a la celda del tracker en el método de coloreado de filas
- [x] 3.6 Revisar y actualizar todas las referencias a índices de columna en `task_table.py` que usen números mágicos o constantes desplazadas (menús contextuales, edición inline, señales)
- [x] 3.7 Revisar y actualizar referencias a columnas en `app/main_window.py` si las hubiera (ej. al leer/escribir datos de la tabla)

## 4. Paginación de proyectos

- [x] 4.1 Modificar `get_projects()` en `app/services/redmine_client.py` para aceptar parámetros opcionales `offset=0` y `limit=100`, usándolos en la petición a `/projects.json`
- [x] 4.2 Crear método `get_all_projects()` en `redmine_client.py` que itere llamando a `get_projects()` con offset incremental hasta recibir una lista vacía, con un máximo de 20 páginas (2000 proyectos)
- [x] 4.3 Actualizar `main_window.py` para usar `get_all_projects()` en lugar de `get_projects()` al cargar la lista inicial de proyectos
- [x] 4.4 Verificar que la jerarquía de proyectos (campo `parent` del JSON de Redmine) se preserva correctamente al unir resultados de múltiples páginas en `get_all_projects()`

## 5. Priorización del usuario actual en asignación

- [x] 5.1 Cachear el ID del usuario actual en `RedmineClient` añadiendo un atributo `_current_user_id` que se obtenga mediante `get_current_user_id()` en la primera llamada y se reuse
- [x] 5.2 Pasar el `current_user_id` al constructor de `TaskDialog` desde `main_window.py` (o hacer que el diálogo lo obtenga del cliente)
- [x] 5.3 Modificar `_populate_members()` en `task_dialog.py` para: (1) mantener "(Sin asignar)" como primer item, (2) colocar el usuario actual (si es miembro) en segunda posición, (3) ordenar el resto de miembros alfabéticamente por nombre
- [x] 5.4 Actualizar también `_load_members_for_project()` para que al recargar miembros dinámicamente al cambiar de proyecto, se aplique el mismo orden con el usuario actual primero

## 6. Verificación y pruebas

- [x] 6.1 Ejecutar tests unitarios existentes para verificar que no haya regresiones: `python -m pytest tests/ -v`
- [x] 6.2 Verificar manualmente que la creación de tareas muestra errores de validación cuando Redmine rechaza la petición
- [x] 6.3 Verificar que el tracker es modificable desde la pantalla de edición de una tarea existente
- [x] 6.4 Verificar que la columna de tracker aparece en el grid y se ordena correctamente
- [x] 6.5 Verificar que todos los proyectos se cargan en instancias con más de 200 proyectos
- [x] 6.6 Verificar que el usuario actual aparece primero en la lista de asignación al crear/editar tareas
