## 1. Preparación

- [x] 1.1 Confirmar la línea base en headless: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` en verde antes de tocar código.
- [x] 1.2 **CARACTERIZACIÓN** — Revisar los tests existentes que podrían fijar el comportamiento antiguo: `test_unsupported_format_falls_back_to_line_edit`, `test_empty_fields_omitted_unless_previously_set`, `test_list_without_options_disabled_with_help`, `test_multiple_without_options_disabled_and_preserves_previous_value`, `test_list_previous_value_outside_options_is_preserved`, `test_multiple_previous_value_partially_representable_preserves_unknown` y `test_aceptar_sin_cambios_conserva_representables_y_omite_no_representables`. **Hecho verificado leyendo `tests/test_task_dialog_custom_fields.py` y `tests/test_custom_field_resolution_integration.py`: hoy NO existe ningún test que combine fallback de texto con valor previo en forma de lista; por tanto no hay que actualizar ningún test antiguo, solo añadir los nuevos.** Mantener los tests listados sin cambios como red de seguridad: ninguno fija el comportamiento antiguo del fallback de lista, por lo que no requieren ajuste.
- [x] 1.3 Localizar los puntos de cambio exactos: `_apply_custom_field_values` (`app/dialogs/task_dialog.py:722`), `_set_custom_field_value` (`:783`), `_read_custom_field_value` (`:821`) y la propiedad `custom_fields` (`:872`), confirmando que no hace falta tocar `_build_custom_field_widget` (`:628`) ni `redmine_client`.

## 2. Renderizado legible de listas en el fallback de texto

- [x] 2.1 **RED** — Añadir en `tests/test_task_dialog_custom_fields.py` `test_fallback_string_renders_previous_list_without_repr` y `test_fallback_text_renders_previous_list_without_repr`: un campo `field_format=""` (o `"link"`) con `previous=["Petición de mejora / usabilidad", "Otra"]` debe mostrar `Petición de mejora / usabilidad, Otra` en `QLineEdit` y en `QPlainTextEdit`, sin `[`, `]` ni comillas. Verificar que fallan con el código actual (`str(lista)`).
- [x] 2.2 **GREEN** — Añadir el helper `_render_previous_text(value)` que devuelve `", ".join(str(v) for v in value if v not in (None, ""))` si `value` es lista y `str(value)` en caso contrario. Usarlo en `_set_custom_field_value` para `kind` "string" y "text"; hacer pasar 2.1.
- [x] 2.3 **CARACTERIZACIÓN** — Añadir `test_render_previous_list_omits_empty_and_none_items`: una lista con `None` y `""` no genera separadores vacíos. Debe pasar con el filtro de 2.2; si no, corregir 2.4.
- [x] 2.4 **GREEN (si 2.3 falla)** — Ajustar el filtro del helper para excluir `None` y `""` sin alterar el orden ni el resto de elementos; hacer pasar 2.3.

## 3. Conservación del tipo lista en el payload

- [x] 3.1 **RED** — Añadir `test_fallback_string_accept_unchanged_resends_original_list` y su variante para `text`: con valor previo `["A", "B"]`, aceptar sin tocar el texto debe devolver en `custom_fields` la lista `["A", "B"]` intacta. Verificar que fallan (hoy devuelven la cadena `"['A', 'B']"`).
- [x] 3.2 **RED** — Añadir `test_fallback_string_unchanged_list_with_spaces_preserves_elements`: con valor previo `[" A", "B"]` (espacio inicial en el primer elemento), aceptar sin tocar el texto debe devolver `[" A", "B"]` intacta. Este test falla si la comparación aplica `strip` solo al texto del widget; cubre la asimetría descrita en D2.
- [x] 3.3 **GREEN** — En `_apply_custom_field_values`, cuando `kind` sea "string"/"text" y `previous` sea lista, guardar `entry["previo_lista"] = list(previous)` y `entry["previo_texto"] = _render_previous_text(previous)`. En `_read_custom_field_value`, comparar el texto CRUDO del widget (sin `strip`) con `previo_texto` exacto y, si coincide, devolver `list(previo_lista)`; hacer pasar 3.1 y 3.2. Aplicar `strip` solo al construir el valor final editado.
- [x] 3.4 **RED** — Añadir `test_fallback_string_edited_resends_single_item_list`: editar el texto a `"Solo este"` debe devolver `["Solo este"]`. Verificar que falla.
- [x] 3.5 **GREEN** — En `_read_custom_field_value`, si hubo edición y el texto (tras `strip`) no está vacío, devolver `[texto]` cuando la entrada tenga `previo_lista`; hacer pasar 3.4. Documentar en el docstring que las comas no separan elementos.
- [x] 3.6 **RED** — Añadir `test_fallback_string_cleared_resends_empty_list_not_empty_string`: vaciar el texto de un campo con `previo_lista` debe producir `custom_fields == {cf_id: []}` y NO `{cf_id: ""}`. Verificar que falla por la conversión genérica de `[]` a `""` en `custom_fields`.
- [x] 3.7 **GREEN** — En `_read_custom_field_value`, si hubo edición y el texto queda vacío, devolver `[]` cuando la entrada tenga `previo_lista`. En `custom_fields`, si la entrada tiene `previo_lista` y el valor serializado es `[]` (o vacío), enviar `[]` y no convertirlo a `""`; hacer pasar 3.6.
- [x] 3.8 **CARACTERIZACIÓN** — Añadir `test_fallback_string_commas_are_single_item`: editar a `"A, B"` envía `["A, B"]` como un único elemento. Dejarlo en verde como contrato de la limitación documentada en D2.

## 4. Refuerzo de la omisión de valores no representables

- [x] 4.1 **RED** — Añadir `test_list_kind_with_single_valid_previous_list_selects_value`: `field_format="list"`, `multiple=False`, `possible_values=["A", "B"]` y `previous=["A"]` debe seleccionar "A" en el combo y enviar `{cf_id: "A"}`; NO debe marcarse como no representable ni omitirse. Verificar que falla (hoy `findData("['A']")` no encuentra opción y el valor se pierde).
- [x] 4.2 **GREEN** — En `_apply_custom_field_values`, para `kind == "list"` con `previous` lista: si `len(previous) == 1` y su único valor está en `possible_values`, normalizarlo a ese escalar antes de `_set_custom_field_value` (para que el combo lo seleccione con `findData`) y tratarlo como representable; hacer pasar 4.1.
- [x] 4.3 **RED** — Añadir `test_list_kind_with_non_representable_previous_list_is_omitted`: `field_format="list"`, `multiple=False` y valor previo en forma de lista con varios elementos (`["A", "B"]`) o con un único elemento ausente de `possible_values` (`["Z"]`) debe marcar `previo_no_representable` y omitir el campo del payload. Verificar que falla.
- [x] 4.4 **GREEN** — En `_apply_custom_field_values`, marcar `entry["previo_no_representable"] = True` solo si `len(previous) != 1` o su único valor no está en `possible_values`; hacer pasar 4.3 sin romper 4.1.
- [x] 4.5 **RED** — Añadir `test_no_representable_with_non_empty_serialized_value_is_omitted`: un campo `list` o `multiple` marcado `previo_no_representable` cuyo control produce un valor no vacío (por ejemplo, forzar la marca y seleccionar una opción válida en el combo) debe seguir omitiéndose de `custom_fields`. Verificar que falla (hoy `custom_fields` solo omite si el valor serializado queda vacío).
- [x] 4.6 **GREEN** — En `custom_fields`, omitir el campo siempre que `entry.get("previo_no_representable")` sea verdadero, sin condicionarlo a `value == ""` ni a `value == []`, de modo que la omisión no dependa de que el widget esté vacío; esto cubre 4.3 y 4.5. Documentar que la marca se fija explícitamente también para listas/múltiples sin opciones.
- [x] 4.7 **CARACTERIZACIÓN** — Añadir `test_list_without_options_previous_value_is_omitted` y `test_multiple_without_options_previous_value_is_omitted`: el comportamiento de escenario 6 ya es correcto hoy (valor serializado vacío + marca existente). Deben pasar y quedar como blindaje; si fallan, corregir en 4.6.
- [x] 4.8 **CARACTERIZACIÓN** — Añadir `test_multiple_with_injectable_values_is_not_marked_not_representable`: un `multiple` con `possible_values` no vacíos y un valor ausente inyectado debe enviar la lista completa y no marcarse como no representable. Dejarlo en verde para blindar que D3 no rompe la inyección.

## 5. No reinterpretar cadenas con corchetes

- [x] 5.1 **CARACTERIZACIÓN** — Añadir `test_string_with_brackets_is_treated_as_text`: con valor previo `"['A']"` en un campo de texto, debe mostrarse tal cual y reenviarse como la cadena `"['A']"`, no como lista `["A"]`. Hoy ya es correcto (el escalar no se transforma), así que debe pasar; si falla, corregir en 5.2.
- [x] 5.2 **GREEN (si 5.1 falla)** — Garantizar que el helper y la lectura solo transforman listas reales (`isinstance(value, list)`) y que no se usa `ast.literal_eval`, regex ni parser ad hoc; hacer pasar 5.1.

## 6. Regresión y confirmación de tests existentes

- [x] 6.1 **CARACTERIZACIÓN** — Añadir `test_plain_string_previous_value_still_roundtrips`: un valor previo escalar en `string`/`text` se muestra y se reenvía sin cambios. Dejarlo en verde.
- [x] 6.2 **CARACTERIZACIÓN** — Añadir `test_representable_multiple_still_sends_full_list`: un `multiple` con `possible_values` no vacíos mantiene el renderizado, la inyección y el payload de lista. Dejarlo en verde.
- [x] 6.3 Confirmar el resultado de 1.2: **hoy NO existe ningún test que combine fallback de texto con valor previo lista**, por lo que no hay que actualizar ningún test antiguo; solo se añaden los nuevos. Mantener los tests existentes de 1.2 sin cambios (red de seguridad) y dejar constancia explícita en el commit o en la nota de la tarea de que no se relajó ninguna aserción. Un fallo en ellos durante 6.4 indicaría un error en la implementación, no en el test.
- [x] 6.4 Ejecutar `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` y confirmar la suite completa en verde.

## 7. Verificación final

- [x] 7.1 Ejecutar `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` y confirmar que no hay fallos ni errores de colección.
- [x] 7.2 Ejecutar `openspec validate "corregir-corrupcion-campos-multivalor" --type change` y corregir el formato sin perder contenido si el validador lo rechaza.
- [x] 7.3 Ejecutar `openspec status --change "corregir-corrupcion-campos-multivalor" --json` y confirmar `isComplete: true` con todos los artefactos en `done`.
- [x] 7.4 Revisar `MANUAL.md`: solo modificar la sección "Campos personalizados y Cookie de sesion" si describe el comportamiento afectado; el detalle de serialización de multivalores degradados no está documentado hoy, así que lo esperado es no cambiarlo.
- [x] 7.5 Confirmar que no se toca `app/services/redmine_client.py`, que no hay dependencias nuevas en `requirements.txt` ni `pyproject.toml` y que el rollback consiste únicamente en revertir el commit.

## 8. Observaciones de la verificación

- [x] 8.1 Documentar y fijar el límite de D2: test de caracterización con `previo_lista=["A","B"]` y `setText("A, B")` (texto idéntico al render) que reenvía `["A","B"]`, y nota en `design.md` D2 de que una edición indistinguible del render se trata como "sin cambios".
- [x] 8.2 Alinear la asimetría de `""`/`None` en `multiple`: excluirlos tanto del cálculo de valores faltantes como del marcado como no representable, con test de multiple con opciones y previo `["A", "", "B"]` que conserva los válidos y no se omite.
- [x] 8.3 Verificar: suite completa en verde (>=801), `openspec validate`, `openspec status`, `git diff --check`/`--stat`/`status --short`, sin dependencias nuevas ni ficheros ajenos.

## 9. Sugerencias de la verificación

- [x] 9.1 **(S1)** En el test de campo string, comprobar `isinstance(entry["widget"], QLineEdit)`.
- [x] 9.2 **(S3)** Comprobar `QSpinBox` para `int` y `QDoubleSpinBox` para `float`, con rango y decimales del float.
- [x] 9.3 **(S4)** Comprobar `QDateEdit` para `date`.
- [x] 9.4 **(S5)** Comprobar `QCheckBox` para `bool`.
- [x] 9.5 **(S11)** Test medible de elisión y tooltip completo en textos largos del selector múltiple.
- [x] 9.6 **(S17/S32)** Test: múltiple con valores inyectados y todos desmarcados envía `{id: []}`.
- [x] 9.7 **(refactor)** Extraer `_previos_y_opciones(previous, field_def)` y usarlo en inyección, normalización de lista y marcado, sin cambio de comportamiento.
- [x] 9.8 Actualizar referencias de línea obsoletas en `design.md` y `tasks.md` (1.3) verificando las líneas reales.
- [x] 9.9 Precisar la redacción del `strip` en el delta de spec (comparación con texto crudo; `strip` solo al construir el valor editado).
- [x] 9.10 Verificación final: pytest, openspec validate/status, git diff/status, sin dependencias ni cambios en `redmine_client.py`.
