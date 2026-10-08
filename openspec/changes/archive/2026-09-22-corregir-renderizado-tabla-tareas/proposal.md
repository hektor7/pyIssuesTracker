## Why

Tras el cambio de filtro multiproyecto y columnas configurables, el listado de tareas se corrompe cuando la tabla tiene una ordenación activa: las filas mezclan datos de varias tareas (una fila resaltada en rojo aparece "menos el final", la barra de progreso desaparece y se ve el texto crudo `100`, etc.) y las acciones sobre una fila operan sobre una tarea distinta. Pulsar "Refrescar" no lo corrige porque el defecto está en el proceso de repoblado de la tabla, no en los datos recibidos.

Causa raíz identificada: `TaskTable` (`app/widgets/task_table.py`) combina `setSortingEnabled(True)` con un repoblado basado en índices lógicos (`setItem(row, …)` / `setCellWidget(row, …)`) y con el acceso `self._issues[row]`. En cuanto hay una columna de ordenación activa, la vista reordena las filas a mitad del poblado, de modo que las celdas de una tarea aterrizan en filas distintas y el índice de fila deja de coincidir con la posición en `self._issues`. El filtro multiproyecto reagrupa y recarga la tabla con frecuencia, haciendo alcanzable este defecto latente en el flujo normal de uso.

## What Changes

- Aislar el repoblado de la ordenación: desactivar la ordenación mientras se rellenan las filas y reaplicar la ordenación activa al terminar.
- Eliminar la dependencia de `self._issues[row]`: resolver la tarea de una fila por su `id` (almacenado en el propio item), no por el índice de fila.
- Sustituir el `QProgressBar` de la columna "Progreso %" (cell widget + item dummy de ordenación) por un `QStyledItemDelegate` que pinta la barra a partir del dato del modelo.
- Sustituir el `QToolButton` de la columna URL por un item con icono gestionado mediante `cellClicked`.
- Garantizar el resaltado de prioridad en todas las celdas visibles de la fila, incluidas Progreso y URL, y que el resaltado siga a la tarea al ordenar y recargar.
- Sin cambios de comportamiento en la API de Redmine ni en la lógica de filtrado; sin nuevas dependencias.

## Capabilities

### New Capabilities
- `consistencia-tabla-tareas`: invariante de que cada fila visual contiene íntegramente los datos de una única issue bajo ordenación, filtrado, refresco y cambios de columnas; y que cualquier acción sobre una fila se aplica a la tarea mostrada en ella.

### Modified Capabilities
- `resaltado-prioridad-alta`: el resaltado debe cubrir todas las celdas visibles de la fila (la lista de celdas del spec actual está desactualizada) y mantenerse asociado a la tarea, no a la posición, tras ordenar o recargar.
- `barra-progreso`: la barra debe corresponder siempre al `done_ratio` de la tarea mostrada en la fila y nunca sustituirse por texto numérico crudo.
- `ordenacion-columnas`: la ordenación no debe mezclar datos entre tareas y la ordenación activa debe preservarse al refrescar y al cambiar de filtro.

## Impact

- **`app/widgets/task_table.py`**: repoblado (`set_issues`), mapeo fila→tarea, delegate de progreso, celda URL y aplicación del resaltado.
- **Nuevo** `ProgressBarDelegate` (clase interna en `task_table.py` o nuevo `app/widgets/progress_delegate.py`).
- **`tests/`**: nuevo `tests/test_task_table_render.py` (y ajustes menores en los tests existentes de la tabla si aplica).
- Sin cambios en `app/services/redmine_client.py`, `app/main_window.py` (más allá de que `set_issues` reciba la misma estructura) ni en la configuración persistida.
