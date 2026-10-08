## MODIFIED Requirements

### Requirement: Fondo rojo para tareas de prioridad Inmediata
El sistema SHALL mostrar TODAS las celdas visibles de las filas correspondientes a tareas con prioridad "Inmediata" (o "Immediate") con fondo de color `RGB(200, 0, 0)` y texto en blanco (`RGB(255, 255, 255)`).

#### Scenario: Tarea inmediata visible en la tabla
- **WHEN** la tabla de tareas contiene una issue con `priority_name` igual a "Inmediata" o "Immediate"
- **THEN** todas las celdas visibles de esa fila (ID, Tracker, Proyecto, Título, Fecha inicio, Fecha fin, Prioridad, Estado, Asignado a, Categoría, Progreso, URL, Creado, Modificado) tienen fondo rojo `RGB(200, 0, 0)` y texto blanco

#### Scenario: Fila inmediata íntegra con ordenación activa
- **WHEN** la tabla está ordenada por cualquier columna y contiene una issue "Inmediata"
- **THEN** la fila de esa issue se muestra completamente roja, sin ninguna celda sin colorear

#### Scenario: Tarea no inmediata no se ve afectada
- **WHEN** la tabla de tareas contiene una issue con prioridad distinta a "Inmediata"/"Immediate" o "Urgente"/"Urgent"
- **THEN** las celdas de esa fila no tienen fondo rojo y usan los colores por defecto del tema

### Requirement: Fondo rojo para tareas de prioridad Urgente
El sistema SHALL mostrar TODAS las celdas visibles de las filas correspondientes a tareas con prioridad "Urgente" (o "Urgent") con fondo de color `RGB(180, 20, 20)` y texto en blanco (`RGB(255, 255, 255)`).

#### Scenario: Tarea urgente visible en la tabla
- **WHEN** la tabla de tareas contiene una issue con `priority_name` igual a "Urgente" o "Urgent"
- **THEN** todas las celdas visibles de esa fila tienen fondo rojo `RGB(180, 20, 20)` y texto blanco

#### Scenario: Fila urgente íntegra con ordenación activa
- **WHEN** la tabla está ordenada por cualquier columna y contiene una issue "Urgente"
- **THEN** la fila de esa issue se muestra completamente roja, sin ninguna celda sin colorear

### Requirement: El resaltado sigue a la tarea, no a la posición
El sistema SHALL mantener el resaltado de prioridad asociado a cada issue (no a una posición de fila), de modo que al ordenar o recargar la tabla cada fila resaltada corresponda a una issue de prioridad alta.

#### Scenario: Resaltado tras reordenar
- **WHEN** el usuario cambia la columna de ordenación
- **THEN** las filas resaltadas corresponden exactamente a las issues de prioridad "Inmediata" o "Urgente" mostradas