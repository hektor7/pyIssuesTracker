## ADDED Requirements

### Requirement: Preseleccionar proyecto activo al crear tarea
El sistema SHALL preseleccionar automáticamente el proyecto activo en el diálogo de nueva tarea cuando el usuario tenga un filtro de proyecto seleccionado.

#### Scenario: Preselección correcta al abrir diálogo con filtro activo
- **WHEN** el usuario tiene un proyecto seleccionado en la barra de filtros
- **AND** el usuario hace clic en "Nueva tarea"
- **THEN** el combo de proyecto del diálogo se inicializa con ese proyecto seleccionado
- **AND** las categorías del proyecto se cargan automáticamente

#### Scenario: Sin filtro de proyecto activo
- **WHEN** el usuario no tiene ningún proyecto seleccionado en la barra de filtros
- **AND** el usuario hace clic en "Nueva tarea"
- **THEN** el combo de proyecto se muestra vacío o con el valor por defecto
- **AND** el usuario puede seleccionar manualmente un proyecto

#### Scenario: Cambio de proyecto manual tras preselección
- **WHEN** el diálogo de nueva tarea se abre con un proyecto preseleccionado
- **AND** el usuario cambia manualmente a otro proyecto en el combo
- **THEN** las categorías y miembros se recargan según el nuevo proyecto seleccionado
