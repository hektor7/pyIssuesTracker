## Why

Las tareas urgentes e inmediatas en la pantalla principal no destacan lo suficiente: el color rojo actual aplicado al texto no proporciona suficiente contraste visual, especialmente en temas oscuros donde el texto por defecto es blanco. Además, los filtros de Prioridad y Categoría carecen de búsqueda por teclado, obligando al usuario a desplazarse por listas potencialmente largas, lo que ralentiza el flujo de trabajo.

## What Changes

- **Fondo rojo intenso + texto blanco** para filas de tareas con prioridad "Inmediata" o "Urgente", sustituyendo el actual color de texto rojo por un resaltado de fondo completo en cada celda.
- **Aumento de la intensidad del rojo** usado como fondo para asegurar legibilidad del texto blanco superpuesto.
- **Combos de filtro buscables** en Prioridad y Categoría: se añade `setEditable(True)` + `QCompleter` con `MatchContains` para permitir escritura por teclado y filtrado dinámico.

## Capabilities

### New Capabilities
- `resaltado-prioridad-alta`: Las filas de tareas con prioridad Inmediata o Urgente se muestran con fondo rojo intenso y texto blanco en todas las celdas, reemplazando el actual color de texto rojo.
- `filtros-buscables`: Los combos de Prioridad y Categoría en la barra de filtros permiten búsqueda por teclado mediante `QCompleter` con coincidencia parcial (`MatchContains`).

### Modified Capabilities
<!-- Ninguna capacidad existente modifica sus requisitos a nivel de especificación -->

## Impact

- **`app/widgets/task_table.py`**: Cambio en `_priority_fg()` → nuevo método `_priority_bg()` o similar; `set_issues()` usará `setBackground` + `setForeground(Qt.white)` en lugar de solo `setForeground`.
- **`app/widgets/filter_bar.py`**: Modificar `_priority_combo` y `_category_combo` para hacerlos editables con `QCompleter`.
- Sin impacto en API, dependencias externas ni base de datos.
