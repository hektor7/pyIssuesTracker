## Why

Dos carencias del cliente de escritorio PyIssuesTracker que afectan al uso diario del listado y de los diálogos de proyecto:

1. **Los proyectos homónimos anidados son indistinguibles.** Cuando dos proyectos comparten nombre (p. ej. dos subproyectos llamados "Soporte" colgando de dos proyectos padre distintos), el sistema muestra solo el nombre suelto en el filtro, en el listado, en el alta/edición y en el diálogo de envío de una tarea a otro proyecto. Es imposible saber cuál es cuál, tanto al filtrar como al elegir destino.

2. **La tabla solo ordena por una columna.** Los listados reales suelen necesitar un segundo criterio de desempate (p. ej. ordenar por Estado y, dentro de cada estado, por Prioridad). Además, la columna Prioridad se ordena alfabéticamente, de modo que "Alta" queda antes que "Inmediata", lo que no respeta la jerarquía real de prioridades de Redmine.

## What Changes

- Calcular para cada proyecto un **nombre completo con la ruta de ancestros** en formato `Proyecto Padre > Proyecto` (cadena desde la raíz, unida por ` > `).
- Usar ese nombre completo en todas las vistas donde se muestra o elige un proyecto:
  - combo de proyecto del `TaskDialog` (alta y edición),
  - combo de proyecto del `FilterBar` (sustituye la indentación con espacios actual por la ruta completa),
  - columna "Proyecto" del listado de tareas y el tooltip de la fila,
  - diálogo `ProjectSelectDialog` de "Mover a otro proyecto...",
  - lista de proyectos de notificaciones de la ventana de Ajustes.
- Añadir **ordenación por dos criterios** con prioridad entre ellos: el primer clic fija el criterio primario; al hacer clic en otra columna, esta pasa a primaria y la anterior a secundaria; el orden se aplica por primaria y, en caso de empate, por secundaria.
- Mostrar el criterio primario y el secundario con **dos triángulos** (verde y verde más claro; punta hacia arriba para ascendente, hacia abajo para descendente).
- Ordenar la columna **Prioridad** por el orden semántico de Redmine (mayor prioridad primero: Inmediata, Urgente, Alta, Normal, Baja) en lugar de alfabéticamente, tomando el catálogo de prioridades de Redmine cuando esté disponible.

## Capabilities

### New Capabilities
- `nombre-completo-proyecto`: cálculo y presentación del nombre de proyecto con su ruta de ancestros (`Padre > Hijo`) en el listado de tareas, los diálogos de alta/edición, el filtro de proyectos y el envío de una tarea a otro proyecto.

### Modified Capabilities
- `ordenacion-columnas`: la ordenación pasa de un único criterio a dos criterios con prioridad entre ellos, con indicadores visuales primario/secundario y orden semántico de la columna Prioridad.
- `paginacion-proyectos`: la jerarquía de proyectos en el combo de filtro se representa con el nombre completo `Padre > Hijo` en lugar de la indentación visual.

## Impact

- `app/services/redmine_client.py`: nuevo campo `full_name` en `RedmineProject`, poblado en `get_all_projects()`.
- `app/utils/projects.py` (nuevo): helper puro `build_project_full_names(projects) -> dict[int, str]` con la lógica de composición de la ruta de ancestros.
- `app/main_window.py`: `_cargar_proyectos()` construye `_projects` con nombres completos y un mapa `project_id -> nombre completo`; `_cargar_issues()` usa el nombre completo en `project_name` y añade `priority_id` al dict de issue; pasa las prioridades a la tabla.
- `app/widgets/task_table.py`: `MultiSortHeaderView` con pintado de dos triángulos; estado `_sort_keys`; motor de ordenación multicriterio estable; rol de rango de prioridad; `set_priorities()`.
- `app/widgets/filter_bar.py`: `populate_projects()` usa el nombre completo recibido, sin añadir indentación.
- `tests/`: nuevos tests del helper de nombres, del encabezado multicriterio y del orden de prioridad; ajustes de tests existentes de filtros si procede.
