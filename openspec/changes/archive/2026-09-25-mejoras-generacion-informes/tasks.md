## 1. Tests (TDD): búsqueda y tooltips en MultiSelectCombo

- [x] 1.1 Ampliar `tests/test_mejoras_filtros.py` con tests de que el popup incluye un campo de búsqueda (`_search_edit`) y de que al escribir reduce los ítems visibles por subcadena sin distinguir mayúsculas.
- [x] 1.2 Test: el filtrado preserva el estado de marcado de los ítems que quedan ocultos (`_selected_ids` intacto).
- [x] 1.3 Test: vaciar el campo de búsqueda restaura todos los ítems conservando la selección.
- [x] 1.4 Test: las opciones fijas ("Todos", "Sin asignar", "Asignado a mí") permanecen visibles con el filtro activo.
- [x] 1.5 Test: cada `QListWidgetItem` recibe un tooltip con su texto (`item.toolTip()`), tanto fijo como dinámico.
- [x] 1.6 Test: con selección única, el texto del botón y su tooltip coinciden con el nombre completo; con "Todos" o multiselección el tooltip no muestra un nombre de ítem.
- [x] 1.7 Test de integración: `FilterBar.populate_projects([(1, "Padre > Hijo muy largo")])` expone el nombre completo en el tooltip del ítem.

## 2. MultiSelectCombo: búsqueda y tooltips

- [x] 2.1 Añadir un `QLineEdit` (`_search_edit`) al popup por encima de `_list`, con placeholder "Buscar..." y `textChanged` conectado a `_apply_filter`.
- [x] 2.2 Implementar `_apply_filter(texto)`: ocultar (`setHidden`) los ítems cuyo texto no contenga la subcadena, ignorando mayúsculas/minúsculas; no ocultar nunca las opciones fijas.
- [x] 2.3 Reaplicar el filtro vigente al final de `_rebuild_list()` para no perderlo al cambiar ítems.
- [x] 2.4 Asignar `item.setToolTip(texto)` en `_rebuild_list()` para ítems fijos y dinámicos.
- [x] 2.5 Asignar `self._button.setToolTip(nombre)` en `_update_button_text()` cuando hay una única selección; limpiar el tooltip en "Todos" y en multiselección.
- [x] 2.6 Vaciar el campo de búsqueda en `_toggle_popup()` y en `hideEvent()`.

## 3. Tests (TDD): orden de usuarios del informe

- [x] 3.1 Test en `tests/test_main_window.py`: `_report_users()` devuelve los usuarios ordenados alfabéticamente por nombre sin distinguir mayúsculas.
- [x] 3.2 Test: si `_current_user_id` está entre los miembros, aparece primero y el resto queda alfabético.
- [x] 3.3 Test: si `_current_user_id` es 0 o no está entre los miembros, el orden es puramente alfabético.
- [x] 3.4 Test: se mantiene la deduplicación por `user_id`.

## 4. MainWindow: orden de usuarios

- [x] 4.1 En `_report_users()`, tras deduplicar, separar el usuario actual (si `_current_user_id` > 0 y presente), ordenar el resto por `name.lower()` y devolver actual + resto, reutilizando el patrón de `TaskDialog`.

## 5. Tests (TDD): campo Descripción

- [x] 5.1 Actualizar `tests/test_report_generator.py`: `EXPECTED_FIELD_KEYS` con 18 claves incluyendo `descripcion` tras `titulo`; asserts 17→18; `REPORT_COLUMNS` con "Descripción".
- [x] 5.2 Actualizar `tests/test_report_dialog.py`: el grupo de campos pasa a 18 casillas y `len(...) == 18`.
- [x] 5.3 Test: `ReportDialog.selected_fields` incluye `descripcion` por defecto en el orden canónico.
- [x] 5.4 Actualizar `tests/test_main_window.py::test_por_defecto_sin_columnas_personalizadas` a 18 y añadir test de que `_generar_informe()` vuelca `issue.description` en la columna "Descripción".

## 6. Catálogo y generación de la columna Descripción

- [x] 6.1 Añadir `("descripcion", "Descripción")` a `REPORT_FIELDS` en `app/services/report_generator.py`, tras `titulo`.
- [x] 6.2 Devolver `issue.description` para la clave `descripcion` en `MainWindow._report_field_value()`.
- [x] 6.3 Confirmar que `_compose_report_rows()` y el ODS generan la columna sin cambios adicionales (ancho y celda son genéricos).

## 7. Tests (TDD): participante histórico

- [x] 7.1 Tests de `RedmineJournal.details` en `tests/test_redmine_client.py`: `_parse_journals` conserva `details` (propiedad, valor anterior, valor nuevo) y devuelve lista vacía si no hay.
- [x] 7.2 Test: `roles_for_user(u)` devuelve `participante` para el valor anterior de un detalle `assigned_to_id`.
- [x] 7.3 Test: también para el valor nuevo del detalle.
- [x] 7.4 Test: se mantiene `participante` para el asignado actual y para el autor de notas (no regresión).
- [x] 7.5 Test de integración: `matches_user_filter({u}, {"participante"})` casa con un asignado histórico sin journals con notas.
- [x] 7.6 Test: también se reconoce la propiedad legada `assigned_to`.

## 8. RedmineClient: details y rol participante histórico

- [x] 8.1 Añadir `details: list[dict]` con `default_factory=list` a `RedmineJournal`.
- [x] 8.2 Parsear `j.get("details", [])` en `_parse_journals()`, normalizando cada detalle con propiedad, valor anterior y valor nuevo.
- [x] 8.3 En `roles_for_user()`, añadir "participante" si el usuario coincide con el valor anterior o nuevo de algún detalle de asignación (`assigned_to_id` o `assigned_to`), comparando como cadena.

## 9. Tests (TDD): subproyectos en el informe

- [x] 9.1 Test unitario (en `tests/test_project_full_names.py` o en un nuevo `tests/test_mejoras_informes.py`): `descendant_project_ids([P], hierarchy)` devuelve P y todos sus descendientes transitivos.
- [x] 9.2 Test: proyecto sin hijos devuelve solo su id; lista de entrada vacía devuelve lista vacía; orden estable.
- [x] 9.3 Test: `_generar_informe()` llama a `get_issues` con `project_id` expandido (padre + descendientes).
- [x] 9.4 Test: seleccionar padre y descendiente no duplica ids y el merge de `get_issues` deduplica tareas.

## 10. Expansión a descendientes

- [x] 10.1 Añadir `descendant_project_ids(project_ids, hierarchy)` a `app/utils/projects.py` (puro, sin PyQt).
- [x] 10.2 En `_generar_informe()`, expandir `dlg.selected_project_ids` con `self._project_hierarchy` antes de llamar a `get_issues`; si no hay selección, seguir usando `None` (todos).
- [x] 10.3 Confirmar el deduplicado por id ya existente en el merge multi-proyecto de `get_issues()`.

## 11. Tests (TDD): filtro de estado del informe

- [x] 11.1 Tests en `tests/test_report_dialog.py`: existe el grupo "Estado de la tarea" con `_status_combo` (`MultiSelectCombo`) y `selected_status_ids` por defecto `[]` ("Todas").
- [x] 11.2 Test: al marcar un estado, `selected_status_ids == [id]`; al marcar varios, lista ordenada.
- [x] 11.3 Test: con catálogo de estados vacío solo queda "Todas".
- [x] 11.4 Test en `tests/test_main_window.py`: `selected_status_ids == []` llama a `get_issues(status_filter="*")`; `[1]` llama con `1`; `[1, 2]` con la lista acordada.
- [x] 11.5 Test de `RedmineClient.get_issues` con `status_filter=[1, 2]` → `params["status_id"] == "1,2"`.

## 12. ReportDialog y get_issues: filtro de estado

- [x] 12.1 `ReportDialog.__init__` acepta `statuses=None`; `_build_status_group()` con `MultiSelectCombo` y opción fija "Todas"; propiedad `selected_status_ids`.
- [x] 12.2 `MainWindow._generar_informe()` pasa `statuses=self._statuses` al `ReportDialog` y traduce `selected_status_ids` a `status_filter` ("*" si está vacío).
- [x] 12.3 Ampliar `RedmineClient.get_issues(status_filter)` para aceptar entero o lista y construir `status_id` uniendo con ",".

## 13. Verificación

- [x] 13.1 Ejecutar `QT_QPA_PLATFORM=offscreen pytest` y confirmar 0 fallos (incluye `test_report_generator.py`, `test_report_dialog.py`, `test_main_window.py`, `test_redmine_client.py`, `test_mejoras_filtros.py` y `test_project_full_names.py`).
- [ ] 13.2 Comprobación manual: filtro de proyecto con nombre largo muestra tooltip al pasar el ratón (botón con selección única y cada ítem de la lista).
- [ ] 13.3 Comprobación manual: la lista de usuarios del informe está ordenada (usuario actual primero) y el campo de búsqueda reduce los ítems.
- [ ] 13.4 Comprobación manual: generar un informe con "Descripción" y verificar la columna y su contenido.
- [ ] 13.5 Comprobación manual: filtrar por proyecto padre e incluir tareas de subproyectos; comprobar que un usuario con asignación histórica y comentarios aparece con rol "Participante".
- [ ] 13.6 Comprobación manual: filtro de estado del informe con "Todas" (por defecto), un estado y varios estados.

## 14. Correcciones de la verificación

- [x] 14.1 Corregir el cierre del popup de `MultiSelectCombo` por clic fuera (limpiar búsqueda y resetear `_popup_open`) + test.
- [x] 14.2 Endurecer la comparación de ids de asignación histórica con `str(...)` en ambos lados + test con valores int.
- [x] 14.3 Ampliar `participant_ids` para incluir asignados históricos + tests (columna "Usuarios implicados").
- [x] 14.4 Corregir el fallback de `_update_button_text()` (buscar también en opciones fijas; tooltip solo si se conoce el nombre) + test.

## 15. Cobertura de tests de la verificación

- [x] 15.1 Test: el `ReportDialog` muestra los cinco grupos (campos, usuarios implicados, fechas de creación, estado de la tarea, proyectos).
- [x] 15.2 Test: el combo de proyectos del `ReportDialog` expone tooltip con el nombre completo en cada ítem.
- [x] 15.3 Test: el combo de usuarios del `ReportDialog` expone tooltip con el nombre largo del usuario.
- [x] 15.4 Test: la columna "Descripción" se escribe en el ODS con el contenido de la tarea (end-to-end de escritura y lectura del fichero).
- [x] 15.5 Test: un usuario que tuvo la tarea asignada históricamente **y además** comentó cumple el rol "Participante" y la tarea aparece al filtrar por él como participante.