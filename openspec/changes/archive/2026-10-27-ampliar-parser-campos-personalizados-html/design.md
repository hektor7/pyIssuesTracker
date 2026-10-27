## Context

PyIssuesTracker es una aplicación PyQt6 con el parser puro de formularios Redmine en `app/services/custom_field_definitions.py`, consumido por `RedmineClient._get_project_issue_form_definitions()` y probado con pytest (`QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`).

Estado actual verificado:

- `parse_issue_form_custom_fields()` solo procesa `<select>`: lista simple, lista múltiple y booleano 1/0. Ignora explícitamente `textarea`, `input` y grupos de radios/checkboxes, de modo que el booleano de Redmine core renderizado como `checkbox` + `hidden` queda hoy en `definition_source="none"`.
- `TaskDialog._build_custom_field_widget()` ya sabe renderizar `text` (`QPlainTextEdit`), `date` (`QDateEdit`), `int` (`QSpinBox`), `string` (`QLineEdit`) y `bool` (`QCheckBox`); el problema no está en el diálogo sino en que esos formatos nunca llegan desde la vía HTML.
- `TaskDialog._load_custom_fields_for_project()` muestra el aviso si y solo si algún campo tiene `definition_source == "none"`. No requiere lógica nueva.
- El cambio archivado `2026-10-26-obtener-definiciones-campos-personalizados` recortó deliberadamente estos controles porque la vía de administrador los resolvía. Este cambio **supera ese non-goal** para la vía HTML: sin API admin, el HTML es la única fuente y el recorte produce un falso positivo del aviso.

Restricciones: sin dependencias nuevas (`html.parser` de la stdlib), sin ciclo de imports, sin cambios en `redmine_client.py` ni en `task_dialog.py`, y sin tocar el contrato de `get_project_custom_fields`.

## Goals / Non-Goals

**Goals:**

- Resolver `text`, `date`, `int`, `string` y el booleano de Redmine core (`checkbox` + `hidden` con el mismo nombre) desde el formulario HTML con el mapeo de controles estándar de Redmine.
- Eliminar el falso positivo del aviso al hacer que esos campos pasen a `definition_source="html"`.
- Conservar el comportamiento de listas, booleanos por `<select>`, `hidden` no emparejado, radios/checkboxes y del discriminador `value == etiqueta`, y preservar el orden de aparición de los campos en el documento **en el diccionario del parser**; la lista pública mantiene el orden de la pertenencia.
- Documentar las limitaciones inevitables del HTML (int/float reales y fechas antiguas indistinguibles de string).
- Cubrir con tests TDD la precedencia, la robustez, la integración con el diálogo y la regresión.

**Non-Goals:**

- Reconocer grupos de radios o checkboxes (incluidas las listas con `edit_tag_style = check_box`). El único `checkbox` reconocido es el booleano core con nombre sin sufijo `[]` y acompañado de un `hidden` del mismo nombre; los checkboxes con sufijo `[]` siguen fuera de alcance.
- Soportar definiciones por tracker ni campos de solo lectura/ocultos que no aparecen en el formulario, incluidos los campos de otro tracker ausentes del formulario HTML.
- Obtener `is_required`, `default_value`, `visible` o `editable` desde HTML.
- Sustituir la API de administrador cuando esté disponible.
- Reparar datos corrompidos o normalizar valores previos ya guardados.
- Implementar login automático u obtener cookies.
- Cambiar la lógica del diálogo, del cliente o del payload.

## Decisions

### D1. Tabla de mapeo control → `field_format` y precedencia

| Control (nombre `issue[custom_field_values][N]`) | Señal | Resultado |
|---|---|---|
| `<select>` con valores no vacíos exactamente `1` y `0` | sin atributo `multiple` y sin sufijo `[]` | `bool`, `multiple=False` |
| `<select>` simple | todos los `value` no vacíos == etiqueta | `list`, `multiple=False`, etiquetas en orden |
| `<select multiple>` o nombre con sufijo `[]` | 1/0 o discriminador de lista | `list`, `multiple=True` |
| `<textarea>` sin sufijo | — | `text`, `multiple=False` |
| `<input type="date">` sin sufijo | — | `date`, `multiple=False` |
| `<input type="number">` sin sufijo | — | `int`, `multiple=False` |
| `<input type="text">` sin sufijo | — | `string`, `multiple=False` |
| `<input type="checkbox">` + `<input type="hidden">` con el MISMO nombre sin sufijo `[]` | par checkbox/hidden de Redmine core | `bool`, `multiple=False`, sin `possible_values` |
| `<input type="hidden">` | — | se descarta como control propio; solo se consume al formar el par de bool |
| `<input type="radio|checkbox|file|submit|...">` | `checkbox` con sufijo `[]`, `checkbox` sin pareja `hidden`, o cualquier otro tipo | se ignora |
| `<select>` con valores tipo id (user/version/enumeration) | no cumple el discriminador | no se reconoce |
| Nombre ajeno al patrón o `type` ausente/desconocido | — | se ignora |

Precedencia explícita:

1. `input[type="hidden"]` nunca produce una definición por sí solo, incluido el `hidden` vacío que Redmine añade para múltiples. Si comparte el nombre exacto (sin sufijo `[]`) con un `checkbox`, ambos forman el par booleano y el resultado es `bool`; el `hidden` no se clasifica como `string`.
2. En un `<select>`, la comprobación `1`/`0` (`bool`) se evalúa **antes** del discriminador de lista, pero solo aplica si el control **no es múltiple** (sin atributo `multiple` y sin sufijo `[]`). Un `<select multiple>` con valores `1`/`0` se evalúa con el discriminador y se resuelve como `list` con `multiple=True`.
3. Un `<select>` reconocido para un id prevalece sobre cualquier `<input>`/`<textarea>` o par `checkbox` + `hidden` del mismo id, porque es la señal más específica y la única que aporta `multiple`/`possible_values`. Entre los dos restantes, el par `checkbox` + `hidden` prevalece sobre un `<input>`/`<textarea>` del mismo id: el par es una señal booleana completa y el input suelto sería una lectura ambigua del mismo id. No es un caso observable en el HTML real de Redmine (un id genera un único control), pero la regla debe ser determinista y no depender del orden de las ramas.
4. Entre controles del mismo tipo para el mismo id prevalece la **primera aparición reconocida**, deduplicando por id también en `input`/`textarea`: un segundo control del mismo id no sobrescribe el candidato ya aceptado. El par `checkbox` + `hidden` cuenta como un único control de tipo booleano.
5. Los grupos de radios/checkboxes nunca se agrupan ni se reconocen, aunque compartan nombre. El único `checkbox` aceptado es el de nombre sin `[]` que tiene un `hidden` pareja con el mismo nombre.

Implementación: el parser acumula candidatos por id junto con la posición de la primera aparición real de ese id en el documento, distinguiendo `select`, `input`/`textarea` y pares `checkbox` + `hidden`. La posición del par se registra en cuanto se completa (al llegar el segundo de sus dos controles), no al fusionar, para que un `select` posterior del mismo id no la sustituya por una posición más tardía. La deduplicación por id con **primera aparición reconocida** se aplica también a `input`/`textarea`: un segundo control del mismo id no sobrescribe el candidato ya aceptado. Al finalizar elige una definición ganadora por id según la precedencia (select > par checkbox+hidden > input/textarea) y emite los ids **ordenados por su primera aparición en el documento**, no por tipo, en el diccionario devuelto por `parse_issue_form_custom_fields`. Así, un `textarea` del campo A que aparece antes que un `select` del campo B produce A antes que B, y un `select` posterior para el mismo id no adelanta la posición de ese campo. Ese orden es interno del parseo y de la fusión; la lista pública de `get_project_custom_fields` sigue el orden de la pertenencia y no se reordena por el documento. La precedencia es determinista y no depende del orden de las ramas en `handle_starttag`.

*Alternativas descartadas:* (a) escribir directamente en un único diccionario según llega el tag — hace que un `<input>` anterior gane a un `<select>` posterior, contra la precedencia pedida; (b) expresiones regulares sobre el HTML — frágiles con atributos en cualquier orden; (c) clasificar todo `input[type=text]` como `float` — rompe `string` y enmascara enteros.

### D2. Nombres de control y multiplicidad

Se reutiliza el patrón `^issue\[custom_field_values\]\[(?P<id>\d+)\](?P<multiple>\[\])?$`. El sufijo `[]` solo tiene efecto en `<select>` (multiplicidad) y en los controles que se descartan. Para `textarea` e `input` se exige ausencia de sufijo: los controles con `[]` y tipo no-select corresponden a grupos de checkboxes/radios y se ignoran. El par booleano `checkbox` + `hidden` se reconoce únicamente cuando ambos nombres son exactamente el nombre del campo **sin** `[]`; un `checkbox` con sufijo `[]` no se reconoce aunque tenga un `hidden` con el mismo sufijo. `multiple` queda siempre `False` en `text`, `date`, `int`, `string` y `bool`.

### D3. Limitaciones inevitables del HTML y documentación

- `int` y `float` reales comparten `<input type="text">`; ambos se resuelven como `string`. Es una pérdida de fidelidad aceptable: el control de texto libre envía la misma cadena que Redmine espera y no rompe valores previos.
- Las versiones antiguas de Redmine renderizan `date` como `<input type="text">`; se resuelven como `string`, no como `date`.
- `input type="number"` se mapea a `int`; no se distingue `float` porque Redmine no emite `type="number"` con paso decimal de forma fiable.
- `text` con `edit_tag_style` distinto de `textarea` y listas con `edit_tag_style = check_box` siguen sin resolverse.
- Los grupos de radios o de checkboxes con sufijo `[]` siguen sin resolverse.
- El booleano de Redmine core (`checkbox` + `hidden` con el mismo nombre sin `[]`) **sí** se resuelve como `bool`; no queda como limitación.
- Los campos de otro tracker o los controles ocultos que no aparecen en el formulario siguen sin poder resolverse.

Estas limitaciones se documentan junto a la tabla de controles y la precedencia en el docstring del módulo.

### D4. El aviso es consecuencia de `definition_source`, no lógica nueva

`TaskDialog` ya calcula `any(definition_source == "none")`. Al resolver más formatos por HTML, esos campos dejan de ser `"none"` y el aviso desaparece sin tocar el diálogo. No se añade ninguna condición nueva, ningún flag y ningún texto. La spec solo explicita el resultado esperado: aviso ausente cuando todos los campos del proyecto se resuelven por HTML y presente cuando alguno queda `"none"` (por ejemplo, un campo de otro tracker o un grupo de radios).

*Alternativa descartada:* inferir en el diálogo si el formato es "suficiente" para ocultar el aviso; duplicaría la fuente de verdad y ocultaría degradaciones reales.

### D5. Robustez y determinismo

- HTML vacío, malformado, parcial o página de login → `{}`, sin lanzar.
- El parser no importa `redmine_client` (dirección `redmine_client` → `custom_field_definitions`).
- Se aplica `html.unescape` y `strip` a nombres de opción y valores como hoy; las opciones de un mismo `<select>` **no** se deduplican.
- Se deduplican ids: primera aparición reconocida por tipo, incluidos `input`/`textarea`; la precedencia de D1 decide qué definición gana.
- `input`/`textarea` sin `name` válido o con id no numérico se ignoran.
- Un `<select>` sin cerrar sigue descartándose (comportamiento actual).
- Un `hidden` sin pareja `checkbox` del mismo nombre y sin `[]` no produce definición `string`; se descarta. Un `checkbox` sin `hidden` pareja tampoco se reconoce.
- La fusión entre tipos conserva la primera aparición de cada id en el documento **en el diccionario del parser**; la prioridad `select` > `input`/`textarea` solo decide qué definición gana para ese id, no su posición. La lista pública de `get_project_custom_fields` sigue el orden de la pertenencia y no se reordena por el documento.

## Risks / Trade-offs

- **[Un `input[type=text]` de un campo multivalor podría confundirse con string]** → Se exige que el nombre no lleve sufijo `[]`; los multivalores de Redmine se renderizan como `select multiple` o checkboxes, no como input simple.
- **[El `hidden` "0" del booleano podría clasificarse como `string`]** → El `hidden` se descarta como control propio y solo se consume al formar el par con un `checkbox` del mismo nombre sin `[]`; hay test explícito de que un `hidden` sin sufijo no produce `string`.
- **[Un checkbox de grupo con `[]` podría confundirse con el bool core]** → El par booleano exige nombre exacto sin `[]`; los checkboxes con sufijo `[]` siguen ignorándose.
- **[Un `select multiple` con 1/0 podría clasificarse como `bool`]** → La comprobación 1/0 exige ausencia de `multiple` y de sufijo `[]`; si es múltiple se resuelve como `list` con `multiple=True`.
- **[Regresión en listas por cambios en el flujo del parser]** → Tests de caracterización de select simple/múltiple/bool/discriminador e integración con `QComboBox`/`MultiValueCombo`.
- **[Orden de los campos alterado al fusionar por tipo]** → La emisión del diccionario del parser se ordena por la primera aparición de cada id en el documento, con test de orden entre `textarea` y `select` de ids distintos; la lista pública no se reordena.
- **[Falso negativo nuevo: campo `float` mostrado como `QLineEdit`]** → Aceptado y documentado; el payload sigue siendo válido y el control permite escribir decimales.
- **[HTML de versiones antiguas con `date` como texto]** → Aceptado y documentado; se resuelve como `string`.
- **[Doble control para el mismo id en HTML malformado]** → Precedencia determinista `select` > `input`/`textarea`, primera aparición; el par checkbox+hidden cuenta como un solo control.
- **[El aviso sigue apareciendo por campos legítimamente no resolubles]** → Es el comportamiento correcto: la degradación es real (radios, checkboxes múltiples, otro tracker, solo lectura).

## Migration Plan

- Sin migración de datos ni cambios de esquema; los valores existentes no se tocan.
- Despliegue: actualizar el módulo y los tests; no requiere configuración nueva.
- Rollback: revertir el commit del módulo y de los tests. Al no haber datos persistidos ni cambios de contrato, el rollback es inmediato.
- Verificación: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`, `openspec validate "ampliar-parser-campos-personalizados-html" --type change` y `openspec status --change ... --json`.
