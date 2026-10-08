## ADDED Requirements

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
