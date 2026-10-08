## Purpose

Definir los filtros y combos de PyIssuesTracker con capacidades de búsqueda por teclado y multiselección: búsqueda dinámica en Prioridad y Categoría, multiselección en "Asignado a", y el widget `MultiSelectCombo` con campo de búsqueda por texto y tooltips con el texto completo.

## Requirements

### Requirement: Combo de Prioridad con búsqueda por teclado
El sistema SHALL permitir al usuario escribir en el combo de Prioridad del `FilterBar` para filtrar dinámicamente las opciones, buscando coincidencias en cualquier parte del texto (no solo prefijo).

#### Scenario: Búsqueda por nombre parcial en combo de Prioridad
- **WHEN** el usuario escribe "alt" en el combo de Prioridad del `FilterBar`
- **THEN** el dropdown muestra solo las opciones cuyo texto contenga "alt" (ej. "Alta"), ignorando mayúsculas/minúsculas

#### Scenario: Selección directa con teclado
- **WHEN** el usuario escribe el nombre exacto de una prioridad y pulsa Enter
- **THEN** el combo selecciona esa prioridad y emite la señal de cambio de filtro

### Requirement: Combo de Categoría con búsqueda por teclado
El sistema SHALL permitir al usuario escribir en el combo de Categoría del `FilterBar` para filtrar dinámicamente las opciones, buscando coincidencias en cualquier parte del texto.

#### Scenario: Búsqueda por nombre parcial en combo de Categoría
- **WHEN** el usuario escribe "bug" en el combo de Categoría del `FilterBar`
- **THEN** el dropdown muestra solo las categorías cuyo nombre contenga "bug" (ej. "Bug", "Bug Report", "Debug"), ignorando mayúsculas/minúsculas

### Requirement: Comportamiento consistente con filtros existentes
El sistema SHALL implementar la búsqueda en Prioridad y Categoría usando el mismo mecanismo que los combos de Proyecto y Asignado: `setEditable(True)`, `setInsertPolicy(NoInsert)`, y `QCompleter` con `MatchContains`.

#### Scenario: Mismo comportamiento que filtro de Proyecto
- **WHEN** el usuario interactúa con los combos de Prioridad o Categoría
- **THEN** la experiencia de búsqueda es idéntica a la del combo de Proyecto: escribir filtra, Enter selecciona, Escape cierra

### Requirement: Filtro de Asignado a con multiselección
El sistema SHALL permitir seleccionar múltiples usuarios en el filtro "Asignado a" del `FilterBar`. El widget de asignado SHALL reemplazar el `QComboBox` actual por un control que muestre checkboxes para cada miembro del proyecto y permita marcar/desmarcar varios.

#### Scenario: Seleccionar múltiples asignados
- **WHEN** el usuario abre el dropdown de "Asignado a" y marca los checkboxes de "Ana" y "Carlos"
- **THEN** el botón del filtro muestra "2 seleccionados" o los nombres de los seleccionados
- **AND** la tabla se refresca mostrando tareas asignadas a Ana O a Carlos

#### Scenario: Incluir "Sin asignar" junto con miembros
- **WHEN** el usuario marca "Sin asignar" y también marca "Ana"
- **THEN** la tabla muestra tareas sin asignar Y tareas asignadas a Ana

#### Scenario: Incluir "Asignado a mí" junto con miembros
- **WHEN** el usuario marca "Asignado a mí" y también marca "Carlos"
- **THEN** la tabla muestra tareas asignadas al usuario actual Y tareas asignadas a Carlos

#### Scenario: Desmarcar todos los asignados
- **WHEN** el usuario desmarca todos los checkboxes en el filtro "Asignado a"
- **THEN** el filtro equivale a "(Todos)" — no se aplica filtro por asignado
- **AND** la tabla muestra tareas de cualquier asignado

#### Scenario: Persistencia de múltiples asignados
- **WHEN** el usuario selecciona "Ana" y "Carlos", cierra la app y la vuelve a abrir
- **THEN** el filtro "Asignado a" muestra a Ana y Carlos como seleccionados
- **AND** la tabla muestra las tareas filtradas por esos asignados

### Requirement: Integración de multiselección con RedmineClient
El `RedmineClient.get_issues()` SHALL aceptar una lista de IDs de asignado y construir los parámetros de consulta adecuados para filtrar por múltiples asignados.

#### Scenario: Filtro con un solo asignado
- **WHEN** `get_issues()` recibe `assigned_to_id=[5]`
- **THEN** envía `assigned_to_id=5` a la API

#### Scenario: Filtro con múltiples asignados
- **WHEN** `get_issues()` recibe `assigned_to_id=[5, 8, 12]`
- **THEN** el sistema aplica el filtro para mostrar tareas de cualquiera de esos asignados (OR lógico)
- **AND** si la API no soporta múltiples valores, el sistema obtiene todas las tareas y filtra client-side por los IDs indicados

#### Scenario: Filtro con "Sin asignar" y miembros
- **WHEN** `get_issues()` recibe `assigned_to_id=["!*", 5]`
- **THEN** el sistema aplica un filtro OR: tareas sin asignar O asignadas al usuario 5

#### Scenario: Combinación con otros filtros
- **WHEN** el filtro de asignado tiene múltiples valores y también hay filtros de estado, fecha y prioridad activos
- **THEN** todos los filtros se combinan con AND (el filtro de asignado opera como OR internamente y luego se cruza con AND con los demás)

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
