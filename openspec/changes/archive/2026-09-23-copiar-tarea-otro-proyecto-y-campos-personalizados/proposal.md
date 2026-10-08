## Why

Dos carencias del cliente de escritorio PyIssuesTracker frente a la interfaz web de Redmine:

1. **No existe forma de crear una tarea en otro proyecto partiendo de una existente.** Cuando el usuario detecta que una tarea está en el proyecto equivocado, o quiere duplicarla en otro proyecto, hoy debe recrearla a mano: copiar el asunto, copiar y citar la descripción y volver a subir cada adjunto. El cliente no ofrece ninguna acción para ello desde el listado de tareas.

2. **Los campos personalizados de Redmine son invisibles para la aplicación.** `RedmineIssue` no los parsea, `create_issue`/`update_issue` no los envían y el `TaskDialog` no los muestra. Como muchos proyectos exigen campos personalizados obligatorios o los usan para clasificar, las tareas creadas o editadas desde la app quedan incompletas o la API responde 422 con un error que el usuario no puede resolver desde la aplicación.

## What Changes

- Añadir al menú contextual genérico de `TaskTable` la acción "Mover a otro proyecto..." que emite una señal nueva con el `id` de la tarea origen (resuelto por ID de fila, no por índice).
- Añadir un diálogo de selección de proyecto destino con combo buscable (patrón `_make_searchable_combo`).
- Abrir `TaskDialog` en modo creación con el proyecto destino preseleccionado, el asunto de la tarea origen copiado (editable) y la descripción compuesta por el texto literal `Tarea creada partiendo de la tarea #<id_origen>` seguido del contenido original citado en blockquote (cada línea prefijada con `> `).
- Mostrar en el `TaskDialog` los adjuntos de la tarea origen como **propuesta de copia**, con botón de eliminar que solo los quita de la propuesta y **nunca** llama a `delete_attachment`.
- Copiar realmente los adjuntos mediante descarga a fichero temporal (`download_attachment`) + resubida (`upload_file`) para obtener tokens `uploads`, porque la API de Redmine no permite adjuntar un `attachment_id` existente a un issue nuevo.
- Recargar categorías, miembros y campos personalizados del proyecto destino y dejar vacíos los atributos que no existan en él, sin que la operación falle.
- Crear la tarea con `create_issue` en el proyecto destino; la tarea origen no se modifica.
- Parsear `custom_fields` en `RedmineIssue` y en `get_issue_with_journals`.
- Añadir la dataclass `RedmineCustomField` y el método `get_project_custom_fields(project_id)` (GET `/projects/{id}.json?include=issue_custom_fields`).
- Aceptar `custom_fields` en `create_issue` y `update_issue`, enviándolos como `[{"id": N, "value": X}]`.
- Añadir al `TaskDialog` una sección "Campos personalizados" situada **antes** del grupo Comentarios, oculta si el proyecto no tiene campos y recargada al cambiar de proyecto (alta y edición).
- Enviar los campos personalizados al guardar, tanto en creación como en edición.

## Capabilities

### New Capabilities
- `copiar-tarea-otro-proyecto`: flujo completo de copiar/mandar una tarea existente a otro proyecto desde el menú contextual de la tabla, incluyendo la composición de la descripción citada, la propuesta de adjuntos no destructiva y la creación de la tarea en el proyecto destino sin tocar el origen.
- `campos-personalizados-tarea`: lectura, edición y envío de los campos personalizados de Redmine por proyecto, tanto en el cliente REST (`RedmineCustomField`, `get_project_custom_fields`, parseo de `custom_fields`, envío en create/update) como en el `TaskDialog`.

### Modified Capabilities
- Ninguna. El comportamiento de `document-attachments-download` en el flujo normal (modo edición) no cambia. La regla "el botón − de la propuesta de copia no borra en el servidor" es un requisito propio de la capacidad nueva `copiar-tarea-otro-proyecto`, no una modificación de aquella.

## Impact

- `app/services/redmine_client.py`: nueva dataclass `RedmineCustomField`; campo `custom_fields` en `RedmineIssue`; parseo en `_issue_from_json` y `get_issue_with_journals`; nuevo método `get_project_custom_fields(project_id)`; parámetro `custom_fields` en `create_issue` y `update_issue`; soporte de resubida de adjuntos para la copia (descarga temporal + `upload_file`).
- `app/dialogs/task_dialog.py`: nuevo grupo `_custom_fields_group` insertado entre Checklist y Comentarios; widgets dinámicos por `field_format`; recarga en `_on_project_changed`; carga de valores actuales en edición; modo "propuesta de adjuntos" no destructivo; nueva propiedad `custom_fields`.
- `app/widgets/task_table.py`: nueva señal `tarea_mover_proyecto(int)` y acción "Mover a otro proyecto..." en el menú contextual genérico.
- `app/main_window.py`: manejo de la señal, diálogo de selección de proyecto, composición de la descripción citada, descarga + resubida de adjuntos y llamada a `create_issue` con `custom_fields`; envío de `custom_fields` también en `_editar_tarea()`.
- `tests/`: nuevos tests de cliente (campos personalizados y copia de adjuntos) y de diálogo (sección de campos, propuesta de adjuntos), además de ajustes en `tests/test_main_window.py` si procede.
