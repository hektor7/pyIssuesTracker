## 1. Bug #1 — Restaurar menú contextual de progreso en QProgressBar

- [x] 1.1 En `app/widgets/task_table.py`, método `_create_progress_bar`: eliminar `bar.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)` y reemplazar por `bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)` con conexión de `bar.customContextMenuRequested` para reemitir `self.customContextMenuRequested.emit(bar.mapTo(self.viewport(), pos))`
- [x] 1.2 Verificar que el `sort_item` introducido en commit `29a93ad` no interfiera con `rowAt()`/`columnAt()` en `_show_context_menu`. Si interfiere, ajustar el mapeo de coordenadas
- [x] 1.3 Probar manualmente: clic derecho sobre barra de progreso → debe aparecer el menú con 0%, 20%, 40%, 60%, 80%, 100%
- [x] 2.3 Probar manualmente: intentar cambiar estado de un issue a uno no permitido → debe mostrar mensaje descriptivo en lugar de error genérico
- [x] 3.5 Probar manualmente: pulsar botón "Completada" en un issue sin `due_date` → debe completarse sin error. Pulsar "Completada" en un issue con `due_date` → debe completarse con la fecha actual
- [x] 4.3 Probar manualmente: hacer doble clic en una tarea que tenga persona asignada → el diálogo de edición debe mostrar la persona asignada seleccionada en el combo "Asignado a"

## 5. Tests

- [x] 5.1 Añadir test en `tests/test_main_window.py` para verificar que `_editar_tarea` incluye `assigned_to_id` en `task_data` cuando el issue tiene `assigned_to`
- [x] 5.2 Añadir test en `tests/test_main_window.py` para verificar que `_editar_tarea` incluye `assigned_to_id=0` cuando el issue no tiene `assigned_to`
- [x] 5.3 Añadir test en `tests/test_task_dialog_members.py` para verificar que `_populate_fields` precarga `assigned_to_id` en el combo
- [x] 5.4 Añadir test en `tests/test_main_window.py` para verificar que `_completar_tarea` no incluye `due_date` cuando el issue no lo tiene
- [x] 5.5 Añadir test en `tests/test_main_window.py` para verificar que `_completar_tarea` muestra advertencia si `resolved_status` es `None`
- [x] 5.6 Ejecutar todos los tests existentes: `python -m pytest tests/ -v` — todos deben pasar

## 6. Verificación final

- [x] 6.1 Verificar que el menú rápido de progreso funciona en todas las filas de la tabla
- [x] 6.2 Verificar que el cambio de estado muestra mensaje descriptivo al fallar
- [x] 6.3 Verificar que el botón "Completada" funciona en issues con y sin `due_date`
- [x] 6.4 Verificar que el doble clic muestra la persona asignada correctamente
- [x] 6.5 Verificar que no hay regresiones en otras funcionalidades (crear tarea, editar tarea, asignar, filtrar, etc.)
