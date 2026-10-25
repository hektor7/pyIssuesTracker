## Why

Al actualizar una tarea desde el diálogo de modificación (editar descripción, añadir un comentario o adjuntar un fichero), Redmine rechaza la operación con "Redmine rechazó la actualización: Categoría no está incluido en la lista". El fallo ocurre **solo** cuando el proyecto de la tarea no tiene categorías definidas y, en cambio, las acciones rápidas (menú contextual de estado/progreso/asignación y el botón "Completada"/cerrar) funcionan correctamente.

La causa raíz es que `RedmineClient.update_issue()` vuelca los campos tal cual y envía `"category_id": 0` cuando no hay categoría, mientras que `create_issue()` ya lo evita con un guard `if category_id:`. Redmine valida la inclusión de la categoría en el proyecto y `0` es un valor presente pero inválido (en Ruby `0` es *truthy*), por lo que devuelve HTTP 422 `Category is not included in the list`. Las operaciones rápidas no incluyen `category_id` en su payload y por eso no fallan. El formulario web nativo de Redmine envía `category_id=""` para la opción "(ninguna)".

## What Changes

- Normalizar el valor de `category_id` en `RedmineClient.update_issue()`: si se recibe un valor *falsy* (`0` o `None`), enviarlo como cadena vacía `""` (semántica nativa de Redmine para "sin categoría") en lugar de `0`.
- Mantener el id real cuando existe: un id positivo válido se envía tal cual.
- Añadir tests de regresión que aseguren que el payload de `PUT /issues/:id.json` **nunca** lleva `category_id: 0` y que la creación de tareas mantiene su comportamiento actual.
- No se modifica la UI: el diálogo ya ofrece "(Sin categoría)" con data `0`.

## Capabilities

### New Capabilities
- `edicion-categoria-tarea`: serialización válida del campo `category_id` al actualizar una tarea, normalizando los valores *falsy* a `""` y preservando los ids válidos, sin regresión en la creación.

### Modified Capabilities
- (ninguna)

## Impact

- `app/services/redmine_client.py`: método `update_issue()` (normalización de `category_id`). `create_issue()` no cambia (ya omite `0`).
- `tests/test_redmine_client.py`: nuevos tests de regresión del payload de actualización.
- Sin cambios de UI ni de esquema de Redmine. Cambio aditivo, sin migración de datos.
