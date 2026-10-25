## MODIFIED Requirements

### Requirement: Fondo rojo para tareas de prioridad Inmediata
El sistema SHALL mostrar TODAS las celdas visibles de las filas correspondientes a tareas con prioridad "Inmediata" (o "Immediate") con fondo de color `RGB(139, 0, 0)` y texto en blanco (`RGB(255, 255, 255)`).

#### Scenario: Tarea inmediata visible en la tabla
- **WHEN** la tabla de tareas contiene una issue con `priority_name` igual a "Inmediata" o "Immediate"
- **THEN** todas las celdas visibles de esa fila (ID, Tracker, Proyecto, Título, Fecha inicio, Fecha fin, Prioridad, Estado, Asignado a, Categoría, Progreso, URL, Creado, Modificado) tienen fondo `RGB(139, 0, 0)` y texto blanco

#### Scenario: Fila inmediata íntegra con ordenación activa
- **WHEN** la tabla está ordenada por cualquier columna y contiene una issue "Inmediata"
- **THEN** la fila de esa issue se muestra completamente coloreada, sin ninguna celda sin colorear

#### Scenario: Inmediata es el nivel más oscuro de la escala
- **WHEN** la tabla muestra simultáneamente issues de prioridad "Alta", "Urgente" e "Inmediata"
- **THEN** el fondo de la fila "Inmediata" es el de menor luminancia de los tres

### Requirement: Fondo rojo para tareas de prioridad Urgente
El sistema SHALL mostrar TODAS las celdas visibles de las filas correspondientes a tareas con prioridad "Urgente" (o "Urgent") con fondo de color `RGB(200, 0, 0)` y texto en blanco (`RGB(255, 255, 255)`).

#### Scenario: Tarea urgente visible en la tabla
- **WHEN** la tabla de tareas contiene una issue con `priority_name` igual a "Urgente" o "Urgent"
- **THEN** todas las celdas visibles de esa fila tienen fondo `RGB(200, 0, 0)` y texto blanco

#### Scenario: Fila urgente íntegra con ordenación activa
- **WHEN** la tabla está ordenada por cualquier columna y contiene una issue "Urgente"
- **THEN** la fila de esa issue se muestra completamente coloreada, sin ninguna celda sin colorear

### Requirement: El resaltado sigue a la tarea, no a la posición
El sistema SHALL mantener el resaltado de prioridad asociado a cada issue (no a una posición de fila), de modo que al ordenar o recargar la tabla cada fila resaltada corresponda a una issue de prioridad alta.

#### Scenario: Resaltado tras reordenar
- **WHEN** el usuario cambia la columna de ordenación
- **THEN** las filas resaltadas corresponden exactamente a las issues de prioridad "Alta", "Urgente" o "Inmediata" mostradas

### Requirement: Prioridades normales mantienen apariencia original
El sistema SHALL mantener sin cambios la apariencia de las filas con prioridades "Normal" o "Baja", así como la de cualquier otra prioridad no incluida en el resaltado.

#### Scenario: Tarea normal sin cambios
- **WHEN** la tabla de tareas contiene una issue con `priority_name` igual a "Normal"
- **THEN** las celdas de esa fila usan los colores por defecto del tema, sin fondo coloreado ni texto blanco forzado

#### Scenario: Tarea baja sin cambios
- **WHEN** la tabla de tareas contiene una issue con `priority_name` igual a "Baja" o "Low"
- **THEN** las celdas de esa fila usan los colores por defecto del tema, sin fondo coloreado ni texto blanco forzado

#### Scenario: Prioridad personalizada sin resaltado
- **WHEN** la tabla de tareas contiene una issue con una prioridad no incluida en el resaltado (por ejemplo "Crítica" o "Minor")
- **THEN** las celdas de esa fila usan los colores por defecto del tema, sin fondo coloreado ni texto blanco forzado

## ADDED Requirements

### Requirement: Fondo naranja rojizo para tareas de prioridad Alta
El sistema SHALL mostrar TODAS las celdas visibles de las filas correspondientes a tareas con prioridad "Alta" (o "High") con fondo de color `RGB(198, 81, 0)` y texto en blanco (`RGB(255, 255, 255)`).

#### Scenario: Tarea alta visible en la tabla
- **WHEN** la tabla de tareas contiene una issue con `priority_name` igual a "Alta" o "High"
- **THEN** todas las celdas visibles de esa fila (ID, Tracker, Proyecto, Título, Fecha inicio, Fecha fin, Prioridad, Estado, Asignado a, Categoría, Progreso, URL, Creado, Modificado) tienen fondo `RGB(198, 81, 0)` y texto blanco

#### Scenario: Fila alta íntegra con ordenación activa
- **WHEN** la tabla está ordenada por cualquier columna y contiene una issue "Alta"
- **THEN** la fila de esa issue se muestra completamente coloreada, sin ninguna celda sin colorear

#### Scenario: Escala de tres niveles distinguible
- **WHEN** la tabla muestra simultáneamente issues de prioridad "Alta", "Urgente" e "Inmediata"
- **THEN** los tres fondos son distintos entre sí y su luminancia relativa es estrictamente decreciente en el orden Alta, Urgente, Inmediata
