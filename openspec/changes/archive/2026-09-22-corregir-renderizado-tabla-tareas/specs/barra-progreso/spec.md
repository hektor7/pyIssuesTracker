## ADDED Requirements

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