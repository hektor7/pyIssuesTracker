## 1. Tests (TDD) de reproducción y blindaje

- [x] 1.1 Crear `tests/test_task_table_render.py` con un test que, con una ordenación activa (`sortItems`), verifique que cada fila de `TaskTable` contiene datos coherentes de una única issue (ID, título y prioridad de la misma tarea) tras `set_issues`.
- [x] 1.2 Test: `_issue_at_row(row)` devuelve la issue mostrada en la fila tras ordenar, no la de `self._issues[row]`.
- [x] 1.3 Test: `set_issues` con ordenación activa no reordena a mitad del poblado y conserva `horizontalHeader().sortIndicatorSection()` y `.sortIndicatorOrder()`.
- [x] 1.4 Test: la columna Progreso no usa cell widget, y su item guarda el entero en `DisplayRole` (ordenación numérica) sin exponer texto crudo.
- [x] 1.5 Test: todas las celdas visibles de una fila "Inmediata"/"Urgente" tienen `background()` rojo, tanto tras ordenar como tras un segundo `set_issues`.
- [x] 1.6 Test: recargar con menos issues no deja filas ni widgets residuales.

## 2. Repoblado aislado de la ordenación

- [x] 2.1 En `TaskTable.set_issues`, capturar `sortIndicatorSection()`/`sortIndicatorOrder()`, desactivar la ordenación (`setSortingEnabled(False)`), limpiar celdas e items y repoblar.
- [x] 2.2 Al finalizar el poblado, reactivar la ordenación y reaplicar la ordenación capturada (`sortItems(section, order)` con guarda si `section < 0`).
- [x] 2.3 Verificar que, con la ordenación desactivada, `setItem` no dispara reordenado durante el poblado.

## 3. Mapeo fila → tarea por ID

- [x] 3.1 Definir `TaskTable.ISSUE_ID_ROLE` y guardar el `id` de la issue en los items de cada fila.
- [x] 3.2 Mantener `self._issues_by_id: dict[int, dict]` en `set_issues`.
- [x] 3.3 Añadir los helpers `_issue_at_row(row)` y `_issue_id_at_row(row)` que resuelvan por el rol de ID.
- [x] 3.4 Migrar `_on_double_click`, `_show_context_menu`, `_on_due_date_edited`, `refresh_due_date_cell`, `get_selected_issue_id` y `get_selected_row_data` a los helpers.
- [x] 3.5 Sustituir `_editing_row` por `_editing_issue_id` en el flujo de edición inline de fecha (`eventFilter`, `_commit_due_date_edit`, `_cancel_due_date_edit`).

## 4. Delegate de la barra de progreso

- [x] 4.1 Implementar `ProgressBarDelegate(QStyledItemDelegate)` que pinte la barra según el entero de `DisplayRole`, respetando `item.background()`/`item.foreground()` y el color por progreso (verde 100 / naranja parcial / gris 0).
- [x] 4.2 Registrar el delegate en `COL_PROGRESS` con `setItemDelegateForColumn` y eliminar el cell widget `QProgressBar` y el item dummy.
- [x] 4.3 Escribir el entero de progreso en `DisplayRole` del item de progreso (mantener formato "N%" mediante el delegate).
- [x] 4.4 Verificar que la ordenación por "Progreso %" sigue siendo numérica.

## 5. Celda URL y resaltado uniforme

- [x] 5.1 Sustituir el `QToolButton` de `COL_URL` por un `QTableWidgetItem` con icono y tooltip; abrir la URL en `cellClicked` filtrando `col == COL_URL`.
- [x] 5.2 Ajustar `_on_double_click` para no abrir la tarea al hacer doble clic en `COL_URL`.
- [x] 5.3 Aplicar fondo y texto de prioridad a todas las celdas visibles, incluidas Progreso y URL.
- [x] 5.4 Eliminar los `removeCellWidget` de `COL_PROGRESS` y `COL_URL` en `set_issues` (ya no hay widgets) y limpiar cualquier residuo.

## 6. Verificación

- [x] 6.1 Ejecutar `pytest` en headless (`QT_QPA_PLATFORM=offscreen`) y confirmar que no hay regresiones.
- [x] 6.2 Verificación manual: filtrar por dos proyectos (padre e hijo), ordenar por varias columnas, refrescar y comprobar filas íntegras, barras correctas y resaltado completo.
- [x] 6.3 Verificación manual: menú contextual de progreso/estado/asignado y doble clic sobre filas ordenadas aplican a la tarea correcta.