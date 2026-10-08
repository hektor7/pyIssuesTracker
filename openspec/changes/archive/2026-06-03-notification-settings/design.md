## Context

Actualmente el polling de nuevas tareas esta hardcodeado en `MainWindow` con un intervalo fijo de 300 segundos y sin filtros de notificacion. Las preferencias se guardan en `QSettings` a traves de `SettingsManager`, que expone propiedades para cada clave. El dialogo `SettingsDialog` tiene 3 pestanas (Redmine, Proxy, Apariencia) con una arquitectura basada en `QTabWidget`.

El cliente Redmine (`RedmineClient.get_issues()`) ya soporta filtrado por `project_id` y `assigned_to_id` (incluyendo `"me"` para el usuario actual). El sistema de notificaciones usa `QSystemTrayIcon.showMessage()` a traves de `TrayManager`.

## Goals / Non-Goals

**Goals:**
- Permitir al usuario habilitar/deshabilitar notificaciones desde la configuracion
- Permitir seleccionar uno o varios proyectos sobre los que recibir notificaciones
- Elegir entre recibir solo tareas asignadas al usuario o todas las del proyecto
- Configurar el intervalo de polling entre comprobaciones
- Persistir las preferencias en QSettings y aplicarlas en tiempo de ejecucion

**Non-Goals:**
- Notificaciones push (WebSocket, server-sent events) -- se mantiene el modelo de polling
- Sonido personalizado por notificacion
- Configuracion de notificaciones por tipo de evento (creacion, edicion, etc.)
- Filtros avanzados (por prioridad, tracker, etc.) -- se delega a futuras iteraciones
- Notificaciones para multiples cuentas Redmine simultaneamente

## Decisions

### 1. Nueva pestana en `SettingsDialog` con `QGroupBox` organizados logicamente

**Alternativa considerada:** Dialogo separado. **Rechazada** porque fragmenta la configuracion. Una pestana dentro del dialogo existente es mas coherente con la UX actual y requiere menos cambios estructurales.

### 2. Selector multiple de proyectos con `QListWidget` + checkboxes

**Alternativa considerada:** `QComboBox` con multi-seleccion. **Rechazada** porque Qt6 no soporta multi-seleccion nativa en `QComboBox` sin herencia compleja. Un `QListWidget` con `checkState` es mas sencillo y da mejor visibilidad de la seleccion. Se incluye un item especial "[TODOS]" como atajo.

### 3. Radio buttons para filtro de asignacion: "Solo mis tareas" / "Todas las tareas"

**Alternativa considerada:** Checkbox unico "Solo mis tareas". **Rechazada** porque no es obvio que significa cuando esta desmarcado. Radio buttons hacen el estado explicito y permiten añadir opciones futuras (ej: "Sin asignar").

### 4. `QSpinBox` para intervalo de polling en minutos (1-60, default 5)

**Alternativa considerada:** Slider. **Rechazada** porque para valores discretos de 1-60 un spinbox es mas preciso y ocupa menos espacio.

### 5. Nuevas claves en `SettingsManager` bajo grupo `notifications/`

Las claves seran:
- `notifications/enabled` (bool, default `true`)
- `notifications/projects` (str, IDs separados por comas, default vacio = todos)
- `notifications/assigned_only` (bool, default `false`)
- `notifications/poll_interval` (int, minutos, default `5`)

El `SettingsManager` expone propiedades con tipos nativos y logica de parseo/serializacion.

### 6. El `MainWindow` lee preferencias al vuelo, sin reinicio

Las preferencias de notificacion se consultan en `_update_poll_timer()` (para el intervalo) y en `_check_new_issues()` (para filtrar por proyecto/asignacion). No se requiere reiniciar la aplicacion ni reconectar.

## Risks / Trade-offs

- **[Riesgo] Proyectos eliminados/renombrados**: Si un proyecto suscrito deja de existir, las notificaciones simplemente no encontraran issues. No es critico. → **Mitigacion**: Al guardar settings, validar que los IDs existen contra la lista actual de proyectos.
- **[Riesgo] Lista de proyectos vacia**: Si el usuario marca solo proyectos que luego no tienen issues nuevas, no recibira notificaciones. → **Mitigacion**: Mostrar un texto informativo en la UI: "Si no seleccionas ningun proyecto, se notificaran todos."
- **[Trade-off] Polling en multiples proyectos**: Con multiples proyectos suscritos, `_check_new_issues` hara una llamada API por proyecto. Para evitar saturar la API, se secuencian las llamadas (no en paralelo). El coste es aceptable para <10 proyectos con intervalo >=1 minuto.
