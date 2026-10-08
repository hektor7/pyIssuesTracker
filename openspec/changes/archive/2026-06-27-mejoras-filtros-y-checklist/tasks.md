## 1. Utilidad de formateo de fecha/hora

- [x] 1.1 Añadir función `iso_datetime_to_display(iso_str: str) -> str` en `app/utils/dates.py` que convierta timestamp ISO 8601 (`2026-06-26T14:45:00Z`) a formato `DD/MM/YY HH:MM`. Manejar casos sin hora (solo `YYYY-MM-DD`), sin timezone y cadena vacía.

## 2. Unificar recolección de filtros (corregir combinación AND)

- [x] 2.1 Añadir atributos `_current_date_from` y `_current_date_to` en `FilterBar`, inicializados como `None`.
- [x] 2.2 Añadir propiedades `selected_date_from` y `selected_date_to` en `FilterBar` que expongan los valores actuales.
- [x] 2.3 Modificar `FilterBar._on_date_preset_changed()` y los handlers de rango personalizado para almacenar las fechas en `_current_date_from`/`_current_date_to` además de emitir la señal.
- [x] 2.4 Eliminar los parámetros `due_date_from`/`due_date_to` de `MainWindow._cargar_issues()`.
- [x] 2.5 Modificar `MainWindow._cargar_issues()` para leer `due_date_from` y `due_date_to` desde `self._filter_bar.selected_date_from` y `self._filter_bar.selected_date_to`.
- [x] 2.6 Simplificar `MainWindow._on_filter_date_changed()` para que solo llame a `_cargar_issues()` sin argumentos.

## 3. Multiselección en filtro "Asignado a"

- [x] 3.1 Crear widget `MultiSelectCombo` en `app/widgets/multi_select_combo.py` que muestre un `QPushButton` con el texto "N seleccionados" y despliegue un popup/menú con checkboxes para cada opción.
- [x] 3.2 Reemplazar `QComboBox` de asignado en `FilterBar` por el nuevo `MultiSelectCombo`, manteniendo las opciones "(Todos)", "Sin asignar", "Asignado a mí" como checkboxes especiales junto a los miembros del proyecto.
- [x] 3.3 Cambiar la señal `asignado_cambiado` en `FilterBar` de `pyqtSignal(int)` a `pyqtSignal(list)`.
- [x] 3.4 Actualizar `FilterBar.selected_assigned_to` para que devuelva `list` en lugar de `int`.
- [x] 3.5 Actualizar `FilterBar.set_assigned_to()` para aceptar una lista.
- [x] 3.6 Modificar `MainWindow._cargar_issues()` y `MainWindow._on_filter_assigned_changed()` para manejar `list` de IDs.
- [x] 3.7 Modificar `RedmineClient.get_issues()` para aceptar `assigned_to_id: int | str | list | None` y construir los query params adecuados. Si la API no soporta múltiples `assigned_to_id`, implementar filtrado client-side.
- [x] 3.8 Adaptar persistencia del filtro de asignado en `SettingsManager` para guardar/cargar la lista de IDs en `QSettings`.

## 4. Columnas "Creado" y "Modificado" en la tabla

- [x] 4.1 Añadir constantes `COL_CREATED = 9` y `COL_UPDATED = 10` en `TaskTable`, y añadir "Creado" y "Modificado" al array `HEADERS`.
- [x] 4.2 Configurar `ResizeToContents` para las nuevas columnas en el `__init__` de `TaskTable`.
- [x] 4.3 Incluir `created_on` y `updated_on` en el diccionario de cada issue en `MainWindow._cargar_issues()`, leyéndolos del objeto `RedmineIssue`.
- [x] 4.4 Añadir las celdas de "Creado" y "Modificado" en `TaskTable.set_issues()`, usando `iso_datetime_to_display()` para formatear los valores.
- [x] 4.5 Verificar que la ordenación por clic en cabecera funciona correctamente para las nuevas columnas (usando `setSortingEnabled(True)` ya activo).

## 5. Checklist en modo creación de tarea

- [x] 5.1 En `TaskDialog._setup_ui()`, mantener `_checklist_group.setVisible(True)` en lugar de ocultarlo; eliminar la línea `setVisible(False)`.
- [x] 5.2 Añadir atributo `_pending_checklist_items: list[str]` en `TaskDialog.__init__()`.
- [x] 5.3 Modificar `_on_checklist_item_added()`: si `not self._is_edit`, añadir el subject a `_pending_checklist_items` en lugar de llamar a la API. Mantener el comportamiento actual para modo edición.
- [x] 5.4 Deshabilitar toggle de checkboxes en modo creación: en `_on_checklist_item_toggled()`, si `not self._is_edit`, ignorar la acción.
- [x] 5.5 Modificar `MainWindow._nueva_tarea()`: tras crear la tarea nueva exitosamente, iterar `dlg.pending_checklist_items` y llamar a `self._redmine.create_checklist_item()` para cada uno. Si algún item falla, mostrar un `QMessageBox.warning`.
- [x] 5.6 Eliminar items del checklist en modo creación: `_on_checklist_item_deleted()` debe eliminar también de `_pending_checklist_items` cuando corresponda.

## 6. Pruebas y verificación

- [x] 6.1 Verificar manualmente que los filtros de estado y fecha se combinan correctamente (AND).
- [x] 6.2 Verificar que el filtro de fecha persiste al cambiar cualquier otro filtro.
- [x] 6.3 Verificar multiselección de asignados: seleccionar varios miembros y comprobar que las tareas mostradas corresponden a cualquiera de ellos.
- [x] 6.4 Verificar que las columnas "Creado" y "Modificado" se muestran con el formato correcto y son ordenables.
- [x] 6.5 Verificar que el checklist aparece y funciona en el diálogo de nueva tarea (añadir, eliminar items, guardar y comprobar que se crean en Redmine).
- [x] 6.6 Ejecutar tests existentes y verificar que no hay regresiones.
