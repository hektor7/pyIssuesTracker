## Context

PyIssuesTracker es un cliente de escritorio Redmine en PyQt6 (Python ≥3.9, httpx, odfpy, pytest) sin componente web, con toda la UI en español. Estado actual del código relevante:

- `app/widgets/multi_select_combo.py`: `MultiSelectCombo(QWidget)` con `QPushButton` + popup `QFrame` con `QListWidget`. Métodos `set_fixed_options`, `set_items`, `set_selected_ids`, `selected_ids`, `_rebuild_list`, `_update_button_text`; constantes `ALL=0`, `NONE=-1`, `ME=-2`; señal `seleccion_cambiada`. NO es buscable ni tiene tooltips.
- `app/widgets/filter_bar.py`: `populate_projects()` usa `MultiSelectCombo` y pasa el nombre completo sin indentación (~147-151); no añade tooltips.
- `app/dialogs/report_dialog.py`: grupos "Campos del informe" (17 casillas desde `REPORT_FIELDS`), "Usuarios implicados" (`MultiSelectCombo` + roles), "Fechas de creación" (`QDateEdit` + checkbox) y "Proyectos" (`MultiSelectCombo` con "Todos"). No hay filtro de estado. Propiedades `selected_user_ids`, `selected_roles`, `created_from`, `created_to`, `selected_project_ids`, `selected_fields`; `accept()` valida campos/roles/rango.
- `app/main_window.py`: `_report_users()` (523-547) deduplica sin ordenar; `_generar_informe()` (589-665) llama a `get_issues(project_id=..., status_filter="*", created_on_from/to, include_journals=True)` y filtra client-side con `matches_user_filter`; la composición de filas es `_compose_report_rows()` + `_report_field_value()` (no `_build_report_rows`). `_cargar_proyectos()` (333-347) ya construye `_projects = [(id, full_name)]`, `_project_full_names` y `_project_hierarchy`. `_cargar_estados()` rellena `self._statuses = [(id, name)]`.
- `app/services/report_generator.py`: `REPORT_FIELDS` (24-42, 17 campos), `DEFAULT_FIELD_KEYS`, `REPORT_COLUMNS`, `ReportGenerator` desacoplado de PyQt.
- `app/services/redmine_client.py`: `RedmineIssue` con `description` y `status_id`; `roles_for_user` (68-87); `participant_ids` (49-66); `RedmineJournal(id, user_id, user_name, notes, created_on)` **sin `details`**; `_parse_journals` (589-605) conserva journals con y sin notas pero **descarta `details`**; `get_issues()` (440-556) admite `project_id: int | list[int] | None` y fusiona multi-proyecto sin duplicados; `get_all_projects()` (400-422) rellena `full_name`.
- `app/dialogs/task_dialog.py` (442-456): patrón ya existente de ordenar miembros "usuario actual primero, resto por `name.lower()`", que se reutiliza.
- Tests: `tests/conftest.py` (fixture `qapp`), `tests/test_report_dialog.py`, `tests/test_report_generator.py` (fija 17 claves), `tests/test_main_window.py` (espera `status_filter="*"` y 17 columnas), `tests/test_redmine_client.py` (roles), `tests/test_mejoras_filtros.py` (`MultiSelectCombo`, nombres completos). Suite headless con `QT_QPA_PLATFORM=offscreen pytest`.

## Goals / Non-Goals

**Goals:**
- Poder leer el nombre completo de cualquier ítem de un `MultiSelectCombo` y buscar dentro de él.
- Ordenar y poder buscar los usuarios del informe.
- Incluir la descripción de la tarea en el informe como campo estándar (18 campos).
- Incluir tareas de subproyectos al seleccionar un proyecto padre, sin duplicados.
- Reconocer como "Participante" a quien tuvo la tarea asignada históricamente.
- Filtrar el informe por estado de tarea, con "Todas" por defecto.

**Non-Goals:**
- No se cambia el formato del ODS ni el motor de escritura (`ReportGenerator`).
- No se persiste ninguna selección nueva (ni estado ni tooltips).
- No se cambia el significado de la columna "Usuarios implicados": la asignación histórica se incorpora como un implicado más, sin alterar el resto de reglas (autor, asignado actual, autores de journals).
- No se añade filtro de estado al `FilterBar` de la ventana principal; solo al informe.
- No se resuelve la sincronización del cambio previo no archivado `nombre-completo-proyecto-y-doble-ordenacion`.

## Decisions

### D1: Búsqueda en `MultiSelectCombo` con campo de texto y `setHidden`
**Decisión**: añadir un `QLineEdit` (`_search_edit`) en el popup por encima de `_list`, con placeholder "Buscar...", conectado a un método `_apply_filter(texto)` que recorre los ítems y aplica `item.setHidden(...)` según si el texto aparece como subcadena (case-insensitive) en `item.text()`. Las opciones fijas (`_fixed_options`) SHALL permanecer siempre visibles. `_rebuild_list()` reaplica el filtro vigente al terminar.

**Razón**: `setHidden` no destruye ítems ni altera checkmarks; la selección vive en `_selected_ids`, así que filtrar/desfiltrar es inocuo. Evita reconstruir la lista en cada pulsación.

**Alternativa considerada**: reconstruir la lista con solo los ítems coincidentes. Descartada: perdería el estado de check de los ítems ocultos y complicaría el manejo de `Todos`.

### D2: Tooltips en `MultiSelectCombo`
**Decisión**: en `_rebuild_list()`, cada `QListWidgetItem` recibe `setToolTip(texto)`. En `_update_button_text()`, con una única selección el botón recibe `setToolTip(nombre_completo)`; con "Todos" o multiselección el tooltip se deja vacío (el botón ya muestra "Todos" o "N seleccionados"). Esto cubre el filtro de proyecto de `FilterBar` y de `ReportDialog`, la lista de usuarios, el filtro de asignados y cualquier otro uso.

**Razón**: `nombre-completo-proyecto-y-doble-ordenacion` dejó explícito como Non-Goal "no se añade tooltip diferenciado por nombre"; este cambio lo supersede, y hacerlo en el widget cubre todos los consumidores a la vez.

### D3: Orden de usuarios del informe
**Decisión**: en `_report_users()`, tras deduplicar por `user_id`, extraer el usuario `_current_user_id` (si > 0 y presente), ordenar el resto con `key=lambda x: x[1].lower()` y devolver `[actual] + resto`. Es exactamente el patrón de `TaskDialog` (442-456).

**Razón**: consistencia con el resto de diálogos y con la petición del usuario ("yo" en cabeza si ya se hacía así).

### D4: Campo estándar "Descripción"
**Decisión**: insertar `("descripcion", "Descripción")` en `REPORT_FIELDS` justo después de `("titulo", "Título")`, quedando 18 campos. `_report_field_value()` devuelve `issue.description`. Se actualizan `DEFAULT_FIELD_KEYS` y `REPORT_COLUMNS` de forma derivada (no cambian) y los tests que fijan 17.

**Razón**: mantener la descripción junto al título es el orden natural; el resto del pipeline (anchos, celdas, ODS) ya es genérico.

### D5: Parseo de `details` en `RedmineJournal`
**Decisión**: añadir `details: list[dict] = field(default_factory=list)` a `RedmineJournal` y parsear `j.get("details", [])` en `_parse_journals()`, normalizando cada entrada a un dict con al menos `property`, `old_value` y `new_value` (valores tal cual llegan, como cadenas o `None`).

**Razón**: Redmine envía los cambios de atributo en `details` (p. ej. `{"property": "assigned_to_id", "old_value": "2", "new_value": "3"}`); hoy se descartan y son la única fuente de la asignación histórica.

### D6: Rol "Participante" histórico
**Decisión**: en `roles_for_user()`, añadir "participante" si el usuario coincide con el `old_value` o el `new_value` de algún detail de asignación (`property` en `{"assigned_to_id", "assigned_to"}`), comparando como cadena con el id del usuario (ver D12). Se mantienen las reglas actuales (autor de journal con notas, asignado actual).

**Razón**: cubre literalmente "un usuario la ha tenido asignada y ha publicado comentarios y la tarea no aparecía".

**Alcance ampliado**: `participant_ids` (y por tanto la columna "Usuarios implicados") SÍ incorpora la asignación histórica: los ids de los asignados históricos (old_value/new_value de details de asignación) se añaden a la lista de implicados, parseados a int de forma segura (ignorando vacíos/no numéricos) y sin duplicados, manteniendo un orden determinista. Esto hace coherente el rol "Participante" con la columna "Usuarios implicados" del informe.

### D7: Expansión a subproyectos descendientes
**Decisión**: añadir en `app/utils/projects.py` la función pura `descendant_project_ids(project_ids, hierarchy) -> list[int]`, que devuelve cada id seleccionado más todos sus descendientes transitivos usando el mapa `project_id -> parent_id`. En `_generar_informe()`, expandir `dlg.selected_project_ids` con `self._project_hierarchy` antes de llamar a `get_issues()`; si la selección está vacía se mantiene `None` (todos).

**Razón**: es determinista, no depende de una versión concreta de Redmine ni de `subproject_id`, reutiliza la jerarquía ya cargada y el merge multi-proyecto existente de `get_issues()` ya deduplica por id.

**Alternativa considerada**: usar el parámetro `subproject_id` de la API. Descartada como mecanismo principal: su semántica varía entre versiones y no cubre descendientes de forma uniforme; el helper puro es testeable sin red.

### D8: Filtro de estado del informe
**Decisión**: `ReportDialog` recibe `statuses: list[tuple[int, str]]` y añade el grupo "Estado de la tarea" con un `MultiSelectCombo` cuya opción fija es "Todas" más un ítem por estado. Propiedad `selected_status_ids` (lista vacía si "Todas"). `_generar_informe()` traduce: vacío → `status_filter="*"` (preserva el comportamiento actual), un id → ese id, varios → la lista.

**Razón**: por defecto "Todas" no rompe informes existentes; el multiselección permite acotar a estados concretos del catálogo real de Redmine.

### D9: `get_issues()` con estado múltiple
**Decisión**: ampliar la firma a `status_filter: str | int | list[int] | None = "open"`. Un único valor se envía escalar; una lista se une con "," en `params["status_id"]`. Si la lista queda vacía se omite o se interpreta como `"*"` según lo pase el llamante (el informe pasa `"*"` explícitamente).

**Riesgo**: algunas versiones de Redmine no soportan varios valores en `status_id`; mitigación: si el servidor lo ignora, hacer una petición por estado y fusionar por id (mismo patrón que multi-proyecto), a confirmar durante la implementación.

### D10: Alcance del tooltip en el nombre de proyecto
**Decisión**: el tooltip no es código específico del filtro de proyecto: se implementa en `MultiSelectCombo` (D2). En `nombre-completo-proyecto` solo se documenta el requisito de UX y se marca el Non-Goal anterior como superseded; no se toca `FilterBar` más allá de heredar el widget.

### D11: Cierre del popup de `MultiSelectCombo` por clic fuera
**Decisión**: instalar un `eventFilter` sobre `self._popup` que, al recibir `QEvent.Type.Hide`, vacíe `_search_edit` y ponga `_popup_open = False`. Así el cierre por clic fuera (que Qt gestiona ocultando el popup) deja el control reabrible con un solo clic y cumple "el campo se vacía al cerrar el popup". Se mantiene el comportamiento actual de `_toggle_popup()` y `hideEvent()`.

**Razón**: sin esto, al cerrar el popup con un clic fuera, `_popup_open` quedaba en `True` y el siguiente clic en el botón cerraba (en vez de abrir) el popup: el bug de "dos clics". Además el campo de búsqueda conservaba el texto filtrado.

### D12: Comparación de ids de asignación histórica con `str(...)` en ambos lados
**Decisión**: en `roles_for_user()` y en el parseo de asignación histórica, la comparación de ids se hace con `str(...)` en ambos lados: `str(user_id)` frente a `str(d.get("old_value"))` / `str(d.get("new_value"))`. Se comprueba explícitamente que el valor no sea `None` antes de comparar (un `str(None) == "None"` no casa con un id numérico, pero se evita por claridad).

**Razón**: Redmine puede devolver `old_value`/`new_value` como cadena (`"2"`) o como entero (`2`) según la versión; comparar ambos lados como cadena es robusto ante ambos tipos.

## Risks / Trade-offs

- **[Riesgo]** El filtrado con `setHidden` puede ocultar "Todos" y dejar al usuario sin forma de restablecer. → **Mitigación**: las opciones fijas nunca se ocultan y el campo se limpia al abrir/cerrar el popup.
- **[Riesgo]** `item.setHidden` en un `QListWidget` con `itemChanged` podría disparar recálculos. → **Mitigación**: ocultar no cambia `checkState`; `_on_item_changed` no se dispara por visibilidad.
- **[Riesgo]** El orden "yo primero" depende de que `_current_user_id` esté cargado; con 0 el comportamiento es alfabético puro. → **Mitigación**: test explícito para `_current_user_id == 0`.
- **[Riesgo]** La expansión de subproyectos multiplica peticiones (una por proyecto en el merge multi-proyecto) si un padre tiene muchos descendientes. → **Mitigación**: la deduplicación ya existe; vigilar el volumen en instancias con árboles muy anchos.
- **[Riesgo]** `details` de Redmine puede usar `assigned_to` (clave antigua) o valores `None`. → **Mitigación**: aceptar ambas propiedades y comparar como cadena en ambos lados (D12), comprobando explícitamente que el valor no sea `None`.
- **[Riesgo]** Cambiar la firma de `status_filter` puede romper llamadas existentes. → **Mitigación**: mantener el default `"open"` y aceptar `str`/`int` como hoy.
- **[Riesgo]** El cierre del popup por clic fuera puede no pasar por `_toggle_popup()`. → **Mitigación**: event filter sobre `QEvent.Type.Hide` del popup (D11) que limpia la búsqueda y resetea `_popup_open` en cualquier vía de cierre.

## Migration Plan

1. Tests TDD en rojo: `MultiSelectCombo` (búsqueda/tooltips), orden de `_report_users`, campo Descripción (17→18), `details`/participante histórico, helper de descendientes, filtro de estado.
2. Implementar D5–D6 (`RedmineJournal.details`, `roles_for_user`).
3. Implementar D7 (`descendant_project_ids` + expansión en `_generar_informe`).
4. Implementar D4 (`REPORT_FIELDS` + `_report_field_value`).
5. Implementar D1–D2 (widget) y D3 (orden de usuarios).
6. Implementar D8–D9 (diálogo de estado + `get_issues`).
7. Ejecutar `QT_QPA_PLATFORM=offscreen pytest` y comprobación manual.
8. Correcciones de la verificación: D11 (event filter del popup), D12 (comparación `str` en ambos lados), `participant_ids` con asignados históricos y fallback de `_update_button_text()`.

**Rollback**: revertir el cambio; no hay migración de datos ni persistencia nueva.

## Open Questions

- ¿Debe la expansión a subproyectos aplicarse también al listado principal (`FilterBar`), no solo al informe? El pedido se limita al informe.
- La spec base `openspec/specs/nombre-completo-proyecto/spec.md` conserva aún el encabezado `## ADDED Requirements` por el cambio previo no archivado; al archivar `mejoras-generacion-informes` deberá sincronizarse correctamente.