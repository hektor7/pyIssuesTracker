## Why

La aplicación tiene cuatro deficiencias que afectan la productividad diaria: (1) no muestra las fechas de creación y modificación de las tareas, obligando a abrir Redmine en el navegador para consultarlas; (2) los filtros de estado y fecha no se combinan con lógica AND — al cambiar el filtro de fecha se ignora el filtro de estado activo; (3) solo se puede filtrar por un único asignado, lo que impide ver tareas de varias personas simultáneamente; (4) el checklist de tareas no aparece al crear una tarea nueva, solo al editarla, forzando un paso extra para añadir subtareas.

## What Changes

- Añadir columnas **Creado** y **Modificado** en la tabla de tareas con formato `DD/MM/YY HH:MM`, ordenables al hacer clic en la cabecera
- Corregir la lógica de filtros para que Estado + Fecha fin se combinen con AND en lugar de sobrescribirse mutuamente
- Convertir el filtro "Asignado a" de selección única a multiselección (permitir elegir varios asignados simultáneamente)
- Mostrar el widget de checklist en el diálogo de creación de tarea (modo alta), no solo en edición

## Capabilities

### New Capabilities
- `checklist-creacion-tarea`: Mostrar el widget de checklist en el diálogo de creación de tarea, permitiendo añadir subtareas desde el momento del alta sin necesidad de editar después

### Modified Capabilities
- `ordenacion-columnas`: Añadir columnas "Creado" y "Modificado" con fecha/hora formateada (`DD/MM/YY HH:MM`), ordenables por clic en cabecera
- `filtro-fecha`: Corregir la combinación de filtros para que el filtro de fecha fin se aplique con AND junto al filtro de estado activo, en lugar de ignorar este último
- `filtros-buscables`: Convertir el combo de "Asignado a" de selección única a multiselección, permitiendo seleccionar varios usuarios simultáneamente con checkboxes

## Impact

- **`app/widgets/task_table.py`**: Añadir columnas `created_at` y `updated_at` con formateo de fecha/hora, soporte de ordenación
- **`app/main_window.py`**: Modificar `_cargar_issues()` para asegurar que los filtros de estado y fecha se pasen simultáneamente a la API; adaptar la recepción de múltiples IDs de asignado
- **`app/widgets/filter_bar.py`**: Cambiar el combo de Asignado a de `QComboBox` simple a un widget multiselección (ej. `QComboBox` con checkboxes o `QListWidget` con checkboxes)
- **`app/dialogs/task_dialog.py`**: Mostrar el `QGroupBox` del checklist en modo creación, permitiendo añadir/eliminar items sin issue_id (persistir al guardar)
- **`app/services/redmine_client.py`**: Soportar múltiples `assigned_to_id` en `get_issues()`
- **`app/utils/`**: Posible utilidad para formateo de fechas `DD/MM/YY HH:MM`
