## Purpose

Definir las preferencias de notificación de nuevas tareas: habilitación global, suscripción por proyecto, filtro por asignación, intervalo de polling configurable y persistencia en QSettings.

## Requirements

### Requirement: Habilitar y deshabilitar notificaciones
El sistema SHALL permitir al usuario activar o desactivar globalmente las notificaciones de nuevas tareas. Cuando las notificaciones estan deshabilitadas, el polling SHALL seguir funcionando para mantener la tabla actualizada, pero no se mostraran notificaciones del sistema (tray).

#### Scenario: Usuario deshabilita notificaciones
- **WHEN** el usuario desmarca el checkbox "Activar notificaciones" en la pestana Notificaciones y guarda los cambios
- **THEN** no se mostraran notificaciones del sistema al detectar nuevas tareas
- **AND** la tabla de tareas seguira actualizandose con el polling

#### Scenario: Usuario habilita notificaciones
- **WHEN** el usuario marca el checkbox "Activar notificaciones" y guarda
- **THEN** se mostraran notificaciones del sistema al detectar nuevas tareas segun el resto de preferencias configuradas

### Requirement: Suscripcion por proyecto
El sistema SHALL permitir al usuario seleccionar uno o varios proyectos de Redmine sobre los que desea recibir notificaciones. Si no se selecciona ningun proyecto, se notificaran tareas de todos los proyectos visibles.

#### Scenario: Usuario selecciona proyectos especificos
- **WHEN** el usuario marca los proyectos "Proyecto A" y "Proyecto B" en la lista de suscripcion y guarda
- **THEN** solo se notificaran nuevas tareas detectadas en "Proyecto A" o "Proyecto B"
- **AND** las tareas de otros proyectos no generaran notificaciones

#### Scenario: Usuario selecciona "Todos los proyectos"
- **WHEN** el usuario marca la opcion "[TODOS]" en la lista de suscripcion
- **THEN** las demas opciones se desmarcan automaticamente
- **AND** se notificaran nuevas tareas de cualquier proyecto visible

#### Scenario: Usuario no selecciona ningun proyecto
- **WHEN** el usuario desmarca todos los proyectos de la lista y guarda
- **THEN** se notificaran tareas de todos los proyectos (comportamiento por defecto)

### Requirement: Filtro por asignacion
El sistema SHALL permitir al usuario elegir entre recibir notificaciones solo de tareas que le estan asignadas o de todas las tareas del proyecto.

#### Scenario: Usuario elige "Solo mis tareas"
- **WHEN** el usuario selecciona el radio button "Solo las tareas que tengo asignadas" y guarda
- **THEN** solo se notificaran nuevas tareas cuyo `assigned_to` coincida con el usuario actual de Redmine

#### Scenario: Usuario elige "Todas las tareas"
- **WHEN** el usuario selecciona el radio button "Todas las tareas del proyecto" y guarda
- **THEN** se notificaran todas las tareas nuevas detectadas, independientemente de su asignacion

### Requirement: Intervalo de polling configurable
El sistema SHALL permitir al usuario configurar el intervalo de tiempo entre comprobaciones de nuevas tareas.

#### Scenario: Usuario cambia el intervalo de polling
- **WHEN** el usuario establece el intervalo en 10 minutos mediante el spinbox y guarda
- **THEN** el timer de polling se reconfigura para ejecutarse cada 10 minutos
- **AND** el cambio se aplica inmediatamente sin necesidad de reiniciar la aplicacion

#### Scenario: Intervalo fuera de rango
- **WHEN** el usuario intenta establecer un valor inferior a 1 minuto o superior a 60 minutos
- **THEN** el spinbox no permite valores fuera del rango 1-60

### Requirement: Persistencia de preferencias de notificacion
El sistema SHALL guardar todas las preferencias de notificacion en QSettings y cargarlas al iniciar la aplicacion.

#### Scenario: Preferencias persisten entre sesiones
- **WHEN** el usuario configura sus preferencias de notificacion, cierra la aplicacion y la vuelve a abrir
- **THEN** las preferencias de notificacion se mantienen tal como las dejo
- **AND** los valores por defecto son: notificaciones habilitadas, todos los proyectos, todas las tareas, intervalo de 5 minutos

### Requirement: Acceso programatico a preferencias desde SettingsManager
El `SettingsManager` SHALL exponer propiedades para consultar las preferencias de notificacion desde cualquier parte de la aplicacion.

#### Scenario: MainWindow consulta preferencias durante el polling
- **WHEN** el timer de polling se dispara
- **THEN** `MainWindow` puede consultar `self._settings.notifications_enabled`, `.notifications_projects`, `.notifications_assigned_only`, y `.poll_interval_minutes` para decidir si notificar y que filtros aplicar
