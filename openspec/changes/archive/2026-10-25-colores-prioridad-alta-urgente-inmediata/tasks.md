## 1. Tests en rojo (TDD)

- [x] 1.1 Actualizar las constantes de color en `tests/test_task_table_render.py`: `BG_INMEDIATA = QColor(139, 0, 0)`, `BG_URGENTE = QColor(200, 0, 0)`, nueva `BG_ALTA = QColor(204, 85, 0)`, y mantener `WHITE = QColor(255, 255, 255)`.
- [x] 1.2 Sustituir los usos de `RED_INMEDIATA`/`RED_URGENTE` por las constantes nuevas en todo el fichero.
- [x] 1.3 Añadir una issue de prioridad "Alta" al escenario de `TestPriorityHighlight.test_highlight_covers_all_visible_cells_after_sort_and_reload` y asertar `BG_ALTA` antes y después de la segunda recarga.
- [x] 1.4 Nuevo test: con las tres prioridades simultáneas, cada fila tiene su fondo propio y la luminancia relativa es estrictamente decreciente en el orden Alta → Urgente → Inmediata.
- [x] 1.5 Nuevo test: los alias en inglés "High", "Urgent" e "Immediate" producen el mismo fondo que "Alta", "Urgente" e "Inmediata".
- [x] 1.6 Ampliar `test_non_priority_rows_not_highlighted` para cubrir "Baja" y "Low", y comprobar que ninguna de ellas recibe ninguno de los tres fondos de prioridad.
- [x] 1.7 Ejecutar `QT_QPA_PLATFORM=offscreen pytest tests/test_task_table_render.py -q` y confirmar que los tests nuevos fallan por los colores antiguos.

## 2. Implementación

- [x] 2.1 En `app/widgets/task_table.py` reasignar las constantes: `_BG_INMEDIATA = QColor(139, 0, 0)` y `_BG_URGENTE = QColor(200, 0, 0)`.
- [x] 2.2 Añadir `_BG_ALTA = QColor(204, 85, 0)` junto a las anteriores.
- [x] 2.3 Ampliar `_priority_bg()` para devolver `_BG_ALTA` cuando el nombre normalizado sea `"alta"` o `"high"`, manteniendo el orden de comprobación Inmediata → Urgente → Alta y devolviendo `None` para el resto.
- [x] 2.4 Confirmar que `_PRIORITY_NAME_RANK` no necesita cambios (ya contiene `"alta": 2, "high": 2`) y que `_apply_issue_style()` sigue aplicando fondo y texto blanco a todas las celdas de la fila.
- [x] 2.5 Verificar que `ProgressBarDelegate` no requiere cambios: la fila "Alta" debe obtener pista blanca, chunk `CHUNK_PRIORITY` (`#ff9800`) y texto blanco a través de `BackgroundRole`. Si no ocurre, ajustar solo `_priority_background()`.

## 3. Documentación

- [x] 3.1 Actualizar `MANUAL.md` (línea 218) para describir los tres niveles: "Alta" con naranja rojizo, "Urgente" con rojo y "Inmediata" con rojo oscuro, todas con texto blanco.
- [x] 3.2 Al archivar o sincronizar el cambio, actualizar el `## Purpose` de `openspec/specs/resaltado-prioridad-alta/spec.md` para que mencione los tres niveles y no solo "Inmediata" y "Urgente".

## 4. Verificación

- [x] 4.1 Ejecutar la suite completa: `QT_QPA_PLATFORM=offscreen pytest -q` y confirmar que no hay regresiones en `test_task_table_multi_sort.py`, `test_task_table_tracker.py` ni `test_main_window.py`.
- [x] 4.2 Verificación manual en la aplicación: comprobar con tareas de prioridad Alta, Urgente e Inmediata que los tres fondos se distinguen, que el texto blanco se lee y que la columna Progreso es coherente, en tema claro y en tema oscuro. (validada visualmente por el usuario sobre /tmp/opencode/prioridad-preview.png en lugar de la app; evidencia headless en la sesión de verificación)
- [x] 4.3 Confirmar que las filas Normal y Baja no han cambiado de apariencia.

## 5. Refuerzo de cobertura tras auditoría

- [x] 5.1 Añadir `TestProgressBarInPriorityRows` en `tests/test_task_table_render.py`: 4 escenarios parametrizados (Urgente/Inmediata/Alta al 30 % y Alta al 0 %) muestreando píxeles reales de un `QImage` offscreen con `visualRect`.
- [x] 5.2 Añadir test de texto blanco en la celda de progreso (`foreground() == WHITE`) para las tres prioridades.
- [x] 5.3 Endurecer `test_highlight_covers_all_visible_cells_after_sort_and_reload` reordenando después de poblar (Título descendente) y reasertando las tres prioridades.
- [x] 5.4 Endurecer `test_non_priority_rows_not_highlighted` comprobando que no se fuerza `foreground` blanco.

## 6. Correcciones tras auditoría

- [x] 6.1 (W1) Subir el contraste de "Alta": `_BG_ALTA = QColor(198, 81, 0)` (`#C65100`) en `app/widgets/task_table.py` y `BG_ALTA = QColor(198, 81, 0)` en `tests/test_task_table_render.py`.
- [x] 6.2 (W1) Actualizar `design.md` (tabla D1, Goal #2, alternativa `#D2491A`, risk residual) y los literales `RGB(198, 81, 0)` en los deltas de `resaltado-prioridad-alta` y `barra-progreso`; verificar contraste WCAG: `L = 0.178906`, ratio `4.5870:1` (≥ 4.5:1 AA).
- [x] 6.3 (S3) Añadir al delta `resaltado-prioridad-alta` el escenario "Prioridad personalizada sin resaltado" bajo "Prioridades normales mantienen apariencia original".
- [x] 6.4 (S3) Ampliar `test_non_priority_rows_not_highlighted` con las issues `Crítica` (4) y `Minor` (5), comprobando que no reciben `BG_ALTA`, `BG_URGENTE`, `BG_INMEDIATA` ni `WHITE` forzado.
- [x] 6.5 (S1) Corregir la deriva de la spec viva `openspec/specs/barra-progreso/spec.md`: `QProgressBar` → barra pintada por `ProgressBarDelegate`, sin tocar requisitos ni escenarios; `openspec validate --specs --strict` OK.
- [x] 6.6 (S4) Borrar `.pytest_cache/v/cache/lastfailed` para eliminar falsos positivos por nodeids inexistentes.
- [x] 6.7 (S2) `git add openspec/changes/colores-prioridad-alta-urgente-inmediata` para versionar los artefactos del change (sin commit ni push).
- [x] 6.8 Generar evidencia visual offscreen (`/tmp/opencode/preview_prioridad.py`) con las 5 prioridades y `done_ratio=30` en tema claro y oscuro, compuesta en `/tmp/opencode/prioridad-preview.png`.
- [x] 6.9 Verificación final: suite completa `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q` y `openspec validate "colores-prioridad-alta-urgente-inmediata" --strict`.
