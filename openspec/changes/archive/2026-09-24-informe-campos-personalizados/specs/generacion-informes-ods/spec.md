## MODIFIED Requirements

### Requirement: Selección de campos del informe
El diálogo SHALL ofrecer un grupo "Campos del informe" con una casilla por campo disponible. Los campos disponibles SHALL ser los 17 campos estándar (ID, Proyecto, Tracker, Título, Estado, Prioridad, Asignado a, Creado por, Fecha de creación, Fecha de inicio, Fecha de fin, % Progreso, Categoría, Última modificación, Usuarios implicados, URL y Comentarios) más los campos personalizados presentes en al menos uno de los proyectos en alcance. Las casillas de los campos estándar SHALL estar marcadas por defecto; las de los campos personalizados SHALL estar desmarcadas por defecto. El sistema MUST NOT permitir generar el informe sin al menos un campo marcado.

#### Scenario: Todos los campos estándar marcados por defecto
- **WHEN** el usuario abre el diálogo sin tocar nada y genera
- **THEN** el informe contiene los 17 campos estándar en el orden canónico y ninguna columna de campo personalizado

#### Scenario: Subconjunto de campos
- **WHEN** el usuario desmarca "Prioridad" y "Categoría" y genera
- **THEN** el informe no contiene esas dos columnas y el resto de campos se mantiene

#### Scenario: Ningún campo marcado
- **WHEN** el usuario desmarca todos los campos e intenta generar
- **THEN** el sistema muestra un aviso y no genera el informe

#### Scenario: Campos personalizados disponibles
- **WHEN** los proyectos en alcance tienen campos personalizados distintos
- **THEN** el grupo muestra la unión de todos ellos como casillas seleccionables

## ADDED Requirements

### Requirement: Campos personalizados como columnas del informe
El informe SHALL poder incluir columnas de campos personalizados. Un campo personalizado SHALL estar disponible si al menos uno de los proyectos en alcance lo define. Cuando el campo esté marcado, el informe SHALL mostrar su valor para las tareas que lo tengan y una celda vacía para el resto. Los valores múltiples SHALL unirse con ", ".

#### Scenario: Campo presente en un proyecto y ausente en otro
- **WHEN** el informe abarca tareas del proyecto A (con el campo "Cliente") y del proyecto B (sin ese campo), y el campo "Cliente" está marcado
- **THEN** la columna "Cliente" muestra el valor en las tareas del proyecto A y queda vacía en las del proyecto B

#### Scenario: Unión de campos personalizados entre proyectos
- **WHEN** el proyecto A define "Cliente" y el proyecto B define "Sprint"
- **THEN** ambos son seleccionables y, si se marcan, el informe contiene las dos columnas

#### Scenario: Campo personalizado multivalor
- **WHEN** una tarea tiene varios valores en un campo personalizado múltiple
- **THEN** la celda los muestra unidos por ", "

#### Scenario: Campo personalizado no seleccionado
- **WHEN** un campo personalizado no está marcado
- **THEN** el informe no contiene su columna
