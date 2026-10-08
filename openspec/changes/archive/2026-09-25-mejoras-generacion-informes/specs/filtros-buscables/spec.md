## ADDED Requirements

### Requirement: Búsqueda por texto en el combo de multiselección
El `MultiSelectCombo` SHALL incluir un campo de texto en su popup que permita filtrar dinámicamente los ítems visibles por coincidencia de subcadena, sin distinguir mayúsculas/minúsculas. El filtrado SHALL NOT alterar la selección ya marcada: los ítems que queden ocultos conservarán su estado. Las opciones fijas (`Todos`, `Sin asignar`, `Asignado a mí`) SHALL permanecer siempre visibles. El campo SHALL vaciarse al abrir el popup y al cerrarlo por cualquier vía: con el botón, al ocultarse el widget padre o por clic fuera del popup.

#### Scenario: Filtrado por subcadena
- **WHEN** el usuario escribe "an" en el campo de búsqueda del combo
- **THEN** solo permanecen visibles los ítems cuyo texto contiene "an", sin distinguir mayúsculas/minúsculas

#### Scenario: La selección se preserva al filtrar
- **WHEN** el usuario tiene marcados "Ana" y "Luis" y escribe "an"
- **THEN** "Ana" sigue marcada aunque "Luis" quede oculto

#### Scenario: Limpiar el filtro restaura todos los ítems
- **WHEN** el usuario vacía el campo de búsqueda
- **THEN** vuelven a mostrarse todos los ítems con su estado de marcado intacto

#### Scenario: Las opciones fijas no se ocultan
- **WHEN** el usuario filtra por un texto que no coincide con "Todos"
- **THEN** la opción "Todos" sigue visible y seleccionable

#### Scenario: Cierre por clic fuera vacía el campo
- **WHEN** el usuario escribe un filtro y cierra el popup haciendo clic fuera de él
- **THEN** el campo de búsqueda queda vacío
- **AND** el siguiente clic en el botón vuelve a abrir el popup con todos los ítems visibles

### Requirement: Tooltips con el texto completo en el combo de multiselección
El `MultiSelectCombo` SHALL mostrar un tooltip con el texto completo de la opción al pasar el ratón sobre cada ítem de la lista desplegable y sobre el botón cuando la selección es única. Aplica a los combos de proyecto (`FilterBar` y `ReportDialog`), a la lista de usuarios implicados del informe y al filtro de asignados.

#### Scenario: Tooltip en cada ítem
- **WHEN** el usuario pasa el ratón sobre un ítem de la lista desplegable
- **THEN** aparece un tooltip con el texto completo de ese ítem

#### Scenario: Tooltip del botón con selección única
- **WHEN** el combo tiene seleccionado un único ítem y el usuario pasa el ratón sobre el botón
- **THEN** aparece un tooltip con el texto completo del ítem seleccionado

#### Scenario: Nombre largo en la lista de usuarios del informe
- **WHEN** el usuario pasa el ratón sobre un nombre de usuario largo en el combo de "Usuarios implicados"
- **THEN** aparece un tooltip con el nombre completo del usuario

#### Scenario: Selección múltiple o "Todos"
- **WHEN** el combo muestra "Todos" o "N seleccionados" en el botón
- **THEN** el tooltip del botón no muestra un nombre de ítem incorrecto