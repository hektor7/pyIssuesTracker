## ADDED Requirements

### Requirement: Menú contextual de asignación rápida
El sistema SHALL mostrar un menú contextual al hacer clic derecho sobre la columna "Asignado a" de una tarea, con la opción "Asignarme a mí" seguida de un separador y las personas frecuentes. Al seleccionar cualquier opción, se mostrará un diálogo de confirmación antes de ejecutar el cambio.

#### Scenario: Asignarse a uno mismo con confirmación
- **WHEN** el usuario hace clic derecho en la celda "Asignado a", selecciona "Asignarme a mí" y confirma en el diálogo
- **THEN** la tarea se asigna al usuario actual y la tabla se refresca

#### Scenario: Cancelar asignación
- **WHEN** el usuario hace clic derecho, selecciona una persona y pulsa "No" en el diálogo de confirmación
- **THEN** la tarea no se modifica

#### Scenario: Sin personas frecuentes
- **WHEN** el usuario hace clic derecho y no hay personas frecuentes registradas
- **THEN** se muestra la opción deshabilitada "No hay personas frecuentes" después del separador

### Requirement: Almacenamiento automático de personas frecuentes
El sistema SHALL almacenar en QSettings los IDs de los últimos 5 usuarios distintos a los que se ha asignado una tarea, excluyendo al usuario actual. La lista debe mantener el más reciente al inicio y no contener duplicados.

#### Scenario: Registrar nueva asignación
- **WHEN** se asigna una tarea al usuario con ID 7 (distinto al usuario actual)
- **THEN** el ID 7 se añade al frente de la lista de frecuentes, y si la lista excede 5 elementos, el último se elimina

#### Scenario: Reasignar a persona ya frecuente
- **WHEN** se asigna una tarea al usuario ID 3, que ya está en la lista de frecuentes
- **THEN** el ID 3 se mueve al frente de la lista, sin duplicados

#### Scenario: No registrar asignación a uno mismo
- **WHEN** el usuario se asigna una tarea a sí mismo
- **THEN** la lista de personas frecuentes no se modifica
