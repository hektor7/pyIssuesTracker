## ADDED Requirements

### Requirement: Fondo rojo para tareas de prioridad Inmediata
El sistema SHALL mostrar las celdas de las filas correspondientes a tareas con prioridad "Inmediata" (o "Immediate") con fondo de color `RGB(200, 0, 0)` y texto en blanco (`RGB(255, 255, 255)`).

#### Scenario: Tarea inmediata visible en la tabla
- **WHEN** la tabla de tareas contiene una issue con `priority_name` igual a "Inmediata" o "Immediate"
- **THEN** todas las celdas de esa fila (ID, Título, Fecha inicio, Estado, Asignado, Progreso) tienen fondo rojo `RGB(200, 0, 0)` y texto blanco

#### Scenario: Tarea no inmediata no se ve afectada
- **WHEN** la tabla de tareas contiene una issue con prioridad distinta a "Inmediata"/"Immediate" o "Urgente"/"Urgent"
- **THEN** las celdas de esa fila no tienen fondo rojo y usan los colores por defecto del tema

### Requirement: Fondo rojo para tareas de prioridad Urgente
El sistema SHALL mostrar las celdas de las filas correspondientes a tareas con prioridad "Urgente" (o "Urgent") con fondo de color `RGB(180, 20, 20)` y texto en blanco (`RGB(255, 255, 255)`).

#### Scenario: Tarea urgente visible en la tabla
- **WHEN** la tabla de tareas contiene una issue con `priority_name` igual a "Urgente" o "Urgent"
- **THEN** todas las celdas de esa fila tienen fondo rojo `RGB(180, 20, 20)` y texto blanco

### Requirement: Prioridades normales mantienen apariencia original
El sistema SHALL mantener sin cambios la apariencia de las filas con prioridades "Normal", "Baja" u otras no urgentes/inmediatas.

#### Scenario: Tarea normal sin cambios
- **WHEN** la tabla de tareas contiene una issue con `priority_name` igual a "Normal"
- **THEN** las celdas de esa fila usan los colores por defecto del tema, sin fondo coloreado ni texto blanco forzado
