## ADDED Requirements

### Requirement: Usuario actual primero en lista de asignación
El sistema SHALL ordenar la lista de miembros en el combo de "Asignado a" del diálogo de creación/edición de tareas, colocando al usuario actual autenticado en primera posición, inmediatamente después de la opción "(Sin asignar)".

#### Scenario: Usuario autenticado entre los miembros del proyecto
- **WHEN** el usuario actual es miembro del proyecto seleccionado
- **THEN** su nombre aparece en primera posición en el combo de asignación, después de "(Sin asignar)"

#### Scenario: Usuario autenticado no es miembro del proyecto
- **WHEN** el usuario actual no es miembro del proyecto seleccionado
- **THEN** la lista de miembros se muestra en orden alfabético después de "(Sin asignar)"

#### Scenario: Resto de miembros ordenados alfabéticamente
- **WHEN** se muestra la lista de miembros del proyecto
- **THEN** los miembros distintos al usuario actual aparecen ordenados alfabéticamente por nombre

### Requirement: Opción "(Sin asignar)" siempre al inicio
El sistema SHALL mantener la opción "(Sin asignar)" como primer elemento del combo de asignación, independientemente del orden del resto de miembros.

#### Scenario: Combo de asignación en creación de tarea
- **WHEN** se abre el diálogo de nueva tarea
- **THEN** el combo muestra "(Sin asignar)" como primera opción, seguido del usuario actual (si es miembro), y luego el resto ordenado alfabéticamente
