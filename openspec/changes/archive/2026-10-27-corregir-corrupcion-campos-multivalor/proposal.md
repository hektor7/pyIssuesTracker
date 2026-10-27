## Why

Cuando un campo personalizado multivalor de Redmine llega con `value` en forma de lista pero su definición no se resuelve (`field_format=""`, `multiple=False`), el diálogo lo muestra con `str(value)` en un `QLineEdit` y, al aceptar sin cambios, reenvía ese texto como `"['X']"` en lugar de `["X"]`. Se incumple el requisito vigente "la degradación no altera el valor previo": Redmine pasa de una lista a una cadena con el `repr` de Python, con pérdida y corrupción silenciosa del dato.

## What Changes

- En el fallback de texto (`kind` `string` y `text`), renderizar los valores previos en forma de lista unidos por `", "`, sin corchetes ni comillas, mediante un helper único que nunca use `str(lista)`.
- Conservar el tipo lista al serializar: al aceptar sin cambios se reenvía la lista original intacta; al editar el texto se envía una lista de un elemento; al vaciar el campo se envía `[]` y no `""`, también a través de `custom_fields`.
- Reforzar la omisión de valores no representables: marcar las listas simples cuyo valor previo en forma de lista no sea un único elemento presente en `possible_values` (varios elementos o uno inválido), además de las listas/múltiples sin opciones; un único valor válido en forma de lista se selecciona y se trata como representable. Omitir esos campos del payload siempre que estén marcados, no solo cuando el valor serializado quede vacío.
- No reinterpretar cadenas que contengan corchetes (`"['A']"`): son texto legítimo y no se reconstruyen como lista.
- Añadir tests de round-trip (aplicar → leer) para los escenarios anteriores. No hay tests existentes que ajustar: hoy ninguno combina el fallback de texto con un valor previo en forma de lista.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `campos-personalizados-tarea`: se modifica el requisito "Edición de valores según el formato del campo" para el renderizado legible de listas en el fallback de texto, la conservación del tipo y la omisión reforzada de no representables, y el requisito "Payload y alineación con la definición" para garantizar que la degradación no altera el tipo ni el valor previo.

## Impact

- `app/dialogs/task_dialog.py`: helper de renderizado, ampliación de `_apply_custom_field_values`, ajuste de `_set_custom_field_value`, `_read_custom_field_value` y `custom_fields` (solo el bug de multivalor degradado).
- `tests/test_task_dialog_custom_fields.py` y `tests/test_custom_field_resolution_integration.py`: nuevos tests de round-trip; no se modifica ningún test existente porque ninguno fija el comportamiento antiguo del fallback de lista (se conservan como red de seguridad).
- `MANUAL.md` (opcional): solo si describe el comportamiento afectado (hoy no documenta el detalle de serialización de multivalores degradados).
- Sin cambios en `app/services/redmine_client.py`, sin dependencias nuevas y sin migración de datos.
