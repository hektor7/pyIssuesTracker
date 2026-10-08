## 1. Tests (TDD) del cliente: journals, participantes y fecha de creación

- [x] 1.1 En `tests/test_redmine_client.py`, test: `_issue_from_json` parsea `journals` con `user_id`, `user_name`, `notes` y `created_on`, y conserva los journals sin notas.
- [x] 1.2 Test: `RedmineIssue.participant_ids` devuelve la unión sin duplicados de autor, asignado y autores de journals.
- [x] 1.3 Test: `get_issues(created_on_from="2026-01-01", created_on_to="2026-03-31")` envía `created_on=><2026-01-01|2026-03-31`; solo `from` → `>=`; solo `to` → `<=`.
- [x] 1.4 Test: `get_issues(include_journals=True)` incluye `journals` en el parámetro `include` de la petición.

## 2. RedmineClient: journals, participantes y `created_on`

- [x] 2.1 Añadir el campo `user_id` a la dataclass `RedmineJournal` en `app/services/redmine_client.py`.
- [x] 2.2 Parsear `journals` en `_issue_from_json` (conservando los journals sin notas) y guardarlos en el issue.
- [x] 2.3 Añadir a `RedmineIssue` la lista `participant_ids` sin duplicados (autor ∪ asignado ∪ autores de journals).
- [x] 2.4 Implementar la clasificación por rol (Creador / Actualizador / Participante) accesible desde el issue.
- [x] 2.5 Añadir a `get_issues()` los parámetros `created_on_from`, `created_on_to` e `include_journals`; construir `created_on` con la sintaxis de rango y añadir `journals` al `include`.

## 3. ReportGenerator (escritura ODS)

- [x] 3.1 Añadir `odfpy>=1.4` a `requirements.txt` y a `pyproject.toml`.
- [x] 3.2 Crear `tests/test_report_generator.py`: genera un ODS en un directorio temporal y verifica que es un ODF válido (ZIP con `content.xml`), que la cabecera está en negrita, el número de filas y los tipos de fecha y progreso.
- [x] 3.3 Implementar `app/services/report_generator.py` con la clase `ReportGenerator(columns, sheet_name)` y el método `write(path)`; cabecera en negrita, fila congelada, fechas como tipo fecha ODF, progreso numérico y anchos de columna.
- [x] 3.4 Implementar y testear el saneado del nombre de hoja (caracteres prohibidos por ODF y longitud máxima).

## 4. ReportDialog

- [x] 4.1 Crear `tests/test_report_dialog.py` con tests de: construcción del diálogo, precarga de proyectos, validación de rango inválido y lectura de las propiedades de filtros.
- [x] 4.2 Implementar `app/dialogs/report_dialog.py` con los grupos "Usuarios implicados" (`MultiSelectCombo` + checkboxes de rol), "Fechas de creación" (dos `QDateEdit` con checkbox habilitador) y "Proyectos" (`MultiSelectCombo`).
- [x] 4.3 Exponer `selected_user_ids`, `selected_roles`, `created_from`, `created_to` y `selected_project_ids`, y validar `desde <= hasta` antes de aceptar.

## 5. Toolbar y MainWindow

- [x] 5.1 Añadir la señal `informe_clicked` y la acción/botón "Informe" a `IssueToolbar` en `app/widgets/toolbar.py`.
- [x] 5.2 Conectar la señal en `MainWindow._connect_toolbar_signals`.
- [x] 5.3 Implementar `_generar_informe()` en `app/main_window.py`: comprobar conexión, construir el `ReportDialog` con proyectos y usuarios, obtener los datos y aplicar los filtros.
- [x] 5.4 Implementar `_compose_report_rows(issues)` que construye las filas del informe y la lista de usuarios implicados por tarea.
- [x] 5.5 Solicitar la ruta con `QFileDialog.getSaveFileName` (nombre por defecto `informe_<AAAAMMDD>_<HHMM>.ods`), invocar `ReportGenerator` con cursor de espera y mostrar confirmación.
- [x] 5.6 Manejar el caso "sin resultados" y los errores de consulta o de escritura con mensajes claros.

## 6. Verificación

- [x] 6.1 Crear/ajustar tests de `MainWindow` para la conexión del botón "Informe" y el flujo de generación (con `RedmineClient` y `ReportGenerator` mockeados).
- [x] 6.2 Ejecutar `QT_QPA_PLATFORM=offscreen pytest` y confirmar que no hay regresiones.
- [x] 6.3 Verificación manual: generar un informe filtrado por usuario, rango de fechas y proyectos, y abrirlo en LibreOffice Calc comprobando cabecera, fechas y usuarios implicados.
