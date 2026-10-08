## Context

Actualmente el diálogo de asignación (`AssignDialog`) tiene un `QComboBox` no editable sin búsqueda para seleccionar el usuario destino. La acción de completar es un simple `QMessageBox.question` sin posibilidad de añadir comentario. Esto contrasta con `RejectDialog`, que ya tiene campo de comentarios, y con el patrón de combos buscables ya establecido en `FilterBar` y `TaskDialog`.

El proyecto ya cuenta con:
- Patrón `QCompleter` + `MatchContains` consolidado en múltiples widgets
- `RejectDialog` como referencia de diálogo con comentarios
- API `add_issue_note()` disponible para añadir notas vía REST

## Goals / Non-Goals

**Goals:**
- Permitir búsqueda por teclado en el combo de usuarios del diálogo de asignación.
- Añadir un campo de comentarios opcional tanto al asignar como al completar.
- Reemplazar el `QMessageBox` de completar por un diálogo propio con campo de comentarios.

**Non-Goals:**
- No se modifica `RejectDialog` (ya tiene comentarios).
- No se modifica el `FilterBar` (ya tiene búsqueda en el filtro de asignado).
- No se añaden atajos de teclado ni menús contextuales nuevos.

## Decisions

### 1. Añadir comentario como nota de Redmine (no como propiedad de la issue)

**Alternativa considerada:** Guardar el comentario como un campo personalizado.
**Decisión:** Usar `notes` en la petición PUT a Redmine (`/issues/{id}.json` con `{"issue": {"notes": "..."}}`), igual que hace `reject_issue()` y `add_issue_note()`.

**Razón:** Es el mecanismo estándar de Redmine. El comentario aparece en el historial de la issue como una nota del usuario.

### 2. Modificar `assign_issue()` y `complete_issue()` para aceptar `notes`

**Alternativa considerada:** Hacer dos llamadas API separadas (asignar + añadir nota).
**Decisión:** Añadir parámetro `notes: str = ""` a ambos métodos y fusionarlo en la misma petición PUT.

**Razón:** Una sola petición atómica. Si el comentario falla, la asignación/completado también falla, evitando estados inconsistentes. Es el mismo patrón que `reject_issue()`.

### 3. Crear `CompleteDialog` como diálogo independiente

**Alternativa considerada:** Reutilizar `RejectDialog` o hacer un diálogo genérico.
**Decisión:** Crear `CompleteDialog` específico — simple, con solo un `QPlainTextEdit` y botones OK/Cancel.

**Razón:** `RejectDialog` tiene lógica adicional (selección de estado) que no aplica. Un diálogo nuevo y simple es más mantenible y claro en su propósito. Solo ~30 líneas de código.

### 4. Reutilizar patrón de combo buscable en AssignDialog

**Decisión:** Aplicar directamente `setEditable(True)` + `QCompleter` con `MatchContains` en el combo de usuarios, idéntico al patrón de `FilterBar._assigned_combo`. Además, sincronizar el modelo del completer con los nombres de los miembros al poblar el combo.

**Razón:** Consistencia con el resto del proyecto. El usuario ya está familiarizado con este comportamiento en los filtros.

### 5. Mantener el checkbox "Asignarme a mí" como atajo principal

**Decisión:** Conservar el checkbox existente con el mismo comportamiento: marcado por defecto, deshabilita el combo. El combo solo se usa cuando se desmarca el checkbox.

**Razón:** El caso más común es asignarse a uno mismo. No se debe penalizar ese flujo añadiendo pasos extra.

## Risks / Trade-offs

- **[Riesgo] Cambio en la firma de `assign_issue()` y `complete_issue()`** → El nuevo parámetro `notes` es opcional con valor por defecto `""`, así que las llamadas existentes no se rompen.
- **[Trade-off] El diálogo de completar añade un clic extra** respecto al `QMessageBox` actual → Se compensa con la utilidad de poder documentar el motivo. El usuario puede simplemente pulsar Enter si no quiere escribir comentario.
