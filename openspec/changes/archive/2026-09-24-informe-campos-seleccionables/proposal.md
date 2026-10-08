## Why

El informe ODS actual exporta siempre las mismas 15 columnas fijas y no incluye la URL ni los comentarios de cada tarea. Los usuarios necesitan adaptar cada informe a su caso (por ejemplo, incluir solo ID, Título y Estado; o añadir la URL de la tarea y sus comentarios con autor, fecha y hora), pero hoy no pueden elegir qué campos aparecen.

## What Changes

- Añadir al `ReportDialog` un grupo **"Campos del informe"** con una casilla por campo disponible.
- Campos disponibles: los 15 actuales más **URL** y **Comentarios** (17 en total).
- Todas las casillas marcadas por defecto (se conserva el comportamiento actual).
- Validar que haya al menos un campo marcado para poder generar el informe.
- El informe usa como columnas exactamente los campos marcados, en el orden canónico del catálogo.
- Nuevo campo **URL**: URL absoluta de la tarea (`{redmine_url}/issues/{id}`).
- Nuevo campo **Comentarios**: por tarea, sus comentarios (journals con notas) con autor, fecha y hora, en formato `[DD/MM/YYYY HH:MM] Autor: texto`, separados por saltos de línea en la misma celda.
- El generador ODS soporta texto multilínea (varios párrafos por celda).

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `generacion-informes-ods`: el diálogo de configuración incorpora la selección de campos; el contenido y formato del ODS pasan a depender de los campos elegidos; se añaden los campos URL y Comentarios por tarea.

## Impact

- `app/dialogs/report_dialog.py`: nuevo grupo "Campos del informe" (checkboxes), propiedad `selected_fields` y validación de al menos un campo.
- `app/services/report_generator.py`: catálogo `REPORT_FIELDS` (clave → etiqueta) y soporte de texto multilínea en las celdas.
- `app/main_window.py`: `_compose_report_rows(issues, field_keys)` construye columnas y filas según los campos elegidos; genera la URL y los comentarios.
- `app/utils/dates.py`: reutilizado para formatear fecha y hora de los comentarios.
- `tests/`: nuevos tests del diálogo (selección y validación), del generador (multilínea y catálogo) y de `MainWindow` (columnas según selección, URL y comentarios).
