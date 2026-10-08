## Why

El diálogo de asignación (`AssignDialog`) obliga al usuario a navegar manualmente una lista potencialmente larga de miembros sin posibilidad de buscar por teclado. Además, ni la acción de asignar ni la de completar permiten añadir un comentario explicativo, a diferencia del diálogo de rechazo (`RejectDialog`) que sí lo permite. Esto obliga a abrir la tarea por separado solo para documentar el motivo del cambio.

## What Changes

- **Combo de usuarios buscable** en `AssignDialog`: se añade `QCompleter` con `MatchContains` para filtrar miembros escribiendo.
- **Campo de comentarios en `AssignDialog`**: nuevo `QPlainTextEdit` para añadir una nota opcional al asignar.
- **Diálogo propio para completar**: se reemplaza el `QMessageBox.question` actual por un nuevo `CompleteDialog` con campo de comentarios opcional.
- **API para comentarios en asignar/completar**: `assign_issue()` y `complete_issue()` aceptan un parámetro opcional `notes` para enviar el comentario junto con la acción.

## Capabilities

### New Capabilities
- `asignar-con-busqueda-y-comentario`: El diálogo de asignación permite buscar usuarios por teclado y añadir un comentario opcional que se guarda como nota en la issue.
- `completar-con-comentario`: La acción de completar muestra un diálogo propio con campo de comentario opcional, en lugar del simple cuadro de confirmación actual.

### Modified Capabilities
<!-- Ninguna capacidad existente modifica sus requisitos -->

## Impact

- **`app/dialogs/assign_dialog.py`**: Modificación sustancial: añadir `QCompleter`, `QPlainTextEdit` para comentarios, actualizar layout y propiedad `selected_user_id` + nueva propiedad `notes`.
- **`app/dialogs/complete_dialog.py`**: Archivo nuevo. Diálogo simple con `QPlainTextEdit` para comentario opcional y botones Aceptar/Cancelar.
- **`app/main_window.py`**: Modificar `_asignar_tarea()` para pasar `notes` al API; reescribir `_completar_tarea()` para usar `CompleteDialog` en lugar de `QMessageBox`.
- **`app/services/redmine_client.py`**: Añadir parámetro `notes` opcional a `assign_issue()` y `complete_issue()`.
- Sin impacto en dependencias externas ni base de datos.
