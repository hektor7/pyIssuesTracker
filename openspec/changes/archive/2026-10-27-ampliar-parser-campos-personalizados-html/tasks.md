## 1. Preparación y línea base

- [x] 1.1 Confirmar la línea base en headless con la suite completa en verde: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`.
- [x] 1.2 Ejecutar la caracterización actual del recorte: `tests/test_custom_field_definitions.py::TestControlesNoSoportados` debe pasar afirmando que `textarea`, `input date`, `input number` e `input text` devuelven `{}` antes del cambio. Dejarlo documentado como comportamiento a modificar.
- [x] 1.3 Revisar el contrato vigente de `ParsedCustomField` y del patrón `issue[custom_field_values][N]` en `app/services/custom_field_definitions.py`, y confirmar que la dirección de dependencia `redmine_client` → `custom_field_definitions` no cambia.
- [x] 1.4 Revisar los fixtures existentes en `tests/fixtures/custom_field_forms/` y decidir si basta con HTML inline para los nuevos controles (sin añadir dependencias ni fixtures innecesarios).

## 2. Parser: textarea, date, number y text (RED/GREEN)

- [x] 2.1 **RED** — Añadir en `tests/test_custom_field_definitions.py` `test_textarea_se_resuelve_como_text`: un `<textarea name="issue[custom_field_values][7]">` devuelve `field_format="text"`, `multiple=False` y `possible_values=[]`; verificar que falla (hoy devuelve `{}`).
- [x] 2.2 **GREEN** — Implementar en el parser el reconocimiento de `textarea` con nombre válido y sin sufijo `[]`, sin tocar el resto de controles; hacer pasar 2.1.
- [x] 2.3 **RED** — Añadir `test_input_date_se_resuelve_como_date`: `<input type="date" name="issue[custom_field_values][8]">` devuelve `field_format="date"`, `multiple=False` y `possible_values=[]`; verificar que falla hoy (devuelve `{}`).
- [x] 2.4 **GREEN** — Implementar el reconocimiento de `input` con `type="date"`, descartando sufijo `[]`; hacer pasar 2.3.
- [x] 2.5 **RED** — Añadir `test_input_number_se_resuelve_como_int`: `<input type="number" name="issue[custom_field_values][9]">` devuelve `field_format="int"`, `multiple=False` y `possible_values=[]`; verificar que falla hoy (devuelve `{}`).
- [x] 2.6 **GREEN** — Implementar el reconocimiento de `input` con `type="number"`, descartando sufijo `[]`; hacer pasar 2.5.
- [x] 2.7 **RED** — Añadir `test_input_text_se_resuelve_como_string` con `<input type="text" name="issue[custom_field_values][10]">`; verificar que falla.
- [x] 2.8 **GREEN** — Implementar `input type="text"` → `string` con `multiple=False`; hacer pasar 2.7.
- [x] 2.9 **CARACTERIZACIÓN** (tras 2.8) — Añadir `test_valores_no_estandar_renderizados_como_texto_se_resuelven_como_string`, parametrizado con dos `input type="text"` (uno decimal y otro fecha ISO): ambos devuelven `string`; verificar que ya pasan con la rama `string` de 2.8 y dejarlos en verde.
- [x] 2.10 **GREEN/DOCUMENTACIÓN** — Confirmar que la rama `string` cubre ambos casos sin heurísticas adicionales y documentar la limitación en el docstring del módulo; 2.9 queda en verde.

## 3. Precedencia, hidden, radios y checkboxes

- [x] 3.1 **RED real (tras la sección 2)** — Añadir `test_select_prevalece_sobre_input_del_mismo_id`: un `<input type="text">` seguido de un `<select>` reconocible para el mismo id se resuelve como `list` con las opciones del select. No era CARACTERIZACIÓN: tras 2.8 el `input` ya se reconoce como `string`, así que el test fallaba con `string` y 3.2 lo deja en verde con la fusión por precedencia.
- [x] 3.2 **GREEN** — Separar candidatos de `select` y de `input`/`textarea`, fusionarlos al finalizar dando prioridad al `select` y conservando la primera aparición reconocida por tipo. Aplicar la deduplicación por id con "primera aparición reconocida" también a `input`/`textarea`: un segundo control del mismo id NO debe sobrescribir el candidato ya aceptado. Mantener 3.1 en verde. En este paso la emisión puede seguir agrupada por tipo: el orden del documento se aborda en 3.17/3.18.
- [x] 3.3 **CARACTERIZACIÓN** (tras 3.2) — Añadir `test_primera_aparicion_prevalece_entre_controles_del_mismo_tipo`: dos `input` del mismo id sin `select` (primero `type="text"`, después `type="date"`) conservan la primera definición reconocida (`string`), y dos `select` del mismo id conservan la primera (`list` con las opciones del primero); verificar que pasa tras la deduplicación de 3.2 y dejarlo en verde.
- [x] 3.4 **CARACTERIZACIÓN** — Añadir `test_hidden_sigue_ignorado_con_los_nuevos_controles`: comparar el resultado de un HTML con `textarea`/`date`/`number`/`text` más un `input type="hidden"` vacío del campo 15 contra el mismo HTML sin el `hidden`; ambos resultados son idénticos y el id 15 no aparece. Verificar que ya pasa hoy (ambos resultados vacíos) y que sigue pasando tras 2.2/2.4/2.6/2.8 con los demás controles resueltos; dejarlo en verde.
- [x] 3.5 **GREEN/DOCUMENTACIÓN** — Descartar explícitamente `input[type="hidden"]` antes de clasificar cualquier otro `input` y documentar que nunca produce definición propia; 3.4 queda en verde.
- [x] 3.6 **CARACTERIZACIÓN** — Añadir `test_controles_no_select_con_sufijo_corchetes_no_se_reconocen`: `name="...[]"` en `input`/`textarea` no produce definición; verificar que ya pasa hoy (todo `input`/`textarea` se ignora) y que sigue pasando tras 2.2/2.4/2.6/2.8 con la restricción de sufijo; dejarlo en verde.
- [x] 3.7 **GREEN/DOCUMENTACIÓN** — Restringir el sufijo `[]` a `select` y exigir ausencia de sufijo en `input`/`textarea`; 3.6 queda en verde.
- [x] 3.8 **CARACTERIZACIÓN** — Renombrar el test actual de controles no soportados a `test_grupo_de_radios_no_se_reconoce` para que solo afirme que el grupo de radios no se reconoce, y mantener `test_grupo_de_checkboxes_no_se_reconoce`; verificar que quedan en verde con el nuevo parser.
- [x] 3.9 **RED** — Añadir `test_bool_checkbox_con_hidden_se_resuelve_como_bool`: `<input type="checkbox" name="issue[custom_field_values][11]" value="1">` más `<input type="hidden" name="issue[custom_field_values][11]" value="0">` devuelve `field_format="bool"`, `multiple=False` y `possible_values=[]`; verificar que falla hoy (devuelve `{}`).
- [x] 3.10 **GREEN** — Implementar el par booleano: `checkbox` sin sufijo `[]` con un `hidden` del MISMO nombre se resuelve como `bool` y el `hidden` se consume sin generar definición propia; hacer pasar 3.9.
- [x] 3.11 **CARACTERIZACIÓN** — Añadir `test_hidden_sin_sufijo_no_se_resuelve_como_string`: un `<input type="hidden" name="issue[custom_field_values][12]" value="0">` sin checkbox pareja no produce definición y NO se clasifica como `string`; verificar que ya pasa hoy (el parser ignora todo `input`) y que tras 3.10 sigue pasando; dejarlo en verde.
- [x] 3.12 **GREEN/DOCUMENTACIÓN** — Descartar como control propio todo `hidden` que no forme par booleano, incluido el `hidden` sin sufijo `[]`; 3.11 queda en verde.
- [x] 3.13 **CARACTERIZACIÓN** — Añadir `test_checkbox_con_sufijo_corchetes_sigue_sin_reconocerse`: `checkbox` y `hidden` con nombre `...[]` no producen definición aunque compartan nombre; verificar que ya pasa hoy (el parser ignora todo `input`) y que tras 3.10/3.12 sigue pasando; dejarlo en verde.
- [x] 3.14 **GREEN/DOCUMENTACIÓN** — Restringir el par booleano al nombre exacto sin `[]`; 3.13 queda en verde.
- [x] 3.15 **RED** — Añadir `test_select_multiple_1_0_se_resuelve_como_lista_no_bool`: un `<select multiple>` (o con sufijo `[]`) con valores `1` y `0` devuelve `list` con `multiple=True`; verificar que falla hoy porque se clasifica como `bool`.
- [x] 3.16 **GREEN** — Evaluar la comprobación 1/0 solo cuando el `select` no es múltiple; hacer pasar 3.15.
- [x] 3.17 **RED** — Añadir `test_orden_entre_tipos_preserva_el_documento`: un `textarea` del campo 7 antes de un `select` de lista del campo 3 devuelve las claves en orden `[7, 3]`; verificar que falla antes de 3.18: hoy solo se reconoce el campo 3 y, tras 3.2, la emisión agrupada por tipo no garantiza `[7, 3]`.
- [x] 3.18 **GREEN** — Fusionar eligiendo la definición ganadora por id pero emitiendo los ids por su primera aparición en el documento, también entre tipos; incluir el caso de un `select` posterior del mismo id que no adelanta la posición; hacer pasar 3.17.

## 4. Integración con el diálogo (403 + Cookie)

- [x] 4.1 **CARACTERIZACIÓN/INTEGRACIÓN (no RED)** — Añadir en `tests/test_custom_field_resolution_integration.py` `test_lista_textarea_fecha_por_html_se_renderizan_con_su_widget`: `GET /custom_fields.json` responde 403, hay `session_cookie` y el HTML contiene un `select` de lista, un `textarea` y un `input type="date"`; esperar `QComboBox`, `QPlainTextEdit` y `QDateEdit`. Pasó a la primera porque la sección 2 ya había ampliado el parser; no se revirtió código para forzar un fallo artificial.
- [x] 4.2 **GREEN** — Confirmar que la integración pasa solo con el parser ampliado, sin tocar `redmine_client.py` ni `task_dialog.py`; corregir únicamente el parser si falla.
- [x] 4.3 **CARACTERIZACIÓN** — Añadir `test_campos_resueltos_por_html_tienen_definition_source_html` para lista, textarea, date, number, text y booleano core, comprobando `definition_source == "html"` y que no hay `degraded_reason`; verificar que ya pasa con el parser ampliado de las secciones 2 y 3 y dejarlo en verde.
- [x] 4.4 **GREEN/DOCUMENTACIÓN** — Confirmar que la fusión del cliente asigna `"html"` a todos los formatos nuevos sin cambios en `redmine_client.py`; 4.3 queda en verde.
- [x] 4.5 **CARACTERIZACIÓN/INTEGRACIÓN (no RED)** — Añadir `test_aviso_no_aparece_cuando_lista_textarea_fecha_se_resuelven_por_html`: el `QLabel` de aviso no es visible. Pasó a la primera porque textarea/date ya se resuelven por HTML; el aviso es consecuencia de `definition_source`, no lógica nueva del diálogo.
- [x] 4.6 **GREEN** — Confirmar que basta con que ningún campo quede `"none"` para ocultar el aviso; no añadir lógica al diálogo; hacer pasar 4.5.
- [x] 4.7 **CARACTERIZACIÓN** — Añadir `test_aviso_aparece_si_queda_un_campo_sin_resolver`: una lista y un `textarea` por HTML más un grupo de radios no reconocido; el aviso es visible una sola vez y el campo de radios es `QLineEdit`; verificar que ya pasa porque el aviso depende de `definition_source == "none"` y el grupo de radios sigue degradado.
- [x] 4.8 **GREEN/DOCUMENTACIÓN** — Verificar que el aviso sigue dependiendo solo de `definition_source == "none"` y que el campo de radios se degrada; 4.7 queda en verde.

## 5. Regresión de listas, booleanos y discriminador

- [x] 5.1 **CARACTERIZACIÓN** — Mantener en verde todos los tests existentes de `TestParseSelectSimple`, `TestSelectMultiple`, `TestSelectBooleano`, `TestDiscriminadorLista`, `TestDesplegablesNoLista`, `TestFiltradoYOrden` y `TestRobustezHTML`.
- [x] 5.2 **CARACTERIZACIÓN** — Mantener en verde `test_lista_resuelta_por_admin_se_renderiza_combo`, `test_lista_resuelta_por_html_se_renderiza_combo`, `test_multiple_resuelto_se_renderiza_como_multivalue` y `test_multiple_resuelto_por_html_se_renderiza_como_multivalue`.
- [x] 5.3 **CARACTERIZACIÓN** — Añadir `test_regresion_lista_bool_por_html_siguen_resolviendose`: HTML con un `select` de lista, un `select` 1/0 y un booleano core (`checkbox` + `hidden`) resuelve `list` y `bool` con `definition_source="html"`; dejarlo en verde como red de seguridad.
- [x] 5.4 **CARACTERIZACIÓN** — Añadir `test_discriminador_no_confunde_user_version_enumeration_con_lista` con los tres tipos, comprobando que siguen sin resolverse; dejarlo en verde.
- [x] 5.5 **CARACTERIZACIÓN** — Revisar el diff final para confirmar que `app/dialogs/task_dialog.py`, `app/services/redmine_client.py`, `requirements.txt` y `pyproject.toml` no cambian.

## 6. Documentación y cierre

- [x] 6.1 Actualizar el docstring de `app/services/custom_field_definitions.py` con la tabla control → `field_format`, la precedencia (hidden descartado/consumido, bool 1/0 solo no múltiple, par checkbox+hidden, select sobre inputs, primera aparición y orden global por documento) y las limitaciones (`int`/`float` reales y fechas antiguas → `string`; radios y checkboxes con `[]` no soportados; campos de otro tracker; sin reparación de datos).
- [x] 6.2 Revisar nombres y textos de tests en español, coherentes con el estilo del repositorio, y eliminar aserciones que documentaban el recorte anterior.
- [x] 6.3 Ejecutar `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` y confirmar la suite completa en verde.
- [x] 6.4 Ejecutar `openspec validate "ampliar-parser-campos-personalizados-html" --type change` y corregir cualquier error de formato o de escenarios.
- [x] 6.5 Ejecutar `openspec status --change ampliar-parser-campos-personalizados-html --json` y confirmar `isComplete: true` con `proposal`, `design`, `specs` y `tasks` en `done`.

## 7. Observaciones de la verificación

- [x] 7.1 **BUG DE ORDEN (bloqueante)** — Corregir `app/services/custom_field_definitions.py`: la posición del par `checkbox`+`hidden` se registra ahora al completarse el par, con la primera aparición real del id, y no en `_merge_candidates`. Añadir test RED/GREEN `test_par_bool_anterior_a_select_conserva_su_posicion`: un par del campo 9 antes de un `select` del campo 3 y de un `select` posterior del campo 9 devuelve las claves `[9, 3]`.
- [x] 7.2 **DOCUMENTACIÓN TDD** — Corregir en este `tasks.md` las etiquetas de 3.1 (RED real tras la sección 2) y de 4.1/4.5 (caracterización/integración, no RED), ajustándolas a lo observado durante la implementación.
- [x] 7.3 **ASSERTS DEL AVISO** — Ampliar `test_aviso_no_aparece_cuando_lista_textarea_fecha_se_resuelven_por_html` para comprobar que el grupo está visible, que los campos 3, 4 y 5 tienen `definition_source == "html"` y que el aviso no es visible.
- [x] 7.4 **COBERTURA** — Añadir tests para: (a) `checkbox` sin `hidden` pareja no se reconoce como `bool`; (b) `hidden` antes del `checkbox` sí forma el par y resuelve `bool`; (c) `get_project_custom_fields` mantiene el orden de la pertenencia aunque el HTML tenga otro orden.
- [x] 7.5 **ACLARACIÓN DESIGN** — Documentar en `design.md` que, para el mismo id, el par `checkbox`+`hidden` prevalece sobre un `input`/`textarea` (y `select` sobre ambos), que la regla es determinista y que no es observable en el HTML real de Redmine.

## 8. Issues de la verificación

- [x] 8.1 **Escenario 26 PARCIAL: fecha con opción de vaciado** — Añadido `test_fecha_por_html_incluye_checkbox_sin_valor_y_vacia_payload` en `tests/test_custom_field_resolution_integration.py`: el campo `date` resuelto por HTML renderiza `QDateEdit`, incluye el `QCheckBox` "Sin valor" y, al marcarlo sobre un valor previo, `custom_fields` envía `""` para ese campo.
- [x] 8.2 **Escenario 48 PARCIAL: aviso con combinación completa** — Añadido `test_combinacion_completa_de_formatos_por_html_sin_aviso`: HTML con los seis formatos resueltos (lista, textarea, date, text, number y bool core) comprueba grupo visible, `definition_source == "html"` en los seis, widgets `QComboBox`/`QPlainTextEdit`/`QDateEdit`/`QLineEdit`/`QSpinBox`/`QCheckBox` y aviso oculto.
- [x] 8.3 **Fixture huérfana** — Verificado con `rg -n "textarea\.html" .` (excluyendo `.venv`) que nadie referencia `tests/fixtures/custom_field_forms/textarea.html`; se eliminó con `git rm`. Los tests de textarea usan HTML inline, conforme al design.
