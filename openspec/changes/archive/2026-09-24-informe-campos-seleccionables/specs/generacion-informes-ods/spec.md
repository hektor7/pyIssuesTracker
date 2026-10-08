## MODIFIED Requirements

### Requirement: Diálogo de configuración del informe
El sistema SHALL mostrar un diálogo (`ReportDialog`) con cuatro grupos: campos del informe, usuarios implicados, rango de fechas de creación y proyectos. El diálogo SHALL permitir generar el informe y cancelar la operación.

#### Scenario: Apertura del diálogo
- **WHEN** el usuario pulsa el botón "Informe"
- **THEN** el diálogo muestra los selectores de campos del informe, de usuarios implicados, el rango de fechas de creación y los proyectos
- **AND** los proyectos precargan la selección actual del `FilterBar` si la hay

#### Scenario: Cancelar el diálogo
- **WHEN** el usuario cierra el diálogo sin generar
- **THEN** no se escribe ningún fichero ni se realiza ninguna consulta

### Requirement: Contenido y formato del ODS
El informe SHALL contener una hoja con una fila de cabecera destacada (en negrita) y una fila por tarea incluida. Las columnas SHALL ser exactamente los campos marcados en el grupo "Campos del informe", en el orden canónico del catálogo (por defecto, los 17 campos disponibles). Las fechas SHALL escribirse como valores de tipo fecha (no texto) y el porcentaje como valor numérico. La fila de cabecera SHALL permanecer fija al desplazarse.

#### Scenario: Fila de cabecera
- **WHEN** se genera el informe
- **THEN** la primera fila contiene los nombres de los campos seleccionados en negrita
- **AND** la fila de cabecera está congelada

#### Scenario: Columnas según los campos seleccionados
- **WHEN** el usuario selecciona solo "ID", "Título" y "Estado"
- **THEN** el informe contiene exactamente esas tres columnas, en ese orden

#### Scenario: Tipos de datos
- **WHEN** una tarea tiene fecha de creación, fecha de fin y porcentaje de progreso
- **THEN** las fechas se escriben como valores de tipo fecha reconocidos por LibreOffice
- **AND** el progreso se escribe como número entero

#### Scenario: Una fila por tarea
- **WHEN** el resultado contiene N tareas
- **THEN** el informe contiene exactamente N filas de datos más la cabecera

## ADDED Requirements

### Requirement: Selección de campos del informe
El diálogo SHALL ofrecer un grupo "Campos del informe" con una casilla por campo disponible. Los campos disponibles SHALL ser: ID, Proyecto, Tracker, Título, Estado, Prioridad, Asignado a, Creado por, Fecha de creación, Fecha de inicio, Fecha de fin, % Progreso, Categoría, Última modificación, Usuarios implicados, URL y Comentarios. Todas las casillas SHALL estar marcadas por defecto. El sistema MUST NOT permitir generar el informe sin al menos un campo marcado.

#### Scenario: Todos los campos marcados por defecto
- **WHEN** el usuario abre el diálogo sin tocar nada y genera
- **THEN** el informe contiene los 17 campos en el orden canónico

#### Scenario: Subconjunto de campos
- **WHEN** el usuario desmarca "Prioridad" y "Categoría" y genera
- **THEN** el informe no contiene esas dos columnas y el resto de campos se mantiene

#### Scenario: Ningún campo marcado
- **WHEN** el usuario desmarca todos los campos e intenta generar
- **THEN** el sistema muestra un aviso y no genera el informe

### Requirement: URL de la tarea en el informe
Cuando el campo "URL" esté marcado, el informe SHALL incluir, para cada tarea, su URL absoluta en Redmine con el formato `{redmine_url}/issues/{id}`.

#### Scenario: URL incluida
- **WHEN** el campo "URL" está marcado y la tarea tiene id 42 con Redmine en `https://redmine.example.com`
- **THEN** la celda URL muestra `https://redmine.example.com/issues/42`

#### Scenario: URL no seleccionada
- **WHEN** el campo "URL" no está marcado
- **THEN** el informe no contiene la columna URL

### Requirement: Comentarios por tarea en el informe
Cuando el campo "Comentarios" esté marcado, el informe SHALL incluir, en la fila de cada tarea, sus comentarios (journals con notas). Cada comentario SHALL mostrarse con autor, fecha y hora en el formato `[DD/MM/YYYY HH:MM] Autor: texto`. Los comentarios de una misma tarea SHALL separarse por saltos de línea dentro de la misma celda, y la celda SHALL conservar los saltos de línea. Una tarea sin comentarios SHALL mostrar la celda vacía.

#### Scenario: Tarea con comentarios
- **WHEN** una tarea tiene dos comentarios de autores distintos con fecha y hora
- **THEN** la celda "Comentarios" contiene ambos, cada uno con `[DD/MM/YYYY HH:MM] Autor: texto`, separados por salto de línea

#### Scenario: Tarea sin comentarios
- **WHEN** una tarea no tiene journals con notas
- **THEN** la celda "Comentarios" queda vacía

#### Scenario: Saltos de línea preservados en el ODS
- **WHEN** se escribe una celda con varias líneas
- **THEN** el fichero ODS conserva la separación en líneas
