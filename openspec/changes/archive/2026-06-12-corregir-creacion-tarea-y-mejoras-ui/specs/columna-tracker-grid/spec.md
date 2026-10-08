## ADDED Requirements

### Requirement: Columna de tracker en la tabla de issues
El sistema SHALL mostrar una columna con el nombre del tracker (tipo de tarea) en la tabla principal de issues, ubicada después de la columna ID y antes de la columna Título.

#### Scenario: Visualización del tracker en el grid
- **WHEN** se cargan issues en la tabla principal
- **THEN** cada fila muestra el nombre del tracker (Bug, Feature, Support, etc.) en la columna correspondiente

#### Scenario: Ordenación por columna tracker
- **WHEN** el usuario hace clic en el encabezado de la columna tracker
- **THEN** la tabla se ordena alfabéticamente por el nombre del tracker

#### Scenario: Tooltip de fila incluye el tracker
- **WHEN** el usuario posa el cursor sobre una fila
- **THEN** el tooltip HTML muestra el nombre del tracker como parte de la información de la tarea (ya existente, se verifica que siga mostrándose)

#### Scenario: Compatibilidad con resaltado de prioridad
- **WHEN** una tarea tiene prioridad Inmediata o Urgente
- **THEN** la celda del tracker también se resalta con el color de fondo rojo correspondiente a la fila completa
