## Purpose

Definir la serialización del campo categoría (`category_id`) al actualizar una tarea de Redmine, evitando el envío de valores inválidos que el servidor rechaza (HTTP 422 "Category is not included in the list") y preservando el comportamiento de la creación de tareas.

## Requirements

### Requirement: Serialización válida de la categoría al actualizar una tarea
`RedmineClient.update_issue()` SHALL NOT enviar `category_id: 0`. El sistema SHALL normalizar cualquier valor *falsy* de `category_id` (`0` o `None`) a la cadena vacía `""` antes de construir el payload de `PUT /issues/:id.json`, y SHALL enviar un id positivo válido tal cual.

#### Scenario: Proyecto sin categorías al editar
- **WHEN** el usuario actualiza una tarea cuyo proyecto no tiene categorías y `category_id` vale `0`
- **THEN** el payload enviado contiene `"category_id": ""`
- **AND** el payload nunca contiene `"category_id": 0`
- **AND** Redmine no rechaza la actualización

#### Scenario: Categoría válida seleccionada
- **WHEN** el usuario actualiza una tarea y `category_id` vale `7`
- **THEN** el payload enviado contiene `"category_id": 7`

#### Scenario: Limpiar categoría existente
- **WHEN** el usuario actualiza una tarea que tenía categoría y `category_id` vale `0`
- **THEN** el payload enviado contiene `"category_id": ""`
- **AND** la categoría de la tarea queda limpia en Redmine

#### Scenario: Sin categoría en el payload
- **WHEN** se llama a `update_issue()` sin el argumento `category_id`
- **THEN** la clave `category_id` NO se incluye en el payload

### Requirement: No regresión en la creación de tareas
`create_issue()` SHALL mantener su comportamiento actual: cuando recibe `category_id=0`, NO SHALL incluir la clave `category_id` en el payload.

#### Scenario: Creación sin categoría
- **WHEN** se llama a `create_issue()` con `category_id=0`
- **THEN** el payload enviado NO incluye la clave `category_id`
