## Purpose

Definir el soporte de campos personalizados de Redmine en PyIssuesTracker: modelo de datos, obtención y parseo, edición en el diálogo de tarea según el formato del campo y envío en creación y actualización.
## Requirements
### Requirement: Modelo de datos de campos personalizados
El `RedmineClient` SHALL exponer una dataclass `RedmineCustomField` que represente la definición de un campo personalizado de un proyecto, con los atributos: `id`, `name`, `field_format`, `is_required`, `multiple`, `possible_values`, `default_value`, `visible` y `editable`.

#### Scenario: Construcción de un campo personalizado
- **WHEN** se mapea una entrada de `issue_custom_fields` con id 3, name "Severidad", field_format "list" y possible_values ["Baja", "Alta"]
- **THEN** el `RedmineCustomField` resultante tiene `id=3`, `name="Severidad"`, `field_format="list"` y `possible_values=["Baja", "Alta"]`

### Requirement: Obtención de los campos personalizados del proyecto
El `RedmineClient` SHALL exponer un método `get_project_custom_fields(project_id)` que realice `GET /projects/{id}.json?include=issue_custom_fields` y devuelva la lista de campos personalizados definidos en ese proyecto.

#### Scenario: Proyecto con campos personalizados
- **WHEN** se llama a `get_project_custom_fields(7)` y el proyecto define tres campos personalizados
- **THEN** el método devuelve una lista con tres `RedmineCustomField` correspondientes a las entradas de `issue_custom_fields`

#### Scenario: Proyecto sin campos personalizados
- **WHEN** el proyecto no define ningún campo personalizado
- **THEN** el método devuelve una lista vacía y no lanza excepción

#### Scenario: Error al obtener los campos
- **WHEN** la llamada al proyecto falla o el proyecto no es accesible
- **THEN** el error se propaga como `RedmineError` y la interfaz oculta la sección de campos personalizados sin romper el diálogo

### Requirement: Parseo de los valores de campos personalizados del issue
El sistema SHALL parsear el array `custom_fields` de la respuesta de un issue y exponer los valores actuales. `RedmineIssue` SHALL incluir un campo `custom_fields` como diccionario de `id` de campo a valor, y `get_issue_with_journals` SHALL incluir los valores actuales del issue.

#### Scenario: Issue con valores de campos personalizados
- **WHEN** la API devuelve `custom_fields` con `[{"id": 3, "value": "Alta"}, {"id": 4, "value": "texto"}]`
- **THEN** `RedmineIssue.custom_fields` es `{3: "Alta", 4: "texto"}`

#### Scenario: Campo personalizado con valor múltiple
- **WHEN** la API devuelve un campo con `value` como lista
- **THEN** el valor almacenado en el diccionario es esa lista

#### Scenario: Issue sin campos personalizados
- **WHEN** la respuesta del issue no incluye la clave `custom_fields`
- **THEN** `RedmineIssue.custom_fields` es un diccionario vacío

#### Scenario: Detalle de issue incluye valores personalizados
- **WHEN** se obtiene un issue mediante `get_issue_with_journals`
- **THEN** el dict devuelto incluye `_custom_fields` con los valores actuales del issue

### Requirement: Envío de campos personalizados en creación y actualización
`create_issue` y `update_issue` SHALL aceptar campos personalizados y enviarlos en el payload de la API como una lista de objetos `{"id": N, "value": X}` dentro de `{"issue": {...}}`.

#### Scenario: Creación con campos personalizados
- **WHEN** se llama a `create_issue(..., custom_fields={3: "Alta"})`
- **THEN** el payload enviado a `POST /issues.json` contiene `{"issue": {..., "custom_fields": [{"id": 3, "value": "Alta"}]}}`

#### Scenario: Actualización con campos personalizados
- **WHEN** se llama a `update_issue(42, custom_fields={3: "Baja"})`
- **THEN** el payload enviado a `PUT /issues/42.json` contiene `{"issue": {"custom_fields": [{"id": 3, "value": "Baja"}]}}`

#### Scenario: Limpiar un campo personalizado
- **WHEN** se envía una entrada con `value` igual a cadena vacía
- **THEN** la entrada se incluye en el payload con `value: ""` para permitir limpiar el campo

#### Scenario: Sin campos personalizados
- **WHEN** se llama a `create_issue` o `update_issue` sin `custom_fields` o con un diccionario vacío
- **THEN** la clave `custom_fields` no se incluye en el payload

### Requirement: Sección de campos personalizados en el diálogo de tarea
El `TaskDialog` SHALL mostrar una sección "Campos personalizados" situada ANTES del grupo "Comentarios". La sección SHALL cargar los campos del proyecto seleccionado, SHALL ocultarse cuando el proyecto no tiene campos y SHALL recargarse al cambiar de proyecto tanto en alta como en edición.

#### Scenario: Proyecto con campos personalizados
- **WHEN** se abre el `TaskDialog` con un proyecto que tiene campos personalizados
- **THEN** la sección "Campos personalizados" es visible y contiene un control por cada campo definido en el proyecto
- **AND** la sección aparece antes del grupo "Comentarios"

#### Scenario: Proyecto sin campos personalizados
- **WHEN** el proyecto seleccionado no tiene campos personalizados
- **THEN** la sección "Campos personalizados" no se muestra

#### Scenario: Recarga al cambiar de proyecto
- **WHEN** el usuario cambia el proyecto seleccionado en el `TaskDialog`
- **THEN** la sección de campos personalizados se recarga con los campos del nuevo proyecto

#### Scenario: Carga de valores actuales en edición
- **WHEN** se abre el `TaskDialog` en modo edición para un issue que tiene valores en sus campos personalizados
- **THEN** cada control muestra el valor actual del issue para su campo

### Requirement: Edición de valores según el formato del campo
El `TaskDialog` SHALL construir el control de edición de cada campo personalizado en función de su `field_format` y SHALL soportar campos de valor múltiple. Los textos de las opciones SHALL mostrarse elididos cuando no quepan, con tooltip del valor completo, y los campos sin `possible_values` SHALL mostrarse deshabilitados con un texto de ayuda. Los campos de lista cuyo valor previo no sea representable SHALL omitirse del payload para conservar el valor existente en Redmine.

#### Scenario: Campo de tipo texto corto
- **WHEN** el campo tiene `field_format` "string"
- **THEN** se muestra un `QLineEdit`

#### Scenario: Campo de tipo texto largo
- **WHEN** el campo tiene `field_format` "text"
- **THEN** se muestra un `QPlainTextEdit`

#### Scenario: Campo numérico
- **WHEN** el campo tiene `field_format` "int" o "float"
- **THEN** se muestra un control numérico adecuado al tipo

#### Scenario: Campo de fecha
- **WHEN** el campo tiene `field_format` "date"
- **THEN** se muestra un `QDateEdit` con opción de dejarlo vacío

#### Scenario: Campo booleano
- **WHEN** el campo tiene `field_format` "bool"
- **THEN** se muestra un `QCheckBox`

#### Scenario: Campo de lista de selección simple
- **WHEN** el campo tiene `field_format` "list", `multiple` falso y `possible_values` no está vacío
- **THEN** se muestra un `QComboBox` con una opción vacía inicial y los valores posibles
- **AND** el combo tiene un ancho mínimo razonable y elide por la derecha los textos que no caben
- **AND** cada opción expone un tooltip con su valor completo

#### Scenario: Campo de lista de selección simple sin opciones
- **WHEN** el campo tiene `field_format` "list" y `possible_values` está vacío
- **THEN** el control se muestra deshabilitado con un texto de ayuda que indica que no hay opciones disponibles

#### Scenario: Campo de valor múltiple
- **WHEN** el campo tiene `multiple` verdadero
- **THEN** se muestra un selector multiselección plegado con un botón de resumen
- **AND** al desplegarlo se muestran las `possible_values` como opciones con checkbox
- **AND** el control permite seleccionar y conservar más de un valor

#### Scenario: Resumen del selector multiselección
- **WHEN** el selector multiselección no tiene ninguna opción marcada
- **THEN** el botón no muestra ningún valor
- **WHEN** tiene exactamente una opción marcada
- **THEN** el botón muestra el texto de esa opción, elidido si no cabe
- **WHEN** tiene dos o más opciones marcadas
- **THEN** el botón muestra un resumen con el número de opciones seleccionadas
- **AND** en todos los casos el tooltip del botón contiene los valores completos seleccionados

#### Scenario: Búsqueda en el selector multiselección
- **WHEN** el usuario escribe en el campo de búsqueda del popup
- **THEN** solo se muestran las opciones cuyo texto contiene la subcadena, sin distinguir mayúsculas
- **AND** la búsqueda no altera las opciones ya marcadas
- **AND** el campo de búsqueda se vacía al abrir y al cerrar el popup

#### Scenario: Textos largos en el selector multiselección
- **WHEN** una opción del selector multiselección no cabe en el ancho disponible
- **THEN** su texto se muestra elidido por la derecha
- **AND** la opción expone un tooltip con el texto completo

#### Scenario: Selector multiselección sin opciones
- **WHEN** el campo tiene `multiple` verdadero y `possible_values` está vacío
- **THEN** el selector se muestra deshabilitado con un texto de ayuda que indica que no hay opciones disponibles

#### Scenario: Formato no soportado
- **WHEN** el campo tiene un `field_format` no contemplado y `multiple` falso
- **THEN** se muestra un control de texto libre y la carga no falla

#### Scenario: Formato no soportado con valor múltiple
- **WHEN** el campo tiene un `field_format` no contemplado y `multiple` verdadero
- **THEN** se muestra el selector multiselección, porque la condición `multiple` tiene precedencia sobre el formato

#### Scenario: Vaciado de un campo de valor múltiple con valor previo
- **WHEN** el campo tiene `multiple` verdadero, el issue tenía valores previos representables y el usuario desmarca todas las opciones
- **THEN** el valor se serializa como lista vacía para limpiar el campo en Redmine

#### Scenario: Campo de lista con valor previo no representable
- **WHEN** el campo es de lista simple o de valor múltiple y el valor previo del issue no está entre las `possible_values` (incluido el caso de `possible_values` vacío)
- **THEN** el campo no se incluye en el payload y el valor existente se conserva en Redmine

### Requirement: Marcado de campos obligatorios y valor por defecto
El `TaskDialog` SHALL indicar visualmente los campos personalizados con `is_required` verdadero y SHALL aplicar el `default_value` del campo cuando exista.

#### Scenario: Campo obligatorio
- **WHEN** un campo personalizado tiene `is_required` verdadero
- **THEN** su etiqueta indica que es obligatorio

#### Scenario: Valor por defecto
- **WHEN** un campo personalizado define `default_value` y no hay valor previo del issue
- **THEN** el control se inicializa con ese valor por defecto

### Requirement: Envío de los campos personalizados al guardar
Al aceptar el `TaskDialog`, el sistema SHALL exponer los valores de los campos personalizados para que `MainWindow` los envíe en `create_issue` o `update_issue`, serializando cada valor según su formato.

#### Scenario: Serialización de valores
- **WHEN** se recogen los valores de los campos personalizados
- **THEN** un campo booleano se serializa como "1" o "0", un campo de fecha como fecha ISO `YYYY-MM-DD`, un campo numérico como cadena y un campo múltiple como lista de valores

#### Scenario: Envío en creación
- **WHEN** el usuario guarda una tarea nueva con campos personalizados rellenos
- **THEN** `MainWindow` incluye esos valores en la llamada a `create_issue`

#### Scenario: Envío en edición
- **WHEN** el usuario guarda los cambios de una tarea existente con campos personalizados
- **THEN** `MainWindow` incluye esos valores en la llamada a `update_issue`

#### Scenario: Campo vacío sin valor previo
- **WHEN** un campo personalizado no tiene valor y el issue no tenía valor previo
- **THEN** ese campo no se incluye en el payload enviado

