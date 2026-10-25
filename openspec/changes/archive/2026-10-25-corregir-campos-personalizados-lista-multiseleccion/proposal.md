## Why

En el diálogo de crear/editar tarea, los campos personalizados de Redmine que son listas de valores se muestran como si fueran texto libre: el selector de selección múltiple vuelca todas las opciones en un `QListWidget` sin checkboxes ni selección visible, con los textos largos cortados. El usuario no percibe que puede seleccionar valores y, además, la selección simple no elide los textos largos. Esto hace que campos como "Causa de la Incidencia" sean prácticamente inutilizables.

## What Changes

- Los campos personalizados con `multiple == True` se renderizan con un selector multiselección explícito: plegado por defecto con un resumen ("N seleccionados" o el valor único), popup con checkboxes, búsqueda cuando hay muchas opciones, y texto elidido con tooltip.
- Los campos de formato `list` de selección simple mantienen `QComboBox`, pero con textos largos elididos, tooltip con el valor completo y un ancho mínimo razonable.
- Los campos con `possible_values` vacío se muestran deshabilitados con un texto de ayuda en lugar de un control vacío y **no se envían** en el payload, de modo que no se borra el valor previo del issue (mejoras adyacentes al síntoma reportado, acotadas para no ampliar el diff más allá de la rama de campos de lista).
- Se preserva sin cambios el contrato de datos: valores previos en edición, `default_value`, recarga al cambiar de proyecto, marcas de obligatorio y la serialización actual (`list[str]` para múltiple; `""`/`[]` para vaciados; omisión de vacíos sin valor previo).
- Los formatos no contemplados (`user`, `version`, `enumeration`, `key_value_list`, `link`, etc.) siguen cayendo en el control de texto libre.

## Capabilities

### New Capabilities

Ninguna. El cambio ajusta comportamiento ya especificado en una capability existente.

### Modified Capabilities

- `campos-personalizados-tarea`: cambia el requisito de edición de valores según el formato del campo. Se precisan los escenarios de lista de selección simple (elisión y tooltip), de valor múltiple (selector con checkboxes, resumen plegado, búsqueda y tooltip) y de `possible_values` vacío (control deshabilitado con ayuda), manteniendo intactos el resto de requisitos.

## Impact

- `app/dialogs/task_dialog.py`: `_build_custom_field_widget()`, `_set_custom_field_value()`, `_read_custom_field_value()` y el contrato público `custom_fields`.
- `app/widgets/`: posible widget reutilizable de multiselección de opciones de texto (patrón de referencia: `app/widgets/multi_select_combo.py`).
- `tests/test_task_dialog_custom_fields.py`: se amplía la cobertura de construcción de widgets, serialización y casos de lista simple/múltiple/vacía, incluida la adaptación de los dos tests acoplados al `QListWidget` al API nuevo del widget.
- Sin cambios en `app/services/redmine_client.py`, en la exportación ODS ni en `MainWindow` más allá del consumo ya existente de `custom_fields`.
