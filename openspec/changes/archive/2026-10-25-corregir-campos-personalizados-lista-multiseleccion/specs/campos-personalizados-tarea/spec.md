## MODIFIED Requirements

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
