## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Filtro de Asignado a con multiselección
El sistema SHALL permitir seleccionar múltiples usuarios en el filtro "Asignado a" del `FilterBar`. El widget de asignado DEBE reemplazar el `QComboBox` actual por un control que muestre checkboxes para cada miembro del proyecto y permita marcar/desmarcar varios.

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
El `RedmineClient.get_issues()` DEBE aceptar una lista de IDs de asignado y construir los parámetros de consulta adecuados para filtrar por múltiples asignados.

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
