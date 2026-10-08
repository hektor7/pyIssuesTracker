## ADDED Requirements

### Requirement: Barra de progreso gráfica en la columna de progreso
El sistema SHALL mostrar una barra de progreso `QProgressBar` en lugar de texto numérico en la columna "Progreso %" de la tabla de tareas.

#### Scenario: Tarea completada al 100%
- **WHEN** una tarea tiene `done_ratio = 100`
- **THEN** la celda de progreso muestra una barra llena de color verde con el texto "100%" visible

#### Scenario: Tarea en progreso parcial
- **WHEN** una tarea tiene `done_ratio = 50`
- **THEN** la celda de progreso muestra una barra al 50% de color naranja con el texto "50%" visible

#### Scenario: Tarea sin empezar
- **WHEN** una tarea tiene `done_ratio = 0`
- **THEN** la celda de progreso muestra una barra vacía de color gris claro con el texto "0%" visible

### Requirement: Barra de progreso compatible con resaltado de prioridad alta
El sistema SHALL mostrar la barra de progreso con fondo rojo y texto blanco cuando la tarea tenga prioridad "Inmediata" o "Urgente", de forma consistente con el resto de celdas de la fila.

#### Scenario: Tarea urgente con progreso parcial
- **WHEN** una tarea tiene prioridad "Urgente" y `done_ratio = 30`
- **THEN** la barra de progreso tiene fondo rojo y el texto "30%" se muestra en blanco
