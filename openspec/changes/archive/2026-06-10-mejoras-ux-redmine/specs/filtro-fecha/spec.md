## ADDED Requirements

### Requirement: Filtro por fecha con presets rapidos
El sistema DEBE incluir un filtro de fecha en el `FilterBar` con un `QComboBox` que ofrezca los siguientes presets: "Sin filtro", "Hoy", "Ayer", "Esta semana", "Semana pasada", "Este mes", "Mes pasado", "Rango personalizado". El filtro DEBE aplicarse sobre el campo `due_date` de las tareas.

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

### Requirement: Rango de fechas personalizado
El sistema DEBE permitir al usuario definir un rango de fechas manual cuando selecciona "Rango personalizado". Se DEBE mostrar dos `QDateEdit` (desde y hasta) para que el usuario seleccione las fechas.

#### Scenario: Usuario define rango personalizado
- **WHEN** el usuario selecciona "Rango personalizado" y elige desde `2026-06-01` hasta `2026-06-15`
- **THEN** el sistema envia a la API de Redmine `due_date=><2026-06-01|2026-06-15`
- **AND** la tabla se refresca con las tareas cuya fecha de fin esta en ese rango

#### Scenario: Usuario cambia del preset al rango personalizado
- **WHEN** el usuario cambia de "Esta semana" a "Rango personalizado"
- **THEN** los `QDateEdit` se hacen visibles
- **AND** el filtro se desactiva hasta que el usuario seleccione fechas explicitamente

### Requirement: Integracion del filtro de fecha con RedmineClient
El `RedmineClient.get_issues()` DEBE aceptar parametros `due_date_from: str | None` y `due_date_to: str | None`. El metodo DEBE construir el parametro de query string `due_date` usando la sintaxis de rango de Redmine (`>=<`).

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
El `SettingsManager` DEBE persistir la seleccion actual del filtro de fecha (indice del preset o valores del rango personalizado) en QSettings, y restaurarla al iniciar la aplicacion.

#### Scenario: Filtro persiste entre sesiones
- **WHEN** el usuario selecciona "Esta semana" en el filtro de fecha, cierra la app y la vuelve a abrir
- **THEN** el filtro de fecha muestra "Esta semana" como estaba seleccionado

### Requirement: Calculo correcto de presets de semana
Los presets "Esta semana" y "Semana pasada" DEBEN calcularse usando la convencion de semana de lunes a domingo (ISO 8601).

#### Scenario: Calculo de esta semana un miercoles
- **WHEN** hoy es miercoles 10 de junio 2026
- **THEN** "Esta semana" calcula el rango desde lunes 8 de junio hasta domingo 14 de junio

#### Scenario: Calculo de semana pasada un martes
- **WHEN** hoy es martes 9 de junio 2026
- **THEN** "Semana pasada" calcula el rango desde lunes 1 de junio hasta domingo 7 de junio
