## Purpose

Definir el filtro de fecha del `FilterBar`: presets rápidos y rango personalizado sobre `due_date`, combinación AND con el resto de filtros, integración con `RedmineClient` y persistencia.

## Requirements

### Requirement: Filtro por fecha con presets rapidos
El sistema SHALL incluir un filtro de fecha en el `FilterBar` con un `QComboBox` que ofrezca los siguientes presets: "Sin filtro", "Hoy", "Ayer", "Esta semana", "Semana pasada", "Este mes", "Mes pasado", "Rango personalizado". El filtro SHALL aplicarse sobre el campo `due_date` de las tareas. El filtro de fecha SHALL combinarse con los demás filtros activos (estado, prioridad, categoría, asignado) usando lógica AND — al cambiar cualquier filtro, todos los filtros activos se envían simultáneamente a la API.

#### Scenario: Usuario selecciona "Hoy"
- **WHEN** el usuario selecciona el preset "Hoy" en el combo de filtro de fecha
- **THEN** el sistema calcula el rango desde la fecha actual hasta la fecha actual (inclusive)
- **AND** envia a la API de Redmine el filtro `due_date=YYYY-MM-DD` (fecha exacta de hoy)
- **AND** la tabla se refresca mostrando solo tareas con fecha de fin igual a hoy

#### Scenario: Usuario selecciona "Esta semana"
- **WHEN** el usuario selecciona "Esta semana" (siendo viernes)
- **THEN** el sistema calcula el rango desde el lunes de la semana actual hasta el domingo de la semana actual
- **AND** envia a la API de Redmine `due_date=><YYYY-MM-DD|YYYY-MM-DD`

#### Scenario: Usuario selecciona "Sin filtro"
- **WHEN** el usuario selecciona "Sin filtro" en el combo
- **THEN** no se aplica ningun filtro de fecha
- **AND** se muestran todas las tareas independientemente de su fecha de fin

#### Scenario: Usuario selecciona "Mes pasado"
- **WHEN** el usuario selecciona "Mes pasado" y la fecha actual es 10 de junio
- **THEN** el sistema calcula el rango desde el 1 de mayo hasta el ultimo dia de mayo

#### Scenario: Filtro de fecha se combina con filtro de estado
- **WHEN** el filtro de estado está en "Abiertas" y el usuario cambia el filtro de fecha de "Sin filtro" a "Esta semana"
- **THEN** la tabla muestra solo tareas que cumplan AMBAS condiciones: estado "Abierta" Y fecha fin dentro de esta semana
- **AND** el filtro de estado no se modifica ni se ignora

#### Scenario: Cambio de filtro de estado mantiene filtro de fecha
- **WHEN** el filtro de fecha está en "Esta semana" y el usuario cambia el filtro de estado de "Abiertas" a "Todas"
- **THEN** la tabla muestra solo tareas que cumplan AMBAS condiciones: cualquier estado Y fecha fin dentro de esta semana
- **AND** el filtro de fecha no se modifica ni se ignora

#### Scenario: Cambio de cualquier filtro mantiene filtro de fecha activo
- **WHEN** el filtro de fecha está en "Hoy" y el usuario cambia la prioridad, categoría, asignado o búsqueda de texto
- **THEN** la tabla muestra tareas que cumplan TODOS los filtros activos combinados con AND (fecha + nuevo filtro)

### Requirement: Rango de fechas personalizado
El sistema SHALL permitir al usuario definir un rango de fechas manual cuando selecciona "Rango personalizado". Se SHALL mostrar dos `QDateEdit` (desde y hasta) para que el usuario seleccione las fechas.

#### Scenario: Usuario define rango personalizado
- **WHEN** el usuario selecciona "Rango personalizado" y elige desde `2026-06-01` hasta `2026-06-15`
- **THEN** el sistema envia a la API de Redmine `due_date=><2026-06-01|2026-06-15`
- **AND** la tabla se refresca con las tareas cuya fecha de fin esta en ese rango

#### Scenario: Usuario cambia del preset al rango personalizado
- **WHEN** el usuario cambia de "Esta semana" a "Rango personalizado"
- **THEN** los `QDateEdit` se hacen visibles
- **AND** el filtro se desactiva hasta que el usuario seleccione fechas explicitamente

### Requirement: Integracion del filtro de fecha con RedmineClient
El `RedmineClient.get_issues()` SHALL aceptar parametros `due_date_from: str | None` y `due_date_to: str | None`. El metodo SHALL construir el parametro de query string `due_date` usando la sintaxis de rango de Redmine (`>=<`). El `MainWindow` SHALL leer siempre los valores actuales del filtro de fecha desde el `FilterBar` en cada llamada a `_cargar_issues()`, sin depender de que el manejador del evento de fecha los pase como argumentos.

#### Scenario: Solo fecha desde
- **WHEN** `get_issues()` recibe `due_date_from="2026-06-01"` y `due_date_to=None`
- **THEN** envia `due_date=>=2026-06-01` a la API

#### Scenario: Solo fecha hasta
- **WHEN** `get_issues()` recibe `due_date_from=None` y `due_date_to="2026-06-15"`
- **THEN** envia `due_date=<=2026-06-15` a la API

#### Scenario: Rango completo
- **WHEN** `get_issues()` recibe `due_date_from="2026-06-01"` y `due_date_to="2026-06-15"`
- **THEN** envia `due_date=><2026-06-01|2026-06-15` a la API

### Requirement: Persistencia del filtro de fecha
El `SettingsManager` SHALL persistir la seleccion actual del filtro de fecha (indice del preset o valores del rango personalizado) en QSettings, y restaurarla al iniciar la aplicacion.

#### Scenario: Filtro persiste entre sesiones
- **WHEN** el usuario selecciona "Esta semana" en el filtro de fecha, cierra la app y la vuelve a abrir
- **THEN** el filtro de fecha muestra "Esta semana" como estaba seleccionado

### Requirement: Calculo correcto de presets de semana
Los presets "Esta semana" y "Semana pasada" SHALL calcularse usando la convencion de semana de lunes a domingo (ISO 8601).

#### Scenario: Calculo de esta semana un miercoles
- **WHEN** hoy es miercoles 10 de junio 2026
- **THEN** "Esta semana" calcula el rango desde lunes 8 de junio hasta domingo 14 de junio

#### Scenario: Calculo de semana pasada un martes
- **WHEN** hoy es martes 9 de junio 2026
- **THEN** "Semana pasada" calcula el rango desde lunes 1 de junio hasta domingo 7 de junio
