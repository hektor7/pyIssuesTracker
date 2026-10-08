## 1. Catálogo y multilínea (TDD)

- [x] 1.1 En `tests/test_report_generator.py`, test: `REPORT_FIELDS` contiene las 17 claves en orden canónico y `DEFAULT_FIELD_KEYS` incluye todas.
- [x] 1.2 Test: `ReportGenerator` escribe un valor multilínea preservando la separación en líneas (varios párrafos en la misma celda).

## 2. Implementación del catálogo y multilínea

- [x] 2.1 Añadir a `app/services/report_generator.py` `REPORT_FIELDS` (lista de (clave, etiqueta) con los 17 campos) y `DEFAULT_FIELD_KEYS`.
- [x] 2.2 Soportar texto multilínea en `_make_cell` (un `text.P` por línea).

## 3. ReportDialog: selección de campos

- [x] 3.1 Tests en `tests/test_report_dialog.py`: grupo con 17 casillas, todas marcadas por defecto; `selected_fields` devuelve las claves marcadas en orden canónico; desmarcar reduce la lista; sin campos marcados no acepta (warning).
- [x] 3.2 Añadir a `ReportDialog` el grupo "Campos del informe" (un `QCheckBox` por campo), la propiedad `selected_fields` y la validación de al menos un campo en `accept()`.

## 4. MainWindow: columnas dinámicas, URL y comentarios

- [x] 4.1 Tests en `tests/test_main_window.py`: `_compose_report_rows(issues, field_keys)` produce filas alineadas con las claves; URL correcta (`{redmine_url}/issues/{id}`); comentarios formateados `[DD/MM/YYYY HH:MM] Autor: texto` y unidos por salto de línea; celda vacía sin comentarios; y que `_generar_informe` pasa a `ReportGenerator` solo las etiquetas de los campos marcados.
- [x] 4.2 Cambiar `_compose_report_rows` para aceptar las claves de campo y construir columnas y filas con el catálogo `REPORT_FIELDS`.
- [x] 4.3 Implementar el valor del campo URL y del campo Comentarios (journals con notas + formateo de fecha/hora).
- [x] 4.4 Pasar `dlg.selected_fields` desde `_generar_informe` y usar sus etiquetas como columnas del `ReportGenerator`.

## 5. Verificación

- [x] 5.1 Ejecutar `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` sin regresiones.
- [x] 5.2 Generar un ODS de muestra con campos seleccionados (incluyendo URL y Comentarios) y verificarlo con LibreOffice headless (conversión a CSV) comprobando columnas y que las celdas de comentarios conservan varias líneas.
