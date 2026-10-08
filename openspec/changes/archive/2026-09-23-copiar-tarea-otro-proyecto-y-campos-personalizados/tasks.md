## 1. Tests (TDD) del cliente: campos personalizados

- [x] 1.1 Crear `tests/test_redmine_custom_fields.py` con un test que, con `httpx` mockeado, verifique que `get_project_custom_fields(7)` hace `GET /projects/7.json?include=issue_custom_fields` y mapea cada entrada de `issue_custom_fields` a un `RedmineCustomField` (id, name, field_format, is_required, multiple, possible_values, default_value, visible, editable).
- [x] 1.2 Test: proyecto sin `issue_custom_fields` devuelve lista vacía sin lanzar excepción.
- [x] 1.3 Test: `_issue_from_json` parsea `custom_fields` a `dict[int, Any]` (id → value), incluyendo valores `multiple` (lista) y ausencia de la clave (dict vacío).
- [x] 1.4 Test: `get_issue_with_journals` incluye `_custom_fields` con los valores actuales del issue.
- [x] 1.5 Test: `create_issue(..., custom_fields={3: "A", 4: ["x", "y"]})` envía en el payload `custom_fields: [{"id": 3, "value": "A"}, {"id": 4, "value": ["x", "y"]}]` dentro de `{"issue": {...}}`.
- [x] 1.6 Test: `update_issue(id, custom_fields={3: ""})` envía la entrada con `value: ""` (permite limpiar el campo).

## 2. RedmineClient: campos personalizados

- [x] 2.1 Añadir la dataclass `RedmineCustomField` en `app/services/redmine_client.py` con los campos id, name, field_format, is_required, multiple, possible_values, default_value, visible, editable.
- [x] 2.2 Añadir el campo `custom_fields: dict[int, Any]` a `RedmineIssue` y parsearlo en `_issue_from_json`.
- [x] 2.3 Añadir `_custom_fields` (dict id → valor) al dict devuelto por `get_issue_with_journals`.
- [x] 2.4 Implementar `get_project_custom_fields(project_id) -> list[RedmineCustomField]` con `GET /projects/{id}.json?include=issue_custom_fields`.
- [x] 2.5 Añadir el parámetro `custom_fields` a `create_issue` y serializarlo como lista `[{"id": N, "value": X}]` solo si no está vacío.
- [x] 2.6 Aceptar `custom_fields` en `update_issue` (dentro del dict `fields`) y serializarlo igual en el payload.

## 3. TaskDialog: sección de campos personalizados

- [x] 3.1 Crear `self._custom_fields_group` (`QGroupBox("Campos personalizados")`) e insertarlo en el `scroll_layout` de `app/dialogs/task_dialog.py` **entre el grupo Checklist y el grupo Comentarios**; oculto por defecto.
- [x] 3.2 Implementar `_load_custom_fields_for_project(project_id)` que llame a `get_project_custom_fields`, construya un widget por campo según `field_format` y oculte el grupo si no hay campos.
- [x] 3.3 Implementar el constructor de widgets por formato: string → `QLineEdit`, text → `QPlainTextEdit`, int → `QSpinBox`, float → `QDoubleSpinBox`, date → `QDateEdit` con checkbox, bool → `QCheckBox`, list → `QComboBox` con `possible_values`, `multiple` → multiselección; fallback a `QLineEdit`.
- [x] 3.4 Marcar visualmente los campos con `is_required` (p. ej. sufijo en la etiqueta) y aplicar `default_value` cuando exista.
- [x] 3.5 Llamar a la carga de campos personalizados desde `_on_project_changed()` (alta y edición) y desde `_populate_fields()` en modo edición.
- [x] 3.6 PreCargar los valores actuales del issue desde `task_data["custom_fields"]` (o `_custom_fields`) al abrir en modo edición.
- [x] 3.7 Implementar la propiedad `custom_fields` que devuelva `dict[int, Any]` serializando por `field_format` (bool → "1"/"0", date → ISO, int/float → str, multiple → lista) e incluyendo con `""` los campos que el issue ya tenía y el usuario ha vaciado.

## 4. MainWindow: envío de campos personalizados

- [x] 4.1 En `app/main_window.py`, añadir `custom_fields=dlg.custom_fields or None` a la llamada a `create_issue()` dentro de `_nueva_tarea()`.
- [x] 4.2 Añadir `custom_fields=dlg.custom_fields or None` a la llamada a `update_issue()` dentro de `_editar_tarea()`.
- [x] 4.3 Incluir `custom_fields` en el `task_data` construido en `_editar_tarea()` a partir de `data.get("_custom_fields", {})`.

## 5. TaskTable + MainWindow: acción "Mover a otro proyecto"

- [x] 5.1 Añadir la señal `tarea_mover_proyecto = pyqtSignal(int)` a `TaskTable` en `app/widgets/task_table.py`.
- [x] 5.2 En la rama genérica de `_show_context_menu`, añadir la acción "Mover a otro proyecto..." que emita `tarea_mover_proyecto` con `int(issue["id"])`, manteniendo "Copiar URL" y "Abrir en Redmine".
- [x] 5.3 Conectar la señal en `app/main_window.py` a un nuevo método `_copiar_tarea_otro_proyecto(issue_id)`.
- [x] 5.4 Implementar el diálogo de selección de proyecto destino (combo buscable con `self._projects`); si el usuario cancela, no hacer nada.

## 6. TaskDialog: modo copia (propuesta de adjuntos no destructiva)

- [x] 6.1 Añadir a `TaskDialog.__init__` los parámetros `copy_from_issue_id: int = 0`, `copy_attachments: list | None = None`, `copy_subject: str = ""` y `copy_description: str = ""` (precarga de asunto/descripción), y el flag interno `self._copy_mode = bool(copy_from_issue_id)`.
- [x] 6.2 En `_setup_ui()`, mostrar el grupo "Documentos adjuntos" en modo copia con los adjuntos propuestos, reutilizando `_load_attachments()` con los datos de `copy_attachments`.
- [x] 6.3 Implementar `_on_remove_proposed_attachment(attachment_id)` que solo elimine el widget y la entrada de la propuesta, sin llamar a `delete_attachment`.
- [x] 6.4 Conectar el botón "−" a `_on_remove_proposed_attachment` cuando `self._copy_mode` sea verdadero, y a `_on_delete_attachment` en el resto de casos.
- [x] 6.5 Añadir la propiedad `proposed_attachments` que devuelva la lista de adjuntos que quedan en la propuesta.

## 7. MainWindow: composición de la descripción y creación en destino

- [x] 7.1 Implementar `_compose_copied_description(issue_id, description)` que genere `Tarea creada partiendo de la tarea #<id>` + línea en blanco + cada línea de la descripción origen prefijada con `> ` (solo la frase si la descripción está vacía).
- [x] 7.2 Obtener la tarea origen con `get_issue_with_journals(issue_id)` para disponer de asunto, descripción y adjuntos.
- [x] 7.3 Cargar categorías, miembros y campos personalizados del proyecto destino antes de construir el `TaskDialog` en modo copia.
- [x] 7.4 Copiar los adjuntos propuestos: descargar cada uno a un fichero temporal con `download_attachment` y resubirlo con `upload_file`, recogiendo los tokens `uploads`; eliminar el directorio temporal al terminar.
- [x] 7.5 Llamar a `create_issue()` en el proyecto destino con asunto, descripción compuesta, atributos del destino, `custom_fields` y `uploads`; refrescar la tabla tras crear.
- [x] 7.6 Verificar que la tarea origen no se modifica en ningún caso (no se llama a `update_issue` sobre el id origen).

## 8. Verificación

- [x] 8.1 Crear `tests/test_task_table_copy_project.py` con un test que verifique la presencia de la acción "Mover a otro proyecto..." y la emisión de `tarea_mover_proyecto` con el id correcto tras ordenar la tabla.
- [x] 8.2 Crear `tests/test_task_dialog_custom_fields.py` con tests de: sección oculta sin campos, sección visible con campos, recarga al cambiar de proyecto, precarga en edición y serialización por `field_format`.
- [x] 8.3 Crear `tests/test_copy_task_project.py` con tests de: composición de la descripción citada (multilínea y vacía) y de que el modo copia **no** invoca `delete_attachment` al eliminar un adjunto propuesto.
- [x] 8.4 Ejecutar `QT_QPA_PLATFORM=offscreen pytest` y confirmar que no hay regresiones en la suite existente.
- [x] 8.5 Verificación manual: copiar una tarea con 2 adjuntos y descripción multilínea a otro proyecto; comprobar asunto/descripción citada, adjuntos copiados, origen intacto y campos personalizados del destino enviados.
