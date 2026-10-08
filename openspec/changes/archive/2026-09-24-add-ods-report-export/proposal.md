## Why

PyIssuesTracker permite consultar y editar tareas de Redmine, pero **no ofrece ninguna forma de extraer los datos**. Hoy, cuando alguien necesita un informe de tareas (para una reunión, una facturación o una auditoría de carga de trabajo), debe hacer capturas de pantalla o copiar filas a mano. Además, la aplicación no sabe quién ha intervenido en una tarea: solo muestra el autor y el asignado, no a quienes la han actualizado o comentado, información que Redmine sí expone a través de los *journals*.

Se necesita un **módulo de generación de informes** que produzca un fichero ODS de LibreOffice, invocable desde la barra superior, y que permita acotar el contenido por usuarios implicados (creador, actualizador o participante), por rango de fechas de creación y por proyectos.

## What Changes

- Añadir un **botón "Informe"** en la barra superior (`IssueToolbar`) que emita una señal nueva y abra un diálogo de configuración del informe.
- Crear un **diálogo de informe** (`ReportDialog`) con tres dimensiones de filtrado combinables:
  - **Usuarios implicados**: multiselección de usuarios + selección de los roles que cuentan como implicación ("Creador", "Actualizador", "Participante"). La tarea entra en el informe si alguno de los usuarios seleccionados cumple alguno de los roles marcados.
  - **Rango de fechas de creación**: dos `QDateEdit` (desde / hasta) sobre `created_on`, opcionales e independientes entre sí.
  - **Proyectos**: multiselección de proyectos (reutilizando `MultiSelectCombo`).
- Añadir el campo **"usuarios implicados"** al modelo de datos del cliente: `RedmineClient` parsea los *journals* del issue (`include=journals`) y expone los ids de los usuarios que crearon, actualizaron o comentaron la tarea.
- Añadir a `RedmineClient.get_issues()` el soporte de `created_on` (rango `><`) y la inclusión de `journals` en la petición.
- Crear un **generador de informes ODS** (`ReportGenerator`) que escriba un fichero `.ods` válido con cabecera destacada, tipos correctos (fechas, progreso) y las columnas de la tabla de tareas.
- **Nueva dependencia**: `odfpy` (escritura de ODS en Python puro).
- NO se modifica el filtro de fecha existente (`due_date`) ni la tabla de tareas: el rango de fechas del informe es sobre la fecha de creación y vive únicamente en el diálogo de informe.

## Capabilities

### New Capabilities
- `generacion-informes-ods`: botón en la barra superior, diálogo de configuración del informe (usuarios implicados por rol, rango de fechas de creación, proyectos), determinación de las tareas incluidas y escritura del fichero `.ods` de LibreOffice con su formato y columnas.
- `participacion-usuarios-tareas`: determinación de los usuarios implicados en una tarea (creador, actualizador y participante) a partir del issue y de sus *journals*, expuesta por `RedmineClient`, y soporte del filtro por fecha de creación en las consultas de tareas.

### Modified Capabilities
- Ninguna. El filtro de fecha por `due_date` de `filtro-fecha` y la tabla de tareas no cambian su comportamiento; el informe aporta sus propias dimensiones de filtrado.

## Impact

- `requirements.txt` / `pyproject.toml`: nueva dependencia `odfpy>=1.4`.
- `app/services/redmine_client.py`: `RedmineJournal` incorpora `user_id`; nuevo campo `participant_ids` (o equivalente) en `RedmineIssue`; parseo de `journals` en `_issue_from_json`; `get_issues()` acepta `created_on_from`, `created_on_to` e `include_journals`; construcción del parámetro `created_on=><from|to`.
- `app/services/report_generator.py` (**nuevo**): clase `ReportGenerator` que serializa filas/columnas a un `.ods` con `odfpy`.
- `app/dialogs/report_dialog.py` (**nuevo**): `ReportDialog` con los filtros y la escritura del fichero.
- `app/widgets/toolbar.py`: nueva señal `informe_clicked` y botón "Informe".
- `app/main_window.py`: conexión de la señal, apertura del diálogo, obtención de los datos con los filtros y llamada a `ReportGenerator`; manejo de errores y confirmación al usuario.
- `app/utils/constants.py`: claves nuevas de `QSettings` si se persiste el último directorio de guardado.
- `tests/`: nuevos tests de cliente (parseo de journals y filtro por fecha de creación), del generador ODS y del diálogo de informe; ajustes en `tests/test_main_window.py` y `tests/test_redmine_client.py` si procede.
