## Context

PyIssuesTracker es un cliente de escritorio **PyQt6** para **Redmine**, con acceso HTTP mediante **httpx**. La jerarquía de excepciones del cliente es:

`RedmineError` → `RedmineAuthError`, `RedmineConnectionError`, `RedmineSSOError`, `RedmineValidationError`.

Los tests usan **pytest + pytest-qt** y se ejecutan con `QT_QPA_PLATFORM=offscreen pytest`.

Estado actual relevante:

- **No existe logging**: cero `import logging`, `basicConfig`, `.log`, `FileHandler` ni ventana de consola en `app/`.
- **Errores silenciados**: `main_window.py:517-518` captura `RedmineError` en la carga de issues y solo cambia el indicador de estado. Existen además decenas de bloques `except RedmineError: pass` en `main_window.py` (`:1410-1411`, `:365-366`, `:409-410`, `:431-432`, `:864-865`, `:869-870`, `:968-969`, `:973-974`, `:1069-1070`, `:1074-1075`, `:1197-1198`, `:1442-1443`, `:907`, `:1161`), `redmine_client.py` (`:294`, `:348`, `:378`), `update_manager.py` (`:38`, `:57`, `:120`), `task_dialog.py` (`:411`, `:469`, `:487`, `:748`, `:760`, `:784`, `:801`) y `report_dialog.py:273`.
- **Merge multi-proyecto abortable**: `get_issues()` (`redmine_client.py:474-489`) resuelve lista de 1 → `int`; lista > 1 → `multiple_projects`, una petición por proyecto (`redmine_client.py:561-572`) **sin `try/except` por proyecto**, de modo que un solo `404/403` aborta todo el merge.
- **Combo de tracker global**: `TaskDialog` (`task_dialog.py:124-129`) puebla el combo con `get_trackers()` (`/trackers.json`, catálogo global), no con los trackers del proyecto. No existe `get_project_trackers`. `tracker_id` cae a `1` si no hay selección (`task_dialog.py:1034-1036`). Como el `tracker_id` global no es válido para el proyecto, Redmine no resuelve proyecto/tipo/estado y devuelve los 3 errores de "en blanco" (`_extract_validation_errors` en `redmine_client.py:278-288`; `_nueva_tarea` en `main_window.py:917-920`).

**Hipótesis "nombre ficticio" investigada y descartada.** Se sospechó que, tras renombrar proyectos, el filtro construyera un nombre (`Padre > Hijo`) y filtrase por él. El código lo desmiente:

- `FilterBar` emite IDs: señal `proyecto_cambiado = pyqtSignal(list)` (`filter_bar.py:13`), `selected_project_ids` (`filter_bar.py:217-223`) y `selected_ids()` (`filter_bar.py:291-292`).
- `MultiSelectCombo` almacena tuplas `(id, texto)` (`multi_select_combo.py:30-31`) y `selected_ids()` devuelve IDs (`multi_select_combo.py:96-98`).
- `main_window.py:445` usa `project_ids = self._filter_bar.selected_project_ids` y `main_window.py:468` llama `get_issues(project_id=project_ids or None, ...)`.
- `build_project_full_names` (`app/utils/projects.py:11-45`, unión con `" > "` en la línea 44) y `full_name` (`redmine_client.py:451-455`; `main_window.py:340-347` y `:488`) son **solo presentación**.
- `filter_project_name` (`settings_manager.py:197-202`, clave en `constants.py:51`) es **código muerto**, nunca invocado.

El síntoma real encaja con IDs huérfanos (proyecto eliminado o `filter_projects` persistido obsoleto): `MultiSelectCombo.set_selected_ids` (`multi_select_combo.py:89-94`) no valida contra `_items`, acepta IDs huérfanos y el botón muestra el ID crudo como fallback (`multi_select_combo.py:207-209`). La petición por ese ID falla y aborta el merge.

## Goals / Non-Goals

**Goals**
- Dotar a la app de un sistema de logging a fichero (rotativo, en carpeta de configuración del usuario, sin secretos) y de una ventana de depuración en vivo.
- Registrar todo error capturado en operaciones clave, con contexto de diagnóstico.
- Hacer visibles los errores de carga de issues (aviso + indicador) y distinguir "sin resultados" de "error de carga".
- Carga multi-proyecto resiliente: aislar fallos por proyecto, conservar los resultados válidos y avisar de los proyectos fallidos.
- Saneado de IDs de proyecto huérfanos (selección y persistencia).
- Interpretar el 422 de alta de tarea cuando el proyecto no tiene trackers y mostrar un mensaje accionable; cargar trackers del proyecto en el diálogo de creación.

**Non-Goals**
- No cambiar autenticación/SSO.
- No rediseñar la UI de filtros.
- No añadir paginación nueva a la consulta de issues.
- No implementar i18n completa de todos los mensajes de Redmine (solo la interpretación del caso "proyecto sin trackers").
- No tocar el polling de notificaciones.

## Decisions

### D1 — Logging con la librería estándar + RotatingFileHandler
- **Decisión**: usar `logging` de la librería estándar con un handler de fichero rotativo (`RotatingFileHandler`) en la carpeta de configuración del usuario (p. ej. `~/.config/PyIssuesTracker/pyissuestracker.log`), con formato que incluya marca de tiempo, nivel y módulo. Añadir además un handler en memoria para la ventana de depuración, implementado como `QtLogHandler(logging.Handler)` que emite una señal Qt (thread-safe). Aplicar un `FiltroSecretos` que impida registrar la cabecera `X-Redmine-API-Key` y el valor de la API key.
- **Alternativa considerada**: escribir a `stdout` o usar un fichero sin rotación. Rechazada: no persiste en entorno de escritorio, no acota crecimiento y no es seguro dejar el secreto en el log.
- **Implementación**: nuevo `app/services/logging_config.py` con `setup_logging()` (ruta, niveles, handlers, filtro) y `QtLogHandler`. Inicialización al arrancar desde `main.py` y disponible en `app/main_window.py`.

### D2 — Ventana de depuración no modal
- **Decisión**: `QDialog` no modal con `QPlainTextEdit` de solo lectura, selector de nivel, y botones Limpiar / Abrir carpeta del log / Copiar. Accesible desde `Ver > Registro de diagnóstico`. Con límite de líneas en memoria para no crecer sin control.
- **Alternativa considerada**: una pestaña o dock permanente. Rechazada: recarga la UI principal y no es depuración puntual.
- **Implementación**: nuevo `app/dialogs/debug_log_dialog.py`, consumiendo los mensajes de `QtLogHandler`; acción de menú añadida en `app/main_window.py`.

### D3 — Resiliencia multi-proyecto en `get_issues()`
- **Decisión**: refactor de la rama `multiple_projects` para iterar proyectos con `try/except RedmineError` **por proyecto**, acumular los resultados correctos y exponer además la lista de proyectos fallidos (p. ej. un dataclass `IssuesResult(issues, failed_projects)` o parámetro out). Mantener compatibilidad con `TestGetIssuesMultiProject` (merge + dedupe + orden `updated_on` desc).
- **Alternativa considerada**: reintentos por proyecto. Rechazada por complejidad; se registra y se avisa en su lugar.
- **Implementación**: `redmine_client.py` (`get_issues`, rama `multiple_projects` en `:561-572`), manteniendo firma y añadiendo el canal de fallidos de forma compatible.

### D4 — Saneado de IDs huérfanos en dos capas
- **Decisión**: (1) `MultiSelectCombo.set_selected_ids` descarta los IDs no presentes en `_items` y los reporta; (2) `MainWindow._cargar_issues` cruza los IDs seleccionados con los proyectos cargados y descarta los huérfanos, avisando y registrando en el log.
- **Alternativa considerada**: conservar el ID y mostrar "(desconocido)". Rechazada: sigue provocando el `404` y mantiene la tabla vacía silenciosa.
- **Implementación**: `app/widgets/multi_select_combo.py` (`set_selected_ids`, `:89-94`) y `app/main_window.py` (`_cargar_issues`).

### D5 — Interpretación del 422 "proyecto sin trackers"
- **Decisión**: añadir `RedmineClient.get_project_trackers(project_id)` (`GET /projects/:id.json?include=trackers`). Ante `RedmineValidationError` en creación, si los errores contienen las etiquetas de `Proyecto/Tipo/Estado` en blanco, consultar si el proyecto tiene trackers; si no tiene, mostrar mensaje accionable; si tiene, mostrar el detalle añadiendo el contexto (proyecto y tracker enviados).
- **Alternativa considerada**: mapear/traducir todos los mensajes de Redmine. Rechazada: alto mantenimiento y el cliente no controla los textos del servidor.
- **Implementación**: `app/services/redmine_client.py` (nuevo método) y `app/main_window.py` (`_nueva_tarea`, `:917-920`), sin alterar la extracción verbatim actual de `_extract_validation_errors` (`:278-288`).

### D6 — Distinción "vacío" vs "error"
- **Decisión**: `_cargar_issues` pasa a modelar tres estados: OK con resultados, OK sin resultados, y error. No se muestra una tabla vacía en silencio ante error.
- **Alternativa considerada**: mantener un único estado vacío. Rechazada: es la raíz de la confusión actual.
- **Implementación**: `app/main_window.py` (`_cargar_issues`, `:517-518` y alrededores).

## Risks / Trade-offs

- **Crecimiento del fichero de log** → mitigado con `RotatingFileHandler` y límite de líneas en memoria para la ventana.
- **Ralentización al consultar trackers por proyecto** → cachear el resultado por `project_id` durante la sesión del diálogo.
- **Ruptura de tests que fijan el comportamiento actual** de `get_issues` y `set_selected_ids` → mitigado manteniendo firmas y añadiendo parámetros opcionales / valores por defecto; no romper `TestGetIssuesMultiProject`, `TestFilterBarMultiProject`, `TestMultiSelectCombo*`, `TestCopyModeMissingDestinationAttributes`.
- **Secretos en el log** → mitigado con `FiltroSecretos` (nunca registrar `X-Redmine-API-Key` ni el valor de la API key).

## Migration Plan

Cambio aditivo y compatible: no requiere migración de datos. El fichero de log se crea en el primer arranque. Los IDs de proyecto obsoletos guardados en `filter_projects`/`notifications_projects` se sanean en tiempo de carga (se descartan y se avisa), sin necesidad de migrar los ajustes existentes. `get_issues()` mantiene su firma y el comportamiento previo para una lista de un solo proyecto; el aislamiento de fallos por proyecto solo afecta a la rama de múltiples proyectos.

## Decisiones resueltas

- **Nivel por defecto del log**: **INFO** (`setup_logging(level=logging.INFO)`). Registra los sucesos normales de la aplicación y todos los WARNING/ERROR; los mensajes DEBUG quedan fuera en producción.
- **Rotación**: **1 MB y 3 backups** (`maxBytes=1_000_000`, `backupCount=3`), valores por defecto de `setup_logging()`.
- **Enlace directo a la configuración del proyecto en Redmine**: **fuera de alcance** (no se implementa). El mensaje accionable del 422 "proyecto sin trackers" indica al usuario que configure los trackers en Redmine o elija otro proyecto, sin abrir una URL concreta del servidor.