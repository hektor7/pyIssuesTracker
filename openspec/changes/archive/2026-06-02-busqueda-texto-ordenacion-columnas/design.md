## Context

Actualmente `FilterBar` usa un único `QHBoxLayout` con 5 combos y 1 checkbox. No hay búsqueda por texto ni ordenación en `TaskTable`. La API de Redmine ya devuelve hasta 100 issues por página, lo que hace viable el filtrado cliente-side sin llamadas额外 al servidor.

## Goals / Non-Goals

**Goals:**
- Añadir una segunda fila al `FilterBar` con un campo de búsqueda por texto.
- Filtrar en tiempo real las tareas mostradas según el texto introducido (título).
- Habilitar ordenación por clic en cabeceras de columna.

**Non-Goals:**
- No se modifica la API de Redmine (filtrado cliente-side).
- No se añaden filtros por fecha ni por tracker en este cambio.
- No se implementa búsqueda en descripción (solo título, por simplicidad y rendimiento).

## Decisions

### 1. Filtrado cliente-side para búsqueda por texto

**Alternativa considerada:** Añadir parámetro `search` al API y filtrar en servidor.
**Decisión:** Filtrar en cliente la lista ya cargada de issues.

**Razón:** La API de Redmine ya devuelve todas las issues del proyecto (hasta 100). El filtrado cliente-side es instantáneo y no genera llamadas de red adicionales. Simplemente se ocultan las filas que no coinciden. Si en el futuro se necesita paginación real, se podrá migrar a filtrado servidor.

### 2. Segunda fila con QVBoxLayout

**Decisión:** Cambiar el layout raíz de `FilterBar` de `QHBoxLayout` a `QVBoxLayout` con dos `QHBoxLayout` hijos: `_row1` y `_row2`.

**Razón:** Es el cambio mínimo para añadir una segunda fila. Mantiene la organización visual limpia. `_row2` solo contiene el campo de búsqueda por ahora, dejando espacio para futuros filtros adicionales.

### 3. Búsqueda en tiempo real con debounce implícito

**Decisión:** Conectar `textChanged` del `QLineEdit` directamente a la señal `busqueda_cambiada`. El `MainWindow` recibe el texto y lo aplica en la siguiente llamada a `_cargar_issues()`.

**Razón:** Qt ya maneja el input del usuario de forma eficiente. No es necesario un debounce explícito porque `_cargar_issues()` opera sobre datos en memoria (filtrado O(n) sobre la lista de issues).

### 4. Ordenación nativa de QTableWidget

**Decisión:** Usar `setSortingEnabled(True)` con datos de ordenación personalizados vía `setData(Qt.ItemDataRole.UserRole)` para columnas numéricas.

**Razón:** La ordenación nativa de `QTableWidget` ordena alfabéticamente por el texto mostrado. Para columnas como ID (numérico), progreso (numérico) y fecha, se debe proporcionar un valor de ordenación numérico o de fecha en un role distinto. Para la columna de progreso (que usa `QProgressBar`), se usará `setData()` con el valor numérico.

### 5. Almacenar el orden de las issues en `_issues`

**Decisión:** Mantener `_issues` como la lista ordenada según el criterio del usuario (o según vienen de la API). Al reordenar con clic en cabecera, el orden se refleja automáticamente porque `QTableWidget` con `setSortingEnabled(True)` reordena las filas visualmente sin necesidad de reordenar `_issues`.

**Riesgo:** Si se accede a `_issues[idx]` después de ordenar, el índice puede no corresponder a la fila visible. → Se usa `self.item(row, 0).text()` o similar para obtener el ID real, no `_issues[idx]`.

## Risks / Trade-offs

- **[Riesgo] La ordenación nativa puede ser lenta con muchas filas** → El límite actual es 100 issues (REDMINE_PAGE_LIMIT). Rendimiento aceptable.
- **[Trade-off] El filtrado cliente-side no escala a cientos de issues** → Para el caso de uso actual (<100 issues) es adecuado. Si se necesita escalar, se migrará a filtrado servidor.
- **[Riesgo] `QProgressBar` en celdas puede interferir con la ordenación** → Se establece `setData(Qt.ItemDataRole.UserRole, progress)` en el `QTableWidgetItem` de la fila para que la ordenación use ese valor numérico.
