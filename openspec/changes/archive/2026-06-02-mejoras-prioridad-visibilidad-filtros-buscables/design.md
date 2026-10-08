## Context

Actualmente el `TaskTable` aplica color rojo al texto (`setForeground`) de las celdas para tareas urgentes/inmediatas. Esto no es suficientemente visible, especialmente con temas oscuros. La barra de filtros (`FilterBar`) tiene combos sin búsqueda para Prioridad y Categoría, obligando al usuario a navegar listas manualmente.

El proyecto ya tiene un patrón establecido de combos buscables en `TaskDialog._make_searchable_combo()` y en los combos de Proyecto y Asignado del propio `FilterBar`.

## Goals / Non-Goals

**Goals:**
- Hacer que las tareas urgentes/inmediatas sean inmediatamente reconocibles en la tabla mediante fondo rojo intenso con texto blanco.
- Permitir búsqueda por teclado en los combos de Prioridad y Categoría del `FilterBar`.

**Non-Goals:**
- No se modifica el combo de Estado (solo 3 opciones fijas, no necesita búsqueda).
- No se modifican otros widgets fuera de `TaskTable` y `FilterBar`.
- No se añaden nuevas dependencias.

## Decisions

### 1. Fondo rojo + texto blanco en lugar de solo texto rojo

**Alternativa considerada:** Mantener `setForeground` con colores más intensos.
**Decisión:** Usar `setBackground` con rojo intenso y `setForeground(Qt.GlobalColor.white)`.

**Razón:** El contraste fondo/texto es mucho más perceptible que solo color de texto. El usuario menciona explícitamente "texto blanco superpuesto". Esto además funciona bien tanto en temas claros como oscuros.

### 2. Colores de fondo elegidos

| Prioridad | Fondo actual (fg) | Fondo nuevo (bg) | Texto |
|-----------|-------------------|-------------------|-------|
| Inmediata | `RGB(200,0,0)` texto | `RGB(200,0,0)` fondo | Blanco |
| Urgente   | `RGB(139,0,0)` texto | `RGB(180,20,20)` fondo | Blanco |

**Razón:**  
- Para "Inmediata" se mantiene el rojo intenso `RGB(200,0,0)` como fondo, ya que sobre él el blanco es perfectamente legible.
- Para "Urgente" se sube ligeramente de `RGB(139,0,0)` a `RGB(180,20,20)` para asegurar que el blanco destaque sin perder la diferenciación entre ambos niveles.
- Se añade también `QColor(220,40,40)` como alternativa más viva si se prefiere.

### 3. Reutilizar el patrón `_make_searchable_combo` en FilterBar

**Alternativa considerada:** Crear una función helper separada.
**Decisión:** Aplicar directamente `setEditable(True)` + `QCompleter` con `MatchContains` en los combos de Prioridad y Categoría, replicando el patrón ya existente en los combos de Proyecto y Asignado del mismo `FilterBar`.

**Razón:** Consistencia con el código existente. No requiere refactorización ni nuevo módulo compartido. La función `_make_searchable_combo` de `TaskDialog` es específica de ese diálogo y no conviene acoplarla.

### 4. No usar fila completa, sino celda a celda

**Decisión:** Aplicar fondo y texto blanco celda por celda en `set_issues()`, igual que ahora se aplica `setForeground`.

**Razón:** `QTableWidget` no soporta estilos de fila nativos. Intentar usar `setRowStyle` o delegados sería más complejo sin beneficio real. Mantener el enfoque actual minimiza el riesgo de regresión.

## Risks / Trade-offs

- **[Riesgo] El rojo de fondo puede ser demasiado agresivo visualmente** → Mitigación: solo se aplica a prioridades "Inmediata" y "Urgente", que por definición deben llamar la atención. El usuario lo pide explícitamente.
- **[Riesgo] Compatibilidad con temas del sistema** → Mitigación: el blanco sobre rojo funciona en cualquier tema. El resto de filas mantienen los colores por defecto del tema.
- **[Trade-off] Los combos buscables pierden el comportamiento nativo de "type-ahead"** → Mitigación: el `MatchContains` es más potente que el type-ahead nativo (busca en cualquier parte del texto, no solo prefijo). Es el mismo comportamiento que ya tienen Proyecto y Asignado.
