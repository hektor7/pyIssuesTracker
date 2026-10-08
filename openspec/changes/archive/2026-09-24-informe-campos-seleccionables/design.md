## Context

Estado del código tras el cambio `add-ods-report-export` (v0.3.26):

- `ReportDialog` (`app/dialogs/report_dialog.py`) tiene tres grupos: usuarios implicados (multiselect + roles), fechas de creación y proyectos.
- `report_generator.py` define `REPORT_COLUMNS` (lista fija de 15 etiquetas) y `ReportGenerator(columns, sheet_name)` genérico con `add_row(values)` y `write(path)`; escribe cabecera en negrita y congelada, fechas como tipo fecha y números como float; `_make_cell` añade un único `text.P` por celda.
- `MainWindow._generar_informe()` usa `ReportGenerator(REPORT_COLUMNS, ...)` y `_compose_report_rows(issues)` fijo; el flujo usa `get_issues(include_journals=True)`, por lo que `RedmineIssue.journals` está disponible.
- `RedmineIssue.journals` contiene `RedmineJournal(user_id, user_name, notes, created_on)`; solo tienen texto los journals con `notes`.
- `app/utils/dates.py` ofrece `iso_datetime_to_display` (ISO 8601 → `DD/MM/YY HH:MM`).

## Goals / Non-Goals

**Goals:**
- Permitir al usuario elegir qué campos aparecen en el informe.
- Añadir los campos URL y Comentarios (con autor, fecha y hora).
- Mantener el comportamiento por defecto (todos los campos).
- Soportar texto multilínea en las celdas ODS.

**Non-Goals:**
- Reordenar columnas por el usuario (orden canónico fijo).
- Exportar a Excel/CSV.
- Desglosar los comentarios en filas o en una hoja/pestaña aparte.
- Incluir campos personalizados de Redmine o adjuntos en el informe.

## Decisions

### D1: Catálogo de campos `REPORT_FIELDS`
**Decisión**: definir en `report_generator.py` `REPORT_FIELDS: list[tuple[str, str]]` (clave → etiqueta) con las 17 entradas en orden canónico, y `DEFAULT_FIELD_KEYS` con todas las claves. `ReportGenerator` sigue recibiendo solo las etiquetas de las columnas elegidas.
**Alternativa considerada**: definir el catálogo en el diálogo — descartada porque `MainWindow` también necesita el mapeo clave→valor y las etiquetas.

### D2: Selección con casillas en el diálogo
**Decisión**: grupo "Campos del informe" con un `QCheckBox` por campo, todos marcados por defecto; `selected_fields` devuelve las claves marcadas en orden canónico; `accept()` avisa si no hay ninguna marcada.
**Alternativa considerada**: `MultiSelectCombo` — descartada por UX: con 17 campos es más claro ver las casillas en el diálogo.

### D3: Composición de filas por campos
**Decisión**: `MainWindow._compose_report_rows(issues, field_keys)` construye cada fila según las claves elegidas y devuelve las filas; las columnas (etiquetas) se derivan del mismo catálogo. Un mapa `clave → función(issue)` produce el valor de cada campo.
**Alternativa considerada**: construir un dict por issue y luego filtrar — descartada por simplicidad de la tupla ordenada.

### D4: URL de la tarea
**Decisión**: construir con `urljoin(redmine_url.rstrip('/') + '/', f'issues/{id}')`, el mismo patrón que usa la tabla (`main_window.py:497`).
**Alternativa considerada**: usar el endpoint de la API — descartada; el usuario espera la URL web.

### D5: Comentarios
**Decisión**: considerar "comentario" todo journal con `notes` no vacío. Formatear cada uno como `[DD/MM/YYYY HH:MM] Autor: texto`, usando la fecha/hora de `created_on`. Unir con `\n`. Si no hay comentarios, cadena vacía.
**Alternativa considerada**: incluir todos los journals (también los cambios de atributos sin notas) — descartada porque el usuario pidió "comentarios".

### D6: Texto multilínea en ODS
**Decisión**: en `_make_cell`, si el valor es una cadena con `\n`, añadir un `text.P` por línea en la misma celda.
**Alternativa considerada**: sustituir saltos por "; " — descartada; el usuario espera los comentarios uno por línea.

### D7: Tipos de datos independientes de la posición
**Decisión**: los campos de fecha siguen escribiéndose como `datetime.date` y el progreso como número; al cambiar las columnas, el tipo se infiere del valor, no de la posición.

## Risks / Trade-offs

- **[Riesgo]** Comentarios muy largos ensanchan la columna/fila. → **Mitigación**: ancho máximo de columna ya existente (40 cm) y saltos de línea.
- **[Riesgo]** Un informe con muchos comentarios genera un fichero grande. → **Trade-off aceptado**: el usuario controla los filtros.
- **[Trade-off]** No se puede reordenar columnas (orden canónico fijo).
- **[Trade-off]** No se incluyen campos personalizados de Redmine.

## Migration Plan

1. Tests TDD del catálogo y del multilínea en `report_generator.py`.
2. Catálogo `REPORT_FIELDS`/`DEFAULT_FIELD_KEYS` y soporte multilínea.
3. Selección de campos en `ReportDialog` (grupo + `selected_fields` + validación).
4. `_compose_report_rows(issues, field_keys)` con URL y Comentarios; wiring en `_generar_informe`.
5. Suite completa y verificación (opcional) con LibreOffice headless.

**Rollback**: revertir el cambio; no hay migración de datos.

## Open Questions

- ¿Debe poder reordenarse el orden de las columnas? (Fuera de alcance; el orden es canónico.)
- ¿Incluir campos personalizados de Redmine como campos seleccionables? (Fuera de alcance de este cambio.)
- ¿Exportar la URL como hipervínculo clicable además de texto? (Fuera de alcance.)
