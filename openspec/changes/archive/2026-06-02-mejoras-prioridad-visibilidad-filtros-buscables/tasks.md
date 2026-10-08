## 1. Resaltado de prioridades en TaskTable

- [x] 1.1 Cambiar `_priority_fg()` a `_priority_bg()` en `app/widgets/task_table.py`: devolver `QColor` de fondo (rojo intenso) o `None` según prioridad. Para "Inmediata" → `RGB(200,0,0)`, para "Urgente" → `RGB(180,20,20)`, resto → `None`.
- [x] 1.2 Modificar `set_issues()` en `TaskTable`: para cada celda donde `_priority_bg()` devuelva un color, aplicar `setBackground(bg_color)` y `setForeground(Qt.GlobalColor.white)`. Mantener el comportamiento existente para el resto de filas.
- [x] 1.3 Verificar visualmente que las filas urgentes/inmediatas se muestran con fondo rojo y texto blanco, y que las filas normales no se ven afectadas.

## 2. Filtros buscables en FilterBar

- [x] 2.1 Hacer editable el combo de Prioridad en `app/widgets/filter_bar.py`: añadir `setEditable(True)`, `setInsertPolicy(NoInsert)` y `QCompleter` con `MatchContains` (mismo patrón que `_project_combo`).
- [x] 2.2 Hacer editable el combo de Categoría en `app/widgets/filter_bar.py`: añadir `setEditable(True)`, `setInsertPolicy(NoInsert)` y `QCompleter` con `MatchContains`.
- [x] 2.3 Verificar que escribir en los combos de Prioridad y Categoría filtra correctamente las opciones del dropdown.

## 3. Verificación final

- [x] 3.1 Ejecutar la aplicación y confirmar: (a) filas urgentes/inmediatas con fondo rojo y texto blanco legible, (b) combos de Prioridad y Categoría permiten escribir para buscar, (c) el resto de funcionalidad no se ve afectada.
