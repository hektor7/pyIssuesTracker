## MODIFIED Requirements

### Requirement: Barra de progreso compatible con resaltado de prioridad alta
El sistema SHALL mostrar la barra de progreso con el fondo del resaltado de prioridad y el texto en blanco cuando la tarea tenga prioridad "Alta", "Urgente" o "Inmediata", de forma consistente con el resto de celdas de la fila.

#### Scenario: Tarea urgente con progreso parcial
- **WHEN** una tarea tiene prioridad "Urgente" y `done_ratio = 30`
- **THEN** la barra de progreso tiene fondo `RGB(200, 0, 0)` y el texto "30%" se muestra en blanco

#### Scenario: Tarea inmediata con progreso parcial
- **WHEN** una tarea tiene prioridad "Inmediata" y `done_ratio = 30`
- **THEN** la barra de progreso tiene fondo `RGB(139, 0, 0)` y el texto "30%" se muestra en blanco

#### Scenario: Tarea alta con progreso parcial
- **WHEN** una tarea tiene prioridad "Alta" y `done_ratio = 30`
- **THEN** la barra de progreso tiene fondo `RGB(198, 81, 0)` y el texto "30%" se muestra en blanco

#### Scenario: Tarea alta al 0 por ciento
- **WHEN** una tarea tiene prioridad "Alta" y `done_ratio = 0`
- **THEN** la celda de progreso usa el fondo de resaltado de la prioridad "Alta" y muestra el texto "0%" en blanco
