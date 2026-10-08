## 1. Tests (TDD): nombre completo de proyecto

- [x] 1.1 Crear `tests/test_project_full_names.py` con tests del helper `build_project_full_names`: proyecto raíz (sin padre) → su nombre; un nivel → `Padre > Hijo`; dos niveles → `Raíz > Intermedio > Hijo`; homónimos bajo padres distintos → rutas distintas; `parent_id` ausente de la lista → se usa el propio nombre sin fallar.
- [x] 1.2 Test: `get_all_projects()` asigna `full_name` a cada `RedmineProject` y ordena el resultado por `full_name.lower()`.
- [x] 1.3 Test en `tests/test_main_window.py`: `_cargar_proyectos()` deja `_projects` con el nombre completo y rellena el mapa `project_id -> nombre completo`.
- [x] 1.4 Test: `_cargar_issues()` escribe `project_name` con el nombre completo del proyecto de cada issue y añade `priority_id` al dict.
- [x] 1.5 Test en `tests/test_mejoras_filtros.py`: `FilterBar.populate_projects([(1, "Padre > Hijo")])` usa el nombre tal cual, sin indentación añadida.

## 2. RedmineClient y helper de nombres

- [x] 2.1 Crear `app/utils/projects.py` con la función pura `build_project_full_names(projects) -> dict[int, str]` (composición de la ruta de ancestros unida por ` > `, con corte si un ancestro no está en la lista).
- [x] 2.2 Añadir el campo `full_name: str = ""` a `RedmineProject` en `app/services/redmine_client.py`.
- [x] 2.3 Poblar `full_name` en `get_all_projects()` usando el helper y ordenar la lista resultante por `full_name.lower()`.

## 3. MainWindow

- [x] 3.1 En `_cargar_proyectos()`: construir `self._projects = [(p.id, p.full_name or p.name)]` y `self._project_full_names = {p.id: p.full_name or p.name}`; mantener `self._project_hierarchy`.
- [x] 3.2 En `_cargar_issues()`: usar `self._project_full_names.get(iss.project_id, iss.project_name)` como `project_name` y añadir `"priority_id": iss.priority_id` al dict de issue.
- [x] 3.3 Pasar el catálogo de prioridades a la tabla con `self._task_table.set_priorities(self._priorities)` **desde `_cargar_priorities()`**, justo después de cargar el catálogo, para que la tabla reciba el orden real de Redmine en cuanto esté disponible (y no un fallback vacío en la primera llamada a `_update_task_table_context()`).

## 4. FilterBar

- [x] 4.1 En `populate_projects()`, eliminar el cálculo de indentación y usar directamente el nombre recibido (mantener la firma con `hierarchy=None` por compatibilidad).

## 5. TaskTable: encabezado y ordenación múltiple

- [x] 5.1 Crear `MultiSortHeaderView(QHeaderView)` en `app/widgets/task_table.py` con `sort_keys: list[tuple[int, Qt.SortOrder]]` y `paintSection()` sobrescrito para dibujar hasta dos triángulos (verde `#2e7d32` primario, verde claro `#81c784` secundario; punta arriba en ascendente, abajo en descendente).
- [x] 5.2 En `TaskTable.__init__`, sustituir el encabezado horizontal por `MultiSortHeaderView`, llamar a `setSortIndicatorShown(False)`, `setSortingEnabled(False)` y conectar `header.sectionClicked` a `_on_header_clicked`; reaplicar después el resize de las 14 columnas, el ancho fijo de `COL_URL` y el menú contextual de cabeceras.
- [x] 5.3 Implementar `_on_header_clicked(col)` con las reglas de interacción (primario invierte dirección; secundario se promueve y desplaza al primario; columna nueva pasa a primario ascendente y desplaza al primario anterior a secundario, descartando el secundario anterior).
- [x] 5.4 Implementar `_apply_sort()`: ordenación estable encadenada de menos a más significativa con clave tipada por columna y repoblado de filas con `_populate_row`; limpiar cell widgets residuales antes de repoblar.
- [x] 5.5 Sobrescribir `sortItems(column, order)` para fijar un único criterio, actualizar `setSortIndicator` y llamar a `_apply_sort()` (compatibilidad con tests existentes).
- [x] 5.6 Modificar `set_issues()` para preservar `self._sort_keys` y reaplicar con `_apply_sort()` en lugar de `sortItems`.

## 6. TaskTable: orden semántico de prioridad

- [x] 6.1 Añadir `set_priorities(priorities: list[tuple[int, str]])` a `TaskTable` y almacenar el catálogo.
- [x] 6.2 Definir el rol `PRIORITY_RANK_ROLE` y calcular el rango de cada prioridad (`len(catálogo) - 1 - index`) con fallback por nombre (`inmediata/immediate=0`, `urgente/urgent=1`, `alta/high=2`, `normal=3`, `baja/low=4`).
- [x] 6.3 En `_populate_row()`, guardar el rango en `PRIORITY_RANK_ROLE` del item de la columna Prioridad y usar ese rol en `_apply_sort()`.

## 7. Verificación

- [x] 7.1 Crear `tests/test_task_table_multi_sort.py` con tests de: ordenación por dos criterios (secundario desempata dentro del primario), reglas de interacción del clic, estabilidad, indicadores (estado interno `sort_keys` del encabezado) y preservación de los dos criterios tras `set_issues`.
- [x] 7.2 Crear tests del orden de prioridad: primer clic mayor→menor (Inmediata, Urgente, Alta, Normal, Baja), segundo clic invertido, no alfabético y uso del catálogo de Redmine.
- [x] 7.3 Ejecutar `QT_QPA_PLATFORM=offscreen pytest` y confirmar que no hay regresiones en la suite existente (incluidos `test_task_table_render.py`, `test_task_table_tracker.py`, `test_mejoras_filtros.py`).
- [x] 7.4 Verificación manual: con dos subproyectos "Soporte" homónimos, comprobar que se distinguen en el filtro, el listado, el alta/edición y el diálogo de envío a otro proyecto; ordenar por Estado (primario) y Prioridad (secundario) y comprobar los dos triángulos.