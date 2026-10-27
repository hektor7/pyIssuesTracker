## Why

Sin API de administrador, el formulario HTML con Cookie de sesión es la única fuente de definiciones de campos personalizados. El parser actual solo reconoce `<select>` (listas y booleanos 1/0), de modo que los campos `text`, `date`, `string`, `int` y el booleano core renderizado como `checkbox` + `hidden` quedan con `definition_source="none"`: se renderizan como `QLineEdit` en lugar de `QPlainTextEdit`/`QDateEdit`/`QCheckBox` y disparan el aviso de "tipos no obtenidos" aunque el campo sí esté visible y editable. El resultado es un falso positivo del aviso y una pérdida de fidelidad de tipos en instalaciones sin administrador.

## What Changes

- Ampliar `parse_issue_form_custom_fields` para reconocer, además de los `<select>` actuales:
  - `<textarea name="issue[custom_field_values][N]">` → `field_format="text"`, `multiple=False`.
  - `<input type="date" name="issue[custom_field_values][N]">` → `field_format="date"`, `multiple=False`.
  - `<input type="number" name="issue[custom_field_values][N]">` → `field_format="int"`, `multiple=False`.
  - `<input type="text" name="issue[custom_field_values][N]">` → `field_format="string"`, `multiple=False`. Incluye los campos `int`/`float` reales y las fechas de Redmine antiguas que se renderizan como texto; la limitación se documenta en el módulo.
  - `<input type="checkbox" name="issue[custom_field_values][N]" value="1">` junto con `<input type="hidden" name="issue[custom_field_values][N]" value="0">` → `field_format="bool"`, `multiple=False`, sin `possible_values`. El `hidden` se consume como parte del par y no se clasifica como `string`.
- Mantener sin cambios el reconocimiento de `<select>` simple/múltiple, el discriminador `value == etiqueta` de las listas y la exclusión de grupos de radios/checkboxes con sufijo `[]`.
- Un `<select>` con valores 1/0 se resuelve como `bool` solo si no es múltiple; un `<select multiple>` (o con sufijo `[]`) con 1/0 se resuelve como `list` con `multiple=True`.
- Un `<input type="hidden">` sin sufijo `[]` (el `0` del booleano) no se clasifica como `string`: se descarta como control propio salvo que forme par con un `checkbox`.
- Conservar el orden de primera aparición de cada campo en el documento, también cuando el HTML mezcla tipos de control; la prioridad de un `<select>` posterior para el mismo id no adelanta la posición del campo.
- Hacer que el aviso de definición incompleta sea preciso por consecuencia, no por lógica nueva: al resolverse más campos pasan a `definition_source="html"` y el aviso solo permanece si algún campo sigue en `"none"`. No se modifica `task_dialog.py`.
- Actualizar la spec de `campos-personalizados-tarea` para reflejar el nuevo mapeo de controles y el alcance real del aviso.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `campos-personalizados-tarea`: la resolución por formulario HTML amplía los controles reconocidos (`textarea`, `input` date/number/text y el par `checkbox` + `hidden` del bool core), precisa que 1/0 solo es `bool` en `select` no múltiple, que el `hidden` sin `[]` no es `string`, que el orden entre tipos sigue el documento y que el aviso visible solo aparece cuando queda algún campo con `definition_source="none"`.

## Impact

- `app/services/custom_field_definitions.py`: único módulo de producción afectado (mapeo de controles y docstring de limitaciones).
- `tests/test_custom_field_definitions.py`: caracterización y nuevos casos de parser.
- `tests/test_custom_field_resolution_integration.py`: integración 403 + Cookie hasta los widgets y el aviso.
- `tests/test_redmine_custom_fields.py`: regresión de la cascada HTML y de `definition_source`.
- `openspec/specs/campos-personalizados-tarea/spec.md` (vía delta): requisitos modificados.
- Sin cambios en `app/dialogs/task_dialog.py`, `app/services/redmine_client.py`, dependencias ni datos persistidos.
