## 1. RedmineClient: soporte API

- [x] 1.1 Añadir parámetro `uploads=None` al método `update_issue()` en `app/services/redmine_client.py`, incluyéndolo en el payload si no es `None` (misma lógica que `create_issue()`)
- [x] 1.2 Implementar método `delete_attachment(attachment_id: int) -> bool` que haga `DELETE /attachments/{id}.json` y retorne `True` si el código es 2xx, `False` en caso contrario

## 2. TaskDialog: adjuntar archivos en edición

- [x] 2.1 Cambiar `self._upload_group.setVisible(not self._is_edit)` por `self._upload_group.setVisible(True)` en `app/dialogs/task_dialog.py` para mostrar la sección de adjuntar archivos también en modo edición

## 3. TaskDialog: botón Eliminar en adjuntos existentes

- [x] 3.1 Añadir un `QPushButton("−")` con tooltip "Eliminar adjunto" junto al botón "Descargar" en el método `_load_attachments()` de `app/dialogs/task_dialog.py`
- [x] 3.2 Conectar el botón "Eliminar" a un nuevo método `_on_delete_attachment(attachment_id, filename)` que muestre `QMessageBox.question` de confirmación y llame a `self._redmine.delete_attachment(attachment_id)`, eliminando el widget de la lista si tiene éxito o mostrando `QMessageBox.warning` si falla

## 4. MainWindow: pasar uploads al editar

- [x] 4.1 En `app/main_window.py`, dentro de `_editar_tarea()`, pasar `uploads=dlg.upload_tokens or None` en la llamada a `self._redmine.update_issue()`
