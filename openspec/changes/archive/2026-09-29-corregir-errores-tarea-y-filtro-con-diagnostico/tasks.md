## 1. Tests (TDD)

- [x] 1.1 Test de formateo y ruta del log: `setup_logging()` crea el fichero en la carpeta de configuración del usuario y las entradas incluyen marca de tiempo, nivel y módulo.
- [x] 1.2 Test de rotación: al superar el tamaño máximo, `RotatingFileHandler` rota y conserva el número de backups configurado.
- [x] 1.3 Test de ocultación de secretos: mensajes con `X-Redmine-API-Key` o el valor de la API key NO aparecen en el fichero de log.
- [x] 1.4 Test de `QtLogHandler`: al emitir un `LogRecord`, el handler notifica a la ventana de depuración sin bloquear el hilo de UI.
- [x] 1.5 `get_issues()` multi-proyecto aísla fallos: si un proyecto devuelve `404/403` y otro responde, se devuelven los issues del que responde y la lista de proyectos fallidos lo incluye.
- [x] 1.6 Test de saneado de IDs huérfanos en el flujo del filtro: al poblar/restaurar el filtro de proyectos, los IDs no presentes en la lista de proyectos cargados se descartan y se reportan, SIN alterar el fallback visual de `MultiSelectCombo` con IDs desconocidos (cubierto por `TestMultiSelectComboFallbackBoton`).
- [x] 1.7 `_cargar_issues()` sanea huérfanos y avisa: IDs seleccionados no presentes en los proyectos cargados se descartan con aviso y registro.
- [x] 1.8 `_cargar_issues()` distingue vacío de error: sin resultados muestra "sin resultados"; con `RedmineError` muestra aviso de error (no tabla vacía silenciosa).
- [x] 1.9 `get_project_trackers(project_id)` devuelve los trackers del proyecto desde `GET /projects/:id.json?include=trackers`.
- [x] 1.10 `_nueva_tarea()` muestra mensaje accionable cuando el proyecto no tiene trackers (422 con Proyecto/Tipo/Estado en blanco y `get_project_trackers` vacío).

## 2. Logging

- [x] 2.1 Crear `app/services/logging_config.py` con `setup_logging()` (ruta en carpeta de configuración del usuario, `RotatingFileHandler`, formato con timestamp/nivel/módulo).
- [x] 2.2 Implementar `FiltroSecretos` para excluir `X-Redmine-API-Key` y el valor de la API key.
- [x] 2.3 Implementar `QtLogHandler(logging.Handler)` que emita una señal Qt hacia la ventana de depuración.
- [x] 2.4 Inicializar `setup_logging()` al arrancar desde `main.py` y usarlo desde `app/main_window.py`.

## 3. Ventana de depuración

- [x] 3.1 Crear `app/dialogs/debug_log_dialog.py` (`QDialog` no modal, `QPlainTextEdit` solo lectura, límite de líneas).
- [x] 3.2 Añadir selector de nivel y botones Limpiar, Copiar y Abrir carpeta/fichero de log.
- [x] 3.3 Añadir la acción de menú `Ver > Registro de diagnóstico` en `app/main_window.py`.

## 4. RedmineClient

- [x] 4.1 Añadir `get_project_trackers(project_id)` (`GET /projects/:id.json?include=trackers`).
- [x] 4.2 Refactor resiliente de la rama `multiple_projects` de `get_issues()` con `try/except RedmineError` por proyecto, manteniendo firma y compatibilidad (merge + dedupe + orden `updated_on` desc).
- [x] 4.3 Exponer los proyectos fallidos (dataclass/parámetro out) sin romper `TestGetIssuesMultiProject`.
- [x] 4.4 Registrar en el log los errores HTTP de las peticiones (sustituir los `except RedmineError: pass` de `:294`, `:348`, `:378`).

## 5. MainWindow

- [x] 5.1 `_cargar_issues()`: mostrar aviso ante `RedmineError` en lugar de solo cambiar el indicador (`:517-518`), y registrar en el log.
- [x] 5.2 `_cargar_issues()`: sanear IDs de proyecto huérfanos antes de consultar (aviso + log).
- [x] 5.3 `_cargar_issues()`: distinguir "sin resultados" de "error de carga".
- [x] 5.4 `_cargar_issues()`: mostrar qué proyectos fallaron y conservar los resultados válidos.
- [x] 5.5 `_nueva_tarea()` (`:917-920`): interpretar el 422 con Proyecto/Tipo/Estado en blanco y mostrar mensaje accionable si el proyecto no tiene trackers.
- [x] 5.6 Sustituir por registro los `except RedmineError: pass` de operaciones clave (`main_window.py:1410-1411, :365-366, :409-410, :431-432, :864-865, :869-870, :968-969, :973-974, :1069-1070, :1074-1075, :1197-1198, :1442-1443, :907, :1161`).

## 6. Diálogos y widgets

- [x] 6.1 `app/dialogs/task_dialog.py`: en modo creación, cargar trackers del proyecto al cambiar el combo de proyecto (sustituir el uso de `get_trackers()` global en `:124-129`).
- [x] 6.2 `app/dialogs/task_dialog.py`: avisar si el proyecto no tiene trackers y evitar el fallback silencioso a `tracker_id=1` (`:1034-1036`).
- [x] 6.3 `app/widgets/filter_bar.py` (y/o `MainWindow`): descartar IDs de proyecto huérfanos al poblar/restaurar el filtro de proyectos, antes de consultar la API (aviso + registro). Mantener INTACTO el contrato de `MultiSelectCombo.set_selected_ids` (fallback visual con id desconocido, test 14.4).
- [x] 6.4 Saneado de IDs de proyecto inválidos en la capa que conoce los proyectos (`FilterBar.populate_projects`/`select_projects` y `MainWindow._cargar_issues`), ya que `settings_manager` no puede validar IDs: al restaurar `filter_projects`/`notifications_projects` se descartan los IDs huérfanos antes de consultar.
- [x] 6.5 `app/services/settings_manager.py`: retirar el código muerto `filter_project_name` (`:197-202`).
- [x] 6.6 `app/dialogs/task_dialog.py`: sustituir los `except ...: pass` de las cargas auxiliares (`:411`, `:469`, `:487`, `:748`, `:760`, `:784`, `:801`) por registro en el log de diagnóstico.
- [x] 6.7 `app/dialogs/report_dialog.py`: registrar en el log de diagnóstico la excepción capturada en `:273`.
- [x] 6.8 `app/services/update_manager.py`: registrar en el log de diagnóstico las excepciones capturadas en `:38`, `:57` y `:120`.

## 7. Verificación

- [x] 7.1 Ejecutar `QT_QPA_PLATFORM=offscreen pytest` y comprobar que la suite pasa.
- [x] 7.2 Comprobar no regresión en `tests/test_mejoras_filtros.py` (`TestFilterBarMultiProject`, `TestFilterBarNombresCompletos`, `TestMultiSelectCombo*`).
- [x] 7.3 Comprobar no regresión en `tests/test_redmine_client.py` (`TestGetIssuesMultiProject`, `TestExtractValidationErrors`, `TestGetAllProjects`).
- [x] 7.4 Comprobar no regresión en `tests/test_main_window.py` (`TestNuevaTareaValidationErrors`, `TestCargarProyectosNombresCompletos`, `TestCargarIssuesNombresCompletos`, `TestFiltroFijadoPersistencia`).
- [x] 7.5 Comprobar no regresión en `tests/test_copy_task_project.py::TestCopyModeMissingDestinationAttributes`.
- [ ] 7.6 Verificación manual: proyecto sin trackers → mensaje accionable en alta de tarea.
- [ ] 7.7 Verificación manual: filtro con un proyecto borrado + otros válidos → resultados de los válidos + aviso del fallido.
- [x] 7.8 Verificación manual: apertura del fichero de log y de la ventana `Ver > Registro de diagnóstico` (verificado: arranque real de MainWindow y DebugLogDialog recibiendo mensajes en vivo).
- [x] 7.9 Comprobar que las excepciones de operaciones clave en `task_dialog.py`, `report_dialog.py` y `update_manager.py` quedan registradas en el log (no silenciadas) (verificado por inspección: no quedan `except RedmineError: pass`).

## 8. Correcciones de la verificación (/opsx-verify)

- [x] 8.1 Registrar a nivel ERROR las excepciones inesperadas (`except Exception`) en alta, edición, copia e informes (`main_window.py`).
- [x] 8.2 Registrar a nivel ERROR los `RedmineValidationError`, `RedmineConnectionError` y `RedmineError` capturados en las operaciones clave y cambios rápidos, con contexto de operación (`main_window.py`).
- [x] 8.3 Tests (caplog) que asertan el registro en log de errores de carga, alta y excepción inesperada (`tests/`).
- [x] 8.4 Tests de la ventana de depuración: apertura, límite de líneas, filtro por nivel y limpiar (`tests/test_debug_log_dialog.py`).
- [x] 8.5 Tests del aviso de proyectos no accesibles y del caso "todos fallan" a nivel UI (`tests/test_main_window.py`).
- [x] 8.6 `sys.excepthook` global que registra excepciones no capturadas (`main.py`).
- [x] 8.7 Registrar a nivel WARNING el fallo de `delete_attachment` (`redmine_client.py`).
- [x] 8.8 `setup_logging()` no escribe fichero bajo pytest cuando no se indica `log_dir`.
- [x] 8.9 Resolver las Open Questions en `design.md`.