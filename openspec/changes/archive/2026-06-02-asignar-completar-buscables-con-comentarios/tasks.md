## 1. API: soporte de comentarios en asignar y completar

- [x] 1.1 Añadir parámetro `notes: str = ""` a `assign_issue()` en `app/services/redmine_client.py`. Si se proporciona, incluirlo en el payload del PUT.
- [x] 1.2 Añadir parámetro `notes: str = ""` a `complete_issue()` en `app/services/redmine_client.py`. Si se proporciona, incluirlo en el payload del PUT.

## 2. AssignDialog: búsqueda por teclado y campo de comentario

- [x] 2.1 Hacer editable el combo de usuarios en `app/dialogs/assign_dialog.py`: añadir `setEditable(True)`, `setInsertPolicy(NoInsert)` y `QCompleter` con `MatchContains`. Sincronizar el modelo del completer al poblar los miembros.
- [x] 2.2 Añadir `QPlainTextEdit` para comentarios opcionales en `AssignDialog`, con placeholder "Añadir un comentario (opcional)...". Ajustar layout y tamaño del diálogo.
- [x] 2.3 Añadir propiedad `notes` al diálogo que devuelva el texto del campo de comentario.
- [x] 2.4 Modificar `_asignar_tarea()` en `app/main_window.py` para pasar `notes=dlg.notes` a `self._redmine.assign_issue()`.

## 3. CompleteDialog: nuevo diálogo para completar tarea

- [x] 3.1 Crear `app/dialogs/complete_dialog.py` con una clase `CompleteDialog(QDialog)` que contenga `QPlainTextEdit` para comentario opcional y botones Aceptar/Cancelar.
- [x] 3.2 Añadir propiedad `notes` al diálogo.
- [x] 3.3 Reescribir `_completar_tarea()` en `app/main_window.py`: sustituir `QMessageBox.question` por `CompleteDialog` y pasar `notes=dlg.notes` a `self._redmine.complete_issue()`.

## 4. Verificación

- [x] 4.1 Verificar que el combo de usuarios en AssignDialog permite buscar escribiendo.
- [x] 4.2 Verificar que al asignar con comentario, la nota aparece en el historial de Redmine.
- [x] 4.3 Verificar que al completar con comentario, la nota aparece en el historial de Redmine.
- [x] 4.4 Verificar que asignar/completar sin comentario sigue funcionando correctamente.
