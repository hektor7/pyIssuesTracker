## Context

PyIssuesTracker (PyQt6) muestra las tareas de Redmine en un `QTableWidget` (`TaskTable`, `app/widgets/task_table.py`). El cambio reciente de filtro multiproyecto y columnas configurables hizo que la tabla se recargue con mucha más frecuencia y añadió columnas opcionales (Proyecto, Prioridad, Categoría). La tabla tiene la ordenación activada (`setSortingEnabled(True)`).

Diagnóstico reproducido en headless (PyQt6 6.11):
- `set_issues` rellena las filas con `setItem(row, …)` y `setCellWidget(row, …)` usando el índice lógico. Con una columna de ordenación activa, el modelo reordena a mitad del poblado: las celdas de una tarea aterrizan en filas distintas (de ahí la fila roja "menos el final"), algunas barras de progreso quedan ausentes o cruzadas y se revela el item dummy de ordenación, que muestra el texto crudo `100`.
- `self._issues[row]` se usa en el menú contextual, el doble clic, la edición de fecha y la selección. Tras ordenar, apunta a una tarea distinta de la visible (comportamiento "aleatorio").
- Cada `set_issues` con ordenación activa vuelve a corromper el estado; por eso refrescar no lo corrige.
- La introducción de `setItem` para las columnas opcionales y el filtro multiproyecto (que llama a `set_issues` con más frecuencia) hizo alcanzable el defecto latente.

## Goals / Non-Goals

**Goals:**
1. Garantizar que cada fila visual contiene íntegramente los datos de una única issue.
2. Que toda acción sobre una fila actúe sobre la tarea mostrada, con independencia del orden.
3. Mostrar la barra de progreso correcta y nunca el texto numérico crudo.
4. Mantener el resaltado de prioridad en todas las celdas visibles de la fila.
5. Preservar la ordenación activa al refrescar y al cambiar de filtro.

**Non-Goals:**
- No se cambia la API de Redmine ni la lógica de consulta/filtrado.
- No se rediseña la UI ni se añaden columnas nuevas.
- No se persiste el criterio de ordenación entre sesiones (solo se preserva durante la sesión).
- No se migra `QTableWidget` a un modelo/vista completo (`QTableView` + `QAbstractTableModel`).

## Decisions

### D1: Repoblado aislado de la ordenación
**Decisión**: en `set_issues`, capturar la ordenación activa, llamar a `setSortingEnabled(False)`, limpiar y repoblar, y al final `setSortingEnabled(True)` + reaplicar `sortItems(section, order)`.

**Razón**: el reordenado a mitad del poblado es la causa directa de la mezcla de celdas. Desactivar la ordenación durante el poblado y reaplicarla al final garantiza filas íntegras y conserva la preferencia del usuario.

**Alternativa descartada**: ordenar los datos en Python antes de insertarlos y dejar la ordenación activada. No evita el reordenado implícito durante `setItem` ni resuelve el desacople de `self._issues[row]`.

### D2: Filas identificadas por ID (no por índice)
**Decisión**: guardar el `id` de la issue en un rol propio (`ISSUE_ID_ROLE`) en los items de cada fila, mantener un diccionario `id → issue` y resolver la tarea con helpers `_issue_at_row(row)` / `_issue_id_at_row(row)`.

**Razón**: el acoplamiento índice-de-fila ↔ índice-de-datos es la causa del comportamiento aleatorio. Resolver por ID es invariante ante cualquier reordenación.

**Alternativa descartada**: reordenar `self._issues` a la par que la vista. Es frágil y duplica la lógica de ordenación de Qt.

### D3: Barra de progreso mediante delegate
**Decisión**: `ProgressBarDelegate(QStyledItemDelegate)` registrado en `COL_PROGRESS` con `setItemDelegateForColumn`. Pinta la barra a partir del entero de `DisplayRole`, respeta `item.background()`/`item.foreground()` (prioridad) y usa color por progreso (verde 100 / naranja parcial / gris 0). Se eliminan el cell widget `QProgressBar` y el item dummy.

**Razón**: los cell widgets son el origen de las barras huérfanas y del texto crudo. Un delegate hace que el progreso sea dato puro del modelo y garantiza que siga a su fila.

**Alternativa descartada**: mantener el cell widget y recrearlo tras ordenar. Costoso y sigue siendo frágil.

### D4: Celda URL como item con icono
**Decisión**: sustituir el `QToolButton` de `COL_URL` por un item con icono y tooltip; abrir la URL en `cellClicked` cuando `col == COL_URL`.

**Razón**: elimina el último cell widget y permite que el resaltado de prioridad cubra la celda.

**Alternativa descartada**: conservar el botón y colorearlo con `setStyleSheet`. Mantiene un widget en la celda y complica el resaltado uniforme.

### D5: Resaltado a nivel de celda incluyendo Progreso
**Decisión**: aplicar fondo/foreground de prioridad a todos los items de la fila; el delegate de progreso respeta el fondo del item.

**Razón**: cumplir el requisito de fila totalmente coloreada del spec `resaltado-prioridad-alta`.

## Risks / Trade-offs

- [Riesgo] El delegate rompe la ordenación numérica de la columna Progreso → **Mitigación**: escribir el entero en `DisplayRole` y cubrirlo con un test.
- [Riesgo] `cellClicked` en `COL_URL` dispara también con doble clic → **Mitigación**: en `_on_double_click`, ignorar `COL_URL`.
- [Riesgo] Regresiones en tests existentes que asumen el cell widget de progreso o el item dummy → **Mitigación**: revisar `tests/test_task_table_tracker.py` y `tests/test_main_window.py`; los tests actuales no dependen del cell widget.
- [Riesgo] Edición inline de fecha con ordenación activa → **Mitigación**: migrar `_editing_row` a `_editing_issue_id` y localizar la fila por ID en commit/cancel.
- [Trade-off] No se persiste el criterio de ordenación entre sesiones (fuera de alcance).

## Migration Plan

1. Añadir tests de reproducción en rojo.
2. Implementar D1 + D2 (repoblado y mapeo por ID).
3. Implementar D3 (delegate) y D4 (celda URL).
4. Aplicar D5 y limpiar la gestión de widgets obsoleta en `set_issues`.
5. Ejecutar la suite completa en headless y verificación manual.

**Rollback**: revertir el cambio. No hay migración de datos ni persistencia afectada.

## Open Questions

- ¿Debe persistirse el criterio de ordenación entre reinicios? (fuera de alcance de este cambio).
- ¿El doble clic sobre la celda URL debe abrir Redmine o el diálogo de la tarea? Propuesta: ignorarlo.
