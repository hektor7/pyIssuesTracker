## Why

Actualmente la aplicacion notifica al usuario de todas las tareas nuevas detectadas en el proyecto seleccionado, sin posibilidad de filtrar por proyecto, por asignacion, ni de deshabilitar las notificaciones. El intervalo de polling esta hardcodeado a 5 minutos y no hay ninguna configuracion de notificaciones en el dialogo de ajustes. Esto genera ruido innecesario cuando el usuario solo quiere estar al tanto de sus propias tareas o de proyectos concretos.

## What Changes

- Nueva pestana **Notificaciones** en el dialogo de configuracion (`SettingsDialog`) con:
  - Checkbox para **habilitar/deshabilitar** notificaciones globalmente
  - Selector multiple de **proyectos** a los que suscribirse (o "todos")
  - Radio buttons para elegir entre recibir **solo las asignadas al usuario** o **todas** las tareas del proyecto
  - Control del **intervalo de polling** (en minutos, con un rango razonable)
- Las preferencias se persisten en `QSettings` (claves nuevas en `notifications/`)
- El `MainWindow` lee estas preferencias al iniciar y cada vez que cambian para ajustar el comportamiento del polling
- El `SettingsManager` expone nuevas propiedades para acceder a estas preferencias

## Capabilities

### New Capabilities
- `notification-settings`: Configuracion de notificaciones desde el dialogo de ajustes: habilitacion global, suscripcion por proyecto, filtro por asignacion (solo mias/todas), e intervalo de polling configurable.

### Modified Capabilities
<!-- Ninguno - los cambios son puramente aditivos, no se modifican requisitos de specs existentes -->

## Impact

- `app/dialogs/settings_dialog.py`: Nueva pestana con widgets de notificacion
- `app/services/settings_manager.py`: Nuevas propiedades `notifications_enabled`, `notifications_projects`, `notifications_assigned_only`, `poll_interval_minutes`
- `app/utils/constants.py`: Nuevas claves de QSettings en grupo `notifications/`
- `app/main_window.py`: Uso de `SettingsManager` para leer preferencias en `_check_new_issues()` y `_update_poll_timer()`
- No hay impacto en `RedmineClient` ni en la API REST (los filtros ya existen)
