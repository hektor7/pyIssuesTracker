## Context

Estado tras `informe-campos-seleccionables` (v0.3.27):

- `ReportDialog` (`app/dialogs/report_dialog.py`) tiene un grupo "Campos del informe" con una casilla por entrada de `REPORT_FIELDS` (17 estándar), todas marcadas; `selected_fields` devuelve claves en orden canónico; valida ≥1 campo.
- `report_generator.py` define `REPORT_FIELDS` (clave→etiqueta) y `DEFAULT_FIELD_KEYS`.
- `MainWindow._compose_report_rows(issues, field_keys)` mapea cada clave a un valor mediante `_report_field_value`; el flujo usa `get_issues(include_journals=True)`.
- `RedmineClient.get_project_custom_fields(project_id) -> list[RedmineCustomField]` ya existe (id, name, field_format, multiple, possible_values…).
- `RedmineIssue.custom_fields: dict[int, Any]` ya se parsea de la respuesta de issues (`_parse_custom_fields`).
- `MainWindow._projects: list[tuple[int, str]]` (id, nombre completo).

## Goals / Non-Goals

**Goals:**
- Poder seleccionar cualquier campo personalizado existente en los proyectos en alcance.
- Mostrar el valor relleno donde exista y vacío donde no.
- No cambiar el informe por defecto (campos personalizados desmarcados).

**Non-Goals:**
- Reordenar columnas por el usuario.
- Filtrar tareas por valor de campo personalizado.
- Desglosar campos multivalor en filas.
- Incluir campos personalizados en el `FilterBar` o en la tabla de tareas.

## Decisions

### D1: Claves `cf_<id>` para los campos personalizados
**Decisión**: los campos personalizados se identifican en la selección con la clave `cf_<field_id>` (p. ej. `cf_7`) y su etiqueta es el nombre del campo. No entran en `REPORT_FIELDS` (que sigue siendo el catálogo estándar); el diálogo recibe la lista dinámica aparte.
**Alternativa considerada**: añadirlos a `REPORT_FIELDS` — descartada porque el catálogo deja de ser estático/dependiente de la sesión.

### D2: Unión de campos personalizados por proyectos en alcance
**Decisión**: `MainWindow` calcula la unión de `get_project_custom_fields(pid)` sobre los proyectos **en alcance**: los preseleccionados en el diálogo (los del `FilterBar`) o todos los cargados si no hay preselección. Deduplica por id de campo y ordena por nombre. El diálogo recibe esa unión como lista inicial y un `custom_fields_provider` (callback) que recalcula la unión al cambiar la selección de proyectos, de modo que los campos siempre corresponden a los proyectos elegidos. `_report_custom_fields()` (unión de todos los proyectos) se mantiene como delegación de `_report_custom_fields_for_projects(None)` y se usa para construir las etiquetas de cualquier clave `cf_<id>` seleccionable.
**Alternativa considerada**: calcular solo para los proyectos del `FilterBar` sin recargar en el diálogo — descartada porque el usuario puede elegir otros proyectos en el diálogo y faltarían campos; calcular siempre sobre todos los proyectos — descartada porque los campos no corresponderían a los proyectos en alcance.

### D3: Subgrupo "Campos personalizados" desmarcados por defecto
**Decisión**: dentro del grupo de campos, un subgrupo "Campos personalizados" con casillas desmarcadas por defecto; `selected_fields` los incluye solo si se marcan.
**Alternativa considerada**: marcados por defecto — descartada porque dispararía el número de columnas y cambiaría el informe actual.

### D4: Valor del campo personalizado
**Decisión**: `_report_field_value` reconoce `cf_<id>` y devuelve `issue.custom_fields.get(id)`; si es lista, se une con ", "; si es `None` o vacío, cadena vacía. Las tareas sin ese campo quedan con celda vacía.
**Alternativa considerada**: omitir la columna si algún proyecto no la tiene — descartada; el requisito pide mostrarla rellena donde exista y vacía donde no.

### D5: Orden de columnas
**Decisión**: primero los campos estándar en orden canónico y después los campos personalizados en el orden recibido (por nombre).

## Risks / Trade-offs

- **[Riesgo]** Muchos proyectos → muchas peticiones `get_project_custom_fields` al abrir el diálogo y al cambiar la selección. → **Mitigación**: dedupe por id, try/except por proyecto (un proyecto que falle no rompe el diálogo) y try/except en el provider (si falla, el subgrupo queda vacío).
- **[Riesgo]** Etiquetas de campos personalizados que colisionan con nombres estándar. → **Trade-off aceptado**: se muestran con su nombre.
- **[Trade-off]** No se puede filtrar por valor de campo personalizado (fuera de alcance).
- **[Trade-off]** Los campos personalizados desmarcados por defecto no aparecen salvo que el usuario los marque.

## Migration Plan

1. Tests TDD de la recolección/unión de campos personalizados y del valor por clave `cf_<id>`.
2. `MainWindow`: recolectar la unión y pasarla al diálogo; `_report_field_value` soporta `cf_<id>`.
3. `ReportDialog`: parámetro `custom_fields` + subgrupo de casillas + integración en `selected_fields`.
4. Suite completa y verificación opcional con LibreOffice headless.

**Rollback**: revertir el cambio; no hay migración de datos.

## Open Questions

- ¿Marcar por defecto los campos personalizados? (Se decide desmarcados; fácil de invertir.)
- ¿Filtrar por valor de campo personalizado? (Fuera de alcance.)
