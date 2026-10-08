## 1. Implementación de barra de progreso

- [x] 1.1 Añadir `QProgressBar` a los imports en `app/widgets/task_table.py`.
- [x] 1.2 Crear método helper `_create_progress_bar(progress: int, bg_color: QColor | None) -> QProgressBar` que cree y configure la barra con el estilo adecuado según el valor de progreso y el color de fondo de prioridad.
- [x] 1.3 Reemplazar la creación de `QTableWidgetItem` para `COL_PROGRESS` en `set_issues()` por `self.setCellWidget(row, self.COL_PROGRESS, bar)` usando el helper.
- [x] 1.4 Ajustar la altura de fila si es necesario para que la barra se vea correctamente (ej. `setRowHeight` o `verticalHeader().setDefaultSectionSize`).

## 2. Verificación

- [x] 2.1 Verificar que las barras se muestran correctamente para tareas con 0%, 50% y 100%.
- [x] 2.2 Verificar que las barras en filas urgentes/inmediatas muestran fondo rojo con texto blanco.
- [x] 2.3 Verificar que el rendimiento no se degrada con muchas filas (>200).
