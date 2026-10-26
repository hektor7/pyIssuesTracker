## Why

Los campos personalizados de Redmine de tipo lista ("Causa de la Incidencia") se muestran en el diálogo de tarea como caja de texto libre, mientras que los de texto libre ("Remitente de la Petición") se muestran bien solo por casualidad. La causa está verificada en código y en el código fuente de Redmine: `get_project_custom_fields()` obtiene la pertenencia al proyecto con `GET /projects/{id}.json?include=issue_custom_fields`, pero ese `include` serializa únicamente `id` y `name` (`api.custom_field(:id => ..., :name => ...)` en `app/helpers/projects_helper.rb`). Como consecuencia, `field_format` llega vacío, `multiple` llega falso y `_build_custom_field_widget()` cae siempre en el fallback de `QLineEdit`: las ramas `list`, `multiple`, `date`, `bool`, `int` y `float` son inalcanzables en producción. Los tests actuales no lo detectan porque su fixture asume datos que la API real no devuelve.

## What Changes

- La obtención de campos personalizados pasa a resolver la definición mediante una cascada de tres niveles: API de definiciones con permisos de administrador, formulario HTML de nueva incidencia con cookie de sesión como alternativa sin administrador, y texto libre como último recurso. La definición completa (`is_required`, `default_value`, `visible`, `editable`) solo se garantiza por la vía de administrador; la vía HTML resuelve únicamente `field_format`, `multiple` y `possible_values`.
- El parser HTML se recorta al objetivo real del cambio: `<select>` simple y múltiple (lista) y `<select>` con valores exactos `1`/`0` (booleano). Se descarta el soporte de `textarea`, fechas, numéricos, radios y grupos de checkboxes: no resolverlos no es regresión porque hoy ya se muestran como texto libre, y la ruta de administrador sí los resuelve todos.
- El parser vive en un módulo puro sin ciclo de imports: `app/services/custom_field_definitions.py` define su propia dataclass `ParsedCustomField` y `parse_issue_form_custom_fields(html) -> dict[int, ParsedCustomField]`. `RedmineClient` importa ese módulo y mapea a `RedmineCustomField`; nunca al revés.
- Se añade un discriminador de `<select>` para evitar falsos positivos: solo se clasifica como `list` si todos los valores no vacíos coinciden exactamente con el texto de su etiqueta. Los desplegables de `user`, `version` y `enumeration` usan `value="ID"` con etiqueta distinta y quedan sin resolver, respetando el Non-Goal. La excepción previa es el `<select>` con valores exactos `1` y `0`, que se clasifica como `bool`.
- Se añade caché en memoria por proyecto, caché global de definiciones y caché negativa global del fallo de autenticación del formulario HTML, con invalidación explícita y por cambio de cliente (URL/API key).
- Se añade a la capa HTTP la capacidad de devolver el cuerpo HTML de una página y de exponer el código de estado en los errores. `_get_text` mapea `httpx.ConnectError` y `httpx.TimeoutException` a `RedmineConnectionError`. La cascada captura cualquier `RedmineError` de los niveles 2 y 3 y solo propaga el fallo de la pertenencia.
- Se toca la UI de forma acotada: si algún campo queda sin definición (`definition_source == "none"`), el diálogo de tarea muestra un aviso discreto, no modal y no repetido por campo dentro del grupo "Campos personalizados", con instrucciones para configurar la Cookie de sesión o usar una API key de administrador. Se actualiza la ayuda/tooltip del campo Cookie en Ajustes.
- Se corrigen los fixtures engañosos y se añade cobertura de la cascada, del parseo HTML, de la caché, del caso sin administrador, de la paginación defensiva de `/custom_fields.json`, de la alineación del payload con Redmine y del aviso visible.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `campos-personalizados-tarea`: la obtención de campos deja de asumir que el `include` del proyecto trae la definición y se especifica la cascada de resolución, el filtrado por tipo y proyecto, la caché, la degradación a texto libre con diagnóstico, el aviso visible en el diálogo, la alineación intencional del payload cuando la definición aporta `is_required` o `default_value` y el alcance real de la definición según la vía de resolución.

## Impact

- `app/services/redmine_client.py`: resolución en cascada, caché, `_get_text()`, `_raise_for_status()`, `status_code` en `RedmineError`, `definition_source` y `degraded_reason` en `RedmineCustomField`.
- `app/services/custom_field_definitions.py` (nuevo): dataclass `ParsedCustomField`, parseo puro del formulario HTML y normalización de `possible_values`, con la librería estándar (`html.parser`), sin dependencias nuevas y sin importar `redmine_client`.
- `app/dialogs/task_dialog.py`: aviso visible y accionable cuando hay campos con `definition_source == "none"`; no cambia la lógica de widgets ni el contrato general de serialización.
- `app/dialogs/settings_dialog.py`: texto de ayuda y tooltip del campo Cookie explicando su papel en la resolución de campos personalizados cuando la API key no es de administrador.
- `MANUAL.md` (opcional): documentar la Cookie de sesión y el aviso de degradación.
- `tests/test_redmine_client.py`: cobertura de la capa HTTP (`_get_text`, `status_code`, timeout, conexión y redirecciones).
- `tests/test_redmine_custom_fields.py`: corrección de los fixtures y cobertura de la cascada, la caché, la paginación y el alcance de la definición.
- `tests/test_custom_field_definitions.py` (nuevo): contrato del parser, discriminador de `<select>`, lista, múltiple, booleano y controles no soportados.
- `tests/test_custom_field_resolution_integration.py` (nuevo): cliente real con HTTP mockeado hasta el `TaskDialog`, incluido el aviso visible y la alineación de obligatoriedad/valor por defecto.
