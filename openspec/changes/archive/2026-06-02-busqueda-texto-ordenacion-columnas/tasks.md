## 1. FilterBar: segunda fila con búsqueda por texto

- [x] 1.1 Cambiar el layout raíz de `FilterBar.__init__()` de `QHBoxLayout` a `QVBoxLayout`. Mover todos los widgets existentes a un `QHBoxLayout` hijo (`_row1`). Crear un segundo `QHBoxLayout` (`_row2`) para el campo de búsqueda.
- [x] 1.2 Añadir `QLineEdit` en `_row2` con placeholder "Buscar por título..." y tamaño mínimo adecuado. Conectar `textChanged` a un nuevo método `_on_search_text_changed`.
- [x] 1.3 Añadir señal `busqueda_cambiada = pyqtSignal(str)` y emitirla desde `_on_search_text_changed` con el texto actual.
- [x] 1.4 Añadir método `set_search_text(text: str)` para restaurar el texto desde fuera (por si se persiste en QSettings en el futuro).

## 2. TaskTable: habilitar ordenación por columna

- [x] 2.1 Añadir `self.setSortingEnabled(True)` en `TaskTable.__init__()`.
- [x] 2.2 En `set_issues()`, para cada columna que necesite ordenación numérica o por fecha, añadir `setData(Qt.ItemDataRole.UserRole, valor)` con el tipo correcto: ID (int), fecha inicio (str ISO o QDate), progreso (int). Para columnas de texto (título, estado, asignado) la ordenación por defecto es suficiente.
- [x] 2.3 Para la columna de progreso (que usa `QProgressBar` vía `setCellWidget`), crear un `QTableWidgetItem` dummy con el valor numérico y llamar a `setItem()` ANTES de `setCellWidget()`, para que la ordenación funcione. Asignar `setData(Qt.ItemDataRole.UserRole, progress)` para ordenación numérica.

## 3. MainWindow: integrar búsqueda y ordenación

- [x] 3.1 Conectar `filter_bar.busqueda_cambiada` a un nuevo slot `_on_busqueda_cambiada(text)` que almacene el texto en `self._search_text`.
- [x] 3.2 En `_cargar_issues()`, después de obtener las issues de la API, aplicar filtro cliente-side: si `self._search_text` no está vacío, filtrar la lista para incluir solo aquellas cuyo `subject` contenga el texto (case-insensitive).
- [x] 3.3 Añadir atributo `_search_text: str = ""` en `MainWindow.__init__()`.

## 4. Verificación

- [x] 4.1 Verificar que al escribir en el campo de búsqueda, la tabla se filtra en tiempo real.
- [x] 4.2 Verificar que al borrar el texto, se muestran todas las tareas de nuevo.
- [x] 4.3 Verificar que al hacer clic en las cabeceras de columna, la tabla se ordena correctamente (ascendente/descendente).
- [x] 4.4 Verificar que la ordenación funciona para todas las columnas: ID (numérica), Título (alfabética), Fecha inicio (cronológica), Estado (alfabética), Asignado a (alfabética) y Progreso (numérica).
