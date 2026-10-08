## ADDED Requirements

### Requirement: Vaciar fecha fin al desmarcar checkbox en diálogo
El sistema DEBE vaciar (resetear) el valor del `QDateEdit` de fecha fin cuando el usuario desmarca el checkbox "Fecha fin:" en el diálogo de edición/alta de tareas.

#### Scenario: Desmarcar checkbox limpia el campo de fecha
- **WHEN** el usuario desmarca el checkbox "Fecha fin:" en el diálogo de edición/alta
- **THEN** el `QDateEdit` de fecha fin se deshabilita
- **AND** el `QDateEdit` muestra la fecha actual (`date.today()`) como valor por defecto

#### Scenario: Marcar checkbox restaura fecha por defecto
- **WHEN** el usuario vuelve a marcar el checkbox "Fecha fin:" tras haberlo desmarcado
- **THEN** el `QDateEdit` de fecha fin se habilita
- **AND** el `QDateEdit` mantiene la fecha actual (`date.today()`) como valor

#### Scenario: Guardar con checkbox desmarcado envía fecha vacía
- **WHEN** el usuario desmarca el checkbox "Fecha fin:", rellena el resto de campos obligatorios y guarda el formulario
- **THEN** el sistema envía `due_date=""` a Redmine
- **AND** la tarea se crea/actualiza sin fecha de fin

#### Scenario: Guardar con checkbox marcado envía la fecha seleccionada
- **WHEN** el usuario marca el checkbox "Fecha fin:", selecciona una fecha en el `QDateEdit` y guarda el formulario
- **THEN** el sistema envía la fecha seleccionada en formato `yyyy-MM-dd` a Redmine
- **AND** la tarea se crea/actualiza con la fecha de fin correspondiente

#### Scenario: Editar tarea con fecha existente y desmarcar
- **WHEN** el usuario abre una tarea que tiene `due_date` establecido, desmarca el checkbox "Fecha fin:" y guarda
- **THEN** el `QDateEdit` se deshabilita y muestra la fecha actual
- **AND** el sistema envía `due_date=""` a Redmine, eliminando la fecha de fin previamente establecida
