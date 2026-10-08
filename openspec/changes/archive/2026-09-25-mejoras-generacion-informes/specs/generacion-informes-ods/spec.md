## MODIFIED Requirements

### Requirement: Diálogo de configuración del informe
El sistema SHALL mostrar un diálogo (`ReportDialog`) con cinco grupos: campos del informe, usuarios implicados, rango de fechas de creación, proyectos y estado de la tarea. El diálogo SHALL permitir generar el informe y cancelar la operación.

#### Scenario: Apertura del diálogo
- **WHEN** el usuario pulsa el botón "Informe"
- **THEN** el diálogo muestra los selectores de campos del informe, de usuarios implicados, el rango de fechas de creación, los proyectos y el estado de la tarea
- **AND** los proyectos precargan la selección actual del `FilterBar` si la hay
- **AND** el filtro de estado muestra "Todas" seleccionado por defecto

#### Scenario: Cancelar el diálogo
- **WHEN** el usuario cierra el diálogo sin generar
- **THEN** no se escribe ningún fichero ni se realiza ninguna consulta

### Requirement: Selección de campos del informe
El diálogo SHALL ofrecer un grupo "Campos del informe" con una casilla por campo disponible. Los campos disponibles SHALL ser los 18 campos estándar (ID, Proyecto, Tracker, Título, Descripción, Estado, Prioridad, Asignado a, Creado por, Fecha de creación, Fecha de inicio, Fecha de fin, % Progreso, Categoría, Última modificación, Usuarios implicados, URL y Comentarios) más los campos personalizados presentes en al menos uno de los proyectos en alcance. Las casillas de los campos estándar SHALL estar marcadas por defecto; las de los campos personalizados SHALL estar desmarcadas por defecto. El sistema MUST NOT permitir generar el informe sin al menos un campo marcado.

#### Scenario: Todos los campos estándar marcados por defecto
- **WHEN** el usuario abre el diálogo sin tocar nada y genera
- **THEN** el informe contiene los 18 campos estándar en el orden canónico y ninguna columna de campo personalizado

#### Scenario: Descripción disponible como campo estándar
- **WHEN** el usuario abre el grupo "Campos del informe"
- **THEN** existe una casilla "Descripción" marcada por defecto junto a "Título"

#### Scenario: Subconjunto de campos
- **WHEN** el usuario desmarca "Prioridad" y "Categoría" y genera
- **THEN** el informe no contiene esas dos columnas y el resto de campos se mantiene

#### Scenario: Ningún campo marcado
- **WHEN** el usuario desmarca todos los campos e intenta generar
- **THEN** el sistema muestra un aviso y no genera el informe

#### Scenario: Campos personalizados disponibles
- **WHEN** los proyectos en alcance tienen campos personalizados distintos
- **THEN** el grupo muestra la unión de todos ellos como casillas seleccionables

### Requirement: Filtrado por proyectos
El diálogo SHALL permitir seleccionar uno o varios proyectos mediante un `MultiSelectCombo`. Si no se selecciona ninguno, el informe SHALL abarcar todos los proyectos accesibles. La consulta SHALL incluir, además de cada proyecto seleccionado, las tareas de todos sus subproyectos descendientes (hijos, nietos, etc.), sin duplicar tareas cuando se seleccione a la vez un proyecto y alguno de sus descendientes.

#### Scenario: Varios proyectos
- **WHEN** el usuario selecciona los proyectos "A" y "B"
- **THEN** el informe incluye las tareas de ambos proyectos y de sus descendientes

#### Scenario: Sin proyectos seleccionados
- **WHEN** el usuario no selecciona ningún proyecto
- **THEN** el informe abarca las tareas de todos los proyectos que cumplen el resto de filtros

#### Scenario: Proyecto padre incluye tareas de subproyectos
- **WHEN** el usuario selecciona el proyecto padre "P1", que tiene el subproyecto "P1 > Hijo"
- **THEN** el informe incluye las tareas de "P1" y de "P1 > Hijo"

#### Scenario: Varios proyectos con descendientes solapados
- **WHEN** el usuario selecciona a la vez el proyecto "P1" y su descendiente "P1 > Hijo"
- **THEN** cada tarea aparece exactamente una vez en el informe

#### Scenario: Proyecto sin descendientes
- **WHEN** el proyecto seleccionado no tiene subproyectos
- **THEN** el informe incluye solo las tareas de ese proyecto

### Requirement: Contenido y formato del ODS
El informe SHALL contener una hoja con una fila de cabecera destacada (en negrita) y una fila por tarea incluida. Las columnas SHALL ser exactamente los campos marcados en el grupo "Campos del informe", en el orden canónico del catálogo (por defecto, los 18 campos disponibles). Las fechas SHALL escribirse como valores de tipo fecha (no texto) y el porcentaje como valor numérico. La fila de cabecera SHALL permanecer fija al desplazarse.

#### Scenario: Fila de cabecera
- **WHEN** se genera el informe
- **THEN** la primera fila contiene los nombres de los campos seleccionados en negrita
- **AND** la fila de cabecera está congelada

#### Scenario: Columnas según los campos seleccionados
- **WHEN** el usuario selecciona solo "ID", "Título" y "Estado"
- **THEN** el informe contiene exactamente esas tres columnas, en ese orden

#### Scenario: Columna Descripción
- **WHEN** el usuario mantiene "Descripción" marcado y una tarea tiene descripción
- **THEN** la columna "Descripción" contiene la descripción de la tarea y queda vacía para las tareas sin descripción

#### Scenario: Tipos de datos
- **WHEN** una tarea tiene fecha de creación, fecha de fin y porcentaje de progreso
- **THEN** las fechas se escriben como valores de tipo fecha reconocidos por LibreOffice
- **AND** el progreso se escribe como número entero

#### Scenario: Usuarios implicados en la fila
- **WHEN** una tarea tiene creador, actualizadores y participantes
- **THEN** la columna "Usuarios implicados" lista los nombres de los usuarios implicados separados por ", " sin duplicados

#### Scenario: Asignado histórico en la columna Usuarios implicados
- **WHEN** una tarea tiene un usuario que tuvo la tarea asignada en el pasado (registrado en los `details` de un journal) y ya no es el asignado actual
- **THEN** la columna "Usuarios implicados" incluye el nombre de ese usuario, sin duplicarlo si además es autor o asignado actual

#### Scenario: Una fila por tarea
- **WHEN** el resultado contiene N tareas
- **THEN** el informe contiene exactamente N filas de datos más la cabecera

### Requirement: Integración con RedmineClient para el informe
El `RedmineClient.get_issues()` SHALL aceptar `project_id` como entero o lista de enteros, `status_filter` como cadena (`open`, `closed`, `*`), entero o lista de ids de estado, además de `created_on_from: str | None`, `created_on_to: str | None` e `include_journals: bool`. El método SHALL construir el parámetro `created_on` con la sintaxis de rango de Redmine y el parámetro `status_id` a partir de `status_filter` (un valor escalar o varios separados por coma). Cuando reciba varios proyectos, SHALL fusionar los resultados sin duplicar tareas por id.

#### Scenario: Rango de creación completo
- **WHEN** `get_issues()` recibe `created_on_from="2026-01-01"` y `created_on_to="2026-03-31"`
- **THEN** envía a la API `created_on=><2026-01-01|2026-03-31`

#### Scenario: Solo creación desde
- **WHEN** `get_issues()` recibe `created_on_from="2026-01-01"` y `created_on_to=None`
- **THEN** envía a la API `created_on=>=2026-01-01`

#### Scenario: Inclusión de journals
- **WHEN** `get_issues()` recibe `include_journals=True`
- **THEN** la petición incluye `journals` junto con los demás includes necesarios en el parámetro `include`

#### Scenario: Varios estados
- **WHEN** `get_issues()` recibe `status_filter=[1, 2]`
- **THEN** envía a la API `status_id=1,2`

#### Scenario: Varios proyectos sin duplicados
- **WHEN** `get_issues()` recibe `project_id=[2, 3]` y una tarea aparece en ambos
- **THEN** la tarea se devuelve una sola vez

## ADDED Requirements

### Requirement: Filtro por estado de tarea del informe
El `ReportDialog` SHALL ofrecer un grupo "Estado de la tarea" con un `MultiSelectCombo` que permita seleccionar uno o varios estados del catálogo de Redmine obtenido con `get_issue_statuses()`, además de una opción fija "Todas". El valor por defecto SHALL ser "Todas" (todas las tareas), preservando el comportamiento actual del informe. La selección SHALL trasladarse a `RedmineClient.get_issues()` como filtro de estado.

#### Scenario: Comportamiento por defecto
- **WHEN** el usuario abre el diálogo y no toca el filtro de estado
- **THEN** "Todas" está seleccionado
- **AND** el informe incluye tareas de cualquier estado

#### Scenario: Un estado concreto
- **WHEN** el usuario selecciona el estado "Resuelta" y genera
- **THEN** el informe incluye solo tareas en estado "Resuelta"

#### Scenario: Varios estados
- **WHEN** el usuario selecciona los estados "Nueva" y "En curso" y genera
- **THEN** el informe incluye tareas en "Nueva" o "En curso"

#### Scenario: Catálogo de estados no disponible
- **WHEN** el catálogo de estados está vacío (error de red o conexión)
- **THEN** el grupo muestra solo la opción "Todas"
- **AND** el informe se genera con todas las tareas

### Requirement: Usuarios implicados ordenados en el informe
En el grupo "Usuarios implicados", la lista SHALL presentarse ordenada alfabéticamente por nombre sin distinguir mayúsculas/minúsculas. Si el usuario autenticado está entre los usuarios disponibles, SHALL aparecer en primer lugar; el resto SHALL ordenarse alfabéticamente.

#### Scenario: Orden alfabético
- **WHEN** los usuarios disponibles son "Zoe", "ana" y "Luis"
- **THEN** la lista aparece como "ana", "Luis", "Zoe"

#### Scenario: Usuario autenticado primero
- **WHEN** el usuario autenticado es "Zoe" y también hay "ana" y "Luis"
- **THEN** la lista aparece como "Zoe", "ana", "Luis"

#### Scenario: Sin usuario autenticado identificado
- **WHEN** no se conoce el usuario autenticado o no está entre los miembros
- **THEN** la lista aparece en orden alfabético puro