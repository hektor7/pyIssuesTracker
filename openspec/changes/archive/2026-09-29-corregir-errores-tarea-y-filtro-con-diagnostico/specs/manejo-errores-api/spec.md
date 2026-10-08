## MODIFIED Requirements

### Requirement: Visualizar errores de validación de la API

Cuando la API de Redmine rechace una operación con errores de validación, el sistema SHALL mostrar dichos errores al usuario. Además, el sistema SHALL interpretar el caso en el que los errores indiquen campos en blanco de Proyecto, Tipo y Estado, comprobando si el proyecto carece de trackers (tipos) definidos y mostrando un mensaje explicativo y accionable en lugar del texto crudo del servidor.

#### Scenario: Errores de validación genéricos

- **WHEN** Redmine devuelve errores de validación en una operación
- **THEN** el sistema muestra el detalle de los errores al usuario

#### Scenario: Errores de campos en blanco por proyecto sin trackers

- **WHEN** un alta de tarea devuelve 422 con errores de vacío para Proyecto, Tipo y Estado
- **AND** el proyecto no tiene trackers definidos
- **THEN** el sistema muestra un mensaje explicativo y accionable (el proyecto no tiene tipos/trackers; configurarlos en Redmine o elegir otro proyecto)
- **AND** no muestra únicamente el texto crudo del servidor

#### Scenario: Errores de campos en blanco con trackers existentes

- **WHEN** un alta de tarea devuelve 422 con errores de vacío para Proyecto, Tipo y Estado
- **AND** el proyecto sí tiene trackers definidos
- **THEN** el sistema muestra el detalle de los errores añadiendo el contexto del proyecto y el tracker enviados

## ADDED Requirements

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