## Context

El proyecto pyIssuesTracker es una aplicación PyQt6 que gestiona tareas de Redmine. El campo `due_date` se representa como cadena `"yyyy-MM-dd"` o cadena vacía `""` cuando no hay fecha establecida.

Actualmente existen dos vías para modificar la fecha fin:
1. **Edición inline en el grid**: Doble clic en la celda → `QDateEdit` → al confirmar emite `due_date_cambiada(issue_id, due_date)`.
2. **Diálogo de edición/alta**: `QCheckBox` + `QDateEdit`. Al guardar, `main_window.py` condiciona: si checkbox desmarcado → envía `""`; si marcado → envía la fecha del `QDateEdit`.

Problemas detectados:
- No hay menú contextual para vaciar la fecha desde el grid.
- Desmarcar el checkbox en el diálogo no limpia visualmente el `QDateEdit`.
- El `QDateEdit` inline no ofrece una forma directa de forzar valor vacío.

## Goals / Non-Goals

**Goals:**
- Añadir opción "Limpiar fecha fin" en el menú contextual del grid (columna `due_date`).
- Al desmarcar el checkbox "Fecha fin" en el diálogo, vaciar el valor del `QDateEdit`.
- Al volver a marcar el checkbox, restaurar la fecha a hoy (comportamiento por defecto).
- Reutilizar infraestructura existente (`due_date_cambiada`, `RedmineClient.update_issue`) sin crear nuevas señales innecesarias.
- Mantener compatibilidad con la API de Redmine (enviar `""` para vaciar).

**Non-Goals:**
- No modificar `RedmineClient` ni la API de Redmine.
- No añadir validaciones extra ni confirmaciones de borrado.
- No modificar el comportamiento del filtro por fecha.
- No modificar la edición inline (ya envía `""` si la fecha es inválida; el problema es la falta de mecanismo para forzarlo, pero el mecanismo subyacente ya funciona).

## Decisions

### Decisión 1: Reutilizar `due_date_cambiada` para el menú contextual

**Alternativa A**: Crear una nueva señal `due_date_cleared(issue_id)`.
**Alternativa B**: Reutilizar `due_date_cambiada(issue_id, "")`.

**Decisión**: Alternativa B. La señal `due_date_cambiada` ya acepta `str` vacío, y `_on_due_date_changed` ya maneja correctamente el caso `due_date=""`. No añadir nuevas señales mantiene la interfaz simple y reduce el acoplamiento.

### Decisión 2: Limpiar `QDateEdit` al desmarcar checkbox

**Alternativa A**: Guardar la fecha actual en una variable de respaldo, limpiar el `QDateEdit` asignando `date.today()` al desmarcar, y restaurar la fecha guardada al marcar de nuevo.
**Alternativa B**: Simplemente vaciar el `QDateEdit` mostrando la fecha de hoy cuando se desmarca, y mantener `date.today()` cuando se marca.

**Decisión**: Alternativa B (simplificada). Como el `main_window.py` ya maneja la lógica `due_date if dlg.due_enabled else ""`, el valor del `QDateEdit` cuando el checkbox está desmarcado es irrelevante para la persistencia. La propiedad `due_enabled` es la que manda. No obstante, por consistencia visual, al desmarcar se reseteará el `QDateEdit` a `date.today()` para que no muestre una fecha "fantasma". Esto es más simple que la alternativa A y el comportamiento en `main_window.py` ya lo protege.

### Decisión 3: No modificar la edición inline

La edición inline ya soporta técnicamente vaciar la fecha (si `QDateEdit.date().isValid()` es `False`, se envía `""`). El problema es de usabilidad: el usuario no sabe cómo forzar ese estado desde el `QDateEdit`. Con la nueva opción del menú contextual, el usuario tendrá una forma explícita de vaciar la fecha sin depender de la edición inline. Posponemos mejoras en la edición inline para otro cambio.

## Risks / Trade-offs

- **Riesgo**: El usuario desmarca accidentalmente el checkbox en el diálogo y pierde la fecha que había seleccionado. → **Mitigación**: El valor del `QDateEdit` se resetea a `date.today()` visualmente, pero como `main_window.py` usa `due_enabled` para decidir, si el usuario vuelve a marcar el checkbox, verá `date.today()`. Si quiere restaurar la fecha anterior, tendrá que seleccionarla manualmente. Esto es aceptable porque el caso de uso principal es precisamente vaciar la fecha intencionadamente.
- **Riesgo**: El menú contextual "Limpiar fecha fin" podría ejecutarse accidentalmente. → **Mitigación**: No se añade diálogo de confirmación para mantener la fluidez (mismo patrón que el resto de opciones del menú contextual: cambio de progreso, asignación, estado, que tampoco piden confirmación).
