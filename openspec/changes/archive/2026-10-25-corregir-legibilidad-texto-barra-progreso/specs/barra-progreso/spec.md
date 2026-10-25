## MODIFIED Requirements

### Requirement: Barra de progreso compatible con resaltado de prioridad alta
El sistema SHALL mostrar la barra de progreso con el fondo del resaltado de prioridad cuando la tarea tenga prioridad "Alta", "Urgente" o "Inmediata", de forma consistente con el resto de celdas de la fila. El color del texto del porcentaje se rige por el requisito "Legibilidad del texto del porcentaje".

#### Scenario: Tarea urgente con progreso parcial
- **WHEN** una tarea tiene prioridad "Urgente" y `done_ratio = 30`
- **THEN** la barra de progreso tiene fondo `RGB(200, 0, 0)` y el porcentaje "30%" se muestra legible sobre ella

#### Scenario: Tarea inmediata con progreso parcial
- **WHEN** una tarea tiene prioridad "Inmediata" y `done_ratio = 30`
- **THEN** la barra de progreso tiene fondo `RGB(139, 0, 0)` y el porcentaje "30%" se muestra legible sobre ella

#### Scenario: Tarea alta con progreso parcial
- **WHEN** una tarea tiene prioridad "Alta" y `done_ratio = 30`
- **THEN** la barra de progreso tiene fondo `RGB(198, 81, 0)` y el porcentaje "30%" se muestra legible sobre ella

#### Scenario: Tarea alta al 0 por ciento
- **WHEN** una tarea tiene prioridad "Alta" y `done_ratio = 0`
- **THEN** la celda de progreso usa el fondo de resaltado de la prioridad "Alta" y muestra el porcentaje "0%" legible

## ADDED Requirements

### Requirement: Legibilidad del texto del porcentaje
El sistema SHALL pintar el texto del porcentaje de la barra de progreso con un color que garantice un contraste mínimo de 4.5:1 frente al relleno sobre el que se dibuja en cada punto, con independencia del tema activo y de la prioridad de la tarea.

#### Scenario: Porcentaje en fila con prioridad y tema claro
- **WHEN** una tarea tiene prioridad "Alta", "Urgente" o "Inmediata" y `done_ratio = 30`, con tema claro
- **THEN** el texto "30%" se dibuja en color oscuro sobre la pista clara de la barra y es legible, sin coincidir con el color de la pista

#### Scenario: Porcentaje en tema oscuro
- **WHEN** el tema activo es oscuro y una tarea tiene `done_ratio = 30`
- **THEN** el texto "30%" se dibuja en color oscuro sobre la pista clara de la barra y es legible en cualquier prioridad, incluida "Normal"

#### Scenario: Porcentaje sobre tramo relleno oscuro
- **WHEN** una tarea tiene `done_ratio = 100` y el tramo relleno usa el color verde de completado
- **THEN** el texto "100%" se dibuja en blanco sobre el tramo verde, con contraste suficiente

#### Scenario: Porcentaje sobre tramo relleno claro
- **WHEN** una tarea tiene `done_ratio = 50` y el tramo relleno usa el color naranja de progreso parcial
- **THEN** el texto "50%" se dibuja en color oscuro sobre el tramo naranja, con contraste suficiente

#### Scenario: Barra vacía en tema oscuro
- **WHEN** el tema activo es oscuro y una tarea tiene `done_ratio = 0`
- **THEN** el texto "0%" se dibuja en color oscuro sobre la pista gris y es legible

#### Scenario: Nunca texto del mismo color que su relleno
- **WHEN** se pinta el porcentaje en cualquier combinación de tema y prioridad
- **THEN** el color del texto nunca es igual al color del relleno subyacente en el punto donde se dibuja
