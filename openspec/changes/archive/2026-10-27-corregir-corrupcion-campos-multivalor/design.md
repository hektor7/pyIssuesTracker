## Context

PyIssuesTracker es una aplicación de escritorio PyQt6 (código en `app/`, tests en `tests/`, ejecutados con `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`). La sección "Campos personalizados" del `TaskDialog` construye un control por campo, precarga el valor previo del issue y serializa el valor al aceptar.

### Hechos verificados

- Un campo multivalor de Redmine llega como `value: ["Petición de mejora / …"]`. La definición puede no resolverse (`field_format=""`, `multiple=False`) y entonces `_build_custom_field_widget` (`app/dialogs/task_dialog.py:628`) devuelve `QLineEdit` con `kind="string"`.
- En el código previo al cambio, `_set_custom_field_value` (`app/dialogs/task_dialog.py:783`) ejecutaba `widget.setText(str(value))` en la rama `string`/`text`. Con una lista, `str(value)` producía el `repr` de Python: `['Petición de mejora / …']`.
- En el código previo al cambio, `_read_custom_field_value` (`:821`) devolvía `widget.text().strip()`, es decir, el texto con corchetes y comillas, y `custom_fields` (`:872`) lo reenviaba. Redmine recibía `"['X']"` en lugar de `["X"]`: corrupción de tipo.
- Antes del cambio, `previo_no_representable` solo se evaluaba en la rama `had_value` para `kind in ("list", "multiple")` (lógica en `_apply_custom_field_values`, `:722`), y `custom_fields` (`:872`) solo omitía el campo si el valor serializado quedaba vacío (hoy la omisión incondicional está en `:885`). Un `kind=="list"` con valor previo en forma de lista hacía `findData(str(lista))` sin encontrar opción y podía enviar `""`, borrando el valor.
- La suite existente no cubre el caso "definición no resuelta + valor previo lista", porque los fixtures de los tests de fallback usan valores escalares.

### Restricciones

- Solo se toca este bug: no se cambia la resolución de definiciones, la capa HTTP, el informe ODS ni el payload general.
- Sin dependencias nuevas ni cambios de esquema.
- Los datos ya corrompidos en Redmine no se reparan desde la aplicación.

## Goals / Non-Goals

**Goals:**

- Mostrar los valores previos en forma de lista de forma legible en el fallback de texto (`string` y `text`), sin corchetes ni comillas.
- Conservar el tipo lista en el payload: aceptar sin cambios reenvía la lista original; editar envía una lista de un elemento; vaciar envía `[]`.
- Reforzar la omisión de valores no representables para no borrar datos en Redmine.
- Cubrir con tests de round-trip (aplicar valor previo → leer valor serializado) todos los escenarios.

**Non-Goals:**

- Login automático o cambio del flujo de autenticación.
- Resolver definiciones de campos personalizados (cascada admin/HTML/caché): ya implementado y fuera de alcance.
- Reparar datos ya corrompidos en Redmine (`"['X']"` almacenado como cadena): requiere reparación explícita.
- Soporte específico por tracker.
- Cambiar el renderizado de campos que sí se resuelven como lista o múltiple.

## Decisions

### D1. Renderizado legible de listas en el fallback de texto

Se añade un helper privado único, por ejemplo `_render_previous_text(value)`, que devuelve:

```python
", ".join(str(v) for v in value if v not in (None, "")) if isinstance(value, list) else str(value)
```

Se usa en `_set_custom_field_value` para `kind == "string"` y `kind == "text"` (tanto `QLineEdit.setText` como `QPlainTextEdit.setPlainText`). Nunca se llama `str(lista)` sobre un valor previo en esas ramas.

*Alternativas descartadas:* (a) `repr` explícito — es el bug actual; (b) `QListWidget` o control multivalor para el fallback — cambia la semántica del campo degradado y el contrato de serialización; (c) filtrar solo `None` — dejaría separadores vacíos con elementos `""`.

### D2. Conservación del tipo lista en el payload

En `_apply_custom_field_values`, cuando `kind` es `string` o `text` y `previous` es una lista, se guarda en la entrada:

- `entry["previo_lista"] = list(previous)`
- `entry["previo_texto"] = _render_previous_text(previous)`

En `_read_custom_field_value`, para `string`/`text` con `previo_lista`:

- Si no hubo edición, devolver `list(previo_lista)`.
- Si el usuario modificó el texto y no está vacío, devolver `[texto]` (preserva el tipo multivalor).
- Si lo vació, devolver `[]`.

**Detección de edición (comparación simétrica).** La comprobación de "no modificado" compara el texto CRUDO del widget (`text()`/`toPlainText()`, sin `strip`) con `previo_texto` exacto. `previo_texto` se genera con el helper de D1 sin normalizar, de modo que una lista como `[" A", "B"]` produce `" A, B"` y un widget intacto devuelve también `" A, B"`. El `strip` se aplica solo al construir el valor final editado, nunca antes de decidir si hubo edición. Alternativa admitida: normalizar ambos lados de la comparación de forma simétrica; lo que no se permite es aplicar `strip` solo al texto del widget, porque entonces una lista con espacios se consideraría editada y se corrompería a `["A, B"]`.

**Vaciado y `custom_fields`.** Un valor `[]` devuelto por `_read_custom_field_value` no es una cadena vacía. `custom_fields` comprueba `entry.get("previo_lista")`: si existe y el valor serializado queda vacío (`[]`), reenvía `[]` y NUNCA lo convierte a `""` como hace la rama genérica de texto. Así, vaciar un campo degradado que tenía una lista limpia el multivalor en Redmine conservando el tipo, mientras que el resto de campos `string`/`text` sin `previo_lista` siguen enviando `""` al vaciarse.

La detección de edición no depende de señales de Qt ni de un flag de "modificado", lo que mantiene el comportamiento determinista y testeable sin interacción real.

**Limitación documentada:** escribir comas en el texto no separa elementos; se envía un único elemento con el texto completo. No se reinterpreta el contenido. Si el usuario necesita varios elementos, debe resolverse la definición para obtener el control multivalor real. Además, si el usuario edita el texto para que coincida exactamente con el render previo, se tratará como no modificado y se reenviará la lista original.

*Alternativas descartadas:* (a) dividir por comas — ambigua con valores que contienen comas y puede inventar elementos; (b) enviar siempre `[texto]` aunque no haya edición — rompe el round-trip y altera el valor previo; (c) conservar siempre la lista original e ignorar la edición — pierde la edición del usuario.

### D3. Omisión reforzada de valores no representables

Para `kind == "list"` (selección simple) con `previous` en forma de lista se aplica esta regla explícita:

- Si `len(previous) == 1` y su único valor está en `possible_values`, se normaliza a ese escalar (se selecciona en el combo con `findData`) y el campo se trata como **representable**: no se marca y se envía el valor seleccionado.
- Solo se marca `entry["previo_no_representable"] = True` si `len(previous) != 1` o si el único valor no está en `possible_values` (varios elementos o un único elemento inválido: el combo no puede representarlos).

También se marca `previo_no_representable` cuando `kind` es `list` o `multiple` y `possible_values` está vacío con valor previo no vacío (caso ya cubierto parcialmente, se hace explícito y uniforme).

`custom_fields` omite el campo **siempre** que `entry.get("previo_no_representable")` sea verdadero, con independencia de que el valor serializado sea `""`, `[]` o un valor no vacío (por ejemplo, una opción seleccionada). Así no se borra un valor que el control no puede representar; la omisión no depende de que el widget esté vacío.

No se marca como no representable un `multiple` con `possible_values` no vacíos cuyos valores ausentes se inyectan: esos campos son representables mediante inyección y deben enviarse completos. Igualmente, un `list` con un único valor previo válido en forma de lista NO se omite.

*Alternativas descartadas:* (a) seguir omitiendo solo cuando el valor queda vacío — deja pasar corrupciones cuando el control devuelve texto no vacío; (b) deshabilitar siempre el control — impide limpiar campos representables; (c) omitir por comparación de tipos en `custom_fields` sin marcar la entrada — reparte la lógica y duplica condiciones.

### D4. No reinterpretar cadenas con corchetes

Una cadena legítima como `"['A']"` es texto y se trata como tal: no se convierte con `ast.literal_eval`, regex ni ningún parser ad hoc. La única transformación es lista → texto legible en la carga (D1) y texto → lista en la lectura (D2) cuando el valor previo era una lista.

Los datos ya corrompidos en Redmine (cadena `"['A']"` almacenada) no se detectan ni se reparan: quedan como non-goal y requieren una corrección explícita de datos.

*Alternativas descartadas:* (a) `ast.literal_eval` con `try/except` — convierte texto legítimo en lista por accidente y no distingue corrupción real; (b) regex de corchetes — mismo riesgo y falsos positivos; (c) heurística por prefijo `"[`" — frágil y no solicitada.

### D5. `kind == "text"` recibe el mismo tratamiento que `string`

`QPlainTextEdit` se precarga con el mismo helper de D1 (`setPlainText`) y su lectura aplica las mismas reglas de D2. No hay ramas divergentes entre texto corto y largo: el tipo del valor previo manda, no el widget.

*Alternativas descartadas:* (a) tratar `text` como escalar siempre — mantendría la corrupción en campos de texto largo; (b) crear un `kind` nuevo — amplía el contrato sin necesidad.

## Risks / Trade-offs

- **Edición de un multivalor degradado produce un único elemento** → limitación documentada en D2; el usuario puede corregirlo resolviendo la definición (Cookie o API key de administrador). No se inventan separadores.
- **Falso positivo al omitir si el usuario modifica un campo no representable** → el control está deshabilitado en los casos sin opciones y, en los demás, la comparación con el valor inicial determina si hubo edición; la omisión prioriza conservar el dato en Redmine frente a aplicar un cambio dudoso.
- **Una lista previa con elementos `""` se renderiza sin separadores vacíos** → es el comportamiento deseado (D1) y no altera el payload, que se reconstruye desde `previo_lista`.
- **El texto editado con comas no se separa** → documentado; se prefiere un único elemento literal a una separación ambigua.
- **Sin migración de datos**: los valores ya corrompidos siguen corrompidos → non-goal explícito; se evita que el bug siga produciendo nuevas corrupciones.

## Migration Plan

No hay migración de datos, cambios de esquema ni de configuración. Pasos:

1. Añadir el helper de renderizado y usarlo en `_set_custom_field_value` para `string`/`text`.
2. Guardar `previo_lista` y `previo_texto` en `_apply_custom_field_values` cuando el previo sea lista.
3. Ampliar `_read_custom_field_value` para devolver lista según D2.
4. Marcar `previo_no_representable` según D3 y hacer que `custom_fields` omita siempre esos campos.
5. Añadir los tests de round-trip nuevos; no hay tests existentes que ajustar porque ninguno combina fallback de texto con valor previo lista (verificado en `tests/test_task_dialog_custom_fields.py` y `tests/test_custom_field_resolution_integration.py`).
6. Ejecutar `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` y `openspec validate`.

Rollback: revertir el commit. No hay estado persistido ni pasos manuales; los datos de Redmine no se tocan y la reversión restaura el comportamiento anterior.

## Open Questions

Ninguna bloqueante. Supuestos explícitos: la lista previa se renderiza con `", "` y se reconstruye desde `previo_lista` mientras el texto no cambie (D1/D2); la edición no separa por comas (D2); los no representables se omiten siempre, incluidos los de texto degradado si se marcan (D3); las cadenas con corchetes son texto legítimo (D4); `text` y `string` comparten tratamiento (D5).
