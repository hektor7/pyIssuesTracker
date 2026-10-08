## Context

PyIssuesTracker es un cliente de escritorio Redmine en PyQt6 (Python ≥3.9, httpx, pytest) sin componente web. Estado actual del código relevante:

- `RedmineProject` (`app/services/redmine_client.py`) tiene `id`, `name`, `identifier`, `parent_id`, `children`. `get_projects()` parsea `parent.id`; `get_all_projects()` pagina y devuelve una lista plana ordenada por `name.lower()`.
- `MainWindow` (`app/main_window.py`): `_cargar_proyectos()` guarda `self._projects = [(p.id, p.name)]` y `self._project_hierarchy = {p.id: p.parent_id}`. `self._projects` se pasa a `TaskDialog`, `ProjectSelectDialog`, `SettingsDialog` y `FilterBar.populate_projects(...)`.
- `FilterBar.populate_projects()` (`app/widgets/filter_bar.py`) construye la indentación recorriendo `hierarchy` y prefijando `"  "` por nivel de profundidad.
- `MainWindow._cargar_issues()` construye `issues_dict` con `project_name = iss.project_name` (nombre hoja) y `priority_name`, pero **no** incluye `priority_id`.
- `TaskTable` (`app/widgets/task_table.py`): 14 columnas; `setSortingEnabled(True)`; `DateSortItem` guarda el ISO en un rol propio para ordenar fechas; `ProgressBarDelegate` pinta la barra de progreso; `_apply_issue_style()` guarda `ISSUE_ID_ROLE` y aplica el resaltado de prioridad. `set_issues()` lee `header.sortIndicatorSection()/Order()`, desactiva la ordenación durante el poblado y al final la reactiva reaplicando `sortItems(section, order)`.
- Tests existentes (`tests/test_task_table_render.py`) llaman a `table.sortItems(col, order)` y comprueban `header.sortIndicatorSection()`.
- `QHeaderView` solo soporta **un** indicador de ordenación integrado.
- La API de Redmine ya devuelve la jerarquía (`parent.id`) en `/projects.json`, por lo que no se necesitan llamadas nuevas.

## Goals / Non-Goals

**Goals:**
- Mostrar en todas las vistas el nombre completo `Raíz > ... > Proyecto`.
- Ordenación estable por dos criterios con indicadores verde (primario) y verde claro (secundario).
- Ordenar la columna Prioridad por el orden semántico de Redmine.
- Mantener compatibilidad con la API que usan los tests actuales (`sortItems`, `sortIndicatorSection`).

**Non-Goals:**
- No se persiste la ordenación ni sus criterios entre sesiones (hoy no se persiste).
- No se muestra el `identifier` ni se añade tooltip diferenciado por nombre.
- No se añaden llamadas nuevas a la API (la jerarquía ya viene en `/projects.json`).
- No se admiten más de dos criterios simultáneos.
- No se modifica el resaltado de prioridad existente ni el formato del nombre (solo el texto mostrado del proyecto).

## Decisions

### D1: Nombre completo en el modelo de proyecto
**Decisión**: añadir el campo `full_name: str = ""` a `RedmineProject` y poblarlo en `get_all_projects()`, que ya dispone de la lista completa. El cálculo se extrae a una función pura `build_project_full_names(projects) -> dict[int, str]` en `app/utils/projects.py`: para cada proyecto sube por `parent_id` hasta la raíz y une los nombres con ` > `; si un `parent_id` no está en la lista, se detiene y usa los ancestros conocidos; si no tiene padre, el nombre es el propio. `get_all_projects()` pasa a ordenar por `full_name.lower()`.

**Alternativa considerada**: calcular el nombre solo en la UI. Descartada: duplicaría la lógica en `MainWindow`, `FilterBar`, `TaskDialog` y `ProjectSelectDialog`.

### D2: Fuente única para todas las vistas
**Decisión**: `MainWindow._cargar_proyectos()` construye `self._projects = [(p.id, p.full_name or p.name)]` y mantiene el mapa `self._project_full_names = {p.id: p.full_name or p.name}`. Como `_projects` ya alimenta a `TaskDialog`, `ProjectSelectDialog`, `SettingsDialog` y `FilterBar`, todos ellos pasan a mostrar el nombre completo sin cambios adicionales.

**Razón**: el nombre completo se resuelve una sola vez y todas las vistas quedan consistentes.

### D3: Nombre completo en la columna "Proyecto" del listado
**Decisión**: en `_cargar_issues()`, componer `"project_name": self._project_full_names.get(iss.project_id, iss.project_name)` y añadir `"priority_id": iss.priority_id`. La columna "Proyecto" y el tooltip de `TaskTable` ya usan `project_name`, por lo que muestran el nombre completo sin cambios en la tabla.

**Alternativa considerada**: cambiar `RedmineIssue.project_name` en el cliente. Descartada: el cliente parsea issues sin conocer la jerarquía completa.

### D4: Encabezado con dos indicadores de ordenación
**Decisión**: crear `MultiSortHeaderView(QHeaderView)` y sustituir el encabezado horizontal de `TaskTable` (`self.setHorizontalHeader(MultiSortHeaderView(Qt.Orientation.Horizontal, self))`). El encabezado guarda `sort_keys: list[tuple[int, Qt.SortOrder]]` (máximo dos, primario primero) y sobrescribe `paintSection()` para dibujar el texto y, tras él, hasta dos triángulos: primario en verde `#2e7d32` y secundario en verde claro `#81c784`; punta hacia arriba en ascendente y hacia abajo en descendente. Se llama a `setSortIndicatorShown(False)` para suprimir la flecha integrada de Qt. Tras sustituir el encabezado hay que reaplicar `setSectionResizeMode` de las 14 columnas, el ancho fijo de `COL_URL` y el menú contextual de cabeceras.

**Alternativa considerada**: pintar los triángulos desde un delegate. Descartada: el delegate pinta celdas, no cabeceras; el sitio natural es `QHeaderView.paintSection`.

### D5: Reglas de interacción del clic en cabecera
**Decisión**: `TaskTable` conecta `header.sectionClicked` a `_on_header_clicked(col)`:
- Si `col` es el criterio **primario**: se invierte su dirección y se conserva el secundario.
- Si `col` es el criterio **secundario**: pasa a primario y el primario anterior pasa a secundario, conservando cada uno su dirección.
- En cualquier otro caso: `col` pasa a primario con dirección ascendente; el primario anterior pasa a secundario; el secundario anterior se descarta.

**Razón**: cumple literalmente "clic en una columna nueva → esa manda; clic en otra → la anterior pasa a segunda".

### D6: Motor de ordenación estable multicriterio
**Decisión**: `TaskTable._apply_sort()` ordena los índices de fila de menos significativo a más significativo (ordenación estable encadenada, cada criterio con su propia dirección) y repuebla las filas con `_populate_row` en el orden resultante; `_issues` y `_issues_by_id` conservan el orden de inserción. La clave por columna es tipada:
- `COL_ID` y `COL_PROGRESS`: entero de `DisplayRole`.
- `COL_PRIORITY`: rango entero guardado en un rol nuevo (`PRIORITY_RANK_ROLE`).
- `COL_START_DATE`, `COL_DUE_DATE`, `COL_CREATED`, `COL_UPDATED`: ISO de `DateSortItem.ISO_ROLE` (cadena vacía primero).
- Resto: `text().casefold()`.

Para conservar la compatibilidad con los tests existentes, `TaskTable` sobrescribe `sortItems(column, order)` delegando en este motor con un único criterio y actualizando `setSortIndicator`. `set_issues()` preserva `self._sort_keys` (leído antes de repoblar) y llama a `_apply_sort()` al final, en lugar de reaplicar `sortItems`.

**Alternativa considerada**: mantener la ordenación integrada de Qt y desempatar con un segundo pase. Descartada: Qt no conserva el orden previo de forma garantizada y solo admite un criterio.

### D7: Orden semántico de la columna Prioridad
**Decisión**: `TaskTable.set_priorities(priorities)` recibe el catálogo ordenado de Redmine (`[(id, name)]`). El rango se calcula como `len(priorities) - 1 - index(id)`, de modo que la última prioridad del catálogo (la de mayor posición en Redmine) recibe el rango 0. Si un proyecto no tiene catálogo o falta un id, se aplica un fallback por nombre: `inmediata/immediate=0`, `urgente/urgent=1`, `alta/high=2`, `normal=3`, `baja/low=4`, resto = valor alto. Así, el primer clic (ascendente) muestra Inmediata → Baja y el segundo clic lo invierte.

**Alternativa considerada**: usar una lista fija por nombre. Descartada: el usuario pidió usar la parametrización de Redmine cuando exista.

**Call site**: el catálogo se inyecta con `TaskTable.set_priorities()` desde `MainWindow._cargar_priorities()`, justo después de obtener `self._priorities`, para garantizar determinismo (evita que la tabla use el fallback por nombre durante la ventana en que `_update_task_table_context()` aún ve la lista vacía).

### D8: Jerarquía del filtro por ruta, no por indentación
**Decisión**: `FilterBar.populate_projects(projects, hierarchy=None)` mantiene su firma pero deja de añadir indentación: usa directamente el nombre recibido (que ya es el nombre completo). Esto obliga a MODIFICAR el requisito de `paginacion-proyectos` que exigía indentación visual.

## Risks / Trade-offs

- **[Riesgo]** Sustituir el `QHeaderView` rompe el resize de columnas, el ancho fijo de `COL_URL` y el menú contextual de cabeceras. → **Mitigación**: crear el encabezado al inicio de `__init__` y reaplicar después todas las configuraciones de header existentes; test que verifica visibilidad/orden de columnas.
- **[Riesgo]** La repoblación en `_apply_sort()` podría mezclar celdas o dejar `QDateEdit` inline huérfanos. → **Mitigación**: limpiar los cell widgets (como hace `set_issues`) antes de repoblar y reutilizar `_populate_row`.
- **[Riesgo]** `setSortingEnabled(False)` permanente cambia el comportamiento previo; algún test o código podría depender de la ordenación integrada. → **Mitigación**: sobrescribir `sortItems()` y mantener `sortIndicatorSection()/Order()` sincronizados para no romper los tests existentes.
- **[Riesgo]** El supuesto "la última prioridad del catálogo es la de mayor rango" puede no cumplirse en instancias con configuración atípica. → **Mitigación**: fallback por nombre para los valores conocidos.
- **[Trade-off]** No se persisten los criterios de ordenación; al reiniciar se pierden (igual que hoy).

## Migration Plan

1. Tests TDD en rojo (helper de nombres, `full_name` en `get_all_projects`, ordenación multicriterio y orden de prioridad).
2. Implementar D1 (`build_project_full_names` + `RedmineProject.full_name`).
3. Implementar D2/D3 en `MainWindow`.
4. Implementar D8 en `FilterBar`.
5. Implementar D4–D7 en `TaskTable`.
6. Ejecutar la suite completa en headless (`QT_QPA_PLATFORM=offscreen pytest`).

**Rollback**: revertir el cambio. No hay migración de datos ni persistencia afectada.

## Open Questions

- ¿Debe persistirse la ordenación entre sesiones? Fuera de alcance de este cambio.