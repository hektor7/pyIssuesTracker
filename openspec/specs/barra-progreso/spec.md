## Purpose

Definir la representación gráfica del progreso de las tareas: barra de progreso en la columna 'Progreso %', compatible con el resaltado de prioridad alta, siempre correspondiente a la tarea de su fila y con el porcentaje legible en cualquier tema y prioridad.

## Requirements

### Requirement: Barra de progreso gráfica en la columna de progreso
El sistema SHALL mostrar en la columna "Progreso %" de la tabla de tareas una barra gráfica pintada por el delegate `ProgressBarDelegate` (`app/widgets/task_table.py`), en lugar de texto numérico.

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

### Requirement: Correspondencia de la barra con la tarea de la fila
El sistema SHALL mostrar en la columna "Progreso %" la barra de progreso correspondiente al `done_ratio` de la issue mostrada en esa fila, con independencia de la ordenación activa, del filtrado y del número de recargas.

#### Scenario: Barra correcta tras ordenar
- **WHEN** la tabla está ordenada por cualquier columna
- **THEN** cada fila muestra una barra con el porcentaje de la issue que aparece en esa fila

#### Scenario: Nunca se muestra texto numérico crudo
- **WHEN** la columna de progreso se renderiza
- **THEN** nunca aparece un valor como "100" o "50" como texto de celda en lugar de la barra

#### Scenario: Barra tras recargar al cambiar de filtro
- **WHEN** el usuario cambia el filtro (incluido el de varios proyectos) y la tabla se recarga
- **THEN** todas las filas muestran su barra de progreso correctamente

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

