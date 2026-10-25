## Context

PyIssuesTracker es una aplicación de escritorio **PyQt6** (entry `main.py`, código en `app/`, tests en `tests/` con pytest y fixture `qapp`, ejecutados con `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q`).

Estado del diálogo de tarea **antes** de este cambio (las líneas citadas son las del código original) (`app/dialogs/task_dialog.py`):

- `_build_custom_field_widget()` (:601-654) decide el control por `field_format`. Para `multiple == True`, **cualquier** formato cae en un `QListWidget` con `MultiSelection`, todas las `possible_values` volcadas como items y `setMaximumHeight(100)`. Sin checkboxes ni selección visible, con textos largos recortados: visualmente indistinguible de un bloque de texto.
- Para `field_format == "list"` simple se usa un `QComboBox` con una opción vacía inicial, sin elisión ni tooltip.
- Cualquier formato no contemplado cae a `QLineEdit` libre (cubierto por el test con `"link"`).
- `_set_custom_field_value()` (:668-706) y `_read_custom_field_value()` (:708-740) serializan por `kind`; `"multiple"` devuelve la lista de textos seleccionados.
- `custom_fields` (:742-758) es el contrato público: incluye `""`/`[]` para campos con valor previo que el usuario vació y omite los vacíos sin valor previo.

Tras el cambio: `_build_custom_field_widget()` :602-666, `_set_custom_field_value()` :689-724, `_read_custom_field_value()` :726-757, `custom_fields` :759-780.

Existe un patrón probado de multiselección en `app/widgets/multi_select_combo.py` (`MultiSelectCombo`): botón con resumen, popup con checkboxes, búsqueda, tooltips e ítems con `Qt.ItemDataRole.UserRole`. Sus IDs son `int` y aporta opciones fijas ("Todos", "Sin asignar", "Asignado a mí") que aquí no aplican porque las opciones de un campo personalizado son textos.

Tests que definen el comportamiento a preservar: `tests/test_task_dialog_custom_fields.py` (clases `TestSectionVisibility`, `TestReloadOnProjectChange`, `TestEditModePreload`, `TestSerialization`, `TestUnsupportedFieldFormat`, `TestRequiredFieldLabel`), `tests/test_redmine_custom_fields.py` y `tests/test_report_dialog.py`.

## Goals / Non-Goals

**Goals:**

- Que un campo personalizado de selección múltiple se perciba inequívocamente como una lista seleccionable: botón/resumen plegado por defecto, popup con checkboxes, búsqueda y tooltips.
- Elidir los textos largos, tanto en el resumen del multiselector como en el `QComboBox` de selección simple, con tooltip del valor completo.
- Mostrar un control deshabilitado con texto de ayuda cuando `possible_values` está vacío.
- Preservar el contrato de datos y el resto de comportamientos del diálogo (precarga en edición, `default_value`, recarga al cambiar de proyecto, sufijo `*` de obligatorios, fallback a texto libre).
- No romper la suite existente.

**Non-Goals:**

- Resolver opciones de los formatos `user`, `version`, `enumeration` y `key_value_list` vía API: siguen en fallback de texto libre.
- Cambiar el informe ODS ni la exportación (`app/main_window.py`).
- Cambiar `app/services/redmine_client.py` ni la API de Redmine.
- Consultar los flags `visible`/`editable` de `RedmineCustomField`.
- Sustituir o refactorizar `MultiSelectCombo` (se toma solo como referencia de patrón).

## Decisions

### D1. Nuevo widget reutilizable `MultiValueCombo` para multiselección de textos

Se crea `app/widgets/multi_value_combo.py` con la clase `MultiValueCombo(QWidget)`, especializada en valores `str` (no IDs `int`) y sin opciones fijas. Estructura: `QPushButton` (resumen, `setMinimumWidth(150)`) + `QFrame` popup con `Qt.WindowType.Popup | FramelessWindowHint` que contiene un `QLineEdit` de búsqueda y un `QListWidget` de items marcables. La lista interna usa `SelectionMode.NoSelection` y el popup se crea con el propio widget como `parent` (además de `Qt.WindowType.Popup | FramelessWindowHint`), para que se destruya junto al combo cuando se reconstruyen los campos.

API pública:

- `set_items(values: list[str])` — reconstruye las opciones conservando la selección existente.
- `selected_values() -> list[str]` — valores marcados en orden de las opciones.
- `set_selected_values(values: list[str])` — marca las opciones indicadas y actualiza el resumen.
- Señal `seleccion_cambiada(list)` para mantener el widget desacoplado del diálogo.

Resumen del botón: `""` si no hay selección; el texto (elidido) si hay una; `"{n} seleccionados"` si hay varias. Tooltip con los valores completos separados por comas.

*Alternativas consideradas:* (a) reutilizar `MultiSelectCombo` mapeando textos a IDs sintéticos — rechazada porque arrastra las opciones fijas y la semántica "Todos", que producirían selecciones espurias; (b) `QListWidget` con `setItemWidget(QCheckBox)` — rechazada por el coste de sincronización manual y porque no resuelve el popup ni la elisión; (c) `QComboBox` con `setModel` y checkboxes — rechazada por requerir delegado propio y ser más frágil que el patrón ya probado en el repo.

### D2. El `kind` de serialización se mantiene

`_build_custom_field_widget()` sigue devolviendo `kind == "multiple"` para los campos `multiple == True`, con el nuevo widget como `widget`. Así `_set_custom_field_value()`, `_read_custom_field_value()` y la propiedad `custom_fields` conservan su forma (`list[str]`, `[]` al vaciar un campo con valor previo, omisión de vacíos sin valor previo) sin tocar `MainWindow` ni el cliente.

### D3. Contrato explícito del widget y adaptación de dos tests existentes

`MultiValueCombo` expone solo `set_items()`, `selected_values()`, `set_selected_values()` y la señal `seleccion_cambiada`. La `QListWidget` interna se configura con `QAbstractItemView.SelectionMode.NoSelection` y la **única fuente de verdad es `checkState`**: una opción se marca desde el indicador de checkbox de su fila (el clic sobre el texto no marca, igual que en cualquier lista de checkboxes estándar), de modo que no puede producirse el desmarcado cruzado típico de `SingleSelection`/`MultiSelection`.

`set_selected_values(values)` **sustituye** la selección completa: limpia todas las marcas y marca exactamente los valores indicados. `set_items()` reconstruye las opciones conservando las marcas que sigan existiendo.

Los dos únicos tests existentes acoplados al `QListWidget` se adaptan al contrato nuevo (≈6 líneas, sin pérdida de cobertura):

- `tests/test_task_dialog_custom_fields.py:168-173` → `assert w[5]["widget"].selected_values() == ["x", "y"]`
- `tests/test_task_dialog_custom_fields.py:214-215` → `w[8]["widget"].set_selected_values(["x", "z"])`

*Alternativas consideradas:* (a) exponer `count()`/`item(i)` y sincronizar `isSelected()` con `checkState()` para no tocar tests — rechazada: filtra el `QListWidgetItem` interno, crea dos fuentes de verdad, contradice el objetivo de «una única fuente de verdad (`checkState`)» y, con `SingleSelection`/`MultiSelection`, el clic reemplazaría la selección y la sincronización desmarcaría las opciones anteriores, reproduciendo el bug que este cambio corrige; (b) mantener `MultiSelection` con `checkState` desacoplado — rechazada por la misma razón.

### D4. Elisión y tooltip

- Multiselector: el texto del botón se calcula con `QFontMetrics.elidedText(texto, Qt.TextElideMode.ElideRight, ancho disponible)` al establecer la selección y en `resizeEvent`; el tooltip guarda siempre el texto completo.
- `QComboBox` de selección simple: `setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)`, `setMinimumContentsLength(20)`, `setMinimumWidth(200)`; la vista (`combo.view()`) usa `setTextElideMode(Qt.TextElideMode.ElideRight)` y cada item recibe `setToolTip(valor completo)`.
- El popup del multiselector usa `list.setWordWrap(False)` y `list.setTextElideMode(Qt.TextElideMode.ElideRight)`; cada item lleva tooltip con el texto completo.

*Alternativa considerada:* truncar el texto manualmente en el modelo de datos — rechazada porque corrompería la serialización (debe enviarse el valor íntegro a Redmine).

### D5. `possible_values` vacío

Cuando `possible_values` está vacío, se devuelve el mismo tipo de control pero deshabilitado y con el texto fijo de ayuda `"Sin opciones disponibles"` (compartido por el combo simple y el botón del multiselector). El `kind` no cambia. Además, si el issue tenía un valor previo que el control no puede representar —porque `possible_values` está vacío o porque el valor ya no figura entre las opciones— el campo **se omite del payload** (`previo_no_representable`), de modo que Redmine conserva el valor existente en lugar de perderlo al guardar. Como contrapartida, en ese estado el usuario no puede limpiar el campo desde la app. Si el campo de valor múltiple tiene un valor previo solo parcialmente representable y el usuario deja alguna marca, se envía únicamente la selección representable y el valor ausente se pierde.

*Alternativa considerada:* no construir el control y ocultar la fila — rechazada porque el usuario perdería la referencia de que el campo existe y es obligatorio.

### D6. Búsqueda siempre disponible en el popup

Siguiendo el patrón de `MultiSelectCombo`, el `QLineEdit` de búsqueda se muestra siempre en el popup y se vacía al abrir y al cerrar. No se añade un umbral por número de opciones: es la opción más simple, evita ramas y cubre el caso de valores largos. Supuesto explícito: la búsqueda filtra por subcadena `case-insensitive` sobre el texto y no altera la selección.

### D7. Punto de integración acotado

Los cambios se concentran en `_build_custom_field_widget()`, en las ramas `multiple`/`list` de `_set_custom_field_value()` y `_read_custom_field_value()`, y en el nuevo widget. `_load_custom_fields_for_project()` y `_add_custom_field_widget()` no cambian de estructura, y `_apply_custom_field_values()`/`custom_fields` conservan la suya pero incorporan la regla del valor previo no representable (D5). El popup se cierra en `hideEvent()` del widget, igual que en `MultiSelectCombo`, para no dejar ventanas huérfanas al recargar campos al cambiar de proyecto; **además** el popup se crea con el widget como `parent` porque `_clear_custom_fields()` (`app/dialogs/task_dialog.py:574-578`) destruye las filas al cambiar de proyecto y la destrucción no garantiza que llegue `hideEvent()`.

## Risks / Trade-offs

- **Dos tests existentes acoplados al `QListWidget`** (leen `item(i)`/`setSelected`) → se adaptan al API nuevo en la tarea 3.6, conservando toda la cobertura; verificado con la suite completa en headless.
- **Popup como ventana independiente en modo `offscreen`** (puede no recibir eventos de ratón ni ser visible en CI) → la lectura y escritura de valores no dependen de abrir el popup; los tests ejercitan `selected_values()`/`set_selected_values()` y `checkState` directamente.
- **Bucles de señales al marcar opciones** → la lista usa `SelectionMode.NoSelection`, una única fuente de verdad (`checkState`) y `blockSignals(True)` durante la reconstrucción de items.
- **Elisión dependiente del ancho disponible** (cambia con el layout y el tema) → el tooltip se fija siempre con el texto completo y los tests comprueban el tooltip, no el punto exacto de corte.
- **Regresión en la serialización de múltiple vaciado** → se mantiene el test de serialización existente y se añade cobertura de "había valor previo y se desmarca todo" → `[]`.
- **Textos de ayuda en español** → coherente con el resto de la interfaz; los identificadores y rutas siguen en inglés.
- **Precedencia de `multiple` sobre `field_format`** (`app/dialogs/task_dialog.py:611`): un formato no contemplado (`user`, `version`, `link`…) con `multiple` verdadero se renderiza como selector multiselección, no como texto libre. Es el comportamiento actual y queda explicitado en el delta spec.
- **Campo con valor previo no representable** → el campo se omite del payload y Redmine conserva el valor; contrapartida: el usuario no puede limpiarlo desde la app en ese estado.

## Migration Plan

No hay migración de datos ni cambios de esquema. El cambio es de presentación dentro del diálogo:

1. Añadir `app/widgets/multi_value_combo.py`.
2. Integrarlo en `_build_custom_field_widget()` y ajustar las ramas `multiple`/`list` de `_set_/_read_custom_field_value()`.
3. Ejecutar `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` y verificar la suite completa.

Rollback: revertir el commit; no hay estado persistido ni pasos manuales.

## Open Questions

Ninguna bloqueante. Quedan como supuestos explícitos: búsqueda siempre visible (D6), umbral de elisión delegado al ancho del layout (D4) y contrato explícito del widget (D3).
