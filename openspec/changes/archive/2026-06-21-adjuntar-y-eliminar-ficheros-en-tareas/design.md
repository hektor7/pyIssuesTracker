## Context

El `TaskDialog` actual tiene dos secciones relacionadas con archivos:
- **"Documentos adjuntos"**: visible solo en edición, muestra adjuntos existentes con botón "Descargar".
- **"Adjuntar archivos"**: visible solo en creación (`self._upload_group.setVisible(not self._is_edit)`), permite añadir nuevos archivos para subir.

Esta asimetría impide adjuntar ficheros al editar una tarea. Además, ninguna de las dos secciones ofrece botón para eliminar adjuntos existentes.

A nivel de API, `create_issue()` acepta `uploads` (tokens de archivo subidos), pero `update_issue()` no tiene ese parámetro.

El mecanismo de subida real (`_validate_and_accept`) ya está preparado para subir archivos tanto en creación como en edición — solo está bloqueado a nivel de UI.

## Goals / Non-Goals

**Goals:**
- Permitir adjuntar archivos en el modo de edición del `TaskDialog`.
- Permitir eliminar adjuntos existentes desde el `TaskDialog`, tanto en creación como en edición.
- Añadir el endpoint `DELETE /attachments/{id}.json` en `RedmineClient`.
- Mantener el comportamiento existente en creación sin cambios (salvo la adición del botón eliminar).

**Non-Goals:**
- No se modifica el mecanismo de subida en sí (`upload_file`), que ya funciona correctamente.
- No se añade drag & drop para adjuntar archivos.
- No se modifica la visualización de adjuntos existentes (solo se añade el botón eliminar).
- No se modifica el `TaskDialog` para permitir adjuntar archivos en tareas que aún no se han guardado en el servidor.

## Decisions

### D1: Mostrar `_upload_group` siempre, independientemente del modo

**Decisión**: Cambiar `self._upload_group.setVisible(not self._is_edit)` por `self._upload_group.setVisible(True)`.

**Alternativa considerada**: Crear una sección separada para upload en edición. Descartada porque añadiría complejidad innecesaria: la funcionalidad de subida es idéntica en ambos modos.

### D2: Añadir `uploads` como parámetro de `update_issue()`

**Decisión**: Añadir `uploads=None` como parámetro opcional al método `update_issue()`, con la misma lógica que `create_issue()`: si hay uploads, se añaden al payload.

**Alternativa considerada**: Subir los archivos en una llamada separada después del update. Descartada porque la API de Redmine soporta `uploads` en el payload de `PUT /issues/{id}.json`, igual que en `POST`.

### D3: Botón "Eliminar" en cada adjunto existente

**Decisión**: Añadir un `QPushButton("−")` junto al botón "Descargar" en cada fila de adjuntos de `_load_attachments()`. Al pulsarlo, se muestra `QMessageBox.question` de confirmación y, si se acepta, se llama a `redmine.delete_attachment(id)`.

**Alternativa considerada**: Eliminar solo al aceptar el diálogo (borrado diferido). Descartada porque el feedback inmediato es mejor para el usuario y evita confusiones (el adjunto desaparece de la lista al instante).

### D4: Método `delete_attachment()` en RedmineClient

**Decisión**: Añadir `delete_attachment(attachment_id: int) -> bool` que haga `DELETE /attachments/{id}.json`. Retorna `True` si el código de estado es 2xx, `False` en caso contrario.

**Alternativa considerada**: Lanzar excepción en caso de error. Descartada para mantener consistencia con el patrón de la app: mostrar warning al usuario en el diálogo sin interrumpir el flujo.

## Risks / Trade-offs

- **[Riesgo]** El endpoint `DELETE /attachments/{id}.json` podría no estar disponible en todas las versiones de Redmine. → **Mitigación**: Si la API devuelve error, se muestra un mensaje warning al usuario indicando que la operación no está soportada.
- **[Riesgo]** Eliminar un adjunto es irreversible y no tiene vuelta atrás si el usuario cancela el diálogo después. → **Mitigación**: Se muestra siempre un diálogo de confirmación antes de eliminar, con texto claro de que la acción es permanente.
- **[Trade-off]** Los adjuntos se muestran/eliminan también en modo creación si la tarea ya tiene adjuntos (caso raro: tarea creada con adjuntos desde otro cliente). Esto es consistente pero puede sorprender. Es aceptable.
