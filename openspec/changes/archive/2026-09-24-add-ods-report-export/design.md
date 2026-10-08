## Context

PyIssuesTracker es un cliente de escritorio Redmine en PyQt6 (Python ≥3.9, httpx, pytest) sin componente web. Estado actual del código relevante:

- `IssueToolbar` (`app/widgets/toolbar.py`) expone 7 señales (`nuevo_clicked`, `editar_clicked`, `asignar_clicked`, `completar_clicked`, `rechazar_clicked`, `refrescar_clicked`, `configuracion_clicked`) y sus `QAction` con iconos estándar de Qt. No hay botón de informes.
- `FilterBar` (`app/widgets/filter_bar.py`) ya usa `MultiSelectCombo` para proyectos y asignados, con opciones fijas "Todos", "Sin asignar" y "Asignado a mí".
- `RedmineClient` (`app/services/redmine_client.py`) expone `get_issues` (con `include=attachments`), `get_all_projects`, `get_project_memberships`. La dataclass `RedmineJournal` solo tiene `user_name`, `notes`, `created_on`; `RedmineIssue` no expone participantes. `get_issue_with_journals` filtra los journals `if j.get("notes")`.
- `MainWindow` (`app/main_window.py`) construye un dict plano por issue en `_cargar_issues()` y lo pasa a `TaskTable`. Ya existe el patrón de workers en `app/services/download_worker.py` (QThread + señales) usado para descargar actualizaciones.
- La API de Redmine soporta `include=journals` en `GET /issues.json` y el filtro `created_on=><YYYY-MM-DD|YYYY-MM-DD`.
- No existe ninguna dependencia de exportación (`odfpy`, `openpyxl`, `pandas`); `requirements.txt` solo tiene `PyQt6`, `httpx` y `packaging`.

## Goals / Non-Goals

**Goals:**
- Añadir un botón "Informe" en la barra superior que abra un diálogo de configuración del informe.
- Permitir acotar el informe por usuarios implicados (con rol: creador / actualizador / participante), por rango de fechas de creación y por proyectos.
- Determinar los usuarios implicados a partir del author, el assigned_to y los journals, en una sola petición por proyecto.
- Generar un fichero `.ods` válido y bien formateado, abrible en LibreOffice Calc.
- Mantener el módulo de generación desacoplado de la UI para poder probarlo sin `QApplication`.

**Non-Goals:**
- No se exporta a Excel (`.xlsx`) ni CSV. Solo ODS.
- No se modifican el filtro de fecha por `due_date` ni la tabla de tareas.
- No se incluyen journals ni comentarios individuales en el informe: solo la lista agregada de usuarios implicados.
- No se persiste la configuración del informe entre sesiones (salvo, opcionalmente, el último directorio de guardado).
- No se genera el informe de forma asíncrona en esta iteración: se ejecuta de forma síncrona con cursor de espera, coherente con `_cargar_issues()`.
- No se cubren plantillas de informe personalizables por el usuario.

## Decisions

### D1: Biblioteca de escritura ODS — `odfpy`
**Decisión**: usar `odfpy` (`odf.opendocument`, `odf.table`, `odf.text`) para escribir el ODS directamente, sin dependencias pesadas.
**Alternativa considerada**: `pandas` + `odfpy` — descartada por arrastrar numpy/pandas, desproporcionado para un cliente de escritorio ligero. `pyexcel-ods3` — descartada por ser un wrapper con más dependencias transitivas que `odfpy`. `ezodf` — descartada por ser una capa fina sobre `odfpy` que no aporta valor aquí.

### D2: Obtención de participantes en bloque con `include=journals`
**Decisión**: extender `get_issues()` con `include_journals: bool`. Cuando está activo, la petición incluye `journals` en el parámetro `include` y `_issue_from_json` parsea los journals de cada issue. Así, los participantes se obtienen en la misma petición que las tareas (una por proyecto), sin N peticiones.
**Alternativa considerada**: usar `get_issue_with_journals(issue_id)` por tarea — descartada: N peticiones y riesgo de timeout/throttling en informes grandes. Es la única fuente existente hoy, pero no escala.

### D3: Modelo de roles de implicación
**Decisión**: clasificar la implicación en tres roles derivados del issue:
- **Creador**: `author.id`.
- **Actualizador**: autor de cualquier journal (representa cambios).
- **Participante**: autor de un journal con notas (comentario) y, además, el `assigned_to` actual.
`RedmineJournal` incorpora `user_id`; `RedmineIssue` expone `participant_ids` (sin duplicados) y un helper de roles por usuario.
**Alternativa considerada**: un único rol "implicado" — descartada: el usuario pidió poder distinguir quién creó, quién actualizó y quién participó. Un rol único no permite acotar por creador, que es un caso explícito.

### D4: Diálogo de informe con tres grupos de filtros
**Decisión**: `ReportDialog` con: (a) `MultiSelectCombo` de usuarios + `QCheckBox` "Creador"/"Actualizador"/"Participante"; (b) dos `QDateEdit` con `QCheckBox` habilitador cada uno para permitir extremos opcionales; (c) `MultiSelectCombo` de proyectos. Validación de rango `desde <= hasta` antes de aceptar. Los proyectos precargan la selección del `FilterBar`.
**Alternativa considerada**: reutilizar el `FilterBar` — descartada: el `FilterBar` filtra la tabla en vivo y su semántica de fecha es `due_date`; mezclarlo con `created_on` y con roles de implicación confundiría la UI y rompería la tabla.

### D5: Columnas y formato del ODS
**Decisión**: columnas ID, Proyecto, Tracker, Título, Estado, Prioridad, Asignado a, Creado por, Fecha de creación, Fecha de inicio, Fecha de fin, % Progreso, Categoría, Última modificación y Usuarios implicados. Cabecera en negrita y congelada; fechas como tipo fecha ODF; progreso como número entero; anchos de columna razonables; nombre de hoja saneado según ODF.
**Alternativa considerada**: volcar el dict crudo de la tabla sin más — descartada: faltarían "Creado por" y "Usuarios implicados", y las fechas saldrían como texto.

### D6: Filtrado de datos: servidor + cliente
**Decisión**: los filtros de proyecto y rango de `created_on` se delegan a la API de Redmine (parámetro `created_on`); el filtro por usuarios implicados se aplica en cliente sobre `participant_ids`/roles, porque la API de Redmine no permite filtrar por "autor de journal". 
**Alternativa considerada**: filtrar todo en cliente — descartada: descargar todos los proyectos cuando el usuario solo quiere uno o un rango pequeño es innecesario.

### D7: Generación síncrona con cursor de espera
**Decisión**: la obtención de datos y la escritura del ODS se ejecutan de forma síncrona, mostrando `QApplication.setOverrideCursor(Qt.WaitCursor)`. Se apoya en `RedmineClient` ya síncrono.
**Alternativa considerada**: `QThread` con worker como `download_worker.py` — pospuesta a una iteración futura; añade complejidad de UI (progreso, cancelación) que no es necesaria para el volumen esperado. Se documenta como no-goal.

## Risks / Trade-offs

- **[Riesgo]** Informes con muchos proyectos o rango amplio pueden tardar y bloquear la UI al ser síncrono. → **Mitigación**: cursor de espera y mensaje de estado; se documenta la migración a worker como trabajo futuro. Limitar razonablemente y advertir.
- **[Riesgo]** `include=journals` con muchas tareas devuelve respuestas grandes y puede ralentizar. → **Mitigación**: usar paginación existente (`REDMINE_PAGE_LIMIT`) y filtrar por proyecto/rango en servidor para reducir el volumen.
- **[Riesgo]** El filtro por implicación no puede expresarse en la API y se hace en cliente; si Redmine pagina, hay que acumular todas las páginas antes de filtrar. → **Mitigación**: `get_issues` ya pagina; se acumulan resultados por proyecto antes del filtrado cliente.
- **[Riesgo]** `odfpy` no está instalado en entornos existentes. → **Mitigación**: añadir a `requirements.txt` y `pyproject.toml`; comprobar import con mensaje de error claro si falta.
- **[Riesgo]** Nombres de hoja inválidos para ODF (caracteres prohibidos, longitud). → **Mitigación**: función de saneado y test específico.
- **[Trade-off]** Los journals sin notas pueden ser muchos; se conservan para poder clasificar "Actualizador" a costa de memoria.
- **[Trade-off]** No se persiste la configuración del informe: cada apertura parte de los valores del `FilterBar`.

## Migration Plan

1. Tests TDD del cliente en rojo (journals, participantes, `created_on`, `include_journals`).
2. Implementar `RedmineJournal.user_id`, parseo de journals en `_issue_from_json`, `participant_ids` y roles.
3. Añadir `created_on_from`/`created_on_to`/`include_journals` a `get_issues`.
4. Añadir la dependencia `odfpy` y tests del `ReportGenerator`; implementar `app/services/report_generator.py`.
5. Tests del `ReportDialog`; implementar `app/dialogs/report_dialog.py`.
6. Añadir señal y botón "Informe" a `IssueToolbar`; conectar en `MainWindow`; implementar `_generar_informe()`.
7. Ejecutar la suite completa en headless (`QT_QPA_PLATFORM=offscreen`).

**Rollback**: revertir el cambio y eliminar `odfpy` de las dependencias. No hay migración de datos ni persistencia afectada.

## Open Questions

- ¿Debe el informe incluir también tareas cerradas por defecto o respetar el filtro de estado del `FilterBar`? Propuesta: incluir todas las tareas que cumplan los filtros de informe, independientemente del estado, y documentarlo en la UI.
- ¿Se debe ofrecer una segunda hoja con el desglose por usuario (nº de tareas por rol)? Fuera de alcance de esta iteración.
- ¿Conviene migrar la generación a un worker asíncrono si los informes crecen? Se deja como trabajo futuro.
