## Purpose

Definir el soporte de campos personalizados de Redmine en PyIssuesTracker: modelo de datos, obtención y parseo, edición en el diálogo de tarea según el formato del campo y envío en creación y actualización.
## Requirements
### Requirement: Modelo de datos de campos personalizados
El `RedmineClient` SHALL exponer una dataclass `RedmineCustomField` que represente la definición de un campo personalizado de un proyecto, con los atributos: `id`, `name`, `field_format`, `is_required`, `multiple`, `possible_values`, `default_value`, `visible` y `editable`.

#### Scenario: Construcción de un campo personalizado
- **WHEN** se mapea una entrada de `issue_custom_fields` con id 3, name "Severidad", field_format "list" y possible_values ["Baja", "Alta"]
- **THEN** el `RedmineCustomField` resultante tiene `id=3`, `name="Severidad"`, `field_format="list"` y `possible_values=["Baja", "Alta"]`

### Requirement: Obtención de los campos personalizados del proyecto
El `RedmineClient` SHALL exponer `get_project_custom_fields(project_id)` devolviendo, para cada campo personalizado del proyecto, su definición. La pertenencia al proyecto, el nombre y el orden SHALL obtenerse de `GET /projects/{id}.json?include=issue_custom_fields`, que en Redmine solo devuelve `id` y `name`. La definición SHALL resolverse en cascada: (1) `GET /custom_fields.json`, filtrando `customized_type == "issue"` y los ids presentes en la pertenencia, con paginación defensiva: una sola petición si la respuesta no trae `total_count` numérico, y peticiones con `limit`/`offset` hasta `total_count` o hasta una página vacía, con tope de 20 páginas, si lo trae; (2) si esa llamada falla por cualquier motivo (401, 403, 404, 500, timeout, error de conexión o respuesta inválida) o no cubre todos los ids, el formulario HTML `GET /projects/{id}/issues/new` con la cookie de sesión, parseando los controles `issue[custom_field_values][<id>]`; (3) si aun así no hay definición, el campo SHALL devolverse con `field_format` vacío y `definition_source="none"`.

La definición completa (`is_required`, `default_value`, `visible` y `editable`) SHALL garantizarse únicamente por la vía de administrador. Por la vía HTML solo SHALL resolverse `field_format`, `multiple` y `possible_values`; el resto SHALL quedar en sus valores por defecto (`False`, `""`, `True`, `True`). Cada campo devuelto SHALL indicar en `definition_source` el origen de su definición (`"admin"`, `"html"` o `"none"`) y, cuando no se resuelva, un `degraded_reason` legible.

El parser HTML SHALL reconocer los siguientes controles con nombre `issue[custom_field_values][N]`: `<select>` simple y `<select multiple>` o con sufijo `[]` (listas, aplicando el discriminador `value == etiqueta`), `<select>` con valores no vacíos exactamente `1` y `0` **solo si no es múltiple** (booleano), `<input type="checkbox">` junto con `<input type="hidden">` del MISMO nombre sin sufijo `[]` (booleano de Redmine core), `<textarea>` (texto largo), `<input type="date">` (fecha), `<input type="number">` (entero) e `<input type="text">` (texto corto). Un `<input type="hidden">` NO SHALL producir una definición por sí solo, tampoco en su variante sin sufijo `[]` (el `0` del booleano) ni en la variante vacía para campos múltiples; cuando comparte el nombre exacto sin `[]` con un `checkbox`, SHALL consumirse como parte del par booleano y NO SHALL clasificarse como `string`. Los grupos de radios y los checkboxes con sufijo `[]` NO SHALL reconocerse, aunque compartan nombre con un hidden del mismo sufijo. La precedencia SHALL ser: hidden descartado como control propio (salvo el par booleano), booleano 1/0 antes del discriminador de lista solo en `<select>` no múltiple (un `<select multiple>` con 1/0 SHALL resolverse como `list` con `multiple=True`), y un `<select>` reconocido antes que un `input`/`textarea` o par `checkbox` + `hidden` del mismo id; entre controles del mismo tipo SHALL prevalecer la primera aparición reconocida, deduplicando por id también en los controles `input`/`textarea`: un segundo control del mismo id NO SHALL sobrescribir la definición ya aceptada. El diccionario devuelto por `parse_issue_form_custom_fields` SHALL conservar el orden de primera aparición de cada id en el documento, también entre tipos distintos, y la prioridad de un `<select>` posterior NO SHALL adelantar la posición del campo en ese diccionario. Ese orden SHALL ser interno del parseo y de la fusión: la lista pública devuelta por `get_project_custom_fields` NO SHALL reordenarse por el documento y SHALL seguir el orden de la pertenencia del proyecto. Los nombres con sufijo `[]` en `input`/`textarea` NO SHALL reconocerse. Las limitaciones de HTML (los enteros y decimales reales renderizados como `input type="text"` se resuelven como `string`, las fechas de versiones antiguas renderizadas como texto también se resuelven como `string`, los grupos de radios/checkboxes con `[]` y los campos de otro tracker siguen sin resolverse, y no se reparan datos corrompidos) SHALL documentarse en el docstring del módulo de parseo.

Los niveles 2 y 3 SHALL capturar cualquier `RedmineError` y no SHALL propagarlo; solo el fallo de la llamada de pertenencia SHALL propagarse como `RedmineError`.

#### Scenario: Proyecto con campos personalizados
- **WHEN** se llama a `get_project_custom_fields(7)` y el proyecto define tres campos personalizados
- **THEN** el método devuelve una lista con tres `RedmineCustomField` correspondientes a los ids de `issue_custom_fields`

#### Scenario: Proyecto sin campos personalizados
- **WHEN** el proyecto no define ningún campo personalizado
- **THEN** el método devuelve una lista vacía y no lanza excepción

#### Scenario: Error al obtener la pertenencia de los campos
- **WHEN** la llamada a `GET /projects/{id}.json?include=issue_custom_fields` falla o el proyecto no es accesible
- **THEN** el error se propaga como `RedmineError` y la interfaz oculta la sección de campos personalizados sin romper el diálogo

#### Scenario: El include solo devuelve id y nombre
- **WHEN** la pertenencia devuelve entradas con solo `id` y `name` para un campo de formato `list` con opciones
- **AND** `GET /custom_fields.json` devuelve su definición completa
- **THEN** el `RedmineCustomField` resultante tiene `field_format="list"`, las opciones reales en `possible_values` y `definition_source="admin"`

#### Scenario: Definición completa solo por la vía de administrador
- **WHEN** un campo se resuelve con `GET /custom_fields.json`
- **THEN** se conservan `is_required`, `default_value`, `visible` y `editable` de la definición
- **AND** `definition_source` vale `"admin"`

#### Scenario: La vía HTML solo resuelve formato, multiplicidad y opciones
- **WHEN** un campo solo se resuelve por el formulario HTML
- **THEN** `field_format`, `multiple` y `possible_values` reflejan el control encontrado
- **AND** `is_required`, `default_value`, `visible` y `editable` conservan sus valores por defecto
- **AND** `definition_source` vale `"html"`

#### Scenario: Sin permisos de administrador pero con cookie de sesión
- **WHEN** `GET /custom_fields.json` responde HTTP 403 y hay cookie de sesión configurada
- **THEN** el sistema obtiene el formulario HTML de nueva incidencia del proyecto
- **AND** resuelve `field_format`, `multiple` y `possible_values` a partir de los controles `issue[custom_field_values][<id>]`
- **AND** no muestra ningún error al usuario

#### Scenario: API key sin permisos y con HTTP 401
- **WHEN** `GET /custom_fields.json` responde HTTP 401
- **THEN** el sistema intenta el fallback HTML si hay cookie de sesión, con el mismo tratamiento que el 403

#### Scenario: Cualquier fallo de la API de definiciones intenta el fallback HTML
- **WHEN** `GET /custom_fields.json` falla con HTTP 404, HTTP 500, timeout o error de conexión
- **AND** hay cookie de sesión configurada
- **THEN** el sistema intenta el formulario HTML con el mismo tratamiento que para 401/403
- **AND** no propaga el error de la API de definiciones

#### Scenario: Sin cookie de sesión
- **WHEN** `GET /custom_fields.json` falla por cualquier motivo y no hay cookie de sesión configurada
- **THEN** el sistema no realiza ninguna petición HTML
- **AND** devuelve los campos con `field_format=""` y `definition_source="none"` sin lanzar excepción

#### Scenario: Definiciones solo para campos de incidencia
- **WHEN** `GET /custom_fields.json` devuelve definiciones de tipos distintos de incidencia
- **THEN** solo se consideran las que tienen `customized_type` igual a `"issue"`

#### Scenario: Definiciones de campos ajenos al proyecto
- **WHEN** `GET /custom_fields.json` devuelve una definición de incidencia cuyo id no figura en la pertenencia del proyecto
- **THEN** esa definición no se incluye en el resultado

#### Scenario: Paginación defensiva de la API de definiciones
- **WHEN** `GET /custom_fields.json` devuelve `total_count` numérico mayor que el número de definiciones de la primera página
- **THEN** el cliente solicita las páginas siguientes con `limit`/`offset` hasta completar `total_count` o recibir una página vacía
- **AND** aplica un tope de seguridad de 20 páginas para evitar bucles
- **AND** si el endpoint ignora la paginación y devuelve todo, no repite peticiones

#### Scenario: Respuesta sin total_count no pagina
- **WHEN** `GET /custom_fields.json` devuelve definiciones sin `total_count` o con un `total_count` no numérico
- **THEN** el cliente realiza una sola petición y no solicita páginas adicionales con `limit`/`offset`
- **AND** devuelve todas las definiciones recibidas en esa respuesta

#### Scenario: Opciones en formato objeto o cadena
- **WHEN** la definición devuelve `possible_values` como objetos con `value` y `label`, o como cadenas
- **THEN** `possible_values` se normaliza a una lista de cadenas con el valor de cada opción

#### Scenario: Lista renderizada como desplegable en el formulario
- **WHEN** el formulario HTML contiene un `select` simple con el nombre `issue[custom_field_values][3]` y cuyos valores no vacíos coinciden con sus etiquetas
- **THEN** el campo se resuelve como `field_format="list"`, `multiple=False` y las etiquetas en orden en `possible_values`

#### Scenario: Lista múltiple renderizada como desplegable múltiple
- **WHEN** el formulario contiene un `select multiple` o un nombre con sufijo `[]` para el campo
- **AND** sus valores no vacíos coinciden con sus etiquetas
- **THEN** el campo se resuelve como `field_format="list"` con `multiple=True`

#### Scenario: Discriminador de desplegable de lista
- **WHEN** un `select` tiene opciones cuyo `value` no vacío coincide exactamente con el texto de la etiqueta, tras `html.unescape` y `strip`
- **THEN** el campo se clasifica como `list`

#### Scenario: Desplegable de usuario, versión o enumeración no es una lista
- **WHEN** un `select` tiene opciones con `value` numérico de id y etiqueta con el nombre (`value != label`)
- **THEN** el campo NO se clasifica como `list`
- **AND** queda sin resolver con `field_format=""` y `definition_source="none"`

#### Scenario: Booleano renderizado como desplegable
- **WHEN** el desplegable de un campo no múltiple tiene exactamente las opciones `1` y `0`
- **THEN** el campo se resuelve como `bool`
- **AND** esta comprobación prevalece sobre el discriminador de lista

#### Scenario: Booleano 1/0 en desplegable múltiple se resuelve como lista
- **WHEN** el formulario contiene un `<select multiple>` (o un nombre con sufijo `[]`) para el campo con valores no vacíos exactamente `1` y `0`
- **THEN** el campo se resuelve como `field_format="list"` con `multiple=True` y `possible_values=["1", "0"]`
- **AND** NO se resuelve como `bool`

#### Scenario: Booleano renderizado como checkbox con hidden
- **WHEN** el formulario contiene `<input type="checkbox" name="issue[custom_field_values][11]" value="1">` y `<input type="hidden" name="issue[custom_field_values][11]" value="0">`
- **THEN** el campo se resuelve como `field_format="bool"` con `multiple=False` y sin `possible_values`
- **AND** el `hidden` se consume como parte del par y no produce una definición `string`
- **AND** el diálogo lo muestra como `QCheckBox`

#### Scenario: Hidden sin sufijo no se clasifica como string
- **WHEN** el formulario contiene un `<input type="hidden" name="issue[custom_field_values][12]" value="0">` sin un `checkbox` pareja
- **THEN** ese control no se reconoce como definición
- **AND** el campo NO se resuelve como `field_format="string"`
- **AND** queda sin resolver con `field_format=""` y `definition_source="none"` si no hay otro control reconocible

#### Scenario: Checkbox con sufijo de múltiple sigue sin reconocerse
- **WHEN** el formulario contiene un `<input type="checkbox" name="issue[custom_field_values][13][]" value="1">` y un `<input type="hidden" name="issue[custom_field_values][13][]" value="0">`
- **THEN** el campo no se reconoce como `bool`
- **AND** queda sin resolver salvo que exista un `select` reconocido para el mismo id

#### Scenario: Textarea renderizado como texto largo
- **WHEN** el formulario HTML contiene `<textarea name="issue[custom_field_values][7]">` para el campo
- **THEN** el campo se resuelve como `field_format="text"` con `multiple=False` y sin `possible_values`
- **AND** el diálogo lo muestra como `QPlainTextEdit`

#### Scenario: Input de fecha renderizado como fecha
- **WHEN** el formulario HTML contiene `<input type="date" name="issue[custom_field_values][8]">` para el campo
- **THEN** el campo se resuelve como `field_format="date"` con `multiple=False`
- **AND** el diálogo lo muestra como `QDateEdit` con opción de dejarlo vacío

#### Scenario: Input numérico renderizado como entero
- **WHEN** el formulario HTML contiene `<input type="number" name="issue[custom_field_values][9]">` para el campo
- **THEN** el campo se resuelve como `field_format="int"` con `multiple=False`

#### Scenario: Input de texto renderizado como texto corto
- **WHEN** el formulario HTML contiene `<input type="text" name="issue[custom_field_values][10]">` para el campo
- **THEN** el campo se resuelve como `field_format="string"` con `multiple=False`

#### Scenario: Número real renderizado como input de texto
- **WHEN** un campo `float` se renderiza en el formulario como `<input type="text">` porque Redmine no distingue decimales en el control
- **THEN** el campo se resuelve como `field_format="string"` y `multiple=False`
- **AND** la limitación queda documentada en el docstring del módulo de parseo

#### Scenario: Fecha antigua renderizada como input de texto
- **WHEN** una versión antigua de Redmine renderiza un campo `date` como `<input type="text">`
- **THEN** el campo se resuelve como `field_format="string"` y `multiple=False`
- **AND** la limitación queda documentada en el docstring del módulo de parseo

#### Scenario: Hidden con sufijo sigue ignorado
- **WHEN** el formulario contiene `<input type="hidden" name="issue[custom_field_values][15][]" value="">` junto a un `select` reconocible del campo 14
- **THEN** el campo 15 no se reconoce
- **AND** el campo 14 se resuelve con normalidad

#### Scenario: Grupo de radios o checkboxes no soportado por el parser
- **WHEN** el formulario solo ofrece un grupo de `<input type="radio">` o de `<input type="checkbox">` con sufijo `[]` para el campo
- **THEN** el campo no se reconoce y queda sin resolver con `field_format=""` y `definition_source="none"`
- **AND** se comporta como hoy (texto libre), sin regresión
- **AND** la única excepción es el `checkbox` sin sufijo `[]` con un `hidden` pareja del mismo nombre, que se resuelve como `bool`

#### Scenario: Input o textarea con sufijo de múltiple no se reconoce
- **WHEN** un `input` o un `textarea` de campo personalizado lleva sufijo `[]` en el nombre
- **THEN** ese control no se reconoce como definición
- **AND** el campo queda sin resolver salvo que exista un `select` reconocido para el mismo id

#### Scenario: Precedencia de select sobre input para el mismo id
- **WHEN** el formulario contiene un `<input type="text">` y un `<select>` reconocible para el mismo id de campo
- **THEN** prevalece la definición del `select`
- **AND** el campo se resuelve con el formato y las opciones del `select`

#### Scenario: Orden entre tipos preservado
- **WHEN** el formulario contiene un `<textarea>` del campo 7 antes que un `<select>` de lista del campo 3
- **THEN** el diccionario devuelto por `parse_issue_form_custom_fields` contiene el campo 7 antes que el campo 3
- **AND** ese orden refleja la aparición en el documento, no una agrupación por tipo de control
- **AND** la lista pública de `get_project_custom_fields` no se reordena por el documento y sigue el orden de la pertenencia

#### Scenario: Select posterior no adelanta la posición del campo
- **WHEN** un `<textarea>` del campo 7 aparece antes que un `<select>` del campo 3 y después aparece un `<select>` reconocible del campo 7
- **THEN** el campo 7 se resuelve con la definición del `select` (mayor precedencia)
- **AND** en el diccionario de `parse_issue_form_custom_fields` el campo 7 sigue antes que el campo 3, según la primera aparición del id 7
- **AND** la lista pública de `get_project_custom_fields` mantiene el orden de la pertenencia

#### Scenario: Integración de lista, textarea y fecha con Cookie
- **WHEN** `GET /custom_fields.json` responde HTTP 403, hay Cookie de sesión y el formulario HTML contiene un `select` de lista, un `textarea` y un `input type="date"` del proyecto
- **THEN** el diálogo muestra un `QComboBox`, un `QPlainTextEdit` y un `QDateEdit` respectivamente
- **AND** los tres campos tienen `definition_source="html"`

#### Scenario: Formulario HTML sin el campo
- **WHEN** el formulario se obtiene correctamente pero no contiene controles reconocidos para uno de los ids de la pertenencia
- **THEN** ese campo se devuelve con `field_format=""`, `definition_source="none"` y su motivo
- **AND** el resto de campos se resuelven con normalidad

#### Scenario: Formulario HTML redirigido al login
- **WHEN** la petición del formulario HTML redirige a la página de login por cookie caducada o no válida
- **THEN** el sistema trata el intento como fallo de resolución sin lanzar excepción
- **AND** registra un aviso indicando que la cookie no es válida

#### Scenario: Formulario válido sin controles de campos personalizados
- **WHEN** una petición HTML devuelve HTTP 200 con HTML válido pero sin ningún control `issue[custom_field_values][<id>]`
- **THEN** el sistema trata ese resultado como negativo **por proyecto** y devuelve los campos con `field_format=""` sin lanzar excepción
- **AND** no fija el fallo global de autenticación del HTML
- **AND** la resolución de los campos de otro proyecto por HTML sigue siendo posible

#### Scenario: Página de login identificable en una respuesta 200
- **WHEN** la petición HTML devuelve HTTP 200 con un formulario de login identificable (`id="login-form"` o un campo `name="username"`) y sin controles de campos personalizados
- **THEN** el fallo se memoriza globalmente como fallo de autenticación del HTML
- **AND** no se vuelve a pedir el formulario HTML para ningún proyecto

#### Scenario: Formulario válido sin controles del proyecto A no impide resolver el proyecto B
- **WHEN** el formulario HTML del proyecto A es un HTTP 200 válido sin controles de campos personalizados
- **AND** el formulario HTML del proyecto B contiene un `select` reconocible para sus campos
- **THEN** los campos del proyecto A se degradan con `definition_source="none"`
- **AND** los campos del proyecto B se resuelven por HTML con `definition_source="html"`
- **AND** el cliente solicitó el formulario HTML de ambos proyectos

#### Scenario: Claves extra en la pertenencia se ignoran
- **WHEN** la pertenencia incluye claves de definición además de `id` y `name`
- **THEN** esas claves se ignoran deliberadamente
- **AND** la definición solo procede de los niveles 2 o 3

#### Scenario: Nombre de la pertenencia prevalece
- **WHEN** el nombre del campo en la pertenencia difiere del nombre de la definición
- **THEN** el `RedmineCustomField` devuelto usa el nombre de la pertenencia

#### Scenario: Orden de la pertenencia preservado
- **WHEN** la pertenencia devuelve los campos en un orden distinto al del documento HTML y al de la definición global
- **THEN** la lista devuelta por `get_project_custom_fields` conserva el orden de la pertenencia
- **AND** el orden del diccionario de `parse_issue_form_custom_fields` no altera ese orden público

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

### Requirement: Caché de definiciones de campos personalizados
El `RedmineClient` SHALL cachear en memoria el resultado por proyecto y las definiciones globales de incidencia obtenidas de la API de administrador, memorizando también los intentos fallidos para no repetirlos. El fallo de autenticación del formulario HTML —redirección a login/SSO, HTTP 401/403 en la petición HTML o página de login identificable— SHALL memorizarse de forma global en el cliente, de modo que un informe con N proyectos realice como máximo una petición HTML condenada a login. Un HTTP 200 con HTML válido pero sin controles `issue[custom_field_values]` NO SHALL considerarse fallo de autenticación: SHALL memorizarse como negativo por proyecto y NO SHALL impedir resolver los campos de otros proyectos. La caché SHALL vivir en la instancia del cliente y SHALL poder limpiarse explícitamente mediante `clear_custom_field_cache()`. Las excepciones de la llamada de pertenencia no SHALL cachearse.

#### Scenario: Segunda llamada para el mismo proyecto
- **WHEN** se llama dos veces a `get_project_custom_fields` con el mismo id de proyecto
- **THEN** la segunda llamada no realiza ninguna petición HTTP
- **AND** devuelve el mismo contenido de definiciones

#### Scenario: Varios proyectos en una misma sesión
- **WHEN** se consultan los campos de tres proyectos distintos
- **THEN** la API de definiciones se consulta una sola vez
- **AND** la pertenencia se consulta una vez por proyecto

#### Scenario: Proyecto sin campos personalizados
- **WHEN** la pertenencia devuelve una lista vacía
- **THEN** no se consulta la API de definiciones ni el formulario HTML

#### Scenario: Fallo de permisos memorizado entre proyectos
- **WHEN** la API de definiciones responde 403 y hay cookie de sesión
- **AND** se consultan dos proyectos distintos
- **THEN** la API de definiciones se intenta una sola vez
- **AND** el formulario HTML se consulta como máximo una vez por proyecto

#### Scenario: Fallo de autenticación del HTML memorizado globalmente
- **WHEN** el formulario HTML de un proyecto redirige a login, devuelve HTTP 401/403 o devuelve una página de login identificable
- **AND** se consulta otro proyecto con la misma cookie
- **THEN** no se vuelve a pedir el formulario HTML
- **AND** los campos del segundo proyecto se degradan directamente con `definition_source="none"`

#### Scenario: Formulario válido sin controles no se memoriza globalmente
- **WHEN** el formulario HTML del proyecto A devuelve HTTP 200 con HTML válido sin controles de campos personalizados
- **AND** se consulta el proyecto B
- **THEN** el cliente solicita el formulario HTML del proyecto B
- **AND** el resultado negativo del proyecto A no se reutiliza para el proyecto B

#### Scenario: Informe ODS con N proyectos
- **WHEN** el informe recorre N proyectos y la cookie de sesión no es válida
- **THEN** se realiza como máximo una petición HTML fallida por cliente
- **AND** los N proyectos se degradan a texto libre sin lanzar excepción

#### Scenario: Ausencia de cookie memorizada
- **WHEN** no hay cookie de sesión y la API de definiciones falla por cualquier motivo
- **AND** se consultan varios proyectos
- **THEN** no se realiza ninguna petición HTML

#### Scenario: Limpieza explícita de la caché
- **WHEN** la aplicación invoca `clear_custom_field_cache()`
- **THEN** la siguiente consulta vuelve a pedir la pertenencia y las definiciones
- **AND** se olvida el fallo global de autenticación del formulario HTML

#### Scenario: Cambio de URL o de API key
- **WHEN** la aplicación crea un `RedmineClient` nuevo tras cambiar la URL o la API key
- **THEN** el cliente nuevo no reutiliza las definiciones cacheadas por el anterior

#### Scenario: El resultado no expone la caché interna
- **WHEN** el consumidor modifica la lista devuelta por `get_project_custom_fields`
- **THEN** una llamada posterior devuelve el contenido cacheado sin alteraciones

### Requirement: Degradación a texto libre y diagnóstico
Cuando la definición de un campo no pueda resolverse, el sistema SHALL devolver el campo con `field_format=""`, `definition_source="none"` y un `degraded_reason` legible para que el diálogo use el control de texto libre, y SHALL registrar la degradación en el log con el proyecto, el id, el nombre y el motivo. Un campo cuya definición sí se resuelve como lista sin opciones SHALL renderizarse como selector deshabilitado con el texto de ayuda, nunca como caja de texto. La degradación no SHALL alterar el valor previo del issue.

#### Scenario: Campo sin definición resoluble
- **WHEN** un campo de la pertenencia no se resuelve por ninguna de las vías
- **THEN** el diálogo lo muestra como `QLineEdit`
- **AND** la sección de campos personalizados permanece visible y el diálogo no falla
- **AND** el campo tiene `definition_source="none"` y un `degraded_reason` no vacío

#### Scenario: Origen de la definición
- **WHEN** un campo se resuelve por la API de administrador, por el formulario HTML o por ninguna vía
- **THEN** `definition_source` vale `"admin"`, `"html"` o `"none"` respectivamente
- **AND** `degraded_reason` solo tiene contenido en el caso `"none"`

#### Scenario: Lista conocida sin opciones
- **WHEN** un campo se resuelve como `field_format="list"` con `possible_values` vacío
- **THEN** el diálogo muestra el selector deshabilitado con el texto de ayuda de "sin opciones"
- **AND** no lo convierte en caja de texto

#### Scenario: Aviso de degradación
- **WHEN** un campo no se resuelve
- **THEN** el log registra un aviso con el id del proyecto, el id del campo, su nombre y el motivo
- **AND** el aviso no contiene el valor de la cookie de sesión ni la API key

#### Scenario: Valor previo en un campo no resoluble
- **WHEN** un issue tiene valor en un campo cuya definición no se resuelve
- **THEN** el control de texto libre se precarga con ese valor
- **AND** el valor se envía sin cambios si el usuario no lo modifica

#### Scenario: Fallo total de la pertenencia
- **WHEN** falla la obtención de la pertenencia de los campos del proyecto
- **THEN** el diálogo oculta la sección de campos personalizados sin romper el resto del formulario

### Requirement: Aviso visible de definición incompleta en el diálogo
Cuando al menos un campo personalizado tenga `definition_source == "none"`, `TaskDialog` SHALL mostrar un aviso visible, discreto y no modal dentro del grupo "Campos personalizados", con texto accionable que indique configurar la Cookie de sesión en Ajustes o usar una API key de administrador y que los campos se muestran como texto libre. El aviso SHALL depender únicamente de que quede algún campo con `definition_source == "none"` en la carga actual: no SHALL añadirse lógica nueva al diálogo y NO SHALL mostrarse cuando todos los campos se resuelvan por la vía de administrador o por HTML, incluidos los formatos `text`, `date`, `int`, `string` y el booleano core (`checkbox` + `hidden`). El aviso SHALL mostrarse una sola vez por grupo, no repetirse por campo, no bloquear el diálogo y ocultarse cuando todos los campos se resuelvan o no haya campos. El campo Cookie de `settings_dialog.py` SHALL explicar en su ayuda o tooltip que permite resolver campos personalizados cuando la API key no es de administrador.

#### Scenario: Aviso visible cuando hay degradación
- **WHEN** el diálogo carga campos y al menos uno tiene `definition_source="none"`
- **THEN** se muestra un único `QLabel` de aviso dentro del grupo "Campos personalizados"
- **AND** el texto menciona la Cookie de sesión en Ajustes, la API key de administrador y el texto libre
- **AND** el aviso no es un diálogo modal ni bloquea la edición

#### Scenario: Sin aviso cuando todo se resuelve
- **WHEN** todos los campos tienen `definition_source` igual a `"admin"` o `"html"`
- **THEN** el aviso no se muestra

#### Scenario: Sin aviso cuando todos los campos se resuelven por HTML con los nuevos formatos
- **WHEN** el proyecto resuelve por HTML una lista, un `text`, una `date`, un `string` y un booleano core (`checkbox` + `hidden`), y ninguno queda en `"none"`
- **THEN** el aviso no se muestra
- **AND** cada campo conserva `definition_source="html"`

#### Scenario: Aviso presente si algún campo queda sin resolver
- **WHEN** el proyecto resuelve por HTML una lista y un `text`, pero un campo solo se ofrece como grupo de radios y queda con `definition_source="none"`
- **THEN** el aviso se muestra una sola vez
- **AND** el campo no resuelto se renderiza como texto libre

#### Scenario: Sin aviso cuando no hay campos
- **WHEN** el proyecto no tiene campos personalizados o la pertenencia falla
- **THEN** el grupo se oculta y el aviso no se muestra

#### Scenario: El aviso no se repite por campo
- **WHEN** hay tres campos con `definition_source="none"`
- **THEN** solo se muestra un aviso en el grupo
- **AND** no se añade un aviso por cada campo

#### Scenario: El aviso se limpia al cambiar de proyecto
- **WHEN** se recargan los campos de otro proyecto sin degradación
- **THEN** el aviso anterior desaparece

#### Scenario: Ayuda de Cookie en Ajustes
- **WHEN** el usuario consulta la ayuda o el tooltip del campo Cookie
- **THEN** el texto explica que la cookie permite resolver campos personalizados cuando la API key no es de administrador

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

