## ADDED Requirements

### Requirement: Selector de asignado en diálogo de nueva tarea
El diálogo de nueva tarea SHALL incluir un campo editable con búsqueda para seleccionar el usuario asignado, poblado con los miembros del proyecto seleccionado.

#### Scenario: Combo poblado con miembros del proyecto
- **WHEN** el usuario abre el diálogo de nueva tarea
- **AND** hay un proyecto seleccionado
- **THEN** el combo "Asignado a" se puebla con los miembros de ese proyecto
- **AND** el combo permite escribir para filtrar y buscar entre los miembros

#### Scenario: Asignación al crear tarea
- **WHEN** el usuario selecciona un miembro en el combo "Asignado a"
- **AND** el usuario rellena el resto de campos obligatorios
- **AND** el usuario hace clic en "Aceptar"
- **THEN** la tarea se crea con el asignado seleccionado

#### Scenario: Sin asignado seleccionado
- **WHEN** el usuario no selecciona ningún miembro en "Asignado a"
- **AND** el usuario crea la tarea
- **THEN** la tarea se crea sin asignado

#### Scenario: Recarga de miembros al cambiar de proyecto
- **WHEN** el usuario cambia el proyecto seleccionado en el diálogo
- **THEN** el combo "Asignado a" se recarga con los miembros del nuevo proyecto
- **AND** la selección actual se resetea
