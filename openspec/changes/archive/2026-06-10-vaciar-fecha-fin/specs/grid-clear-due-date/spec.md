## ADDED Requirements

### Requirement: Limpiar fecha fin desde menú contextual del grid
El sistema DEBE permitir al usuario vaciar el campo `due_date` de una tarea mediante una opción en el menú contextual (botón derecho) cuando el clic se produce sobre la columna de fecha fin en el grid principal.

#### Scenario: Limpiar fecha fin con menú contextual
- **WHEN** el usuario hace clic derecho sobre la celda de la columna "Fecha fin" de una tarea que tiene una fecha establecida
- **THEN** el sistema muestra un menú contextual que incluye la opción "Limpiar fecha fin"
- **AND** al seleccionar "Limpiar fecha fin", el sistema actualiza la tarea en Redmine con `due_date=""` (vacío)
- **AND** el grid se refresca mostrando la celda de fecha fin vacía

#### Scenario: Menú contextual en celda vacía
- **WHEN** el usuario hace clic derecho sobre la celda de la columna "Fecha fin" de una tarea que NO tiene fecha establecida
- **THEN** el sistema muestra un menú contextual que incluye la opción "Limpiar fecha fin" deshabilitada (greyed out)

#### Scenario: Menú contextual incluye opción existente Abrir en Redmine
- **WHEN** el usuario hace clic derecho sobre la celda de la columna "Fecha fin"
- **THEN** el sistema muestra el menú contextual que incluye TANTO "Limpiar fecha fin" COMO "Abrir en Redmine"

#### Scenario: Error al limpiar fecha fin
- **WHEN** el usuario selecciona "Limpiar fecha fin" y la llamada a la API de Redmine falla
- **THEN** el sistema muestra un mensaje de error indicando que no se pudo actualizar la fecha de fin
- **AND** la fecha en el grid no se modifica
