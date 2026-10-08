## 1. Recolección y unión de campos personalizados (TDD)

- [x] 1.1 En `tests/test_main_window.py`, test: `_report_custom_fields()` devuelve la unión sin duplicados de los campos personalizados de todos los proyectos (`get_project_custom_fields`), ordenada por nombre, y tolera que un proyecto falle (try/except).
- [x] 1.2 Test: `_report_field_value(issue, "cf_7")` devuelve el valor del campo 7; lista → unida por ", "; ausente → "".

## 2. Implementación en MainWindow

- [x] 2.1 Implementar `_report_custom_fields()` (unión por id, orden por nombre, try/except por proyecto).
- [x] 2.2 Ampliar `_report_field_value` para reconocer las claves `cf_<id>` y formatear el valor (multivalor unido por ", ", vacío si ausente).
- [x] 2.3 Pasar `custom_fields` al `ReportDialog` desde `_generar_informe` y construir las columnas del `ReportGenerator` a partir de las claves seleccionadas (estándar + `cf_<id>`).

## 3. ReportDialog: campos personalizados

- [x] 3.1 Tests en `tests/test_report_dialog.py`: con `custom_fields=[(7,"Cliente"),(9,"Sprint")]` el diálogo muestra esas casillas desmarcadas; al marcarlas, `selected_fields` incluye `cf_7`/`cf_9`; sin campos personalizados no se muestra el subgrupo.
- [x] 3.2 Añadir a `ReportDialog` el parámetro `custom_fields`, el subgrupo "Campos personalizados" (casillas desmarcadas) y su integración en `selected_fields` (claves `cf_<id>`).

## 4. Verificación

- [x] 4.1 Ejecutar `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` sin regresiones.
- [x] 4.2 Generar un ODS de muestra con un campo personalizado presente en un proyecto y ausente en otro, y verificar con LibreOffice headless (CSV) que la columna aparece rellena en unas filas y vacía en otras.

## 5. Correcciones de verificación

- [x] 5.1 Test: un campo personalizado disponible pero no seleccionado (`cf_7` fuera de `selected_fields`) no aparece como columna en el `ReportGenerator`.
- [x] 5.2 Test: con la selección estándar por defecto (17 campos, sin `cf_`), el `ReportGenerator` se crea con columnas exactamente `REPORT_COLUMNS`.
- [x] 5.3 Campos por proyecto en alcance: `_report_custom_fields_for_projects(ids)` filtra por proyecto (None/[] → todos) y el `ReportDialog` recalcula el subgrupo al cambiar la selección de proyectos (provider + preservación del marcado previo).
- [x] 5.4 `_generar_informe` pasa `custom_fields` (preselección) y `custom_fields_provider` al diálogo; `label_by_key` usa la unión completa; suite completa en verde.
