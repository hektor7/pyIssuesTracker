## Purpose

Garantizar que el filtro de issues por proyectos múltiples use IDs, sea resiliente a fallos parciales, saneo IDs huérfanos y distinga "sin resultados" de "error de carga".

## Requirements

### Requirement: Filtrado por IDs de proyecto
El filtro de proyectos SHALL operar exclusivamente sobre IDs de proyecto. El nombre completo (`Padre > Hijo`) SHALL usarse solo para presentación y SHALL NOT enviarse nunca a la API.

#### Scenario: Selección múltiple de proyectos
- **WHEN** el usuario selecciona varios proyectos en el filtro
- **THEN** el filtro emite la lista de IDs seleccionados
- **AND** la consulta a Redmine se realiza con esos IDs

#### Scenario: Nombre completo solo de presentación
- **WHEN** se muestra un proyecto cuyo nombre completo es `Padre > Hijo`
- **THEN** ese texto se usa únicamente para presentación
- **AND** no se incluye en ninguna petición a la API

### Requirement: Carga resiliente multi-proyecto
Con varios proyectos seleccionados, un fallo (404/403/timeout/error de red) en uno de ellos SHALL NOT descartar los resultados de los demás.

#### Scenario: Un proyecto falla y otro responde
- **WHEN** se consultan varios proyectos y uno devuelve `404`/`403`/timeout mientras otro responde con issues
- **THEN** se devuelven los issues del proyecto que respondió
- **AND** el fallo del otro proyecto queda registrado y no aborta la operación

#### Scenario: Todos los proyectos fallan
- **WHEN** todos los proyectos consultados fallan
- **THEN** se informa de un error de carga (no de una tabla vacía sin explicación)

### Requirement: Aviso de proyectos no accesibles
La aplicación SHALL informar al usuario de qué proyectos fallaron (nombre/ID) y SHALL mostrar igualmente el resto de resultados.

#### Scenario: Aviso de proyectos fallidos
- **WHEN** la carga multi-proyecto termina con al menos un proyecto fallido
- **THEN** se muestra al usuario la lista de proyectos que fallaron (nombre/ID)
- **AND** se muestran los resultados de los proyectos que sí respondieron

### Requirement: Saneado de IDs de proyecto huérfanos
Los IDs de proyecto seleccionados o restaurados desde ajustes que no existan en la lista de proyectos cargada SHALL descartarse antes de consultar, con aviso y registro en el log.

#### Scenario: ID huérfano en la selección
- **WHEN** la selección contiene un ID que no está en la lista de proyectos cargada
- **THEN** ese ID se descarta antes de consultar a la API
- **AND** se avisa al usuario y se registra en el log

#### Scenario: ID huérfano restaurado desde ajustes
- **WHEN** se restaura desde `filter_projects` un ID cuyo proyecto ya no existe
- **THEN** el ID se descarta y no se envía a la API
- **AND** se avisa al usuario y se registra en el log

#### Scenario: Restauración de IDs válidos
- **WHEN** se restaura desde ajustes un ID que sí existe en la lista cargada
- **THEN** el ID se mantiene seleccionado

### Requirement: Distinción entre vacío y error
La UI SHALL distinguir "sin resultados" de "error de carga". Ante error SHALL NOT mostrar una tabla vacía sin explicación y SHALL registrarlo en el log.

#### Scenario: Consulta sin resultados
- **WHEN** la consulta finaliza correctamente y no hay issues
- **THEN** la UI indica "sin resultados"

#### Scenario: Error de carga
- **WHEN** la consulta finaliza con error
- **THEN** la UI muestra un aviso de error de carga
- **AND** no presenta una tabla vacía sin explicación
- **AND** se registra en el log