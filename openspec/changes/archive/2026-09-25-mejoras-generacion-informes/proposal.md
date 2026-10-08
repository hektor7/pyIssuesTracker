## Why

Cinco carencias detectadas en la generación de informes y en los filtros de PyIssuesTracker:

1. **Los nombres de proyecto largos son ilegibles en los filtros.** El filtro ya compone `Proyecto padre > Proyecto hijo` (`build_project_full_names`), pero cuando el nombre es largo no cabe en el botón del `MultiSelectCombo` y no existe forma de leerlo completo. No hay tooltips ni en el botón (selección única) ni en los ítems de la lista.

2. **La lista de usuarios del informe no está ordenada ni es buscable.** `MainWindow._report_users()` deduplica miembros pero no ordena, y el `MultiSelectCombo` de "Usuarios implicados" obliga a recorrer la lista entera a ojo.

3. **La descripción de la tarea no puede incluirse en el informe.** El catálogo `REPORT_FIELDS` tiene 17 campos estándar y `RedmineIssue.description` ya existe, pero no se ofrece como columna.

4. **Faltan tareas al filtrar por un proyecto padre y la participación está incompleta.** `get_issues()` filtra por `project_id` exacto y no incluye descendientes, de modo que una tarea de un subproyecto no aparece al seleccionar el padre. Además, el rol "Participante" solo mira al asignado **actual** y a los autores de journals con notas: quien tuvo la tarea asignada en el pasado (y comentó) no aparece.

5. **El informe no permite filtrar por estado de tarea.** `_generar_informe()` fuerza `status_filter="*"`, así que no se pueden generar informes acotados a estados concretos.

## What Changes

- **Tooltips en `MultiSelectCombo`**: cada ítem de la lista desplegable expone un tooltip con su texto completo, y el botón expone un tooltip con el nombre completo cuando la selección es única. Afecta al filtro de proyecto (`FilterBar`), al combo de proyectos del informe (`ReportDialog`), a la lista de usuarios y al filtro de asignados.
- **Búsqueda por texto en `MultiSelectCombo`**: campo de filtro en el popup que reduce los ítems por subcadena, sin distinguir mayúsculas/minúsculas, preservando la selección y manteniendo visibles las opciones fijas (`Todos`, `Sin asignar`, `Asignado a mí`).
- **Usuarios del informe ordenados**: `_report_users()` devuelve el usuario autenticado ("yo") primero, si procede, y el resto alfabéticamente por nombre (case-insensitive), reutilizando el patrón ya usado en `TaskDialog`.
- **Nuevo campo estándar "Descripción"**: se añade la clave `descripcion` al catálogo `REPORT_FIELDS` (pasa de 17 a 18), se genera su columna en el ODS y se actualizan los tests que fijan las 17 claves.
- **Subproyectos en el informe**: al seleccionar un proyecto se incluyen también las tareas de todos sus descendientes (hijos, nietos…), sin duplicar tareas, expandiendo la jerarquía ya cargada (`_project_hierarchy`) antes de llamar a `get_issues()`.
- **Rol "Participante" histórico**: se parsean los `details` de los journals y se considera participante a quien haya tenido la tarea asignada en algún cambio de `assigned_to_id`, además del asignado actual y de los autores de notas.
- **Filtro de estado de tarea en el informe**: nuevo grupo "Estado de la tarea" con `MultiSelectCombo` sobre el catálogo de estados de Redmine. Por defecto "Todas", para no romper el comportamiento actual. La selección se traslada a `get_issues()`.

## Capabilities

### New Capabilities
- Ninguna.

### Modified Capabilities
- `generacion-informes-ods`: el diálogo gana el grupo de estado; el catálogo pasa a 18 campos con "Descripción"; el filtrado por proyectos incluye subproyectos; se ordenan los usuarios y se documenta la integración con `get_issues` (proyectos y estados múltiples).
- `participacion-usuarios-tareas`: se parsean los `details` de los journals y el rol "Participante" incorpora la asignación histórica.
- `nombre-completo-proyecto`: el filtro de proyectos muestra tooltip con el nombre completo cuando no cabe (supersede el Non-Goal "no se añade tooltip diferenciado por nombre" del cambio `nombre-completo-proyecto-y-doble-ordenacion`).
- `filtros-buscables`: el `MultiSelectCombo` incorpora búsqueda por texto y tooltips, reutilizables por todos los filtros multiselección.

## Impact

- `app/widgets/multi_select_combo.py`: campo de búsqueda en el popup, filtrado por `setHidden`, tooltips por ítem y en el botón; preservación de la selección al filtrar.
- `app/dialogs/report_dialog.py`: nuevo grupo "Estado de la tarea" con `MultiSelectCombo`; parámetro `statuses`; propiedad `selected_status_ids`; los combos de proyectos y usuarios heredan búsqueda y tooltips.
- `app/widgets/filter_bar.py`: sin cambios de lógica; hereda tooltips/búsqueda del widget para el filtro de proyecto.
- `app/main_window.py`: `_report_users()` ordena (yo primero + alfabético); `_generar_informe()` expande proyectos a descendientes y traduce el estado seleccionado a `status_filter`; `_report_field_value()` devuelve `issue.description` para la clave `descripcion`; `_compose_report_rows()`/`_generar_informe()` generan la nueva columna (nota: la tarea mencionaba `_build_report_rows`, el nombre real es `_compose_report_rows`).
- `app/services/report_generator.py`: `REPORT_FIELDS` pasa a 18 con `("descripcion", "Descripción")` tras `titulo`.
- `app/services/redmine_client.py`: `RedmineJournal.details`; `_parse_journals()` parsea `details`; `roles_for_user()` reconoce la asignación histórica; `get_issues()` acepta `status_filter` como lista de ids.
- `app/utils/projects.py`: helper puro `descendant_project_ids(project_ids, hierarchy)`.
- `tests/`: `test_report_generator.py` y `test_report_dialog.py` (17→18), nuevos tests de `MultiSelectCombo`, roles históricos, expansión de subproyectos, orden de usuarios y filtro de estado; ajustes en `test_main_window.py` y `test_redmine_client.py`.