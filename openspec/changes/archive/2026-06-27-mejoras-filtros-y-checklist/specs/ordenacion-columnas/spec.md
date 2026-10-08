## ADDED Requirements

### Requirement: Columnas de fecha y hora de creación y modificación
El sistema SHALL mostrar dos columnas adicionales en la tabla de tareas: "Creado" (fecha/hora de creación) y "Modificado" (fecha/hora de última modificación), con el formato `DD/MM/YY HH:MM`.

#### Scenario: Visualización de fecha y hora de creación
- **WHEN** una tarea tiene `created_on = "2026-06-15T09:30:00Z"`
- **THEN** la columna "Creado" muestra `15/06/26 09:30`

#### Scenario: Visualización de fecha y hora de modificación
- **WHEN** una tarea tiene `updated_on = "2026-06-26T14:45:00Z"`
- **THEN** la columna "Modificado" muestra `26/06/26 14:45`

#### Scenario: Fecha sin hora
- **WHEN** una tarea tiene `created_on = "2026-06-15"` (solo fecha, sin hora)
- **THEN** la columna "Creado" muestra `15/06/26` (solo fecha, sin hora)

#### Scenario: Campo vacío
- **WHEN** una tarea no tiene valor en `created_on` (cadena vacía)
- **THEN** la columna "Creado" muestra una celda vacía

### Requirement: Ordenación por columnas de fecha y hora
El sistema SHALL permitir ordenar las filas de la tabla haciendo clic en las cabeceras "Creado" y "Modificado", usando el mismo mecanismo de ordenación que el resto de columnas (primer clic ascendente, segundo descendente).

#### Scenario: Ordenar por fecha de creación
- **WHEN** el usuario hace clic en la cabecera "Creado"
- **THEN** las tareas se ordenan cronológicamente por fecha de creación (más antiguas primero en el primer clic, más recientes primero en el segundo)

#### Scenario: Ordenar por fecha de modificación
- **WHEN** el usuario hace clic en la cabecera "Modificado"
- **THEN** las tareas se ordenan cronológicamente por fecha de modificación

## MODIFIED Requirements

### Requirement: Ordenación por clic en cabecera de columna
El sistema SHALL permitir ordenar las filas de la tabla de tareas haciendo clic en la cabecera de cualquier columna (ID, Tracker, Título, Fecha inicio, Fecha fin, Estado, Asignado a, Progreso %, Creado, Modificado). El primer clic ordena ascendentemente, el segundo descendentemente. Las columnas con datos numéricos (ID, Progreso %) ordenarán numéricamente, las de texto (Tracker, Título, Estado, Asignado a) alfabéticamente, y las de fecha cronológicamente.

#### Scenario: Ordenar por ID numéricamente
- **WHEN** el usuario hace clic en la cabecera de la columna "ID"
- **THEN** las tareas se ordenan por ID de menor a mayor (primer clic) o de mayor a menor (segundo clic)

#### Scenario: Ordenar por tracker alfabéticamente
- **WHEN** el usuario hace clic en la cabecera "Tracker"
- **THEN** las tareas se ordenan alfabéticamente por nombre de tracker (Bug, Feature, Support, etc.)

#### Scenario: Ordenar por título alfabéticamente
- **WHEN** el usuario hace clic en la cabecera "Título"
- **THEN** las tareas se ordenan alfabéticamente por título (A-Z / Z-A)

#### Scenario: Ordenar por fecha cronológicamente
- **WHEN** el usuario hace clic en la cabecera "Fecha inicio"
- **THEN** las tareas se ordenan por fecha de inicio de más antigua a más reciente (primer clic) o viceversa

#### Scenario: Ordenar por estado alfabéticamente
- **WHEN** el usuario hace clic en la cabecera "Estado"
- **THEN** las tareas se ordenan alfabéticamente por nombre de estado

#### Scenario: Ordenar por asignado alfabéticamente
- **WHEN** el usuario hace clic en la cabecera "Asignado a"
- **THEN** las tareas se ordenan alfabéticamente por nombre del asignado

#### Scenario: Ordenar por progreso numéricamente
- **WHEN** el usuario hace clic en la cabecera "Progreso %"
- **THEN** las tareas se ordenan por porcentaje de progreso numéricamente (0% → 100% o viceversa)

#### Scenario: Ordenar por fecha de creación cronológicamente
- **WHEN** el usuario hace clic en la cabecera "Creado"
- **THEN** las tareas se ordenan por fecha de creación de más antigua a más reciente (primer clic) o viceversa

#### Scenario: Ordenar por fecha de modificación cronológicamente
- **WHEN** el usuario hace clic en la cabecera "Modificado"
- **THEN** las tareas se ordenan por fecha de modificación de más antigua a más reciente (primer clic) o viceversa

#### Scenario: Indicador visual de ordenación
- **WHEN** una columna está ordenada
- **THEN** la cabecera de esa columna muestra un indicador visual (flecha) que señala la dirección de ordenación
