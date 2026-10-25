## Context

PyIssuesTracker es un cliente de escritorio PyQt6 para Redmine (HTTP vía `httpx`, tests con `pytest` + `pytest-qt`). El diálogo de modificación de tareas permite editar la descripción, añadir un comentario y adjuntar ficheros. Al guardar, `app/main_window.py` (`_editar_tarea()`, aprox. líneas 1123-1138) llama siempre a `self._redmine.update_issue(...)` pasando `category_id=dlg.category_id`.

`TaskDialog.category_id` (`app/dialogs/task_dialog.py`, propiedad ~1140) devuelve `self._cat_combo.currentData() or 0`. Cuando el proyecto de la tarea no tiene categorías definidas, el combo solo contiene el item "(Sin categoría)" con data `0`, por lo que devuelve `0`. `RedmineClient.update_issue()` (`app/services/redmine_client.py`, líneas 792-800) construye `payload = {"issue": fields}` y vuelca los campos tal cual, enviando `"category_id": 0`.

Redmine valida la inclusión de la categoría en el proyecto; `0` es un valor presente pero inválido (en Ruby `0` es *truthy*, por lo que no se omite), y responde HTTP 422 `Category is not included in the list`. `create_issue()` (líneas 749-778) ya protege con `if category_id:` y por eso la creación funciona. Las operaciones rápidas (`assign_issue`, `complete_issue`, `reject_issue`) no incluyen `category_id` y por eso tampoco fallan.

## Goals / Non-Goals

**Goals:**
- Que la actualización de una tarea (descripción, comentario, adjuntos) no falle en proyectos sin categorías.
- Centralizar la corrección en el límite de serialización del payload para cubrir a todos los callers de `update_issue()`.
- Preservar el comportamiento correcto cuando la tarea tiene una categoría válida o cuando se limpia una existente.
- Asegurar por tests que el payload de `PUT /issues/:id.json` nunca lleva `category_id: 0`.

**Non-Goals:**
- No rediseñar el diálogo de edición ni el flujo de edición de tareas.
- No tocar las acciones rápidas (ya funcionan correctamente).
- No cambiar `create_issue()` (ya omite `0`).
- No modificar la UI: el diálogo ya ofrece "(Sin categoría)" con data `0`.

## Decisions

- **D1: Normalizar en el límite de serialización (`RedmineClient.update_issue`).** Se transforma cualquier valor *falsy* de `category_id` (`0` o `None`) en cadena vacía `""`, y se envía el id positivo tal cual. Se elige este punto porque centraliza el arreglo para todos los callers y espeja el guard `if category_id:` que ya existe en `create_issue()`.
- **D2: Enviar `""` (no omitir la clave).** El formulario web nativo de Redmine envía `category_id=""` para "(ninguna)", y Redmine interpreta la cadena vacía como *nil* → sin categoría. Esto permite tanto el caso "proyecto sin categorías" como el de "limpiar una categoría existente".

**Alternativas consideradas y rechazadas:**
- (a) Aplicar el guard solo en `_editar_tarea` de `main_window.py`: cubre únicamente un caller y deja el método inseguro para el resto.
- (b) Omitir la clave `category_id` cuando es `0`: impide limpiar una categoría existente (no se podría dejar una tarea sin categoría).
- (c) Enviar `None`/`null`: Redmine no lo trata como "sin categoría"; sigue siendo un valor inválido para la validación de inclusión.

## Risks / Trade-offs

- [Campo `category_id: ""` extra e inocuo en cada edición de proyectos sin categorías] → Redmine nativo acepta `""` como "sin categoría"; es exactamente lo que envía su propio formulario web.
- [Compatibilidad con instancias Redmine no nativas que rechacen `""`] → Bajo riesgo: `""` es la semántica documentada/nativa para "sin categoría"; el caso de id positivo no cambia.
- [Tests existentes que asumen `category_id=0` en el payload] → Revisar y ajustar los tests afectados en `tests/test_redmine_client.py`.

## Migration Plan

Cambio aditivo y de serialización, sin migración de datos ni cambios de esquema. Rollback: revertir la normalización en `update_issue()`; no hay estado persistido que deshacer.

## Open Questions

- Ninguna pendiente: la causa raíz y la solución están verificadas contra la validación nativa de Redmine.
