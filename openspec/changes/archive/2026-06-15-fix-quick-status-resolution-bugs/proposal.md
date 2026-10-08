## Why

Cuatro funcionalidades que funcionaban correctamente en versiones anteriores han dejado de funcionar debido a regresiones introducidas en commits recientes:

1. El menú contextual de progreso no se abre (regresión de `507f07d`)
2. El cambio de estado muestra error HTTP 422 (regresión de `9a218d6`: el error ahora es visible; antes se ignoraba)
3. El botón "Completada" falla con HTTP 422 (regresión de `e666347`: el nuevo campo `due_date` en el payload es rechazado por Redmine)
4. El diálogo de edición no muestra la persona asignada (omisión desde `017e423`: nunca se incluyó `assigned_to_id` en los datos del diálogo)

## What Changes

- **Bug #1 — Menú rápido de progreso no se abre** (`507f07d` + `29a93ad`): Se corrige la propagación del `contextMenuEvent` desde el `QProgressBar` hacia el `QTableWidget`. El `NoContextMenu` introducido en `507f07d` fue un fix insuficiente. Se instala un `eventFilter` en el `QProgressBar` que reenvía el evento de menú contextual al viewport de la tabla con las coordenadas correctas. Se verifica compatibilidad con el `sort_item` añadido en `29a93ad`.

- **Bug #2 — Cambio de estado muestra error HTTP 422** (`9a218d6`): El manejo de errores mejorado en `9a218d6` hizo visible un error que antes se ignoraba: Redmine rechaza (422) transiciones de estado no permitidas por el workflow del tracker. Se añade captura específica de `RedmineValidationError` en `_on_cambio_rapido` con un mensaje descriptivo que explique al usuario que el estado seleccionado puede no ser válido para el workflow de esa tarea.

- **Bug #3 — Botón "Completada" falla con HTTP 422** (`e666347`): El campo `due_date` añadido en `e666347` es rechazado por algunas instancias de Redmine cuando el tracker no lo soporta o el usuario no tiene permisos. Se implementa un enfoque try-retry: se intenta primero con `due_date=today` y si Redmine rechaza (422), se reintenta sin el campo. Si `resolved_status` es `None`, se muestra advertencia al usuario en lugar de enviar petición incompleta.

- **Bug #4 — Doble clic no muestra persona asignada** (`017e423`): Se añade la extracción de `assigned_to_id` del objeto anidado `assigned_to` en `_editar_tarea`, y se implementa la precarga del valor en `_assigned_combo` dentro de `_populate_fields` del `TaskDialog`.

## Capabilities

### Modified Capabilities
- `menu-contextual-progreso`: Se restaura la funcionalidad del menú contextual de progreso corrigiendo la propagación de eventos desde el `QProgressBar` hacia el `QTableWidget`.
- `menu-contextual-estado`: Se mejora el mensaje de error al capturar `RedmineValidationError`, indicando al usuario que el estado puede no ser válido para el workflow.
- `completar-con-comentario`: Se corrige la regresión de `due_date` que causa HTTP 422, haciendo el campo condicional. Se mejora la detección del estado "Resuelta" y se valida que no sea `None` antes de enviar la petición.
- `manejo-errores-api`: Se extiende la captura de `RedmineValidationError` a los cambios rápidos y al botón "Completada", con mensajes descriptivos.

## Impact

- **Código afectado**:
  - `app/widgets/task_table.py` — `_create_progress_bar()`: eliminar `NoContextMenu`, añadir `eventFilter` para reenviar `contextMenuEvent`
  - `app/main_window.py` — `_on_cambio_rapido()`: capturar `RedmineValidationError`; `_completar_tarea()`: hacer `due_date` condicional, validar `resolved_status`; `_editar_tarea()`: extraer `assigned_to_id`
  - `app/dialogs/task_dialog.py` — `_populate_fields()`: precargar `assigned_to_id` en el combo
  - `app/services/redmine_client.py` — `complete_issue()`: aceptar `due_date` como opcional real (si es `None`, no se incluye)
- **Tests a actualizar**:
  - `tests/test_main_window.py` — tests para `_editar_tarea` con `assigned_to_id`
  - `tests/test_task_dialog_members.py` — verificar precarga de `assigned_to_id`
  - `tests/test_redmine_client.py` — verificar `complete_issue` sin `due_date`
- **No hay breaking changes**
