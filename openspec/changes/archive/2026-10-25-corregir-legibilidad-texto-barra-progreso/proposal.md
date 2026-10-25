## Why

El porcentaje de la columna "Progreso %" es ilegible en dos situaciones, verificadas sobre renderizado real (`grab()` en modo offscreen, temas claro y oscuro):

1. **En las filas con prioridad** Alta, Urgente o Inmediata, el delegate pinta la pista de la barra en blanco (`#ffffff`) y el texto del porcentaje también en blanco, de modo que el número desaparece sobre el fondo.
2. **En el tema oscuro**, el texto se toma de `QPalette.ColorRole.Text`, que es blanco, mientras la pista sigue siendo blanca, de modo que el porcentaje desaparece en **todas** las filas con progreso mayor que cero, no solo en las de prioridad.

La causa raíz es que el color del texto se decide por la *prioridad* (`priority_bg is not None`) o por el *tema* (`Text`), cuando lo que determina la legibilidad es el color del relleno que hay realmente detrás del glifo. Y ese relleno no es uniforme: la barra combina una pista clara con un tramo coloreado cuyo ancho depende del porcentaje, así que un único color de texto nunca puede contrastar con ambos.

## What Changes

- El color del texto pasa a elegirse por **contraste WCAG contra el relleno subyacente**, en lugar de por prioridad o por tema.
- El texto se pinta en **dos pasadas con recorte**: una sobre la pista y otra sobre el tramo relleno, de modo que cada parte del número reciba el color que contrasta con lo que tiene detrás.
- Se elimina la dependencia de `option.palette.color(QPalette.ColorRole.Text)` y del `foreground` del item para el color del porcentaje.
- Se añade un requisito nuevo a `barra-progreso`: el texto del porcentaje debe ser legible (contraste mínimo 4.5:1) en todos los temas y en todas las prioridades.

## Capabilities

### New Capabilities

<!-- Ninguna capacidad nueva: se añade un requisito a una capacidad existente -->

### Modified Capabilities

- `barra-progreso`: se **modifica** el requisito "Barra de progreso compatible con resaltado de prioridad alta" (se elimina la exigencia literal de texto en blanco, que pasa a regirse por el requisito de legibilidad) y se **añade** el requisito "Legibilidad del texto del porcentaje".

## Impact

- **`app/widgets/task_table.py`**: `ProgressBarDelegate` gana un helper de luminancia/contraste y el pintado del texto pasa a dos pasadas con recorte. No se toca el resto de la clase ni `TaskTable`.
- **`tests/test_task_table_render.py`**: tests unitarios del helper de color y tests de renderizado por píxel para los casos de regresión; se reformula `test_progress_percentage_text_is_white_in_priority_rows` para que verifique el color realmente pintado y no el rol `foreground`.
- **`openspec/specs/barra-progreso/spec.md`**: al archivar recibe el requisito nuevo "Legibilidad del texto del porcentaje" y ve modificado el requisito "Barra de progreso compatible con resaltado de prioridad alta".
- Sin impacto en la API de Redmine, dependencias, persistencia ni en el resaltado de prioridad de las demás celdas.

## Sequencing

El change `colores-prioridad-alta-urgente-inmediata` **ya está archivado** y su requisito "Barra de progreso compatible con resaltado de prioridad alta" está ahora en la spec viva `openspec/specs/barra-progreso/spec.md`, que exige literalmente "texto en blanco" en las filas con prioridad. Como este change corrige precisamente esa legibilidad, su delta **MODIFICA** ese requisito (eliminando la exigencia de texto en blanco y remitiendo el color del texto al requisito de legibilidad) **además de AÑADIR** el requisito "Legibilidad del texto del porcentaje". Ambos bloques conviven en el delta y se aplican sobre la misma capacidad al archivar; sin el bloque MODIFIED la spec viva quedaría exigiéndonos simultáneamente "texto en blanco" y contraste ≥ 4.5:1.
