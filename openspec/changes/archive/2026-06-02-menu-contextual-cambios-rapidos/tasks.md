## 1. Infraestructura: señal y menú contextual en TaskTable

- [x] 1.1 Añadir `customContextMenuRequested` a `TaskTable.__init__()` con `self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)` y conectar a `_show_context_menu`.
- [x] 1.2 Crear señal `cambio_rapido = pyqtSignal(int, str, int)` en `TaskTable` con parámetros `(issue_id, tipo, valor)`.
- [x] 1.3 Implementar `_show_context_menu(pos)` que detecte la columna mediante `self.columnAt(pos.x())` y despache al método correspondiente según `COL_PROGRESS`, `COL_ASSIGNED_TO`, `COL_STATUS`. Solo actuar si hay fila seleccionada (`self.currentRow() >= 0`).
- [x] 1.4 Importar `QMenu` y `QAction` en `task_table.py`.

## 2. Menú contextual: progreso (incrementos del 20%)

- [x] 2.1 Implementar `_show_progress_menu(pos, issue_id, current_progress)` que cree un `QMenu` con acciones para 0%, 20%, 40%, 60%, 80%, 100%. Marcar la acción correspondiente al progreso actual como checked.
- [x] 2.2 Conectar cada acción para emitir `cambio_rapido.emit(issue_id, "progreso", valor)`.

## 3. Menú contextual: asignado a

- [x] 3.1 Implementar `_show_assign_menu(pos, issue_id)` que cree un `QMenu` con acción "Asignarme a mí", separador, y acciones para cada persona frecuente (o "No hay personas frecuentes" deshabilitada si la lista está vacía).
- [x] 3.2 Conectar "Asignarme a mí" para emitir `cambio_rapido.emit(issue_id, "asignado", self._current_user_id)` (requiere que TaskTable reciba `_current_user_id`).
- [x] 3.3 Conectar cada persona frecuente para emitir `cambio_rapido.emit(issue_id, "asignado", user_id)`.

## 4. Menú contextual: estado

- [x] 4.1 Añadir atributo `_statuses: list[tuple[int, str]]` a `TaskTable` y método `set_statuses(statuses)` para recibir la lista desde `MainWindow`.
- [x] 4.2 Implementar `_show_status_menu(pos, issue_id, current_status_id)` que cree un `QMenu` con una acción por cada estado. Marcar el estado actual como checked.
- [x] 4.3 Conectar cada acción para emitir `cambio_rapido.emit(issue_id, "estado", status_id)`.

## 5. Personas frecuentes: almacenamiento en SettingsManager

- [x] 5.1 Añadir constante `SETTINGS_KEY_FREQUENT_PEOPLE = "frequent/people"` en `app/utils/constants.py`.
- [x] 5.2 Añadir propiedades `frequent_people` (get/set) en `app/services/settings_manager.py` que lean/guarden una lista de IDs como string separado por comas. El getter devuelve `list[int]`, el setter recibe `list[int]`.
- [x] 5.3 Añadir método `add_frequent_person(user_id: int)` en `SettingsManager` que inserte al frente, elimine duplicados y trunque a 5 elementos.

## 6. Personas frecuentes: registro automático en MainWindow

- [x] 6.1 Pasar `SettingsManager` a `TaskTable` (o usar el existente) para que el menú contextual pueda leer las personas frecuentes.
- [x] 6.2 Crear método `_registrar_asignacion(user_id: int)` en `MainWindow` que llame a `self._settings.add_frequent_person(user_id)` si `user_id != self._current_user_id`.
- [x] 6.3 Llamar a `_registrar_asignacion()` desde `_asignar_tarea()` tras `assign_issue()` exitoso (línea ~473).
- [x] 6.4 Llamar a `_registrar_asignacion()` en el handler del menú contextual de asignación cuando el tipo sea "asignado" y el user_id no sea el propio.

## 7. Integración en MainWindow

- [x] 7.1 Pasar `_statuses` y `_current_user_id` a `TaskTable` desde `MainWindow` tras cargar los estados (método `set_context_data` o setters individuales).
- [x] 7.2 Conectar `task_table.cambio_rapido` a un nuevo slot `_on_cambio_rapido(issue_id, tipo, valor)` en `MainWindow`.
- [x] 7.3 Implementar `_on_cambio_rapido`: según `tipo`, mostrar `QMessageBox.question` de confirmación y, si se acepta, llamar a `update_issue(issue_id, done_ratio=valor)` (progreso), `assign_issue(issue_id, valor)` (asignado, registrando frecuente), o `update_issue(issue_id, status_id=valor)` (estado). Refrescar tabla tras cada cambio exitoso.

## 8. Verificación

- [x] 8.1 Verificar que clic derecho en progreso muestra 6 opciones y actualiza correctamente con confirmación.
- [x] 8.2 Verificar que clic derecho en asignado muestra "Asignarme a mí" y personas frecuentes (o mensaje si vacío).
- [x] 8.3 Verificar que las personas frecuentes se actualizan al asignar desde cualquier vía.
- [x] 8.4 Verificar que clic derecho en estado muestra todos los estados y cambia correctamente.
