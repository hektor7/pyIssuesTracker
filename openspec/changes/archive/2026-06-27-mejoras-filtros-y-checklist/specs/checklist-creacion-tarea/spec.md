## ADDED Requirements

### Requirement: El checklist se muestra en el diálogo de creación de tarea
El sistema SHALL mostrar el widget de checklist en el diálogo de nueva tarea (modo alta), permitiendo al usuario añadir, marcar y eliminar items del checklist antes de guardar la tarea.

#### Scenario: Checklist visible al abrir diálogo de nueva tarea
- **WHEN** el usuario abre el diálogo "Nueva tarea"
- **THEN** el grupo "Checklist" es visible con un campo para añadir items y una lista vacía
- **AND** el usuario puede añadir items de checklist escribiendo texto y pulsando Enter o el botón "+"

#### Scenario: Añadir items al checklist en modo creación
- **WHEN** el usuario escribe "Revisar documentación" en el campo de nuevo item del checklist y pulsa Enter
- **THEN** el item aparece en la lista con un checkbox desmarcado
- **AND** el item se almacena en la lista temporal de items pendientes

#### Scenario: Eliminar items del checklist en modo creación
- **WHEN** el usuario hace clic derecho sobre un item del checklist en modo creación y selecciona "Eliminar"
- **THEN** el item desaparece de la lista visual
- **AND** el item se elimina de la lista temporal de items pendientes

#### Scenario: Items del checklist se crean al guardar la tarea nueva
- **WHEN** el usuario rellena los campos obligatorios, añade 3 items al checklist, y pulsa "Guardar"
- **THEN** el sistema crea la tarea en Redmine
- **AND** tras confirmar la creación, el sistema crea los 3 items del checklist asociados al nuevo issue_id
- **AND** si algún item falla al crearse, se muestra un aviso pero la tarea permanece guardada

#### Scenario: Checklist vacío no causa errores al guardar
- **WHEN** el usuario guarda una tarea nueva sin añadir ningún item al checklist
- **THEN** la tarea se crea normalmente sin errores relacionados con el checklist

### Requirement: Marcar/desmarcar items no aplica en modo creación
El sistema SHALL ignorar las acciones de toggle (marcar/desmarcar) en items del checklist cuando el diálogo está en modo creación, ya que los items aún no tienen un ID en Redmine.

#### Scenario: Click en checkbox de item en modo creación
- **WHEN** el usuario hace clic en el checkbox de un item del checklist en modo creación
- **THEN** el sistema ignora la acción (no intenta actualizar el item en Redmine)
- **AND** el checkbox no cambia de estado visualmente
