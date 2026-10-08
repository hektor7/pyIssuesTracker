## Purpose

Definir la integridad de la tabla de tareas: cada fila refleja íntegramente una única tarea y las acciones sobre una fila se aplican a la issue correcta con independencia de la ordenación.

## Requirements

### Requirement: Cada fila refleja íntegramente una única tarea
La tabla de tareas SHALL garantizar que todas las celdas de una misma fila visual pertenecen a la misma issue, con independencia de la ordenación activa, del filtrado (incluido el filtrado por varios proyectos) y del número de veces que se recargue la tabla.

#### Scenario: Filas íntegras con ordenación activa
- **WHEN** el usuario ha ordenado la tabla por cualquier columna y el listado se recarga (refresco o cambio de filtro)
- **THEN** cada fila muestra exclusivamente los datos (ID, título, prioridad, progreso, fechas, etc.) de una única issue

#### Scenario: Sin celdas huérfanas tras ordenar
- **WHEN** el usuario cambia la ordenación de la tabla
- **THEN** ninguna celda queda desvinculada de su tarea por causa del reordenado

### Requirement: Resolución de la tarea de una fila independiente del orden
Cualquier acción que opere sobre una fila (doble clic para abrir la tarea, menú contextual de progreso/estado/asignado/fecha, edición de fecha) SHALL aplicarse a la issue que se muestra en esa fila, sin depender de que el índice de fila coincida con el orden de inserción de los datos.

#### Scenario: Menú contextual sobre la fila correcta tras ordenar
- **WHEN** el usuario ha ordenado la tabla y abre el menú contextual de la columna "Progreso" en una fila
- **THEN** el cambio de progreso se aplica a la issue mostrada en esa fila

#### Scenario: Doble clic sobre la fila correcta tras ordenar
- **WHEN** el usuario ha ordenado la tabla y hace doble clic sobre una fila
- **THEN** se abre la issue mostrada en esa fila

### Requirement: Repoblado atómico e independiente de la ordenación
El proceso de repoblado de la tabla SHALL ejecutarse sin que la ordenación activa reordene las filas a mitad de la carga, y SHALL reaplicar la ordenación activa una vez finalizado el repoblado.

#### Scenario: Refrescar no corrompe ni pierde la ordenación
- **WHEN** el usuario pulsa "Refrescar" con una ordenación activa
- **THEN** la tabla se repuebla sin mezclar celdas y mantiene la columna y la dirección de ordenación

#### Scenario: Sin residuos entre recargas
- **WHEN** se recarga la tabla con un número de issues distinto al de la carga anterior
- **THEN** no quedan filas ni widgets de la carga anterior