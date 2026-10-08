## ADDED Requirements

### Requirement: Ordenación por dos criterios
El sistema SHALL permitir mantener hasta dos criterios de ordenación simultáneos sobre la tabla de tareas: un criterio primario y un criterio secundario. Las filas SHALL ordenarse por el criterio primario y, para las filas con el mismo valor en el primario, por el criterio secundario. La ordenación SHALL ser estable.

#### Scenario: Ordenar por secundario dentro del primario
- **WHEN** la tabla está ordenada de forma primaria por "Estado" (ascendente) y secundaria por "Prioridad"
- **THEN** dentro de cada estado, las tareas se ordenan por prioridad según el orden semántico de la columna Prioridad
- **AND** las tareas con el mismo estado y la misma prioridad conservan su orden relativo previo

### Requirement: Interacción del clic en la cabecera
El sistema SHALL actualizar los criterios de ordenación al hacer clic en la cabecera de una columna del siguiente modo:
- Si la columna no es ningún criterio activo, pasa a ser el criterio primario (primer clic ascendente) y el primario anterior pasa a ser el secundario, descartándose el secundario anterior.
- Si la columna es el criterio primario, se invierte su dirección (ascendente ↔ descendente) manteniendo el secundario.
- Si la columna es el criterio secundario, pasa a ser el primario y el primario anterior pasa a ser el secundario, conservando cada uno su dirección.

#### Scenario: Primer clic fija el criterio primario
- **WHEN** no hay ordenación activa y el usuario hace clic en "Estado"
- **THEN** la tabla se ordena por "Estado" ascendentemente como criterio primario

#### Scenario: Segundo clic sobre otra columna invierte la prioridad de los criterios
- **WHEN** la tabla está ordenada por "Estado" como criterio primario y el usuario hace clic en "Prioridad"
- **THEN** "Prioridad" pasa a ser el criterio primario
- **AND** "Estado" pasa a ser el criterio secundario

#### Scenario: Clic sobre una tercera columna reordena
- **WHEN** la tabla tiene "Prioridad" como primario y "Estado" como secundario y el usuario hace clic en "Asignado a"
- **THEN** "Asignado a" pasa a ser el criterio primario
- **AND** "Prioridad" pasa a ser el criterio secundario
- **AND** "Estado" deja de ser criterio de ordenación

#### Scenario: Invertir la dirección del primario
- **WHEN** el usuario vuelve a hacer clic en el criterio primario
- **THEN** se invierte su dirección y el secundario se mantiene

### Requirement: Indicadores visuales de orden primario y secundario
La tabla SHALL mostrar dos indicadores de ordenación distintos: un triángulo de color verde para el criterio primario y un triángulo de color verde más claro para el criterio secundario. La punta del triángulo SHALL apuntar hacia arriba cuando la ordenación sea ascendente y hacia abajo cuando sea descendente.

#### Scenario: Indicador del criterio primario
- **WHEN** el usuario ordena por "Estado" de forma ascendente
- **THEN** la cabecera "Estado" muestra un triángulo verde con la punta hacia arriba

#### Scenario: Indicador del criterio secundario
- **WHEN** "Estado" es el primario y "Prioridad" el secundario
- **THEN** la cabecera "Estado" muestra el triángulo verde de criterio primario
- **AND** la cabecera "Prioridad" muestra un triángulo verde más claro

#### Scenario: Dirección descendente
- **WHEN** el criterio primario está en orden descendente
- **THEN** el triángulo del criterio primario apunta hacia abajo

### Requirement: Ordenación semántica de la columna Prioridad
La columna "Prioridad" SHALL ordenarse por el orden de prioridad de Redmine (de mayor a menor prioridad), NO alfabéticamente. El orden canónico de referencia es: Inmediata, Urgente, Alta, Normal, Baja.

#### Scenario: Primer clic ordena de mayor a menor prioridad
- **WHEN** el usuario hace clic por primera vez en la cabecera "Prioridad"
- **THEN** las tareas se muestran de mayor a menor prioridad: Inmediata, luego Urgente, luego Alta, luego Normal y luego Baja

#### Scenario: Segundo clic invierte el orden de prioridad
- **WHEN** el usuario hace un segundo clic en la cabecera "Prioridad"
- **THEN** las tareas se muestran de menor a mayor prioridad: Baja, Normal, Alta, Urgente, Inmediata

#### Scenario: Prioridad no alfabética
- **WHEN** la tabla contiene tareas con prioridades "Alta", "Inmediata" y "Normal"
- **THEN** ordenadas por prioridad aparecen como Inmediata, Alta, Normal (no Alta, Inmediata, Normal)

#### Scenario: Orden tomado de Redmine
- **WHEN** Redmine devuelve el catálogo de prioridades ordenado por su posición (p. ej. Baja, Normal, Alta, Urgente, Inmediata)
- **THEN** el sistema usa ese orden para la ordenación semántica, situando la última prioridad del catálogo como la de mayor rango

## MODIFIED Requirements

### Requirement: Ordenación por clic en cabecera de columna
El sistema SHALL permitir ordenar las filas de la tabla de tareas haciendo clic en la cabecera de cualquier columna (ID, Tracker, Proyecto, Título, Fecha inicio, Fecha fin, Prioridad, Estado, Asignado a, Categoría, Progreso %, Creado, Modificado). La ordenación SHALL admitir hasta dos criterios simultáneos con prioridad entre ellos. Las columnas con datos numéricos (ID, Progreso %) ordenarán numéricamente, las de texto (Tracker, Proyecto, Título, Estado, Asignado a, Categoría) alfabéticamente, las de fecha cronológicamente y la de Prioridad según su orden semántico de prioridad.

#### Scenario: Ordenar por ID numéricamente
- **WHEN** el usuario hace clic en la cabecera de la columna "ID"
- **THEN** las tareas se ordenan por ID de menor a mayor (primer clic) o de mayor a menor (segundo clic)

#### Scenario: Ordenar por título alfabéticamente
- **WHEN** el usuario hace clic en la cabecera "Título"
- **THEN** las tareas se ordenan alfabéticamente por título (A-Z / Z-A)

#### Scenario: Ordenar por fecha cronológicamente
- **WHEN** el usuario hace clic en la cabecera "Fecha inicio"
- **THEN** las tareas se ordenan por fecha de inicio de más antigua a más reciente (primer clic) o viceversa

#### Scenario: Ordenar por tracker alfabéticamente
- **WHEN** el usuario hace clic en la cabecera "Tracker"
- **THEN** las tareas se ordenan alfabéticamente por nombre de tracker (Bug, Feature, Support, etc.)

#### Scenario: Ordenar por estado alfabéticamente
- **WHEN** el usuario hace clic en la cabecera "Estado"
- **THEN** las tareas se ordenan alfabéticamente por nombre de estado

#### Scenario: Ordenar por asignado alfabéticamente
- **WHEN** el usuario hace clic en la cabecera "Asignado a"
- **THEN** las tareas se ordenan alfabéticamente por nombre del asignado

#### Scenario: Ordenar por fecha de creación cronológicamente
- **WHEN** el usuario hace clic en la cabecera "Creado"
- **THEN** las tareas se ordenan por fecha de creación de más antigua a más reciente (primer clic) o viceversa

#### Scenario: Ordenar por fecha de modificación cronológicamente
- **WHEN** el usuario hace clic en la cabecera "Modificado"
- **THEN** las tareas se ordenan por fecha de modificación de más antigua a más reciente (primer clic) o viceversa

#### Scenario: Ordenar por progreso numéricamente
- **WHEN** el usuario hace clic en la cabecera "Progreso %"
- **THEN** las tareas se ordenan por porcentaje de progreso numéricamente (0% → 100% o viceversa)

#### Scenario: Ordenar por prioridad según su orden semántico
- **WHEN** el usuario hace clic en la cabecera "Prioridad"
- **THEN** las tareas se ordenan por el orden de prioridad de Redmine (de mayor a menor prioridad en el primer clic), no alfabéticamente

#### Scenario: Indicador visual de ordenación
- **WHEN** hay una ordenación activa
- **THEN** el criterio primario se marca con un triángulo verde y el secundario (si existe) con un triángulo verde más claro, con la punta hacia arriba o hacia abajo según la dirección

### Requirement: Preservación de la ordenación al refrescar y filtrar
El sistema SHALL preservar los criterios de ordenación activos (primario y secundario) cuando la tabla se repuebla por un refresco manual o por un cambio de filtro.

#### Scenario: Refrescar mantiene la ordenación
- **WHEN** el usuario pulsa "Refrescar" con una ordenación activa de dos criterios
- **THEN** la tabla sigue ordenada por el mismo criterio primario y secundario, en las mismas direcciones

#### Scenario: Cambiar de filtro mantiene la ordenación
- **WHEN** el usuario cambia un filtro con una ordenación activa
- **THEN** la tabla repoblada conserva los criterios y direcciones de ordenación