## Context

PyIssuesTracker es un cliente de escritorio Redmine en PyQt6 (Python ≥3.9, httpx, pytest) sin componente web. Estado actual del código relevante:

- `RedmineClient` (`app/services/redmine_client.py`) expone `get_all_projects`, `get_trackers`, `get_issue_statuses`, `get_issue_priorities`, `get_project_issue_categories`, `get_project_memberships`, `get_issues` (con `include=attachments`), `get_issue_with_journals` (devuelve el dict crudo del issue con `_journals` y `_attachments`), `create_issue`, `update_issue`, `upload_file`, `download_attachment` y `delete_attachment`. La dataclass `RedmineIssue` **no** tiene `custom_fields`, y `create_issue`/`update_issue` **no** envían `custom_fields`.
- `TaskDialog` (`app/dialogs/task_dialog.py`) construye su `scroll_layout` en este orden: **Datos básicos → Detalles → Checklist → Comentarios → Documentos adjuntos → Adjuntar archivos**. `_is_edit = bool(task_data)` decide el modo. `_on_project_changed()` recarga categorías y miembros. `_load_attachments()` pinta cada adjunto con botón "Descargar" y "−" (este último llama a `_on_delete_attachment`, que **borra en el servidor** vía `delete_attachment`). `_validate_and_accept()` sube `self._pending_files` y guarda `self._upload_tokens`.
- `TaskTable` (`app/widgets/task_table.py`) resuelve la issue de una fila por `ISSUE_ID_ROLE` (`_issue_at_row`). El menú contextual genérico (`_show_context_menu`, rama `else`) contiene "Copiar URL", separador y "Abrir en Redmine".
- `MainWindow` (`app/main_window.py`) construye `TaskDialog` en `_nueva_tarea()` (pasa `default_project_id` desde el filtro, categorías y miembros) y en `_editar_tarea(issue_id)` (obtiene `get_issue_with_journals` y arma `task_data`).
- La API de Redmine permite obtener los campos personalizados de un proyecto con `GET /projects/{id}.json?include=issue_custom_fields` (array `issue_custom_fields`) y devuelve los valores del issue en `issue["custom_fields"]` como `[{"id": N, "name": ..., "value": ...}]`.

## Goals / Non-Goals

**Goals:**
- Copiar una tarea a otro proyecto desde el menú contextual, con asunto, descripción citada y adjuntos propuestos, todos editables.
- Garantizar que en modo copia el botón "−" de un adjunto **nunca** borra en el servidor.
- Copiar los adjuntos realmente (descarga + resubida) y no modificar la tarea origen.
- Cargar, editar y enviar los campos personalizados del proyecto en alta y edición, con la sección situada antes de Comentarios.
- No fallar cuando el proyecto destino no tiene los mismos tracker/prioridad/categoría/estado o no tiene campos personalizados.

**Non-Goals:**
- No se copian journals, checklist, tiempo imputado ni relaciones de la tarea origen.
- No se modifica el flujo normal de edición: el botón "−" sigue borrando en el servidor fuera del modo copia.
- No se implementa `attachment_id` directo en `uploads` (no lo soporta la API de Redmine).
- No se persiste el proyecto destino elegido entre sesiones.
- No se cubren `field_format` exóticos (key/value, user, version): se usa un fallback de texto libre.

## Decisions

### D1: Señal dedicada y diálogo de proyecto destino
**Decisión**: añadir la señal `tarea_mover_proyecto = pyqtSignal(int)` a `TaskTable`, emitida desde la rama genérica de `_show_context_menu` con `int(issue["id"])`. `MainWindow` la conecta a `_copiar_tarea_otro_proyecto(issue_id)`, que abre un diálogo de selección de proyecto (combo buscable con `self._projects`) y, si se acepta, continúa el flujo.

**Alternativa considerada**: reutilizar `tarea_doble_click` con un estado global. Descartada: mezcla dos intenciones distintas y rompe la semántica de las señales existentes.

### D2: Descripción compuesta con cita en blockquote
**Decisión**: componer la descripción como la frase literal `Tarea creada partiendo de la tarea #<id_origen>`, una línea en blanco y el contenido de la descripción origen con cada línea prefijada por `> `. Si la descripción origen está vacía, solo se incluye la frase. El texto resultante se carga en `_description_edit` y es editable; lo que se envía es el contenido final editado.

**Alternativa considerada**: mover la tarea (`project_id`) con `update_issue`. Descartada por requisito explícito: la creación real es un `create_issue` en el destino y el origen no se toca.

### D3: Propuesta de adjuntos no destructiva en modo copia
**Decisión**: `TaskDialog` recibe un parámetro nuevo `copy_attachments` (lista de adjuntos de la tarea origen) y un flag interno `_copy_mode`. En `_copy_mode`, `_load_attachments()` pinta los adjuntos de la propuesta y el botón "−" se conecta a `_on_remove_proposed_attachment(attachment_id)`, que **solo** elimina el widget y la entrada de la lista propuesta: nunca llama a `delete_attachment`. En modo edición normal, `_on_delete_attachment` mantiene su comportamiento actual.

**Alternativa considerada**: reutilizar `_on_delete_attachment` con una comprobación de modo dentro. Descartada por claridad: dos métodos separados hacen imposible el borrado accidental en modo copia.

### D4: Copia real de adjuntos = descarga temporal + resubida
**Decisión**: para cada adjunto propuesto que quede al aceptar, `MainWindow` (o el propio diálogo en `_validate_and_accept`) descarga el contenido a un fichero temporal (`tempfile.TemporaryDirectory` + `download_attachment`) y lo resube con `upload_file` para obtener el token, que se añade a `uploads`. El fichero temporal se elimina al terminar.

**Razón**: la API de Redmine no permite referenciar un `attachment_id` existente en el payload de un issue nuevo; el único camino soportado es subir de nuevo el contenido.

**Alternativa considerada**: enviar `attachment_id` en `uploads`. Descartada: no está soportado por la API y produce error de validación.

### D5: Campos personalizados — modelo, endpoint y payload
**Decisión**: añadir la dataclass `RedmineCustomField(id, name, field_format, is_required, multiple, possible_values, default_value, visible, editable)`; `get_project_custom_fields(project_id)` hace `GET /projects/{project_id}.json?include=issue_custom_fields` y mapea `issue_custom_fields`. `RedmineIssue.custom_fields` es un `dict[int, Any]` (id → valor), parseado en `_issue_from_json`; `get_issue_with_journals` añade `_custom_fields` con la misma forma. `create_issue` y `update_issue` aceptan `custom_fields` y lo serializan como `[{"id": N, "value": X}]` dentro de `{"issue": {...}}`.

**Alternativa considerada**: guardar los valores como lista de dicts. Descartada: el acceso por id es más simple para precargar la UI en edición.

### D6: Sección "Campos personalizados" y edición por `field_format`
**Decisión**: crear `self._custom_fields_group` y añadirlo al `scroll_layout` **justo después del grupo Checklist y antes del grupo Comentarios**. Se oculta si el proyecto no tiene campos. Los widgets se construyen dinámicamente según `field_format` (string → `QLineEdit`; text → `QPlainTextEdit`; int → `QSpinBox`; float → `QDoubleSpinBox`; date → `QDateEdit` con checkbox de habilitación; bool → `QCheckBox`; list → `QComboBox` con `possible_values`; `multiple` → multiselección; desconocido → `QLineEdit`). `_on_project_changed` recarga los campos; en edición se precargan los valores actuales del issue.

**Alternativa considerada**: formulario estático. Descartada: los campos son distintos por proyecto y pueden no existir.

### D7: Serialización de valores y campos vacíos
**Decisión**: bool → `"1"`/`"0"`; date → ISO `YYYY-MM-DD`; int/float → cadena; list → valor del combo; multiple → lista de valores. La propiedad `TaskDialog.custom_fields` devuelve un `dict[int, Any]` con los campos con valor no vacío y, además, los campos que el issue ya tenía y el usuario ha vaciado (con `""`), para permitir limpiarlos. Los campos sin valor previo y vacíos se omiten del payload.

**Alternativa considerada**: enviar siempre todos los campos del proyecto. Descartada: enviar `""` a campos obligatorios provoca 422.

## Risks / Trade-offs

- **[Riesgo]** La descarga + resubida de adjuntos grandes alarga el guardado y puede agotar el timeout. → **Mitigación**: `upload_file` ya usa timeout ×4; usar `tempfile.TemporaryDirectory` para no acumular basura y mostrar error claro si falla.
- **[Riesgo]** Un campo personalizado obligatorio sin valor provoca 422 al crear/editar. → **Mitigación**: marcar visualmente los campos `is_required` y mostrar los errores de `RedmineValidationError` (ya se hace en `MainWindow`).
- **[Riesgo]** Regresión: el botón "−" de la propuesta podría acabar llamando a `delete_attachment` y borrar en el servidor. → **Mitigación**: método separado `_on_remove_proposed_attachment` y test explícito que verifica que `delete_attachment` no se invoca en modo copia.
- **[Riesgo]** `field_format` no contemplado (key/value, user, version) o `possible_values` vacío. → **Mitigación**: fallback a `QLineEdit` y no romper la carga.
- **[Riesgo]** El proyecto destino no tiene el mismo tracker/prioridad/categoría/estado. → **Mitigación**: recargar por proyecto y dejar el combo vacío/sin correspondencia sin lanzar error.
- **[Trade-off]** No se copian journals, checklist, tiempo ni relaciones; el usuario puede completarlos tras crear la tarea.
- **[Trade-off]** No se puede limpiar un campo personalizado que el issue nunca tuvo (no aplica); sí los que tenía y se vacían.

## Migration Plan

1. Tests TDD de cliente en rojo (campos personalizados y copia de adjuntos).
2. Implementar D5 (modelo, endpoint, parseo, payload) en `redmine_client.py`.
3. Implementar D6/D7 (sección de campos personalizados) en `task_dialog.py`.
4. Enviar `custom_fields` desde `MainWindow` en alta y edición.
5. Implementar D1 (señal + acción) y el diálogo de proyecto destino.
6. Implementar D2/D3/D4 (modo copia: descripción citada, propuesta no destructiva, descarga + resubida).
7. Ejecutar la suite completa en headless (`QT_QPA_PLATFORM=offscreen`).

**Rollback**: revertir el cambio. No hay migración de datos ni persistencia afectada.

## Open Questions

- ¿Debe poder copiarse la tarea al mismo proyecto (duplicado)? Propuesta: sí, es útil y no añade complejidad.
- ¿Debe copiarse el checklist de la tarea origen? Fuera de alcance de este cambio.
