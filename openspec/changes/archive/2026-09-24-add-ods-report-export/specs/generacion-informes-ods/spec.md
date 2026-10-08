## ADDED Requirements

### Requirement: Botón de generación de informes en la barra superior
El `IssueToolbar` SHALL incluir un botón "Informe" que emita la señal `informe_clicked` al pulsarse. El `MainWindow` SHALL conectar esa señal a la apertura del diálogo de informe.

#### Scenario: Pulsar el botón Informe
- **WHEN** el usuario pulsa el botón "Informe" de la barra superior
- **THEN** se emite la señal `informe_clicked`
- **AND** el `MainWindow` abre el diálogo de configuración del informe

#### Scenario: La barra superior mantiene el resto de acciones
- **WHEN** se añade el botón "Informe"
- **THEN** las acciones existentes (Nuevo, Editar, Asignar, Completada, Rechazar, Refrescar, Configuración) siguen presentes y funcionando

### Requirement: Diálogo de configuración del informe
El sistema SHALL mostrar un diálogo (`ReportDialog`) con tres grupos de filtros: usuarios implicados, rango de fechas de creación y proyectos. El diálogo SHALL permitir generar el informe y cancelar la operación.

#### Scenario: Apertura del diálogo
- **WHEN** el usuario pulsa el botón "Informe"
- **THEN** el diálogo muestra los selectores de usuarios implicados, el rango de fechas de creación y los proyectos
- **AND** los proyectos precargan la selección actual del `FilterBar` si la hay

#### Scenario: Cancelar el diálogo
- **WHEN** el usuario cierra el diálogo sin generar
- **THEN** no se escribe ningún fichero ni se realiza ninguna consulta

### Requirement: Filtrado por usuarios implicados y rol
El diálogo SHALL permitir seleccionar uno o varios usuarios y uno o varios roles de implicación: "Creador", "Actualizador" y "Participante". Una tarea SHALL incluirse en el informe si alguno de los usuarios seleccionados cumple alguno de los roles marcados. Si no se selecciona ningún usuario, la dimensión de usuarios MUST NOT restringir el resultado. El diálogo SHALL exigir que haya al menos un rol marcado para poder generar el informe.

#### Scenario: Filtrado por creador
- **WHEN** el usuario selecciona a "Ana" con el rol "Creador" marcado
- **THEN** el informe incluye las tareas cuyo autor es Ana
- **AND** no incluye tareas en las que Ana solo haya comentado

#### Scenario: Filtrado por actualizador
- **WHEN** el usuario selecciona a "Luis" con el rol "Actualizador" marcado
- **THEN** el informe incluye las tareas en cuyos journals Luis haya registrado un cambio
- **AND** no incluye tareas en las que Luis solo sea el asignado

#### Scenario: Filtrado por participante
- **WHEN** el usuario selecciona a "Marta" con el rol "Participante" marcado
- **THEN** el informe incluye las tareas en cuyos journals Marta haya dejado una nota de comentario
- **AND** también las tareas actualmente asignadas a Marta

#### Scenario: Varios usuarios y varios roles
- **WHEN** el usuario selecciona a "Ana" y "Luis" con "Creador" y "Actualizador" marcados
- **THEN** el informe incluye las tareas creadas por Ana, creadas por Luis, actualizadas por Ana o actualizadas por Luis

#### Scenario: Sin usuarios seleccionados
- **WHEN** el usuario no selecciona ningún usuario
- **THEN** el informe no filtra por implicación y depende solo del resto de filtros

#### Scenario: Ningún rol marcado
- **WHEN** el usuario desmarca los tres roles de implicación e intenta generar
- **THEN** el sistema muestra un aviso y no genera el informe

### Requirement: Filtrado por rango de fechas de creación
El diálogo SHALL ofrecer dos `QDateEdit` (desde y hasta) que filtren por la fecha de creación (`created_on`) de la tarea. Ambos extremos SHALL ser opcionales e independientes. Si la fecha "desde" es posterior a "hasta", el informe MUST NOT generarse y SHALL mostrarse un aviso.

#### Scenario: Solo fecha desde
- **WHEN** el usuario define la fecha "desde" y deja "hasta" vacío
- **THEN** el informe incluye tareas creadas en esa fecha o después

#### Scenario: Solo fecha hasta
- **WHEN** el usuario define la fecha "hasta" y deja "desde" vacío
- **THEN** el informe incluye tareas creadas en esa fecha o antes

#### Scenario: Rango completo
- **WHEN** el usuario define desde `2026-01-01` hasta `2026-03-31`
- **THEN** el informe incluye tareas creadas dentro de ese rango inclusivo

#### Scenario: Rango inválido
- **WHEN** la fecha "desde" es posterior a la fecha "hasta"
- **THEN** el sistema muestra un aviso y no genera el informe

### Requirement: Filtrado por proyectos
El diálogo SHALL permitir seleccionar uno o varios proyectos mediante un `MultiSelectCombo`. Si no se selecciona ninguno, el informe SHALL abarcar todos los proyectos accesibles.

#### Scenario: Varios proyectos
- **WHEN** el usuario selecciona los proyectos "A" y "B"
- **THEN** el informe incluye las tareas de ambos proyectos exclusivamente

#### Scenario: Sin proyectos seleccionados
- **WHEN** el usuario no selecciona ningún proyecto
- **THEN** el informe abarca las tareas de todos los proyectos que cumplen el resto de filtros

### Requirement: Selección de destino y escritura del fichero ODS
Al generar, el sistema SHALL solicitar una ruta de guardado (`QFileDialog.getSaveFileName`) con nombre por defecto `informe_<AAAAMMDD>_<HHMM>.ods` y extensión `.ods`. El fichero SHALL ser un ODS válido abrible en LibreOffice Calc.

#### Scenario: Guardado correcto
- **WHEN** el usuario elige una ruta válida y confirma
- **THEN** el sistema escribe un fichero `.ods` en esa ruta
- **AND** muestra un mensaje de confirmación con la ruta del fichero

#### Scenario: Extensión automática
- **WHEN** el usuario introduce un nombre sin extensión `.ods`
- **THEN** el sistema añade la extensión `.ods`

### Requirement: Contenido y formato del ODS
El informe SHALL contener una hoja con una fila de cabecera destacada (en negrita) y una fila por tarea incluida. Las columnas SHALL ser: ID, Proyecto, Tracker, Título, Estado, Prioridad, Asignado a, Creado por, Fecha de creación, Fecha de inicio, Fecha de fin, % Progreso, Categoría, Última modificación y Usuarios implicados. Las fechas SHALL escribirse como valores de tipo fecha (no texto) y el porcentaje como valor numérico. La fila de cabecera SHALL permanecer fija al desplazarse.

#### Scenario: Fila de cabecera
- **WHEN** se genera el informe
- **THEN** la primera fila contiene los nombres de las columnas en negrita
- **AND** la fila de cabecera está congelada

#### Scenario: Tipos de datos
- **WHEN** una tarea tiene fecha de creación, fecha de fin y porcentaje de progreso
- **THEN** las fechas se escriben como valores de tipo fecha reconocidos por LibreOffice
- **AND** el progreso se escribe como número entero

#### Scenario: Usuarios implicados en la fila
- **WHEN** una tarea tiene creador, actualizadores y participantes
- **THEN** la columna "Usuarios implicados" lista los nombres de los usuarios implicados separados por ", " sin duplicados

#### Scenario: Una fila por tarea
- **WHEN** el resultado contiene N tareas
- **THEN** el informe contiene exactamente N filas de datos más la cabecera

### Requirement: Informe sin resultados
Si ninguna tarea cumple los filtros, el sistema SHALL informar al usuario de que no hay resultados y MUST NOT escribir un fichero vacío.

#### Scenario: Sin coincidencias
- **WHEN** ninguna tarea cumple los filtros seleccionados
- **THEN** el sistema muestra un aviso de "sin resultados"
- **AND** no escribe ningún fichero

### Requirement: Manejo de errores de generación
Si la consulta a Redmine o la escritura del fichero fallan, el sistema SHALL mostrar un mensaje de error claro sin cerrar la aplicación y sin dejar ficheros corruptos.

#### Scenario: Error de escritura
- **WHEN** la ruta de destino no es escribible o se produce un `OSError`
- **THEN** el sistema muestra un mensaje de error con la causa
- **AND** la aplicación sigue operativa

#### Scenario: Sin conexión a Redmine
- **WHEN** el usuario intenta generar un informe sin conexión activa
- **THEN** el sistema muestra un mensaje indicando que debe conectarse primero

### Requirement: Integración con RedmineClient para el informe
El `RedmineClient.get_issues()` SHALL aceptar `created_on_from: str | None`, `created_on_to: str | None` e `include_journals: bool`. El método SHALL construir el parámetro `created_on` con la sintaxis de rango de Redmine.

#### Scenario: Rango de creación completo
- **WHEN** `get_issues()` recibe `created_on_from="2026-01-01"` y `created_on_to="2026-03-31"`
- **THEN** envía a la API `created_on=><2026-01-01|2026-03-31`

#### Scenario: Solo creación desde
- **WHEN** `get_issues()` recibe `created_on_from="2026-01-01"` y `created_on_to=None`
- **THEN** envía a la API `created_on=>=2026-01-01`

#### Scenario: Inclusión de journals
- **WHEN** `get_issues()` recibe `include_journals=True`
- **THEN** la petición incluye `journals` junto con los demás includes necesarios en el parámetro `include`

### Requirement: Generación de ODS desacoplada de la UI
El módulo `ReportGenerator` SHALL ser independiente de PyQt y recibir los datos ya preparados (columnas y filas), de modo que pueda probarse sin interfaz gráfica.

#### Scenario: Generación sin UI
- **WHEN** se instancia `ReportGenerator` y se le pasan columnas y filas, y se invoca la escritura a una ruta temporal
- **THEN** se produce un fichero ODS válido sin necesidad de `QApplication`
