## Purpose

Definir el manejo de errores de la API de Redmine: visualización e interpretación de errores de validación al crear, editar y en cambios rápidos, diagnóstico de proyectos sin trackers, registro de errores de API en el log de diagnóstico, y tracker modificable en edición.

## Requirements

### Requirement: Visualizar errores de validación de la API
Cuando la API de Redmine rechace una operación con errores de validación, el sistema SHALL mostrar dichos errores al usuario. Además, el sistema SHALL interpretar el caso en el que los errores indiquen campos en blanco de Proyecto, Tipo y Estado, comprobando si el proyecto carece de trackers (tipos) definidos y mostrando un mensaje explicativo y accionable en lugar del texto crudo del servidor.

#### Scenario: Errores de validación genéricos
- **WHEN** el usuario envía una tarea o la edita con datos que Redmine rechaza (HTTP 422)
- **THEN** el sistema muestra un diálogo de error con los mensajes de validación devueltos por la API (ej. "Subject cannot be blank")

#### Scenario: Error de red al crear tarea
- **WHEN** ocurre un error de conexión (timeout, desconexión) al enviar la tarea
- **THEN** el sistema muestra un diálogo de error indicando el problema de conexión

#### Scenario: Éxito en la creación muestra confirmación
- **WHEN** la tarea se crea correctamente en Redmine (HTTP 201)
- **THEN** el sistema recarga la lista de issues y no muestra ningún mensaje de error

#### Scenario: Errores de campos en blanco por proyecto sin trackers
- **WHEN** un alta de tarea devuelve 422 con errores de vacío para Proyecto, Tipo y Estado
- **AND** el proyecto no tiene trackers definidos
- **THEN** el sistema muestra un mensaje explicativo y accionable (el proyecto no tiene tipos/trackers; configurarlos en Redmine o elegir otro proyecto)
- **AND** no muestra únicamente el texto crudo del servidor

#### Scenario: Errores de campos en blanco con trackers existentes
- **WHEN** un alta de tarea devuelve 422 con errores de vacío para Proyecto, Tipo y Estado
- **AND** el proyecto sí tiene trackers definidos
- **THEN** el sistema muestra el detalle de los errores añadiendo el contexto del proyecto y el tracker enviados

### Requirement: Errores de validación en edición de tareas
El sistema SHALL capturar y mostrar errores de validación también al actualizar tareas existentes (HTTP 422 en PUT).

#### Scenario: Error de validación al editar tarea
- **WHEN** el usuario modifica una tarea y Redmine rechaza la actualización (HTTP 422)
- **THEN** el sistema muestra un diálogo de error con los mensajes de validación de la API

### Requirement: Errores de validación en cambios rápidos
El sistema SHALL capturar `RedmineValidationError` en las operaciones de cambio rápido (menú contextual de progreso, estado y asignación) y mostrar un diálogo con los mensajes de validación devueltos por la API. El mensaje SHALL ser descriptivo e indicar la causa probable del rechazo.

#### Scenario: Error de validación al cambiar estado desde menú contextual
- **WHEN** el usuario intenta cambiar el estado de una tarea a uno no permitido por el workflow y Redmine devuelve HTTP 422
- **THEN** el sistema muestra un mensaje explicativo: "Redmine rechazó el cambio de estado. Esto suele ocurrir porque el estado seleccionado no está permitido en el workflow de esta tarea." seguido del detalle de errores

#### Scenario: Error de validación al completar tarea
- **WHEN** el usuario pulsa "Completada" y Redmine devuelve HTTP 422
- **THEN** el sistema muestra un mensaje explicativo con las causas probables (estado no válido para el tracker, transición no permitida, fecha no válida) y el detalle de errores

#### Scenario: Error de validación al cambiar progreso
- **WHEN** el usuario cambia el progreso desde el menú contextual y Redmine devuelve HTTP 422
- **THEN** el sistema muestra un diálogo con los mensajes de validación de la API

### Requirement: Tracker modificable en edición
El sistema SHALL permitir al usuario modificar el campo tracker (tipo de tarea) desde el diálogo de edición de una tarea existente, con el mismo comportamiento de búsqueda que en creación.

#### Scenario: Cambiar tracker en modo edición
- **WHEN** el usuario abre una tarea existente en modo edición
- **THEN** el combo de tracker es editable y permite seleccionar cualquier tracker disponible
- **AND** el tracker actual de la tarea aparece preseleccionado

#### Scenario: Guardar cambio de tracker
- **WHEN** el usuario cambia el tracker y presiona OK
- **THEN** la tarea se actualiza en Redmine con el nuevo tracker

### Requirement: Diagnóstico de proyecto sin trackers
Cuando un 422 de alta contenga errores de vacío para Proyecto/Tipo/Estado, el sistema SHALL consultar los trackers del proyecto mediante `get_project_trackers` y, si el proyecto no tiene ninguno, SHALL mostrar un mensaje explicativo accionable en lugar del texto crudo; si tiene trackers, SHALL mostrar el detalle añadiendo el proyecto y el tracker enviados.

#### Scenario: Consulta de trackers tras 422
- **WHEN** el alta devuelve 422 con errores de vacío para Proyecto/Tipo/Estado
- **THEN** el sistema consulta los trackers del proyecto (`get_project_trackers`)

#### Scenario: Proyecto sin trackers
- **WHEN** la consulta confirma que el proyecto no tiene trackers
- **THEN** el sistema muestra un mensaje explicativo y accionable
- **AND** registra el suceso en el log de diagnóstico

#### Scenario: Proyecto con trackers
- **WHEN** la consulta confirma que el proyecto tiene trackers
- **THEN** el sistema muestra el detalle de los errores añadiendo el proyecto y el tracker enviados

### Requirement: Trackers del proyecto en el diálogo de creación
Al seleccionar un proyecto en el diálogo de creación, el combo de tracker SHALL poblarse con los trackers de ese proyecto. Si el proyecto no tiene trackers, SHALL avisarse de forma destacada y SHALL impedirse el envío hasta que el usuario elija otro proyecto o se configuren trackers en Redmine.

#### Scenario: Selección de proyecto con trackers
- **WHEN** el usuario selecciona un proyecto que tiene trackers en el diálogo de creación
- **THEN** el combo de tracker se puebla con los trackers de ese proyecto

#### Scenario: Selección de proyecto sin trackers
- **WHEN** el usuario selecciona un proyecto que no tiene trackers en el diálogo de creación
- **THEN** el sistema avisa de forma destacada de que el proyecto no tiene trackers
- **AND** el envío queda impedido (botón OK deshabilitado) hasta elegir otro proyecto o configurar trackers

### Requirement: Registro de errores de API
Los errores de validación y de red de la API SHALL registrarse en el log de diagnóstico.

#### Scenario: Error de validación registrado
- **WHEN** la API devuelve un error de validación
- **THEN** el suceso se registra en el log de diagnóstico con su contexto

#### Scenario: Error de red registrado
- **WHEN** una petición a la API falla por red o conexión
- **THEN** el suceso se registra en el log de diagnóstico con su contexto
