## 1. Tests en rojo (TDD)

- [x] 1.1 Tests unitarios de `ProgressBarDelegate._text_color_for` parametrizados con los cinco rellenos de la tabla D3 de `design.md`: `#ffffff` → `#333333`, `#bdbdbd` → `#333333`, `#ff9800` → `#333333`, `#f57c00` → `#333333`, `#2e7d32` → blanco.
- [x] 1.2 Test unitario de `ProgressBarDelegate._relative_luminance`: blanco = 1.0, negro = 0.0, `#8b0000` ≈ 0.0549 (±0.002).
- [x] 1.3 Test de renderizado: tema **oscuro**, prioridad "Normal", `done_ratio = 30`. Renderizar con `viewport().grab()` y contar los píxeles de la zona del texto que coinciden con `#333333` (tolerancia ±12 por canal); exigir al menos 5. Con la implementación actual hay **cero** → el test debe fallar en rojo.
- [x] 1.4 Test de renderizado: prioridades "Alta", "Urgente" e "Inmediata" con `done_ratio = 30` en tema claro; conteo de píxeles de texto oscuro ≥ 5 en las tres.
- [x] 1.5 Test de renderizado: `done_ratio = 100`; el texto debe contener píxeles blancos sobre el tramo verde.
- [x] 1.6 Test de invariante "nunca texto del color de su relleno": para cada combinación de tema (claro, oscuro) × prioridad (Alta, Urgente, Inmediata, Normal, Baja) × `done_ratio` (0, 30, 100), comprobar que el contraste entre el color de texto elegido y el relleno correspondiente es ≥ 4.5:1. Puede resolverse sobre `_text_color_for` y los colores conocidos, sin renderizar.
- [x] 1.7 Reformular `test_progress_percentage_text_is_white_in_priority_rows` para que verifique el color realmente pintado en lugar de `item.foreground().color() == WHITE`, que seguirá pasando aunque el texto sea invisible.
- [x] 1.8 Ejecutar `QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_task_table_render.py -q` y confirmar que 1.3 y 1.5 fallan por color, no por error de importación ni de sintaxis.

## 2. Implementación

- [x] 2.1 Añadir a `ProgressBarDelegate` la constante `TEXT_DARK = "#333333"`.
- [x] 2.2 Añadir el método estático `_relative_luminance(color)` con la fórmula WCAG (umbral 0.03928, coeficientes 0.2126 / 0.7152 / 0.0722).
- [x] 2.3 Añadir el método de clase `_text_color_for(background)` que devuelva blanco o `TEXT_DARK` según cuál maximice el contraste.
- [x] 2.4 Sustituir el bloque final de pintado del texto (actualmente líneas ~117-122) por las dos pasadas con recorte: `setClipRect(bar_rect)` con el color derivado de `track_color`, y `setClipRect(chunk_rect)` con el derivado de `chunk_color` cuando exista tramo relleno. Mantener el centrado en `cell_rect`.
- [x] 2.5 Eliminar del delegate cualquier uso de `option.palette.color(QPalette.ColorRole.Text)` y del `foreground` del item para el porcentaje, y las variables que queden sin uso.
- [x] 2.6 Confirmar que no se modifica nada más del delegate: ni la pista, ni el tramo relleno, ni los colores de progreso (verde/naranja/ámbar/gris), ni el relleno del fondo de prioridad.
- [x] 2.7 Re-ejecutar los tests del fichero y obtener verde.
- [x] 2.8 Verificar que el delta MODIFIED de este change empareja por encabezado exacto con el requisito "Barra de progreso compatible con resaltado de prioridad alta" de la spec viva, y que sus escenarios ya no exigen "texto en blanco" sino legibilidad. Nota: la sustitución efectiva en `openspec/specs/barra-progreso/spec.md` ocurre al archivar el change; comprobar entonces que la spec viva ya no dice "texto en blanco".

## 3. Verificación

- [x] 3.1 Ejecutar la suite completa `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` y confirmar que no hay regresiones, en particular en `TestPriorityHighlight` y `TestProgressBarInPriorityRows`.
- [x] 3.2 Regenerar la imagen de evidencia en tema claro y oscuro con las cinco prioridades y `done_ratio` 0, 30 y 100, y confirmar a ojo que todos los porcentajes son legibles.
- [x] 3.3 Confirmar que el resaltado de prioridad de las demás celdas, la ordenación y la barra de progreso siguen funcionando igual.
- [x] 3.4 Actualizar `MANUAL.md` si describe el color del texto del porcentaje; si no lo menciona, dejar constancia de que no requiere cambios.
