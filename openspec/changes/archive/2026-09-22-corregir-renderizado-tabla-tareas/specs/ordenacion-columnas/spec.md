## ADDED Requirements

### Requirement: Integridad de las filas al ordenar
El sistema SHALL ordenar las filas sin mezclar datos entre tareas: tras cualquier operación de ordenación, cada fila SHALL contener exclusivamente los datos de una única issue.

#### Scenario: Ordenar no mezcla celdas
- **WHEN** el usuario ordena por cualquier columna
- **THEN** cada fila mantiene juntos el ID, el título, la prioridad, el progreso y las fechas de la misma tarea

### Requirement: Preservación de la ordenación al refrescar y filtrar
El sistema SHALL preservar la columna y la dirección de ordenación activas cuando la tabla se repuebla por un refresco manual o por un cambio de filtro.

#### Scenario: Refrescar mantiene la ordenación
- **WHEN** el usuario pulsa "Refrescar" con una ordenación activa
- **THEN** la tabla sigue ordenada por la misma columna y en la misma dirección

#### Scenario: Cambiar de filtro mantiene la ordenación
- **WHEN** el usuario cambia un filtro (proyecto, estado, prioridad, fecha, etc.) con una ordenación activa
- **THEN** la tabla repoblada conserva la columna y la dirección de ordenación