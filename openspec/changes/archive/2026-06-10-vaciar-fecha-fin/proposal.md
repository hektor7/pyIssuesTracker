## Why

El campo `due_date` (fecha fin) no puede vaciarse de forma intuitiva desde la interfaz de usuario. En el grid principal no existe ninguna acción que permita limpiar una fecha ya establecida, y en el diálogo de edición/alta, desmarcar el checkbox de "Fecha fin" no vacía el valor del campo (solo lo deshabilita). Esto obliga al usuario a recurrir a workarounds incómodos o a limpiar el campo directamente desde Redmine.

## What Changes

- **Grid (TaskTable):** Añadir opción "Limpiar fecha fin" en el menú contextual (botón derecho) cuando se hace clic sobre la columna `due_date`, permitiendo vaciar la fecha de la tarea seleccionada.
- **Diálogo de edición/alta (TaskDialog):** Al desmarcar el checkbox "Fecha fin", vaciar automáticamente el valor del `QDateEdit` además de deshabilitarlo. Al volver a marcarlo, restaurar la fecha actual o la fecha previamente guardada.
- **Edición inline (TaskTable):** Permitir que al borrar el texto del `QDateEdit` inline y confirmar, la fecha se vacíe correctamente (actualmente si la fecha es inválida, ya se envía `""`, pero no hay forma fácil de forzar ese estado).

## Capabilities

### New Capabilities

- `grid-clear-due-date`: Capacidad de limpiar/vaciar el campo `due_date` desde el menú contextual del grid principal.
- `dialog-clear-due-date`: Capacidad de vaciar la fecha fin al desmarcar el checkbox en el diálogo de edición/alta.

### Modified Capabilities

_(No hay specs existentes que modificar)_

## Impact

- **task_table.py**: Añadir opción en `_show_context_menu` para la columna `COL_DUE_DATE` que emita una nueva señal `due_date_cleared` o reutilice `due_date_cambiada` con valor vacío. Añadir handler en `MainWindow`.
- **task_dialog.py**: Modificar el slot conectado a `_due_check.toggled` para que al desmarcar limpie el `QDateEdit` (o almacene su estado previo). Evaluar si la propiedad `due_date` debe devolver `""` cuando `due_enabled` es `False`.
- **main_window.py**: Añadir handler para la nueva acción de limpiar fecha desde el grid.
