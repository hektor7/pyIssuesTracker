## Why

Actualmente la columna "Progreso %" muestra un valor numérico (ej. "50%") que no transmite visualmente el avance de forma inmediata. Una barra de progreso gráfica permite evaluar el estado de las tareas de un vistazo, sin necesidad de leer números.

## What Changes

- **Barra de progreso gráfica** en la columna "Progreso %" del `TaskTable`: se sustituye el `QTableWidgetItem` con texto por un `QProgressBar` incrustado vía `setCellWidget()`.
- **Colores de la barra**: verde para 100%, naranja/ámbar para valores intermedios (>0%), gris neutro para 0%.
- **Compatibilidad con prioridad alta**: las filas urgentes/inmediatas mantienen el fondo rojo, y la barra se adapta mostrando texto blanco sobre el rojo.
- **Ajuste visual**: la barra ocupa toda la celda, mostrando el porcentaje numérico centrado dentro de la barra.

## Capabilities

### New Capabilities
- `barra-progreso`: La columna de progreso muestra una barra gráfica `QProgressBar` en lugar de texto numérico, con colores que reflejan el grado de avance.

### Modified Capabilities
<!-- Ninguna -->

## Impact

- **`app/widgets/task_table.py`**: Modificar `set_issues()`, reemplazando la creación de `QTableWidgetItem` para la columna `COL_PROGRESS` por un `QProgressBar` con `setCellWidget()`.
- Se añade import de `QProgressBar` desde `PyQt6.QtWidgets`.
- Sin impacto en API, dependencias externas ni base de datos.
