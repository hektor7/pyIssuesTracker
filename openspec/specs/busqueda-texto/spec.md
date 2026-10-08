## Purpose

Definir la búsqueda por texto en la barra de filtros: un campo en una segunda fila que filtra las tareas por coincidencia parcial en el título en tiempo real.

## Requirements

### Requirement: Campo de búsqueda por texto en segunda fila de filtros
El sistema SHALL mostrar un campo de texto en una segunda fila del `FilterBar` que permita buscar tareas por coincidencia parcial en el título, filtrando en tiempo real a medida que el usuario escribe.

#### Scenario: Filtrar por palabra clave
- **WHEN** el usuario escribe "login" en el campo de búsqueda
- **THEN** la tabla muestra solo las tareas cuyo título contenga "login" (ignorando mayúsculas/minúsculas)

#### Scenario: Limpiar búsqueda
- **WHEN** el usuario borra el texto del campo de búsqueda
- **THEN** la tabla vuelve a mostrar todas las tareas sin filtrar por texto

#### Scenario: Búsqueda sin resultados
- **WHEN** el usuario escribe un texto que no coincide con ningún título
- **THEN** la tabla se muestra vacía

### Requirement: Segunda fila en la barra de filtros
El sistema SHALL organizar los filtros en dos filas: la primera con los combos existentes (proyecto, estado, prioridad, categoría, asignado) y la segunda con el campo de búsqueda por texto.

#### Scenario: Visualización en dos filas
- **WHEN** la aplicación se inicia con la barra de filtros visible
- **THEN** se muestran dos filas: arriba los combos de filtro, abajo el campo de búsqueda
