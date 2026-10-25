## 1. Preparación

- [x] 1.1 Confirmar la línea base en headless: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/test_task_dialog_custom_fields.py tests/test_redmine_custom_fields.py tests/test_report_dialog.py` en verde.
- [x] 1.2 Revisar `app/dialogs/task_dialog.py:601-758` y `app/widgets/multi_select_combo.py` para fijar el patrón de popup, búsqueda y tooltips.

## 2. Widget `MultiValueCombo` (TDD)

- [x] 2.1 **RED** — Crear `tests/test_multi_value_combo.py` con un test que instancia `MultiValueCombo`, llama a `set_items(["A", "B"])`, marca "B" con `set_selected_values` y espera `selected_values() == ["B"]`; verificar que falla porque el módulo no existe.
- [x] 2.2 **GREEN** — Crear `app/widgets/multi_value_combo.py` con `MultiValueCombo(QWidget)`: botón de resumen, popup `Qt.WindowType.Popup | FramelessWindowHint` creado con el widget como `parent`, `QLineEdit` de búsqueda y `QListWidget` con `SelectionMode.NoSelection`; hacer pasar 2.1.
- [x] 2.3 **RED** — Añadir test del resumen del botón (vacío, un valor elidido por la derecha, "N seleccionados" y tooltip con los valores completos); verificar que falla.
- [x] 2.4 **RED** — Añadir test de búsqueda `case-insensitive` que oculta opciones no coincidentes sin alterar la selección, y de vaciado de la búsqueda al abrir y cerrar el popup; verificar que falla.
- [x] 2.5 **RED** — Añadir test de tooltip por opción con el texto completo y de estado sin opciones (`set_items([])` → widget deshabilitado con texto de ayuda); verificar que falla.
- [x] 2.6 **GREEN** — Implementar el resumen con elisión y tooltip, la búsqueda con su vaciado, el tooltip por opción y el estado sin opciones; hacer pasar 2.3, 2.4 y 2.5.
- [x] 2.7 **RED** — Añadir test de interacción real: marcar dos opciones seguidas con `setCheckState(Checked)` deja ambas marcadas (`selected_values() == ["A", "B"]`) y la lista interna está en `SelectionMode.NoSelection`; verificar que falla.
- [x] 2.8 **GREEN** — Implementar el marcado basado exclusivamente en `checkState` (sin `SelectionMode`), con `set_selected_values()` sustituyendo la selección completa; hacer pasar 2.7.
- [x] 2.9 **RED** — Añadir test de cierre del popup: tras `hide()` se cumple `assert combo._popup.isVisible() is False` y `combo._popup.parent() is combo`; verificar que falla.
- [x] 2.10 **GREEN** — Cerrar el popup en `hideEvent()` y limpiar la búsqueda; hacer pasar 2.9.

## 3. Integración de campos múltiples en `TaskDialog`

- [x] 3.1 Añadir a `tests/test_task_dialog_custom_fields.py` (o a un nuevo fichero de test) el caso de campo `multiple` con `possible_values` y esperar `kind == "multiple"` y un `MultiValueCombo` como `widget`; verificar que falla con el `QListWidget` actual.
- [x] 3.2 Sustituir la rama `field_def.multiple` de `_build_custom_field_widget()` para devolver `(MultiValueCombo, "multiple", None)` con `set_items(possible_values)`; hacer pasar 3.1.
- [x] 3.3 Adaptar la rama `"multiple"` de `_set_custom_field_value()` para usar `set_selected_values` con lista o valor único, y hacer pasar el test de precarga en edición (`{5: ["x", "y"]}`).
- [x] 3.4 Adaptar la rama `"multiple"` de `_read_custom_field_value()` para usar `selected_values()`, verificando `list[str]` y `[]` al vaciar un campo con valor previo.
- [x] 3.5 Verificar que `_apply_custom_field_values()` sigue aplicando `default_value` a un campo múltiple sin valor previo (test nuevo).
- [x] 3.6 Adaptar al API nuevo los dos tests existentes acoplados al `QListWidget`: `TestEditModePreload` (`tests/test_task_dialog_custom_fields.py:168-173` → `selected_values() == ["x", "y"]`) y `TestSerialization` (`:214-215` → `set_selected_values(["x", "z"])`), sin reducir cobertura.

## 4. Lista de selección simple

- [x] 4.1 Añadir test que comprueba ancho mínimo, `textElideMode == ElideRight` en `combo.view()` y tooltip con el valor completo en cada opción; verificar que falla.
- [x] 4.2 Ajustar la rama `"list"` de `_build_custom_field_widget()` con `setMinimumContentsLength`, `setMinimumWidth`, `setTextElideMode` y `setToolTip` por item; hacer pasar 4.1.
- [x] 4.3 **RED** — Añadir test de `possible_values` vacío en formato `list`: control deshabilitado con texto de ayuda y serialización `""`; verificar que falla.
- [x] 4.4 **GREEN** — Implementar el estado sin opciones en la rama `list` (control deshabilitado con ayuda) y hacer pasar 4.3.
- [x] 4.5 **RED** — Añadir test de `possible_values` vacío con `multiple` verdadero: control deshabilitado con ayuda y serialización `[]` solo si tenía valor previo; verificar que falla.
- [x] 4.6 **GREEN** — Implementar el estado sin opciones en la rama `multiple` y hacer pasar 4.5.

## 5. Preservación del contrato y regresión

- [x] 5.1 Confirmar que las seis clases `TestSectionVisibility`, `TestReloadOnProjectChange`, `TestEditModePreload`, `TestSerialization`, `TestUnsupportedFieldFormat` y `TestRequiredFieldLabel` siguen pasando, con la única adaptación explícita descrita en 3.6.
- [x] 5.2 Confirmar que el fallback de formato `"link"` sigue devolviendo `QLineEdit` con `kind == "string"` y serializa texto libre.
- [x] 5.3 Comprobar que la recarga al cambiar de proyecto (`_load_custom_fields_for_project`) reconstruye el multiselector sin dejar popups abiertos: tras `hide()` y tras la recarga se cumple `_popup.isVisible() is False`, y el popup tiene el combo como `parent` (`_popup.parent() is combo`).
- [x] 5.4 Ejecutar la suite completa: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` en verde.
- [x] 5.5 Revisar docstrings y comentarios nuevos en español y `logger.warning` en fallos de carga no fatales según el estilo del repo.

## 6. Correcciones de la verificación

- [x] 6.1 RED: tests de valor previo no representable (opciones vacías y valor fuera de las opciones) y actualización de las expectativas de los tests 4.3/4.5.
- [x] 6.2 GREEN: `previo_no_representable` en `_apply_custom_field_values()` y omisión del campo en `custom_fields`.
- [x] 6.3 Actualizar `design.md` (D5, riesgos), el delta spec y `proposal.md` a la conducta de preservación.
- [x] 6.4 Añadir test de etiqueta obligatoria en campo de valor múltiple y test de que el popup muestra las opciones al desplegarse.
- [x] 6.5 Eliminar el import duplicado de `Qt` en `tests/test_multi_value_combo.py`.
- [x] 6.6 Alinear docstring de `custom_fields`, D7, la referencia de línea de `Risks` y el escenario de vaciado con la regla de preservación.
