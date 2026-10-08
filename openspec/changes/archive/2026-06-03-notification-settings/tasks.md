## 1. Modelo de datos y persistencia

- [x] 1.1 Anadir claves de QSettings en `app/utils/constants.py`: `NOTIFICATIONS_ENABLED`, `NOTIFICATIONS_PROJECTS`, `NOTIFICATIONS_ASSIGNED_ONLY`, `NOTIFICATIONS_POLL_INTERVAL`
- [x] 1.2 Implementar propiedades en `app/services/settings_manager.py`: `notifications_enabled` (bool), `notifications_projects` (list[int]), `notifications_assigned_only` (bool), `poll_interval_minutes` (int) con lectura/escritura desde QSettings y valores por defecto
- [x] 1.3 Anadir tests unitarios para las nuevas propiedades de `SettingsManager` verificando persistencia, defaults y tipos

## 2. Interfaz de configuracion - Pestana Notificaciones

- [x] 2.1 Crear metodo `_create_notifications_tab()` en `app/dialogs/settings_dialog.py` con: checkbox "Activar notificaciones", QListWidget con checkboxes de proyectos (+ item "[TODOS]"), radio buttons "Solo mis tareas"/"Todas las tareas", QSpinBox para intervalo (1-60 min)
- [x] 2.2 Anadir logica "[TODOS]" en la lista de proyectos: al marcarlo se desmarcan los demas, al marcar un proyecto concreto se desmarca "[TODOS]"
- [x] 2.3 Conectar carga/guardado: `_load_settings()` debe cargar preferencias de notificacion desde `SettingsManager`, `_save_and_accept()` debe guardarlas
- [x] 2.4 Anadir la nueva pestana al `QTabWidget` en `__init__()` de `SettingsDialog`

## 3. Integracion en MainWindow

- [x] 3.1 Modificar `_update_poll_timer()` en `app/main_window.py` para usar `self._settings.poll_interval_minutes` en lugar del valor hardcodeado de 300000 ms
- [x] 3.2 Modificar `_check_new_issues()` para: (a) respetar `notifications_enabled` al decidir si llamar a `_notify_new_issues()`, (b) filtrar issues detectadas por `notifications_projects` y `notifications_assigned_only` antes de notificar
- [x] 3.3 Si `notifications_assigned_only` es true, obtener el `user_id` actual del cliente Redmine y usarlo como filtro en las queries de polling o en el filtrado post-query
- [x] 3.4 Verificar que los cambios de preferencias se aplican sin reinicio: probar cambiar configuracion, guardar, y comprobar que el siguiente poll usa las nuevas preferencias

## 4. Pruebas manuales

- [x] 4.1 Probar habilitar/deshabilitar notificaciones: con notificaciones deshabilitadas no deben aparecer mensajes del sistema
- [x] 4.2 Probar suscripcion por proyecto: seleccionar un solo proyecto y verificar que solo se notifican tareas de ese proyecto
- [x] 4.3 Probar filtro "Solo mis tareas": asignar una tarea a otro usuario y verificar que no genera notificacion
- [x] 4.4 Probar intervalo de polling: cambiar a 1 minuto y verificar que comprueba cada 1 minuto
- [x] 4.5 Probar persistencia: cerrar y reabrir la aplicacion, verificar que las preferencias se mantienen
