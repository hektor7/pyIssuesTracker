## MODIFIED Requirements

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
