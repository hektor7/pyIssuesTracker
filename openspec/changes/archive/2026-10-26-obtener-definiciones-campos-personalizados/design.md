## Context

PyIssuesTracker es una aplicación de escritorio **PyQt6** (entrada `main.py`, código en `app/`, tests en `tests/` con pytest y fixture `qapp`, ejecutados con `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`). El cambio afecta a la resolución de definiciones de campos personalizados y añade un aviso acotado en el diálogo; el renderizado por formato ya está cubierto por la suite.

### Hechos verificados

**Causa raíz**

- `app/services/redmine_client.py:902` (`get_project_custom_fields`) llama a `GET /projects/{id}.json?include=issue_custom_fields` y espera `field_format`, `multiple`, `possible_values`, `is_required` y `default_value` en cada entrada.
- Redmine real solo serializa `id` y `name` en ese `include`: `render_api_includes` en `app/helpers/projects_helper.rb` hace `api.custom_field(:id => custom_field.id, :name => custom_field.name)`. Lo confirma `https://www.redmine.org/issues/43407` y la wiki `Rest_CustomFields`.
- Con `field_format=""` y `multiple=False`, `app/dialogs/task_dialog.py:602` cae en `return QLineEdit(), "string", None`; las ramas `list`, `multiple`, `date`, `bool`, `int` y `float` no se alcanzan nunca en producción.
- `tests/test_redmine_custom_fields.py` usa un fixture inventado que incluye la definición completa en el `include` del proyecto, por lo que valida un comportamiento que la API no ofrece.

**Endpoints y formatos reales**

- `GET /custom_fields.json` existe y devuelve la definición completa (`app/views/custom_fields/index.api.rsb`): `id`, `name`, `customized_type`, `field_format`, `is_required`, `multiple`, `default_value`, `visible`, `editable` y `possible_values`. El controlador aplica `before_action :require_admin` y `accept_api_auth :index`, es decir, exige API key **y** usuario administrador. La vista no emite metadatos de paginación, pero el endpoint acepta `limit`/`offset` en algunas versiones; el cliente lo tratará de forma defensiva.
- En `possible_values` cada elemento es un objeto `{value, label}`; para el formato `list` ambos coinciden con el texto de la opción. Algunas versiones/documentación muestran una lista de cadenas: hay que aceptar ambas formas.
- Los nombres de los controles del formulario son `issue[custom_field_values][<id>]`, con sufijo `[]` si el campo es múltiple (`custom_field_tag_name` en `app/helpers/custom_fields_helper.rb`).
- Renderizado relevante para el cambio (`lib/redmine/field_format.rb` y `app/views/issues/_form_custom_fields.html.erb`):
  - `list`: `<select>` (o `<select multiple>`), salvo que el campo tenga `edit_tag_style = check_box`, en cuyo caso se renderiza un grupo de checkboxes (múltiple) o radios (simple). Esa variante queda fuera de alcance.
  - `bool`: checkbox único, grupo de radios o `<select>` con valores `1` y `0`.
  - `user`, `version` y `enumeration`: `<select>` con `value="<id>"` y etiqueta con el nombre; no son listas de valores seleccionables.
  - `text`: `<textarea>`; `date`: `<input type="date">`; `int`/`float`/`string`: `<input type="text">`. El parser no los resuelve (ver D5).
- El formulario solo incluye `@issue.editable_custom_field_values`, por lo que los campos de solo lectura, los ocultos y los restringidos a otros trackers no aparecen.
- Rutas (`config/routes.rb`): `resources :projects { resources :issues, only: [:index, :new, :create] }` habilita `GET /projects/:project_id/issues/new` (el `project_id` admite id numérico o identificador) y `resources :issues` habilita `GET /issues/new?project_id=`.

**Capa HTTP actual**

- `app/services/redmine_client.py:303` (`_get`) lanza `RedmineAuthError` tanto para 401 como para 403, con mensajes distintos pero **sin código de estado accesible**. Para distinguir "sin permisos de administrador" de otros fallos hace falta un cambio mínimo.
- `_get` termina en `resp.json()`; no existe método para obtener el cuerpo de una página HTML.
- `_check_redirect` (`:406`) convierte cualquier redirección en `RedmineSSOError`. Una redirección a `/login` por cookie caducada cae aquí.
- `_build_client` (`:259`) ya añade la cabecera `Cookie` cuando hay `session_cookie`. La cookie está cableada de extremo a extremo: `KEY_REDMINE_SESSION_COOKIE` (`app/utils/constants.py`), `SettingsManager.session_cookie` con normalización de JSON de DevTools (`app/services/settings_manager.py`), campo en `app/dialogs/settings_dialog.py` y paso al cliente en `app/main_window.py`.
- La cookie es imprescindible para el formulario HTML: la API key por cabecera no autentica peticiones `format.html`.
- Las excepciones existentes y confirmadas son `RedmineError`, `RedmineAuthError`, `RedmineConnectionError`, `RedmineSSOError` y `RedmineValidationError` (`app/services/redmine_client.py:217-242`). `_get` ya mapea `httpx.ConnectError` y `httpx.TimeoutException` a `RedmineConnectionError`.

**Consumidores actuales**

- `TaskDialog._load_custom_fields_for_project` (`app/dialogs/task_dialog.py:547`) consume `get_project_custom_fields` y oculta la sección ante cualquier excepción.
- `TaskDialog._build_custom_field_widget` (`:602`) elige el control por `field_format`/`multiple`; `_add_custom_field_widget` (`:580`) ya renderiza el asterisco de obligatorio y `_apply_custom_field_values` (`:668`) ya aplica `default_value` en altas.
- `MainWindow._report_custom_fields_for_projects` consume solo `cf.id` y `cf.name`, y captura `RedmineError` por proyecto.
- `MainWindow._conectar_redmine` construye un `RedmineClient` nuevo en cada conexión, lo que da un punto natural de invalidación de caché.
- `RedmineCustomField` (`app/services/redmine_client.py:138`) se amplía con dos campos retrocompatibles: `definition_source` y `degraded_reason`.

## Goals / Non-Goals

**Goals:**

- Que un campo `field_format="list"` se renderice como `QComboBox` no editable con sus opciones reales, y `multiple=True` como `MultiValueCombo`, sin reescribir la lógica de widgets.
- Resolver la definición sin exigir permisos de administrador, degradando de forma controlada y visible cuando no sea posible.
- No alterar valores representables ni borrar valores no representables cuando el usuario no cambia nada.
- Mantener intacto el consumo del informe ODS (`id` y `name`).
- Cubrir con tests la causa raíz: que los fixtures reflejen lo que Redmine devuelve de verdad.

**Non-Goals:**

- Resolver opciones de `user`, `version`, `enumeration` o `key_value_list`: siguen en texto libre, como hoy. El discriminador de `<select>` garantiza que no se confundan con `list`.
- Soportar en el parser HTML `textarea`, `date`, `int`, `float`, `string`, radios o grupos de checkboxes: hoy ya se muestran como texto libre y la vía de administrador los resuelve todos, así que no resolverlos no es regresión.
- Filtrar campos por `visible`/`editable` antes de mostrarlos: se conserva el comportamiento actual de mostrar todos los campos del proyecto.
- Obtener `default_value`, `is_required`, `visible` o `editable` desde el formulario HTML: no hay señal fiable.
- Cambiar la lógica de widgets del diálogo, el informe ODS o el formato general del payload.
- Añadir dependencias (nada de BeautifulSoup/lxml).

## Decisions

### D1. Cascada de resolución con tres niveles y parada temprana

`get_project_custom_fields(project_id)` conserva su firma y su contrato (lista de `RedmineCustomField`, `RedmineError` si falla la pertenencia) y resuelve internamente:

1. **Pertenencia y nombre**: `GET /projects/{id}.json?include=issue_custom_fields`. Es la fuente autoritativa de qué campos aplican al proyecto, de su nombre visible y de su orden. De aquí se toma **solo** `id`, `name` y el orden.
2. **Definiciones (primaria)**: `GET /custom_fields.json`, filtrando `customized_type == "issue"` y quedándose con los ids de la pertenencia. La petición es defensiva ante paginación: si la respuesta **no** trae `total_count` o este no es numérico, se hace **una sola petición sin paginar**. Solo se pagina cuando `total_count` es numérico y mayor que el número de elementos acumulados; en ese caso se piden páginas con `limit`/`offset` hasta alcanzar `total_count` o hasta que una página venga vacía, con un tope de seguridad de 20 páginas para evitar bucles. Si el endpoint ignora la paginación y devuelve todo en la primera página, no hay `total_count` superior o la página siguiente llega vacía, se detiene sin repetir peticiones. Si cubre todos los ids, la cascada termina y no se pide HTML.
3. **Definiciones (fallback sin administrador)**: si la primaria falla por **cualquier motivo** (401, 403, 404, 500, timeout, error de conexión, respuesta inválida) o si cubre solo parte de los ids, `GET /projects/{id}/issues/new` con la cookie de sesión y parseo de los controles `issue[custom_field_values][<id>]`. Solo se consulta si `session_cookie` no está vacía y si no se ha memorizado globalmente un fallo de autenticación del HTML. Si cubre los ids que faltaban, termina.
4. **Último recurso**: los ids que sigan sin definición se devuelven con `field_format=""` y `definition_source="none"`, que el diálogo renderiza como `QLineEdit`, registrando un `logger.warning` con proyecto, id, nombre y motivo.

Si la pertenencia falla, la excepción se propaga como hoy (`RedmineError`): `TaskDialog` oculta la sección y el informe ODS ignora ese proyecto. Los fallos de los niveles 2 y 3 **nunca** se propagan: se captura cualquier `RedmineError` (incluidas `RedmineAuthError`, `RedmineConnectionError` y `RedmineSSOError`) y cualquier error de parseo esperado. Solo la pertenencia propaga.

**Alcance de la definición**: la definición completa (`is_required`, `default_value`, `visible`, `editable`) solo se garantiza por la vía de administrador. La vía HTML solo resuelve `field_format`, `multiple` y `possible_values`; el resto queda en sus valores por defecto (`False`, `""`, `True`, `True`).

*Alternativas descartadas:* (a) depender solo de la primaria — rompe instalaciones sin administrador; (b) depender solo del HTML — pierde `int`/`float`, exige cookie y añade una petición por proyecto incluso con administrador; (c) inferir el formato por el nombre del campo — frágil y no verificable; (d) pedir al usuario una API key de administrador — inaceptable como requisito.

### D2. La pertenencia no aporta definición, aunque el servidor la envíe

Aunque un Redmine o un plugin devolviese claves extra en `issue_custom_fields`, se ignoran deliberadamente: la definición tiene una única fuente (nivel 2 o 3). Así el comportamiento es determinista entre versiones y los tests dejan de poder pasar por accidente con un fixture irreal. La pertenencia solo aporta `id`, `name` y el orden; el nombre de la pertenencia prevalece sobre el de la definición y el orden de salida es el de la pertenencia.

*Alternativa descartada:* usar el `field_format` del `include` si viene, como atajo. Habría hecho pasar los tests antiguos sin corregir el fixture y ocultaría regresiones en instalaciones reales.

### D3. Cambio mínimo en la capa HTTP: `status_code`, `_raise_for_status` y `_get_text`

- `RedmineError.__init__(message, status_code: int | None = None)` guarda `self.status_code` con valor por defecto `None`. Es retrocompatible: todas las construcciones actuales siguen funcionando y los mensajes no cambian.
- `_get` y el nuevo `_get_text` comparten `_raise_for_status(resp, path)`, que replica exactamente el mapeo actual (401/403 → `RedmineAuthError`, 404 → `RedmineError`, ≥400 → `RedmineError` con detalle de `errors`) y ahora adjunta `status_code`. `RedmineValidationError` conserva su manejo específico en `_post`/`_put`.
- `_get_text(path, params=None) -> str` ejecuta `GET`, llama a `_check_redirect`, a `_raise_for_status` y devuelve `resp.text`. No parsea JSON.
- `_get_text` mapea `httpx.ConnectError` y `httpx.TimeoutException` a `RedmineConnectionError`, igual que ya hace `_get`.
- El catálogo de excepciones y sus mensajes no cambia; el código nuevo distingue el motivo con `getattr(exc, "status_code", None)` o con `isinstance`.

*Alternativas descartadas:* (a) distinguir 403 por el texto del mensaje — acopla la lógica a cadenas traducibles; (b) crear una excepción nueva — amplía el catálogo sin necesidad; (c) reutilizar `_get` con un flag `raw` — mezcla responsabilidades y complica los mocks existentes.

### D4. Endpoint HTML: `GET /projects/{project_id}/issues/new`

Se usa la ruta anidada con el **id numérico** del proyecto, que Redmine resuelve igual que el identificador y que evita construir query strings. La variante `GET /issues/new?project_id={id}` es equivalente y se descarta por no aportar nada y duplicar superficie.

El fallo típico es una redirección 302 a `/login` por cookie caducada o ausente; `_check_redirect` la convierte en `RedmineSSOError`, que la cascada captura y registra como "cookie caducada o no válida".

La caché negativa global del HTML se reserva **exclusivamente** para señales de autenticación: redirección a login/SSO detectada por `_check_redirect`, HTTP 401/403 en la petición HTML, o una página de login identificable (por ejemplo, un formulario con `id="login-form"` o un campo `name="username"` y ausencia de controles `issue[custom_field_values]`). Un 200 con HTML válido pero **sin** controles de campos personalizados no es un fallo de autenticación: es un negativo **por proyecto** (puede ser legítimo si todos los campos son de solo lectura o pertenecen a otro tracker) y no debe impedir resolver los campos de otros proyectos.

*Alternativa descartada:* `POST /projects/{id}/issues/new` (Redmine lo usa para refrescar el formulario al cambiar de tracker). Obliga a enviar parámetros de issue y no mejora la cobertura de campos restringidos a trackers.

### D5. Parseo HTML en un módulo puro, sin ciclo de imports y recortado al caso de listas

Nuevo `app/services/custom_field_definitions.py` con su propia dataclass y una única función pública:

```python
@dataclass
class ParsedCustomField:
    field_format: str = ""
    multiple: bool = False
    possible_values: list[str] = field(default_factory=list)

def parse_issue_form_custom_fields(html: str) -> dict[int, ParsedCustomField]: ...
```

El módulo **no importa `redmine_client`**. La dirección de dependencia es `redmine_client` → `custom_field_definitions`; `RedmineClient` importa únicamente `parse_issue_form_custom_fields`, consume su resultado y mapea cada entrada a `RedmineCustomField`; no importa la dataclass `ParsedCustomField`. Así se evita un ciclo de imports y el parser se puede probar de forma aislada.

Se implementa con `html.parser.HTMLParser` de la stdlib (no hay BeautifulSoup en `requirements.txt`). Reglas de reconocimiento, deliberadamente limitadas:

| Control encontrado | Señal | Resultado |
|---|---|---|
| `<select>` simple con nombre `issue[custom_field_values][N]` | todos los `value` no vacíos coinciden exactamente con el texto de su etiqueta | `list`, `multiple=False`, `possible_values` = etiquetas |
| `<select multiple>` o nombre con sufijo `[]` | mismo discriminador | `list`, `multiple=True` |
| `<select>` cuyos valores no vacíos son exactamente `1` y `0` | excepción previa al discriminador | `bool` |
| `<select>` con valores tipo id (`user`, `version`, `enumeration`) | algún `value` no vacío no coincide con su etiqueta | **no se reconoce**; el campo queda sin resolver (`field_format=""`) |
| `<input type="hidden">` | — | se ignora (incluido el hidden `""` que Redmine añade para múltiples) |
| `<textarea>`, `<input type="date">`, `<input type="number">`, `<input type="text">` | — | **no soportado**; el campo queda sin resolver |
| Grupo de checkboxes o radios | — | **no soportado**; el campo queda sin resolver |
| Cualquier otro control o nombre ajeno | — | se ignora |

Justificación del recorte: el objetivo del cambio es el bug de las listas. Los demás formatos ya se muestran hoy como texto libre, por lo que no resolverlos no es una regresión; además, en la ruta de administrador (`/custom_fields.json`) sí se resuelven todos. Soportar radios/checkboxes añadía superficie y heurísticas sin mejorar el caso que motiva el cambio.

Detalles de robustez: se aplica `html.unescape` y `strip` a textos y valores antes de comparar; se ignoran opciones con `value=""` (la opción vacía de limpiar); se conserva el orden de aparición; se deduplican los ids de campo (prevalece la primera aparición reconocida, de forma determinista), pero las opciones dentro de un mismo `<select>` **no** se deduplican. El parser no lanza excepciones con HTML malformado, vacío o de login: devuelve `{}`.

Limitaciones asumidas y documentadas en el propio módulo: no se deducen `is_required`, `default_value` ni `visible`/`editable`; los campos de solo lectura o de otro tracker no están en el formulario; las variantes de `list` renderizadas como radios/checkboxes no se reconocen.

*Alternativas descartadas:* (a) expresiones regulares sobre el HTML — frágiles con atributos en cualquier orden y con anidamiento; (b) dependencia nueva — coste de empaquetado y licencias para un caso acotado; (c) clasificar todo `<select>` como `list` — confunde `user`/`version`/`enumeration`; (d) parsear labels para obtener textos — innecesario: para `list` el valor enviado coincide con el texto de la opción.

### D6. Caché por instancia, definiciones globales y caché negativa global solo para fallos de autenticación del HTML

En `RedmineClient`:

- `_project_custom_fields: dict[int, list[RedmineCustomField]]` — resultado final por proyecto.
- `_custom_field_definitions: dict[int, RedmineCustomField] | None` — definiciones de la API de administrador; `None` mientras no se ha intentado. El fallo de `/custom_fields.json` se memoriza **globalmente** en el cliente en `_custom_field_definitions_error`: una vez falla, no se reintenta para ningún proyecto.
- `_project_form_definitions: dict[int, dict[int, RedmineCustomField]]` y su motivo por proyecto — resultado del formulario HTML, también para el caso negativo.
- `_issue_form_auth_failure: str | None` — fallo de autenticación del HTML memorizado **globalmente** en el cliente. Solo se fija con señales de autenticación: redirección a login/SSO (`_check_redirect`), HTTP 401/403 en la petición HTML o página de login identificable (formulario con `id="login-form"` o `name="username"` y ausencia de controles de campos). Un 200 válido sin controles de campos personalizados **no** fija este fallo. Una vez fijado, no se vuelve a pedir el formulario para ningún proyecto.

Se memorizan los fallos para no repetir la misma petición fallida: el informe ODS recorre todos los proyectos y, sin caché negativa global del HTML, un informe con N proyectos haría N peticiones condenadas a redirección a login. Con la caché global se hace como máximo **una** petición HTML fallida por cliente. Un 200 con HTML válido pero sin controles se memoriza como negativo **por proyecto** (puede ser legítimo: campos de solo lectura u otro tracker) y no bloquea la resolución del resto de proyectos. Los fallos del formulario HTML no relacionados con autenticación (500, timeout, conexión) se memorizan por proyecto; ese matiz «por proyecto» aplica solo al resultado del formulario HTML sin controles, no al fallo de `/custom_fields.json`, que es global. El fallo de la pertenencia **no** se cachea: la siguiente llamada reintenta.

`clear_custom_field_cache()` vacía los mapas, los motivos y el fallo global; se expone para tests y para un futuro refresco manual. La invalidación por cambio de URL o API key se garantiza por construcción: `MainWindow._conectar_redmine` crea un `RedmineClient` nuevo en cada conexión y la caché vive en la instancia. No hay caché compartida entre clientes ni persistencia.

Se devuelve una lista nueva en cada llamada (`list(...)`) para que un consumidor no pueda mutar la caché interna.

*Alternativas descartadas:* (a) caché global de módulo — sobrevive a cambios de configuración y contamina tests; (b) caché solo por proyecto sin caché global de definiciones — repetiría `GET /custom_fields.json` por cada proyecto en el informe ODS; (c) caché negativa del HTML solo por proyecto — repetiría N redirecciones a login; (d) TTL temporal — complejidad innecesaria para una sesión de escritorio.

### D7. Degradación, diagnóstico y aviso visible sin romper el diálogo

Si un campo no tiene definición resoluble, se devuelve `RedmineCustomField` con `field_format=""`, `multiple=False`, `possible_values=[]`, `definition_source="none"` y un `degraded_reason` legible, que el diálogo trata como formato no soportado (`QLineEdit`, `kind="string"`). Un campo conocido como `list` con `possible_values` vacío **no** se convierte en texto libre: se resuelve como lista sin opciones y el diálogo muestra el combo deshabilitado con "Sin opciones disponibles" y omite el campo del payload, de modo que Redmine conserva el valor previo.

Cada campo devuelto indica su origen en `definition_source`: `"admin"` (nivel 2), `"html"` (nivel 3) o `"none"` (sin resolver). Cada degradación emite un `logger.warning` con `project_id`, `cf_id`, `name` y un motivo legible: permisos insuficientes, 401, cookie no configurada, redirección a login, HTML sin controles, 500/timeout/conexión o campo ausente del formulario (posible solo lectura u otro tracker). Nunca se registra el valor de la cookie ni la API key.

En `TaskDialog`, si algún campo tiene `definition_source == "none"`, se muestra **una sola vez** un `QLabel` de aviso dentro del grupo "Campos personalizados", discreto y no modal, con texto accionable:

> No se pudieron obtener los tipos de algunos campos personalizados. Configura la Cookie de sesión en Ajustes o usa una API key de administrador. Se muestran como texto libre.

El aviso se oculta si todos los campos se resuelven o si el grupo no tiene campos; no se repite por campo y no bloquea el diálogo. Se limpia junto con el resto del grupo al cambiar de proyecto. Se actualiza además la ayuda y el tooltip del campo Cookie en `settings_dialog.py` para explicar que permite resolver campos personalizados cuando la API key no es de administrador.

### D8. Integración con el diálogo, el informe y el payload

El punto principal de integración sigue siendo `get_project_custom_fields`. `TaskDialog` ya elige el control por `field_format`/`multiple`, ya aplica `possible_values`, ya muestra el asterisco de `is_required`, ya aplica `default_value` en altas y ya contiene la regla de conservación de valores previos. `MainWindow` sigue usando `id` y `name`. El único cambio de UI es el aviso de D7.

La conservación del valor previo distingue tres casos:

- **Múltiple con `possible_values` no vacíos**: si el valor previo contiene elementos que no figuran entre las opciones, `_apply_custom_field_values` los inyecta en el `MultiValueCombo` mediante el nuevo `add_missing_items(values)`, que añade los ítems ausentes desmarcados y sin duplicar los existentes; es `set_selected_values(previous)` quien después los marca. El payload envía la selección completa, incluidos los inyectados (por ejemplo `["x", "z"]`). Si el usuario desmarca explícitamente un ítem inyectado, deja de enviarse; si desmarca todos, se envía `[]` como limpieza explícita. Lo cubren `test_multiple_previous_value_partially_representable_preserves_unknown`, `test_multiple_uncheck_injected_previous_value_removes_it` y `test_add_missing_items_appends_without_duplicates`.
- **Múltiple con `possible_values` vacío**: se mantiene el comportamiento anterior; el widget se muestra deshabilitado y el campo se omite del payload para no borrar el valor en Redmine.
- **Lista simple y demás campos con valor previo no representable**: se omite el campo del payload.

El payload no cambia cuando la resolución no aporta información nueva: un valor de lista se envía como texto de la opción, una múltiple como lista de textos y un campo no resoluble como el texto que el usuario ya veía y editaba. Cuando la definición de administrador aporta `is_required` o `default_value`, el diálogo se alinea intencionadamente con Redmine: muestra el asterisco de obligatorio y aplica el valor por defecto en altas. En una tarea existente sin modificar no se alteran los valores representables; los no representables solo se conservan mediante inyección en los múltiples con opciones y, en el resto de casos, se omiten del payload.

*Alternativa descartada:* mover la resolución a `TaskDialog` con un servicio inyectado. Duplicaría la lógica, dejaría el informe ODS sin mejorar y añadiría acoplamiento en la UI sin beneficio funcional.

## Risks / Trade-offs

- **Dependencia del marcado HTML interno de Redmine** (4.2–7.x): el parser se apoya en nombres de control y en la relación valor/etiqueta de `<select>`, pero un tema o plugin podría alterarlos → parser tolerante, fixtures con las variantes soportadas y degradación a texto libre con warning.
- **Ambigüedad `list` vs `bool` en HTML**: un `<select>` con valores `1`/`0` se interpreta como `bool` → heurística explícita y documentada; el payload resultante (`"1"`/`"0"`) es válido para ambos formatos, por lo que el riesgo se limita al control mostrado.
- **Desplegables de `user`/`version`/`enumeration`**: el discriminador valor-etiqueta los deja sin resolver; siguen en texto libre, como antes, sin falsos `QComboBox` con ids.
- **`textarea`, fechas, numéricos y radios/checkboxes** no se resuelven por HTML → quedan en texto libre solo sin administrador; el valor sigue siendo válido para Redmine. No es regresión porque hoy tampoco se resuelven.
- **Campos ausentes del formulario HTML** (solo lectura, ocultos, restringidos a trackers distintos del predeterminado) → quedan en texto libre con warning; se resuelven por la vía de administrador cuando está disponible.
- **Cookie caducada o ausente** → una petición HTML que acaba en login y un warning; el fallo de autenticación se memoriza globalmente para no repetirlo por cada proyecto del informe ODS.
- **Latencia adicional**: una petición global a `/custom_fields.json` por cliente (no por proyecto) y, en el peor caso, una petición HTML por proyecto la primera vez. Mitigado por la caché.
- **Caché potencialmente obsoleta** si un administrador cambia la definición durante la sesión → `clear_custom_field_cache()` y reconexión; se acepta por ser un escritorio con sesiones cortas.
- **Más peticiones en el informe ODS** para proyectos sin campos → se evita consultando definiciones solo si la pertenencia no está vacía.
- **Seguridad**: la cookie de sesión y la API key nunca se registran; los warnings solo incluyen ids, nombres y motivo.
- **Cambio de forma en `possible_values`** (`{value,label}` frente a cadenas) → normalización defensiva y tests con ambas formas.
- **Paginación heterogénea de `/custom_fields.json`** → petición defensiva con `limit`/`offset`; sin `total_count` numérico se hace una sola petición, y con `total_count` superior a lo acumulado se pagina hasta alcanzarlo o recibir una página vacía, con tope de 20 páginas.

## Migration Plan

No hay migración de datos ni cambios de esquema ni de configuración. Pasos:

1. Añadir `status_code` y `_get_text()` a `RedmineClient`, con el mapeo de timeout/conexión, sin cambiar mensajes ni excepciones.
2. Añadir `app/services/custom_field_definitions.py` con `ParsedCustomField` y el parser puro; verificar que no importa `redmine_client`.
3. Ampliar `RedmineCustomField` con `definition_source` y `degraded_reason` (valores por defecto retrocompatibles).
4. Reescribir el interior de `get_project_custom_fields` con la cascada, la paginación defensiva y la caché (incluida la caché negativa global solo para fallos de autenticación del HTML).
5. Añadir el aviso visible en `TaskDialog` y actualizar la ayuda/tooltip del campo Cookie en `settings_dialog.py`.
6. Corregir los fixtures de `tests/test_redmine_custom_fields.py` y añadir los tests nuevos.
7. Ejecutar `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` y verificar la suite completa.

Rollback: revertir el commit. No hay estado persistido ni pasos manuales; una reversión no afecta a los datos de Redmine. El aviso visible desaparece con el código anterior.

## Open Questions

Ninguna bloqueante. Supuestos explícitos: la definición completa solo se garantiza por administrador (D1); la vía HTML no recupera `is_required`, `default_value`, `visible` ni `editable` (D1/D5); el discriminador valor-etiqueta deja sin resolver `user`/`version`/`enumeration` (D5); la heurística `1`/`0` para `bool` (D5); `textarea`, fechas, numéricos y radios/checkboxes no se soportan por HTML (D5); la caché se invalida por nueva instancia de cliente o por `clear_custom_field_cache()` (D6); `/custom_fields.json` sin `total_count` numérico se consulta en una sola petición y con `total_count` se pagina de forma defensiva tolerando que ignore `limit`/`offset` (D1).
