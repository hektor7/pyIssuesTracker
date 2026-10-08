## MODIFIED Requirements

### Requirement: Actualización vía API al cambiar progreso
El sistema SHALL llamar a `update_issue(issue_id, done_ratio=N)` al confirmar un cambio de progreso, y refrescar la tabla tras la actualización exitosa.

#### Scenario: Progreso actualizado correctamente
- **WHEN** el usuario confirma el cambio de progreso al 100%
- **THEN** la tabla se refresca y la barra de progreso muestra 100% en verde

### Requirement: Menú contextual de progreso con QProgressBar
El sistema SHALL mostrar el menú contextual de progreso al hacer clic derecho sobre la barra de progreso (`QProgressBar`) de una celda. El `QProgressBar` DEBE propagar el evento `contextMenuEvent` al `QTableWidget` padre para que se muestren las opciones 0%, 20%, 40%, 60%, 80% y 100%.

#### Scenario: Clic derecho sobre QProgressBar abre el menú de progreso
- **WHEN** el usuario hace clic derecho sobre la barra de progreso de la tarea #42
- **THEN** se muestra el menú contextual con las opciones 0%, 20%, 40%, 60%, 80% y 100%
- **AND** la opción correspondiente al progreso actual aparece marcada

#### Scenario: Cambiar progreso al 60% con confirmación
- **WHEN** el usuario selecciona "60%" del menú y confirma en el diálogo
- **THEN** la tarea se actualiza a 60% de progreso

#### Scenario: Cancelar cambio de progreso
- **WHEN** el usuario selecciona "40%" y pulsa "No" en el diálogo de confirmación
- **THEN** la tarea no se modifica
