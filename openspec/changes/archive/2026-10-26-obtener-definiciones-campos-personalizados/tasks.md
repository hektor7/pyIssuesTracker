## 1. Preparación

- [x] 1.1 Confirmar la línea base en headless: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` en verde antes de tocar código.
- [x] 1.2 Fijar como referencia las fuentes de Redmine verificadas: `render_api_includes` en `app/helpers/projects_helper.rb` (solo `id` y `name`), `custom_fields_controller.rb` (`require_admin`), `custom_fields/index.api.rsb` (`possible_values` con `value`/`label`), `custom_fields_helper.rb` (`custom_field_tag_name`), `lib/redmine/field_format.rb` (render de `list` y `bool`) y las rutas de `config/routes.rb` para `GET /projects/:id/issues/new`.
- [x] 1.3 Guardar en `tests/fixtures/` (o en constantes del test) seis muestras de formulario HTML: `select` simple de lista, `select multiple`, `select` con valores `1`/`0`, `select` con `value` de id y etiqueta distinta (tipo `user`/`version`), `textarea` y página de login sin controles.

## 2. Capa HTTP de `RedmineClient`

- [x] 2.1 **RED** — Añadir en `tests/test_redmine_client.py` `test_error_expone_status_code_por_defecto_y_explicito`: `RedmineError("x").status_code is None` y `RedmineError("x", status_code=403).status_code == 403`; comprobar que falla.
- [x] 2.2 **GREEN** — Ampliar `RedmineError.__init__(message, status_code=None)` sin cambiar mensajes ni el resto del catálogo; hacer pasar 2.1.
- [x] 2.3 **RED** — Añadir `test_get_403_lanza_auth_error_con_status_code` y `test_get_500_lanza_redmine_error_con_status_code`, comprobando tipo, mensaje actual y `.status_code`; comprobar que fallan.
- [x] 2.4 **GREEN** — Extraer `_raise_for_status(resp, path)` desde `_get` y adjuntar `status_code` en 401, 403, 404 y demás errores; hacer pasar 2.3 sin alterar los mensajes existentes.
- [x] 2.5 **RED** — Añadir `test_get_text_devuelve_el_cuerpo_html` con un `httpx` mockeado que devuelve `text="<html>…</html>"`; comprobar que falla porque `_get_text` no existe.
- [x] 2.6 **GREEN** — Implementar `_get_text(path, params=None)` reutilizando `_check_redirect` y `_raise_for_status`, devolviendo `resp.text`; hacer pasar 2.5.
- [x] 2.7 **RED** — Añadir `test_get_text_403_lanza_auth_error_con_status_code`, `test_get_text_404_lanza_redmine_error` y `test_get_text_500_lanza_redmine_error_con_status_code`; comprobar que fallan.
- [x] 2.8 **GREEN** — Completar `_get_text` con el mapeo de errores 401/403/404/500; hacer pasar 2.7.
- [x] 2.9 **RED** — Añadir `test_get_text_timeout_lanza_connection_error` y `test_get_text_connect_error_lanza_connection_error`, verificando `RedmineConnectionError`; comprobar que fallan.
- [x] 2.10 **GREEN** — Mapear `httpx.TimeoutException` y `httpx.ConnectError` a `RedmineConnectionError` en `_get_text`; hacer pasar 2.9.
- [x] 2.11 **RED** — Añadir `test_get_text_redireccion_a_login_lanza_sso_error`; comprobar que falla.
- [x] 2.12 **GREEN** — Reutilizar `_check_redirect` en `_get_text` para que la redirección a login produzca `RedmineSSOError`; hacer pasar 2.11.
- [x] 2.13 **CARACTERIZACIÓN** — Añadir `test_get_sigue_parseando_json_y_mensajes_401_403_intactos` para blindar la retrocompatibilidad de `_get`; dejarlo en verde como red de seguridad, sin cambio pendiente.

## 3. Parser HTML puro (`app/services/custom_field_definitions.py`)

- [x] 3.1 **RED** — Crear `tests/test_custom_field_definitions.py` con `test_parsea_select_simple_como_lista` y `test_contrato_devuelve_parsed_custom_field`: un `select` con opción vacía y dos valores iguales a sus etiquetas devuelve `{3: ParsedCustomField(field_format="list", possible_values=[...], multiple=False)}`; verificar que falla porque el módulo no existe.
- [x] 3.2 **GREEN** — Crear el módulo con la dataclass propia `ParsedCustomField` y `parse_issue_form_custom_fields(html)` usando `html.parser.HTMLParser`; hacer pasar 3.1. El módulo no debe importar `redmine_client`.
- [x] 3.3 **RED** — Añadir `test_parsea_select_multiple_con_atributo_multiple` y `test_parsea_select_con_sufijo_corchetes`; verificar que fallan.
- [x] 3.4 **GREEN** — Soportar `multiple` y sufijo `[]` como `list` con `multiple=True`; hacer pasar 3.3.
- [x] 3.5 **RED** — Añadir `test_select_con_valores_1_y_0_es_bool` y `test_booleano_prevalece_sobre_discriminador_de_lista`; verificar que fallan.
- [x] 3.6 **GREEN** — Implementar la excepción previa `1`/`0` como `bool` antes del discriminador de lista; hacer pasar 3.5.
- [x] 3.7 **RED** — Añadir `test_select_con_valor_igual_a_etiqueta_es_lista` (incluyendo entidades HTML y espacios) y `test_select_simple_con_opcion_vacia_sigue_siendo_lista`; verificar que fallan.
- [x] 3.8 **GREEN** — Implementar el discriminador: solo es `list` si todos los `value` no vacíos coinciden exactamente con su etiqueta tras `html.unescape` y `strip`; hacer pasar 3.7.
- [x] 3.9 **RED** — Añadir `test_select_con_valores_de_id_no_es_lista` con `value="10"`/etiqueta `"Ana"` y variantes de `user`, `version` y `enumeration`; verificar que el parser no emite el campo.
- [x] 3.10 **GREEN** — Hacer que un `select` que no cumple el discriminador quede sin reconocer (no se incluye en el diccionario); hacer pasar 3.9.
- [x] 3.11 **RED** — Añadir `test_ignora_hidden_de_valor_vacio`, `test_ignora_controles_que_no_son_de_campos_personalizados`, `test_conserva_orden_y_elimina_duplicados` y `test_decodifica_entidades_html`; verificar que fallan.
- [x] 3.12 **GREEN** — Implementar el filtrado de nombres ajenos, el descarte de `input[type=hidden]`, la deduplicación ordenada y `html.unescape`; hacer pasar 3.11.
- [x] 3.13 **RED** — Añadir `test_html_vacio_devuelve_dict_vacio`, `test_html_malformado_no_lanza` y `test_pagina_de_login_devuelve_dict_vacio`; verificar que fallan.
- [x] 3.14 **GREEN** — Endurecer el parser para HTML vacío, malformado y de login; hacer pasar 3.13.
- [x] 3.15 **CARACTERIZACIÓN** — Añadir `test_textarea_input_date_input_number_input_text_y_radios_no_se_reconocen` y `test_grupo_de_checkboxes_no_se_reconoce`: el parser devuelve `{}` para esos controles, dejando el campo sin resolver; dejarlo en verde como contrato del recorte.
- [x] 3.16 **CARACTERIZACIÓN** — Añadir `test_modulo_de_parseo_no_importa_redmine_client` (inspección de importaciones o de `sys.modules`) para fijar la dirección de dependencia; dejarlo en verde.

## 4. Resolución en cascada y caché

- [x] 4.1 **RED** — Reescribir el fixture de `TestGetProjectCustomFields` para que la pertenencia devuelva **solo `id` y `name`** en un orden concreto, con claves extra deliberadas, y `_get("/custom_fields.json")` devuelva la definición completa con otro orden y otro nombre. Añadir `test_maps_entries_using_admin_definitions`, `test_claves_extra_de_la_pertenencia_se_ignoran`, `test_nombre_de_la_pertenencia_prevalece` y `test_orden_de_la_pertenencia_se_preserva`. Verificar que fallan con el código actual.
- [x] 4.2 **GREEN** — Implementar `_fetch_project_custom_field_stubs(project_id)` y la consulta a `/custom_fields.json`, construyendo el `RedmineCustomField` desde la definición, pero usando exclusivamente `id`, `name` y orden de la pertenencia e ignorando claves extra; hacer pasar 4.1.
- [x] 4.3 **RED** — Añadir `test_filtra_por_customized_type_issue` y `test_filtra_por_ids_de_la_pertenencia`; verificar que fallan.
- [x] 4.4 **GREEN** — Aplicar ambos filtros; hacer pasar 4.3.
- [x] 4.5 **RED** — Añadir `test_normaliza_possible_values_en_objetos_y_cadenas`; verificar que falla.
- [x] 4.6 **GREEN** — Normalizar `possible_values` (`value`/`label` frente a cadena); hacer pasar 4.5.
- [x] 4.7 **RED** — Añadir `test_pagina_definiciones_con_total_count_mayor_que_la_pagina` (primera página parcial con `total_count` superior y segunda completa) y `test_sin_total_count_no_pagina` (respuesta sin `total_count` o con `total_count` no numérico: una sola petición, sin `limit`/`offset`); verificar que fallan.
- [x] 4.8 **GREEN** — Implementar la petición defensiva: una sola petición si no hay `total_count` numérico; si lo hay y supera lo acumulado, pedir con `limit`/`offset` hasta alcanzarlo o recibir una página vacía, con tope de 20 páginas; hacer pasar 4.7 y documentar que un endpoint que ignore la paginación no provoca bucles.
- [x] 4.9 **RED** — Añadir `test_403_en_api_de_definiciones_usa_formulario_html` y `test_401_en_api_de_definiciones_usa_formulario_html` (con `session_cookie` y `_get_text` mockeado devolviendo un `select`); verificar que fallan.
- [x] 4.10 **GREEN** — Implementar `_get_project_issue_form_definitions(project_id)` con `_get_text(f"/projects/{project_id}/issues/new")` y el parser, tratando 401 y 403 con la misma degradación; hacer pasar 4.9.
- [x] 4.11 **RED** — Añadir `test_404_en_api_de_definiciones_usa_formulario_html` y `test_500_en_api_de_definiciones_usa_formulario_html`; verificar que fallan.
- [x] 4.12 **GREEN** — Hacer que cualquier `RedmineError` de la API de definiciones active el fallback HTML cuando hay cookie; hacer pasar 4.11.
- [x] 4.13 **RED** — Añadir `test_timeout_en_api_de_definiciones_usa_formulario_html` y `test_error_de_conexion_en_api_de_definiciones_usa_formulario_html`; verificar que fallan.
- [x] 4.14 **GREEN** — Capturar `RedmineConnectionError` en el nivel 2 y continuar con el HTML; hacer pasar 4.13.
- [x] 4.15 **RED** — Añadir `test_sin_cookie_no_pide_formulario_y_degrada_a_texto` con `caplog`, comprobando que `_get_text` no se llama, que `definition_source="none"` y que el motivo aparece en el aviso; verificar que falla.
- [x] 4.16 **GREEN** — Omitir el nivel HTML cuando `session_cookie` está vacía y registrar el motivo; hacer pasar 4.15.
- [x] 4.17 **RED** — Añadir `test_definiciones_parciales_se_completan_con_html`, donde la API de administrador cubre un id y el HTML el otro; verificar que falla.
- [x] 4.18 **GREEN** — Consultar el HTML solo para los ids ausentes y fusionar por id; hacer pasar 4.17.
- [x] 4.19 **RED** — Añadir `test_formulario_sin_el_campo_degrada_solo_ese_campo`, comprobando que el resto queda resuelto y el ausente tiene `field_format=""`, `definition_source="none"` y aviso; verificar que falla.
- [x] 4.20 **GREEN** — Completar los ids no resueltos con `field_format=""` y warning con id/nombre/motivo; hacer pasar 4.19.
- [x] 4.21 **RED** — Añadir `test_redireccion_a_login_degrada_sin_excepcion` y `test_html_sin_controles_degrada_sin_excepcion` (este último como negativo por proyecto, no global); verificar que fallan.
- [x] 4.22 **GREEN** — Capturar `RedmineSSOError` y el caso de 200 válido sin controles, registrando el motivo y sin propagar; el 200 sin controles se memoriza solo para ese proyecto; hacer pasar 4.21.
- [x] 4.23 **CARACTERIZACIÓN** — Añadir `test_fallo_de_pertenencia_se_propaga_como_redmine_error`; verificar que pasa y dejarlo como blindaje de la propagación existente.
- [x] 4.24 **GREEN** — Conservar la propagación de la excepción de pertenencia sin cachearla al reescribir la cascada; verificar 4.23.
- [x] 4.25 **RED** — Añadir `test_proyecto_sin_campos_no_consulta_definiciones`; verificar que falla.
- [x] 4.26 **GREEN** — Salir antes de consultar definiciones cuando la pertenencia está vacía; hacer pasar 4.25.
- [x] 4.27 **RED** — Añadir `test_cache_por_proyecto_no_repite_peticiones` (dos llamadas, un solo `_get` de pertenencia); verificar que falla.
- [x] 4.28 **GREEN** — Añadir `_project_custom_fields` y devolver copia de la lista cacheada; hacer pasar 4.27.
- [x] 4.29 **RED** — Añadir `test_cache_global_de_definiciones_entre_proyectos` (tres proyectos, una sola llamada a `/custom_fields.json`); verificar que falla.
- [x] 4.30 **GREEN** — Cachear las definiciones globales con su motivo de fallo; hacer pasar 4.29.
- [x] 4.31 **RED** — Añadir `test_403_memorizado_entre_proyectos` y `test_ausencia_de_cookie_memorizada`; verificar que fallan.
- [x] 4.32 **GREEN** — Memorizar resultados negativos de administrador y la ausencia de cookie; hacer pasar 4.31.
- [x] 4.33 **RED** — Añadir `test_fallo_de_login_html_memorizado_globalmente` (el primer proyecto redirige a login y el segundo no debe llamar a `_get_text`), `test_pagina_de_login_200_memorizada_globalmente` (formulario con `id="login-form"`/`name="username"` y sin controles) y `test_formulario_valido_sin_controles_del_proyecto_a_no_impide_resolver_b_por_html` (A devuelve 200 válido sin controles y B un `select` reconocible; B se resuelve por HTML); verificar que fallan.
- [x] 4.34 **GREEN** — Añadir `_issue_form_auth_failure` y consultarlo antes de pedir HTML; fijarlo **solo** con señales de autenticación (redirección a login/SSO, 401/403 o página de login identificable), nunca por un 200 válido sin controles, que se memoriza como negativo por proyecto; hacer pasar 4.33.
- [x] 4.35 **RED** — Añadir `test_informe_ods_con_n_proyectos_hace_como_maximo_una_peticion_html_fallida` con tres proyectos y cookie inválida; verificar que falla.
- [x] 4.36 **GREEN** — Asegurar que la caché negativa global cubre solo los fallos de autenticación del recorrido del informe ODS; hacer pasar 4.35.
- [x] 4.37 **RED** — Añadir `test_clear_custom_field_cache_fuerza_recarga_y_olvida_fallo_html`; verificar que falla.
- [x] 4.38 **GREEN** — Implementar `clear_custom_field_cache()` vaciando mapas, motivos y fallo global; hacer pasar 4.37.
- [x] 4.39 **RED** — Añadir `test_cliente_nuevo_no_comparte_cache`; verificar que falla si aparece caché de módulo.
- [x] 4.40 **GREEN** — Mantener la caché estrictamente en la instancia; hacer pasar 4.39.
- [x] 4.41 **RED** — Añadir `test_resultado_modificado_no_contamina_la_cache`; verificar que falla.
- [x] 4.42 **GREEN** — Devolver una lista nueva en cada llamada; hacer pasar 4.41.
- [x] 4.43 **RED** — Añadir `test_definition_source_admin_html_none_y_degraded_reason`: cada vía fija el origen y solo la degradación rellena el motivo; verificar que falla.
- [x] 4.44 **GREEN** — Añadir `definition_source` y `degraded_reason` a `RedmineCustomField` y asignarlos en la cascada; hacer pasar 4.43.

## 5. Integración con el diálogo de tarea y aviso de degradación

- [x] 5.1 **RED** — Crear `tests/test_custom_field_resolution_integration.py` con `test_lista_resuelta_por_admin_se_renderiza_como_combo`: `RedmineClient` real con `_get` mockeado (pertenencia solo id/nombre + definiciones completas) pasado a `TaskDialog`; esperar `QComboBox` con las opciones reales. Verificar que falla con el código actual.
- [x] 5.2 **GREEN** — Verificar que 5.1 pasa solo con el cambio del cliente; si falla, ajustar la resolución, no la lógica de widgets.
- [x] 5.3 **RED** — Añadir `test_lista_resuelta_por_html_se_renderiza_como_combo` con 403, cookie y HTML mockeados; verificar que falla.
- [x] 5.4 **GREEN** — Comprobar que la ruta HTML también produce `QComboBox`; corregir el parser o la fusión si no.
- [x] 5.5 **RED** — Añadir `test_multiple_resuelto_se_renderiza_como_multivalue`; verificar que falla.
- [x] 5.6 **GREEN** — Ajustar lo necesario para que `multiple=True` llegue como `MultiValueCombo` con sus opciones.
- [x] 5.7 **CARACTERIZACIÓN** — Añadir `test_definicion_no_resoluble_sigue_siendo_qlineedit`; verificar que pasa y dejarlo como blindaje del fallback actual.
- [x] 5.8 **CARACTERIZACIÓN** — Añadir `test_lista_conocida_sin_opciones_muestra_combo_deshabilitado`; verificar que pasa (comportamiento ya especificado).
- [x] 5.9 **CARACTERIZACIÓN** — Añadir `test_payload_sin_informacion_nueva_no_cambia`: lista envía el texto de la opción, múltiple envía lista de textos y no resoluble envía texto; verificar que pasa.
- [x] 5.10 **CARACTERIZACIÓN** — Añadir `test_aceptar_sin_cambios_conserva_representables_y_omite_no_representables`; verificar que pasa.
- [x] 5.11 **RED** — Añadir `test_is_required_de_la_definicion_muestra_asterisco`; verificar que falla antes de la cascada y pasa con `is_required` de administrador.
- [x] 5.12 **GREEN** — Confirmar que `_add_custom_field_widget` ya renderiza el asterisco; corregir solo la resolución si no llega `is_required`.
- [x] 5.13 **RED** — Añadir `test_default_value_de_la_definicion_se_aplica_en_alta`; verificar que falla antes de la cascada y pasa con la definición de administrador.
- [x] 5.14 **GREEN** — Confirmar que `_apply_custom_field_values` ya aplica `default_value`; corregir solo la resolución si no llega.
- [x] 5.15 **RED** — Añadir `test_html_no_anade_asterisco_ni_default_distintos` recorriendo el cliente real: `GET /custom_fields.json` responde 403, hay cookie configurada y el formulario HTML contiene un `select` reconocible; el campo resultante tiene `definition_source="html"`, no muestra asterisco de obligatorio y no aplica `default_value`. Verificar que falla antes de implementar la cascada (hoy degrada a `"none"`).
- [x] 5.16 **GREEN** — Garantizar que la ruta HTML deja `is_required`/`default_value` en sus valores por defecto; hacer pasar 5.15.
- [x] 5.17 **RED** — Añadir `test_aviso_visible_cuando_hay_campos_sin_definicion`: con un campo `definition_source="none"`, existe un único `QLabel` visible en el grupo, con texto que menciona Cookie, Ajustes, API key de administrador y texto libre, y no es modal; verificar que falla.
- [x] 5.18 **GREEN** — Añadir el `QLabel` de aviso en `TaskDialog`, dentro del grupo "Campos personalizados", con `wordWrap`, visible solo si hay algún `"none"`; hacer pasar 5.17.
- [x] 5.19 **RED** — Añadir `test_sin_aviso_cuando_todo_se_resuelve_o_no_hay_campos` y `test_aviso_unico_con_varios_campos_degradados`; verificar que fallan.
- [x] 5.20 **GREEN** — Ocultar el aviso cuando todos se resuelven o no hay campos, mostrarlo una sola vez y limpiarlo en `_clear_custom_fields`; hacer pasar 5.19.
- [x] 5.21 **RED** — Añadir `test_ayuda_y_tooltip_de_cookie_mencionan_campos_personalizados` en los tests de Ajustes; verificar que falla.
- [x] 5.22 **GREEN** — Actualizar en `settings_dialog.py` el texto de ayuda y el tooltip del campo Cookie explicando que permite resolver campos personalizados cuando la API key no es de administrador; hacer pasar 5.21.

## 6. Regresión y cierre

- [x] 6.1 Ejecutar `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` y confirmar la suite completa en verde.
- [x] 6.2 Verificar que `MainWindow._report_custom_fields_for_projects` sigue recibiendo `id` y `name` y que dos consultas seguidas del mismo proyecto no repiten peticiones (test de integración del informe).
- [x] 6.3 Confirmar que no se añaden dependencias: `requirements.txt` y `pyproject.toml` sin cambios y parser basado en `html.parser`.
- [x] 6.4 Revisar que los warnings nuevos están en español, incluyen proyecto/id/nombre/motivo y nunca registran la cookie ni la API key.
- [x] 6.5 Revisar docstrings y comentarios del módulo nuevo y del cliente, alineados con el estilo del repo; documentar en `MANUAL.md` la Cookie de sesión y el aviso de degradación (opcional).
- [x] 6.6 Ejecutar `openspec status --change "obtener-definiciones-campos-personalizados" --json` y `openspec validate "obtener-definiciones-campos-personalizados" --type change`; corregir el formato sin perder contenido si el validador lo rechaza.
- [x] 6.7 Si la verificación descubre diferencias con las fuentes de Redmine, actualizar `design.md`, el delta de spec y este `tasks.md` antes de dar el cambio por cerrado.

## 7. Correcciones de verificación final

- [x] 7.1 **RED/GREEN** — Múltiple parcialmente representable: no perder valores previos. Nota: la solución fue inyectar los valores ausentes en el `MultiValueCombo` mediante el nuevo `add_missing_items(values)` y enviar el payload completo (desmarcar un ítem inyectado lo elimina; desmarcar todo envía `[]`). Los tests `test_multiple_previous_value_partially_representable_preserves_unknown`, `test_multiple_uncheck_injected_previous_value_removes_it` y `test_add_missing_items_appends_without_duplicates` están en verde.
- [x] 7.2 **RED/GREEN** — Contener respuesta 200 no-JSON en la obtención de definiciones y degradar al HTML.
- [x] 7.3 **RED/GREEN** — Test de integración HTML -> MultiValueCombo.
- [x] 7.4 — Corregir MANUAL.md sobre el propósito de la Cookie.

## 8. Correcciones de la verificación /opsx-verify

- [x] 8.1 **RED** — W1: tests de redirección benigna (A/B), redirección a login global y HTTP 401/403 del HTML global.
- [x] 8.2 **GREEN** — W1: `location` retrocompatible en `RedmineSSOError`, `_check_redirect` lo propaga y `_is_authentication_redirect` distingue auth de redirección benigna; la cascada solo memoriza globalmente las de autenticación.
- [x] 8.3 **RED** — W2: test de copia profunda de la caché (mutar `name` y `possible_values` no contamina la siguiente llamada).
- [x] 8.4 **GREEN** — W2: devolver `copy.deepcopy` en los dos puntos de salida de la caché.
- [x] 8.5 **RED/GREEN** — R1-S5/R1-S6: assertar `visible`/`editable` por vía admin y sus valores por defecto en la vía HTML.
- [x] 8.6 **RED/GREEN** — R1-S13: test del tope de 20 páginas cuando el endpoint ignora `limit`/`offset`, y de una sola página con `total_count` alto.
- [x] 8.7 **RED/GREEN** — R1-S23/R4-S4: warning de degradación con `caplog` que incluye `project_id`, `cf_id` y `name`, y no contiene API key ni cookie.
- [x] 8.8 **RED/GREEN** — R5-S3: en fallo de pertenencia, el grupo y el label de aviso quedan ocultos.
- [x] 8.9 **RED/GREEN** — Robustez: `_fetch_project_custom_field_stubs` lanza `RedmineError` en español si `project` no es un dict.
- [x] 8.10 **RED/GREEN** — Robustez: `_get`/`_get_text` capturan `httpx.HTTPError` genérico y lo mapean a `RedmineConnectionError`.
- [x] 8.11 **RED/GREEN** — Refactor: `_post`/`_put`/`_delete` reutilizan `_raise_for_status` (incluido 422 → `RedmineValidationError`) preservando los mensajes existentes.
- [x] 8.12 — Ejecutar suite completa y `openspec validate`; confirmar verde.
- [x] 8.13 — Revisar que no hay dependencias nuevas, ficheros ajenos ni secretos en logs.
