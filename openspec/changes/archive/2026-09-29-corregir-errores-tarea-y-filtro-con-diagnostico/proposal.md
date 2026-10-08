## Why

Tres síntomas reportados al usar PyIssuesTracker contra una instancia real de Redmine, todos ellos con la misma raíz: la aplicación **falla sin explicar por qué**.

1. **Alta de tarea con mensaje engañoso.** Al crear una tarea, Redmine responde HTTP 422 con `Proyecto no puede estar en blanco. Tipo no puede estar en blanco. Estado no puede estar en blanco.` El proyecto realmente **no tiene trackers (tipos) definidos**, así que la interfaz web de Redmine tampoco permite crear issues. El cliente **sí envía** `project_id` y `tracker_id`, pero muestra los errores del servidor **verbatim**, sin interpretarlos, de modo que el usuario cree que la app envía campos vacíos. El combo de tracker usa el catálogo **global** de Redmine (no los trackers del proyecto) y cae a `tracker_id=1` cuando no hay selección.

2. **Filtro multi-proyecto vacío y sin error.** Al seleccionar varios proyectos en el filtro, la tabla puede quedar vacía aunque haya issues. La carga multi-proyecto ejecuta una petición por proyecto **sin aislar fallos**: un `404/403` de un solo proyecto (p. ej. un ID huérfano persistido en `filter_projects` o un proyecto renombrado/eliminado) **aborta el merge completo**. Además `_cargar_issues()` captura `RedmineError` y solo cambia el indicador de estado, **sin diálogo y sin log**.

3. **No hay forma de ver los errores.** La aplicación **no tiene sistema de logging** (ni `logging`, ni fichero `.log`, ni ventana de consola). Decenas de bloques `except RedmineError: pass` silencian fallos.

Se investigó además la sospecha de que el filtro construyera un **nombre ficticio** (`Padre > Hijo`) tras renombrar proyectos y filtrase por él. **Queda descartada**: el flujo del filtro usa **IDs** de extremo a extremo (`FilterBar` → `selected_project_ids` → `get_issues(project_id=[...])` → `params["project_id"] = pid`). El nombre completo `Padre > Hijo` es **solo de presentación** y nunca se envía a la API. `filter_project_name` es código muerto. El síntoma real encaja con el punto 2 (ID huérfano → petición fallida → merge abortado → tabla vacía sin aviso).

## What Changes

- Añadir un **sistema de logging a fichero** (rotativo, en la carpeta de configuración del usuario) con niveles, marca de tiempo y módulo, y **sin registrar secretos** (API key, credenciales).
- Añadir una **ventana de depuración** (menú `Ver > Registro de diagnóstico`) que muestre los mensajes en vivo, con filtro por nivel, botones de limpiar, copiar y abrir la carpeta/fichero de log.
- **Registrar todos los errores capturados** (`RedmineError` y excepciones inesperadas) con contexto suficiente para diagnosticar: operación, proyecto(s) implicados, parámetros enviados y mensaje de la API. Sustituir los `except RedmineError: pass` de operaciones clave por registro.
- **Hacer visibles los errores de carga de issues**: cuando la carga falle, mostrar un aviso al usuario en lugar de dejar la tabla vacía en silencio.
- **Carga multi-proyecto resiliente**: ejecutar la consulta de cada proyecto de forma aislada, acumular los resultados de los que respondan, y avisar de qué proyectos fallaron sin descartar el resto.
- **Saneado de IDs huérfanos**: descartar (avisando) los IDs de proyecto seleccionados o persistidos que ya no existan en la lista cargada, antes de consultar la API.
- **Distinguir "sin resultados" de "error de carga"** en la tabla y el indicador de estado.
- **Interpretar el error de validación 422 de alta de tarea**: cuando Redmine devuelva errores de campos en blanco para `Proyecto/Tipo/Estado`, comprobar si el proyecto **no tiene trackers** y mostrar un mensaje accionable ("El proyecto X no tiene tipos (trackers) definidos; configúralos en Redmine o elige otro proyecto") en lugar del texto crudo. Añadir `get_project_trackers()` y, en el diálogo de creación, cargar los trackers **del proyecto** al seleccionarlo, con aviso si no tiene ninguno.

## Capabilities

### New Capabilities
- `diagnostico-aplicacion`: registro de sucesos a fichero con niveles y ocultación de secretos; ventana de depuración en vivo; registro obligatorio de todo error capturado en operaciones clave.
- `filtro-issues-multiproyecto`: carga resiliente de issues cuando el filtro tiene varios proyectos (aislamiento de fallos por proyecto, aviso de proyectos no accesibles, saneado de IDs huérfanos, distinción entre vacío y error, y uso exclusivo de IDs como criterio de filtrado).

### Modified Capabilities
- `manejo-errores-api`: interpretación y mensaje accionable para errores de validación engañosos (proyecto sin trackers) y registro de errores de API en el log de diagnóstico.

## Impact

- `app/services/redmine_client.py`: nuevo `get_project_trackers(project_id)`; `get_issues()` aísla fallos por proyecto (acumula éxitos y expone los proyectos fallidos); registro de errores HTTP en el log; detección de la causa "proyecto sin trackers" sin alterar la extracción verbatim actual de errores.
- `app/main_window.py`: `_cargar_issues()` deja de silenciar `RedmineError` (aviso + log), sanea IDs huérfanos y muestra qué proyectos fallaron; `_nueva_tarea()` interpreta el 422 y muestra el mensaje accionable; nueva acción de menú `Ver > Registro de diagnóstico`; inicialización del logging al arrancar.
- `app/services/logging_config.py` (nuevo): configuración central del logging (`RotatingFileHandler`, formato, ruta del log, filtro de secretos).
- `app/dialogs/debug_log_dialog.py` (nuevo): ventana de depuración que consume los mensajes de logging.
- `app/dialogs/task_dialog.py`: en modo creación, cargar trackers del proyecto al cambiar el combo de proyecto y avisar si el proyecto no tiene ninguno.
- `app/widgets/multi_select_combo.py`: `set_selected_ids()` ignora IDs que no estén en `_items` (y los reporta), evitando selecciones huérfanas.
- `app/services/settings_manager.py`: descartar IDs de proyecto inválidos al cargar `filter_projects`/`notifications_projects`; retirar el código muerto `filter_project_name`.
- `tests/`: nuevos tests de logging, de resiliencia multi-proyecto, de saneado de IDs huérfanos y de interpretación del 422 sin trackers; ajuste de los tests existentes afectados.
- `README.md` / `MANUAL.md`: documentar la ubicación del log y la ventana de depuración.