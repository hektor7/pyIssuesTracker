## 1. Tests (TDD)

- [x] 1.1 Test de `update_issue(42, category_id=0)` (proyecto sin categorías): el payload de `PUT /issues/:id.json` contiene `"category_id": ""` y NUNCA `0`.
- [x] 1.2 Test de `update_issue(42, category_id=7)`: el payload envía `"category_id": 7` tal cual.
- [x] 1.3 Test de `update_issue(42, subject="x")` sin el argumento `category_id`: el payload NO incluye la clave `category_id` (no regresión).
- [x] 1.4 Test de limpieza: `update_issue(42, category_id=0)` sobre una tarea con categoría envía `"category_id": ""` (permite limpiarla).
- [x] 1.5 Test de no regresión de `create_issue(..., category_id=0)`: el payload NO incluye `category_id`.

## 2. Implementación

- [x] 2.1 Normalizar `category_id` *falsy* (`0` o `None`) a `""` en `RedmineClient.update_issue()` antes de construir el payload; enviar el id positivo tal cual.
- [x] 2.2 Verificar que `create_issue()` NO cambia (mantiene su guard `if category_id:`).
- [x] 2.3 Verificar que las acciones rápidas (`assign_issue`, `complete_issue`, `reject_issue`) NO se modifican.

## 3. Verificación

- [x] 3.1 Ejecutar `QT_QPA_PLATFORM=offscreen pytest tests/test_redmine_client.py` y comprobar que pasa.
- [x] 3.2 Ejecutar la suite completa `QT_QPA_PLATFORM=offscreen pytest` sin regresiones.
- [ ] 3.3 Verificación manual: editar descripción, añadir comentario y adjuntar fichero en un proyecto SIN categorías → sin error HTTP 422 "Categoría no está incluido en la lista".
- [ ] 3.4 Verificación manual: editar una tarea en un proyecto CON categorías → sigue enviando el id válido y la categoría se conserva.
