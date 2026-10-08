## ADDED Requirements

### Requirement: Ordenación por clic en cabecera de columna
El sistema SHALL permitir ordenar las filas de la tabla de tareas haciendo clic en la cabecera de cualquier columna (ID, Título, Fecha inicio, Estado, Asignado a, Progreso %). El primer clic ordena ascendentemente, el segundo descendentemente. Las columnas con datos numéricos (ID, Progreso %) ordenarán numéricamente, las de texto (Título, Estado, Asignado a) alfabéticamente, y las de fecha cronológicamente.

#### Scenario: Ordenar por ID numéricamente
- **WHEN** el usuario hace clic en la cabecera de la columna "ID"
- **THEN** las tareas se ordenan por ID de menor a mayor (primer clic) o de mayor a menor (segundo clic)

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

#### Scenario: Indicador visual de ordenación
- **WHEN** una columna está ordenada
- **THEN** la cabecera de esa columna muestra un indicador visual (flecha) que señala la dirección de ordenación
