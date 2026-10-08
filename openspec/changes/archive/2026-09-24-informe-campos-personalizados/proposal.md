## Why

El informe ODS permite elegir entre 17 campos fijos, pero no incluye los **campos personalizados** de Redmine. Como cada proyecto define sus propios campos personalizados y un mismo informe puede abarcar tareas de proyectos distintos, hoy es imposible exportar esa información. Se necesita poder seleccionar cualquier campo personalizado presente en las tareas y mostrarlo relleno donde exista y vacío donde no.

## What Changes

- Añadir al grupo "Campos del informe" del diálogo un subgrupo **"Campos personalizados"** con una casilla por cada campo personalizado presente en **al menos uno** de los proyectos en alcance (unión por id de campo).
- Los campos personalizados son seleccionables como cualquier otro campo; por defecto aparecen **desmarcados** (se conserva el informe actual si no se toca nada).
- Cuando un campo personalizado está marcado, el informe muestra su valor para las tareas que lo tengan y una celda **vacía** para el resto (tareas de proyectos que no lo definen o sin valor).
- Los campos personalizados con varios valores se unen con ", ".
- La unión de campos personalizados se calcula a partir de los proyectos cargados, de modo que cualquier campo de cualquier proyecto es seleccionable.

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `generacion-informes-ods`: la selección de campos incorpora los campos personalizados de Redmine (unión por proyecto) y el ODS los muestra rellenos solo donde existan.

## Impact

- `app/dialogs/report_dialog.py`: nuevo parámetro `custom_fields` y subgrupo "Campos personalizados" con casillas; se integran en `selected_fields`.
- `app/main_window.py`: recolecta la unión de campos personalizados de los proyectos (`get_project_custom_fields`), la pasa al diálogo; `_report_field_value` soporta claves `cf_<id>`; las filas incluyen sus valores (vacíos si no aplica).
- `app/services/report_generator.py`: el catálogo estándar se mantiene; los campos personalizados son dinámicos (no van en `REPORT_FIELDS`).
- `tests/`: nuevos tests del diálogo (campos personalizados listados y seleccionables) y de `MainWindow` (unión, valor relleno/vacío, multivalor).
