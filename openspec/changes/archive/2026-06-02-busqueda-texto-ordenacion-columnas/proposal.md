## Why

La barra de filtros actual tiene 5 combos en una sola fila, lo que la hace visualmente densa y deja poco espacio para añadir nuevos filtros. Además, no existe forma de buscar tareas por texto en el título ni de ordenar la tabla haciendo clic en las cabeceras de columna, dos funcionalidades básicas esperables en cualquier tabla de datos.

## What Changes

- **Segunda fila de filtros**: El `FilterBar` pasa de un `QHBoxLayout` único a un `QVBoxLayout` con dos filas. La primera fila mantiene los filtros existentes; la segunda añade un campo de búsqueda por texto.
- **Búsqueda por texto en tiempo real**: Nuevo `QLineEdit` con placeholder "Buscar por título..." en la segunda fila. Filtra las tareas mostradas en la tabla a medida que el usuario escribe, buscando coincidencias en el título (case-insensitive, coincidencia parcial).
- **Ordenación por columna**: Se habilita `setSortingEnabled(True)` en el `TaskTable`. Cada clic en la cabecera de una columna ordena ascendentemente; un segundo clic ordena descendentemente. Funciona en todas las columnas: ID (numérica), Título (alfabética), Fecha inicio (cronológica), Estado (alfabética), Asignado a (alfabética) y Progreso (numérica).

## Capabilities

### New Capabilities
- `busqueda-texto`: Un campo de texto en una segunda fila del `FilterBar` permite filtrar en tiempo real las tareas por título.
- `ordenacion-columnas`: Las columnas del `TaskTable` se ordenan al hacer clic en su cabecera (ascendente/descendente).

### Modified Capabilities
<!-- Ninguna -->

## Impact

- **`app/widgets/filter_bar.py`**: Cambiar layout de `QHBoxLayout` a `QVBoxLayout` con dos filas. Añadir `QLineEdit` de búsqueda con señal `textChanged` → nueva señal `busqueda_cambiada`. Modificar `__init__` y ajustar espaciado.
- **`app/widgets/task_table.py`**: Añadir `setSortingEnabled(True)` en el constructor. Asegurar que los datos numéricos (ID, progreso) y fechas se ordenen correctamente (usar `setData(Qt.ItemDataRole.UserRole)` o similar con valores numéricos).
- **`app/main_window.py`**: Conectar `busqueda_cambiada` a un nuevo slot que almacene el texto de búsqueda y llame a `_cargar_issues()` para aplicar el filtro. Añadir lógica de filtrado cliente-side en `_cargar_issues()` (filtrar la lista de issues por título antes de pasarla a `set_issues()`).
- Sin impacto en API de Redmine (la búsqueda es cliente-side, no requiere cambios en el servidor).
