## ADDED Requirements

### Requirement: Menú contextual de progreso con incrementos del 20%
El sistema SHALL mostrar un menú contextual al hacer clic derecho sobre la columna "Progreso %" de una tarea, con las opciones 0%, 20%, 40%, 60%, 80% y 100%.

#### Scenario: Cambiar progreso al 60% con confirmación
- **WHEN** el usuario hace clic derecho en la celda de progreso de la tarea #42 y selecciona "60%"
- **THEN** se muestra un diálogo de confirmación "¿Cambiar progreso de tarea #42 al 60%?" y, al aceptar, la tarea se actualiza a 60%

#### Scenario: Cancelar cambio de progreso
- **WHEN** el usuario hace clic derecho, selecciona "40%" y pulsa "No" en el diálogo de confirmación
- **THEN** la tarea no se modifica

#### Scenario: Progreso actual resaltado
- **WHEN** el menú contextual de progreso se abre para una tarea con progreso actual 80%
- **THEN** la opción "80%" aparece marcada o resaltada visualmente

### Requirement: Actualización vía API al cambiar progreso
El sistema SHALL llamar a `update_issue(issue_id, done_ratio=N)` al confirmar un cambio de progreso, y refrescar la tabla tras la actualización exitosa.

#### Scenario: Progreso actualizado correctamente
- **WHEN** el usuario confirma el cambio de progreso al 100%
- **THEN** la tabla se refresca y la barra de progreso muestra 100% en verde
