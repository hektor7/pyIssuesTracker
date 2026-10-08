## 1. Menú contextual del grid — Limpiar fecha fin

- [x] 1.1 Añadir método `_show_due_date_menu(self, pos, issue_id, due_date)` en `task_table.py` que muestre un `QMenu` con la opción "Limpiar fecha fin" y "Abrir en Redmine"
- [x] 1.2 La opción "Limpiar fecha fin" debe estar deshabilitada (`setEnabled(False)`) si `due_date` ya está vacío (`""` o `None`)
- [x] 1.3 Al seleccionar "Limpiar fecha fin", emitir `due_date_cambiada.emit(issue_id, "")`
- [x] 1.4 Modificar `_show_context_menu` para que cuando `col == COL_DUE_DATE` delegue en `_show_due_date_menu` en lugar de mostrar el menú genérico
- [x] 1.5 Verificar que `main_window.py._on_due_date_changed` ya maneja correctamente `due_date=""` (enviando cadena vacía a Redmine) — solo confirmación, sin cambios necesarios

## 2. Diálogo de edición/alta — Vaciar QDateEdit al desmarcar checkbox

- [x] 2.1 Modificar el slot `_due_check.toggled` en `task_dialog.py` para que, además de `setEnabled(checked)`, también haga `self._due_edit.setDate(date.today())` cuando `checked` es `False`
- [x] 2.2 Verificar que al volver a marcar el checkbox, el `QDateEdit` se habilita y muestra `date.today()` (comportamiento por defecto ya cubierto por el código existente)
- [x] 2.3 Confirmar que el comportamiento de guardado en `main_window.py` (líneas ~469 y ~542) sigue funcionando correctamente: `due_date=dlg.due_date if dlg.due_enabled else ""` — solo confirmación, sin cambios necesarios

## 3. Verificación y pruebas

- [x] 3.1 Probar manualmente: abrir tarea con fecha fin → clic derecho en columna fecha fin → "Limpiar fecha fin" → verificar que el grid muestra la celda vacía y Redmine recibe `due_date=""`
- [x] 3.2 Probar manualmente: abrir tarea sin fecha fin → clic derecho en columna fecha fin → verificar que "Limpiar fecha fin" aparece deshabilitada
- [x] 3.3 Probar manualmente: diálogo de edición → marcar checkbox, seleccionar fecha → desmarcar checkbox → verificar que `QDateEdit` se deshabilita y muestra `date.today()` → guardar → verificar que la tarea queda sin fecha fin
- [x] 3.4 Probar manualmente: diálogo de edición → tarea con fecha fin existente → desmarcar checkbox → guardar → verificar que se elimina la fecha fin
