## MODIFIED Requirements

### Requirement: Edición de valores según el formato del campo
El `TaskDialog` SHALL construir el control de edición de cada campo personalizado en función de su `field_format` y SHALL soportar campos de valor múltiple. Los textos de las opciones SHALL mostrarse elididos cuando no quepan, con tooltip del valor completo, y los campos sin `possible_values` SHALL mostrarse deshabilitados con un texto de ayuda. La conservación del valor previo SHALL depender del tipo de control: en un campo de valor múltiple con `possible_values` no vacíos, los valores previos ausentes de las opciones SHALL inyectarse en el selector como ítems adicionales marcados y SHALL enviarse en el payload completo; en un campo de valor múltiple con `possible_values` vacío y en una lista simple cuyo valor previo no sea representable, el campo SHALL omitirse del payload para conservar el valor existente en Redmine. Un valor previo de lista simple es representable cuando es escalar y figura en `possible_values`, o cuando es una lista de exactamente un elemento presente en `possible_values`; en este último caso SHALL seleccionarse ese elemento en el combo (normalizado a escalar). Una lista simple con valor previo en forma de lista de varios elementos, o de un único elemento ausente de `possible_values`, SHALL marcarse como no representable.

Cuando la definición no se resuelva y el campo use el fallback de texto (`kind` "string" o "text"), un valor previo en forma de lista SHALL renderizarse como sus elementos unidos por `", "`, omitiendo los elementos `None` o vacíos, y nunca mediante `str(lista)`. El tipo del valor previo SHALL conservarse al serializar: si el usuario acepta sin modificar el texto, el payload SHALL reenviar la lista original intacta; si modifica el texto y no lo deja vacío, SHALL enviar una lista de un elemento con ese texto; si lo vacía, SHALL enviar una lista vacía `[]`. La comprobación de "sin modificar" SHALL comparar el texto crudo del widget (sin `strip`) con el texto previo exacto, o normalizar ambos lados de forma simétrica; el `strip` SHALL aplicarse solo al construir el valor final editado. Al vaciar un campo con valor previo lista, `custom_fields` SHALL enviar `[]` y no SHALL convertirlo a `""`. Escribir comas en el texto no SHALL separar elementos. Un valor previo no representable SHALL omitirse del payload siempre que esté marcado como tal, con independencia del valor serializado.

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

#### Scenario: Múltiple con valor previo parcialmente representable
- **WHEN** el campo es de valor múltiple, `possible_values` no está vacío y el valor previo del issue contiene elementos que no figuran entre las opciones
- **THEN** los elementos ausentes se inyectan en el selector como ítems adicionales marcados, sin duplicar los ya presentes
- **AND** el payload envía la lista completa, incluidos los valores inyectados

#### Scenario: Desmarcado explícito de un valor inyectado
- **WHEN** el usuario desmarca un valor inyectado en un campo de valor múltiple con `possible_values` no vacío
- **THEN** ese valor deja de enviarse en el payload
- **AND** si desmarca todos los valores, el payload envía una lista vacía como limpieza explícita

#### Scenario: Múltiple sin opciones con valor previo
- **WHEN** el campo es de valor múltiple y `possible_values` está vacío
- **THEN** el campo se omite del payload y el valor existente se conserva en Redmine

#### Scenario: Lista simple con valor previo escalar fuera de las opciones
- **WHEN** el campo es de lista simple y el valor previo del issue es escalar y no está entre las `possible_values`
- **THEN** el campo se omite del payload y el valor existente se conserva en Redmine

#### Scenario: Fallback de texto con valor previo lista
- **WHEN** un campo sin definición resuelta usa `kind` "string" o "text" y su valor previo es `["Petición de mejora / usabilidad", "Otra"]`
- **THEN** el control muestra `Petición de mejora / usabilidad, Otra`
- **AND** el texto no contiene corchetes, comillas ni el `repr` de la lista

#### Scenario: Aceptar sin cambios un campo de texto con valor previo lista
- **WHEN** el campo usa el fallback de texto, el valor previo es una lista y el usuario acepta sin modificar el texto mostrado
- **THEN** el payload reenvía la lista original intacta, elemento por elemento

#### Scenario: Aceptar sin cambios una lista con espacios
- **WHEN** el campo usa el fallback de texto, el valor previo es `[" A", "B"]` y el usuario acepta sin modificar el texto mostrado
- **THEN** el payload reenvía la lista original `[" A", "B"]`, incluidos los espacios de sus elementos
- **AND** la comparación para decidir si el usuario editó el texto se hace entre el texto crudo del widget y el render previo exacto, sin `strip`; `strip` se aplica únicamente al construir el valor final cuando el usuario sí lo editó.

#### Scenario: Editar el texto de un campo con valor previo lista
- **WHEN** el campo usa el fallback de texto, el valor previo es una lista y el usuario modifica el texto y no lo deja vacío
- **THEN** el payload envía una lista de un elemento con el texto editado
- **AND** el texto con comas no se divide en varios elementos

#### Scenario: Vaciar un campo de texto con valor previo lista
- **WHEN** el campo usa el fallback de texto, el valor previo es una lista y el usuario vacía el texto
- **THEN** `_read_custom_field_value` produce `[]` y `custom_fields` envía una lista vacía `[]`
- **AND** no envía una cadena vacía, aunque el control sea de texto

#### Scenario: Lista simple con un único valor previo en forma de lista válido
- **WHEN** el campo tiene `field_format` "list", `multiple` falso, `possible_values` contiene el valor y el valor previo es una lista de exactamente un elemento
- **THEN** el combo selecciona ese valor (normalizado a escalar)
- **AND** el campo se trata como representable y se envía ese valor en el payload

#### Scenario: Lista simple con valor previo en forma de lista no representable
- **WHEN** el campo tiene `field_format` "list", `multiple` falso y el valor previo es una lista con varios elementos, o con un único elemento que no figura en `possible_values`
- **THEN** el campo se marca como no representable
- **AND** se omite del payload y el valor existente se conserva en Redmine

#### Scenario: Lista sin opciones con valor previo no vacío
- **WHEN** el campo es `list` o `multiple` sin `possible_values` y tiene un valor previo no vacío
- **THEN** el campo se marca como no representable
- **AND** se omite del payload y el valor existente se conserva en Redmine

#### Scenario: String legítimo con corchetes
- **WHEN** el valor previo es la cadena `"['A']"`
- **THEN** se trata como texto y se muestra tal cual
- **AND** no se reconstruye como lista ni se reinterpreta con `ast` o expresiones regulares

#### Scenario: Regresión de strings normales y múltiples representables
- **WHEN** el campo es de texto con un valor previo escalar o es un múltiple con `possible_values` no vacíos
- **THEN** el renderizado y el payload mantienen su comportamiento anterior
- **AND** los múltiples con valores inyectables siguen enviando la lista completa

### Requirement: Payload y alineación con la definición
El payload SHALL permanecer sin cambios cuando la resolución no aporte información nueva. Cuando la definición de administrador aporte `is_required` o `default_value`, el diálogo SHALL alinearse intencionadamente con Redmine mostrando el asterisco de obligatorio y aplicando el valor por defecto en altas. En una tarea existente sin modificar, los valores representables SHALL enviarse sin cambios; los valores previos de un campo `multiple` con `possible_values` no vacíos que no figuren entre las opciones SHALL inyectarse en el widget como ítems marcados y SHALL enviarse completos en el payload; un campo `multiple` con `possible_values` vacío y una lista simple con valor previo no representable (escalar ausente de las opciones, lista de varios elementos o lista de un único elemento ausente) SHALL omitirse del payload para conservar el valor existente en Redmine. Una lista simple con una lista previa de exactamente un elemento presente en `possible_values` SHALL seleccionar ese elemento y enviarlo como escalar.

La degradación no SHALL alterar ni el tipo ni el valor previo. En particular, un valor previo en forma de lista en un campo cuyo control es de texto libre SHALL reenviarse como lista cuando el usuario no lo modifique, y nunca como el texto del `repr` de Python. Al vaciar un campo degradado con valor previo lista, el payload SHALL contener `[]` y nunca `""`. Un campo marcado como no representable SHALL omitirse del payload siempre, no solo cuando su valor serializado quede vacío.

#### Scenario: Payload sin cambios si la definición no aporta información nueva
- **WHEN** el usuario abre una tarea existente y acepta sin modificar los campos personalizados
- **AND** la definición solo aporta formato, multiplicidad u opciones
- **THEN** los valores enviados coinciden con los valores previos representables
- **AND** los valores no representables se conservan según su tipo: inyección para los múltiples con opciones y omisión del payload para el resto

#### Scenario: Múltiple con valor previo parcialmente representable
- **WHEN** un campo `multiple` con `possible_values` no vacíos tiene valores previos y alguno de ellos no figura entre las opciones
- **THEN** los valores ausentes se inyectan en el `MultiValueCombo` mediante `add_missing_items` como ítems adicionales marcados
- **AND** el payload envía la lista completa, incluidos los valores inyectados (por ejemplo `["x", "z"]`)
- **AND** los valores inyectados no se duplican si ya estaban presentes

#### Scenario: Desmarcado explícito de un valor inyectado
- **WHEN** el usuario desmarca un valor inyectado en un campo `multiple` con `possible_values` no vacíos
- **THEN** ese valor deja de enviarse en el payload
- **AND** si desmarca todos los valores, el payload envía `[]` como limpieza explícita

#### Scenario: Múltiple sin opciones con valor previo
- **WHEN** un campo `multiple` tiene `possible_values` vacío y el issue tiene valor previo
- **THEN** el widget se muestra deshabilitado y el campo se omite del payload
- **AND** el valor almacenado en Redmine no se borra

#### Scenario: Lista simple con valor previo escalar fuera de las opciones
- **WHEN** una lista simple tiene un valor previo escalar que no figura en `possible_values`
- **THEN** el campo se omite del payload
- **AND** el valor almacenado en Redmine no se borra

#### Scenario: Obligatoriedad aportada por la definición
- **WHEN** la definición de administrador marca un campo con `is_required=True`
- **THEN** el diálogo muestra el asterisco de obligatorio en su etiqueta
- **AND** se mantiene la validación existente del diálogo

#### Scenario: Valor por defecto aplicado en altas
- **WHEN** la definición de administrador aporta `default_value` no vacío y se crea una tarea nueva
- **THEN** el widget del campo se inicializa con ese valor por defecto
- **AND** el payload envía ese valor si el usuario no lo cambia

#### Scenario: La vía HTML no altera obligatoriedad ni valor por defecto
- **WHEN** un campo se resuelve solo por el formulario HTML
- **THEN** el diálogo no añade asterisco ni aplica valor por defecto distintos de los valores por defecto del modelo
- **AND** el payload se comporta como antes del cambio

#### Scenario: Tarea existente sin modificar conserva valores no representables no inyectables
- **WHEN** un campo de lista simple o un campo `multiple` sin opciones tiene valor previo en Redmine y el usuario acepta sin tocarlo
- **THEN** el campo se omite del payload
- **AND** el valor almacenado en Redmine no se borra

#### Scenario: Degradación de un multivalor sin cambios conserva la lista
- **WHEN** un campo sin definición resuelta tiene un valor previo en forma de lista y el usuario acepta sin modificar el texto
- **THEN** el payload contiene la lista original, con sus elementos y su tipo
- **AND** no contiene una cadena con corchetes ni el `repr` de Python

#### Scenario: Degradación de un multivalor editado envía una lista
- **WHEN** un campo sin definición resuelta tiene un valor previo en forma de lista y el usuario modifica el texto sin dejarlo vacío
- **THEN** el payload envía una lista de un elemento con el texto editado

#### Scenario: Degradación de un multivalor vaciado envía lista vacía
- **WHEN** un campo sin definición resuelta tiene un valor previo en forma de lista y el usuario vacía el texto
- **THEN** el payload envía `[]` para limpiar el campo
- **AND** no envía `""`

#### Scenario: Campo no representable omitido aunque el valor serializado no esté vacío
- **WHEN** un campo `list` o `multiple` está marcado como no representable y su control produce un valor no vacío (por ejemplo, una opción seleccionada)
- **THEN** el campo se omite igualmente del payload
- **AND** la omisión no depende de que el widget esté vacío
- **AND** el valor almacenado en Redmine se conserva
