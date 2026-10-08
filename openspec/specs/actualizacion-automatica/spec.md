## Purpose

Definir la verificación y descarga de actualizaciones de PyIssuesTracker desde GitHub Releases: comprobación automática con cooldown y manual, selección del asset según la plataforma, descarga con barra de progreso y soporte de proxy.

## Requirements

### Requirement: Verificar actualizaciones desde GitHub
El sistema SHALL consultar la API de GitHub Releases (`https://api.github.com/repos/hektor7/pyIssuesTracker/releases`) para determinar si existe una version estable mas reciente que la version actual. La verificacion SHALL ignorar releases marcados como `prerelease` o `draft`.

#### Scenario: Hay una nueva version estable disponible
- **WHEN** la API de GitHub devuelve un release estable con tag `v0.4.0` y la version actual es `0.3.0`
- **THEN** el sistema detecta que hay una actualizacion disponible
- **AND** devuelve la informacion de la nueva version (numero, notas, URL de descarga del asset)

#### Scenario: No hay version mas reciente
- **WHEN** la API de GitHub devuelve releases estables y la mas reciente tiene tag `v0.3.0` igual a la version actual
- **THEN** el sistema indica que no hay actualizaciones disponibles

#### Scenario: Solo hay prereleases
- **WHEN** todos los releases en GitHub estan marcados como `prerelease: true`
- **THEN** el sistema indica que no hay actualizaciones disponibles (solo considera releases estables)

#### Scenario: Error de red al consultar GitHub
- **WHEN** la peticion a la API de GitHub falla por timeout o error de red
- **THEN** el sistema captura la excepcion y devuelve `available=False` sin propagar el error

### Requirement: Seleccionar asset segun plataforma
El sistema SHALL filtrar los assets del release para seleccionar el binario correcto segun el sistema operativo: en Windows (`sys.platform == "win32"`) SHALL seleccionar el asset cuyo nombre termine en `.exe`; en Linux (`sys.platform == "linux"`) SHALL seleccionar el asset cuyo nombre NO termine en `.exe`.

#### Scenario: Usuario en Windows
- **WHEN** el sistema operativo es Windows (`sys.platform == "win32"`) y el release contiene los assets `PyIssuesTracker.exe` y `PyIssuesTracker`
- **THEN** `check_for_updates()` devuelve la URL `browser_download_url` del asset `PyIssuesTracker.exe`

#### Scenario: Usuario en Linux
- **WHEN** el sistema operativo es Linux (`sys.platform == "linux"`) y el release contiene los assets `PyIssuesTracker.exe` y `PyIssuesTracker`
- **THEN** `check_for_updates()` devuelve la URL `browser_download_url` del asset `PyIssuesTracker`

#### Scenario: No hay asset para la plataforma actual
- **WHEN** el release solo contiene assets para Windows pero el usuario esta en Linux
- **THEN** el sistema indica que no hay actualizacion disponible (no puede ofrecer un asset incompatible)

### Requirement: Descargar binario con barra de progreso
El sistema SHALL descargar el asset binario desde la URL proporcionada por `check_for_updates()` en un hilo separado (`QThread`) para no bloquear la interfaz. La descarga SHALL mostrar una barra de progreso con porcentaje y permitir cancelacion.

#### Scenario: Descarga exitosa
- **WHEN** el usuario confirma la descarga y la conexion es estable
- **THEN** el sistema descarga el archivo a un directorio temporal del sistema (`tempfile.gettempdir()`)
- **AND** la barra de progreso avanza de 0% a 100% durante la descarga
- **AND** al finalizar se muestra la ruta donde se guardo el archivo

#### Scenario: Usuario cancela la descarga
- **WHEN** el usuario pulsa "Cancelar" durante la descarga
- **THEN** la descarga se detiene y el archivo parcial se elimina
- **AND** el dialogo vuelve al estado inicial permitiendo reintentar

#### Scenario: Error durante la descarga
- **WHEN** la descarga falla por error de red o timeout
- **THEN** el sistema muestra un mensaje de error explicativo
- **AND** el dialogo permite al usuario reintentar la descarga

### Requirement: Dialogo de actualizacion (UpdateDialog)
El sistema SHALL mostrar un dialogo modal (`UpdateDialog`) cuando se detecta una nueva version. El dialogo SHALL incluir: numero de version actual y nueva, notas del release (primeros 500 caracteres, con scroll si es necesario), barra de progreso (durante descarga), y botones "Descargar" y "Cancelar".

#### Scenario: Dialogo al detectar actualizacion
- **WHEN** el sistema detecta una nueva version disponible
- **THEN** se muestra `UpdateDialog` con la version actual, la nueva version, y las notas del release
- **AND** el boton "Descargar" esta habilitado
- **AND** la barra de progreso esta oculta inicialmente

#### Scenario: Dialogo sin actualizacion disponible
- **WHEN** el usuario pulsa "Buscar actualizaciones..." en el menu y no hay version nueva
- **THEN** se muestra un `QMessageBox` informando "No hay actualizaciones disponibles. Ya tienes la version mas reciente."

### Requirement: Verificacion automatica al iniciar con cooldown
El sistema SHALL verificar actualizaciones automaticamente al iniciar la aplicacion si han transcurrido mas de 24 horas desde la ultima verificacion. La fecha de la ultima verificacion SHALL persistir en QSettings (`update/last_check`).

#### Scenario: Primera verificacion automatica tras 24h
- **WHEN** la aplicacion se inicia y la ultima verificacion fue hace mas de 24 horas
- **THEN** el sistema verifica actualizaciones en segundo plano
- **AND** si hay una nueva version, muestra el `UpdateDialog`
- **AND** actualiza `update/last_check` con la fecha actual

#### Scenario: No se verifica si ya se comprobo recientemente
- **WHEN** la aplicacion se inicia y la ultima verificacion fue hace menos de 24 horas
- **THEN** el sistema NO realiza verificacion automatica

### Requirement: Acceso manual a busqueda de actualizaciones
El sistema SHALL incluir un item de menu "Buscar actualizaciones..." en el menu Archivo que permita al usuario verificar actualizaciones bajo demanda, independientemente del cooldown.

#### Scenario: Usuario busca actualizaciones manualmente
- **WHEN** el usuario selecciona "Archivo > Buscar actualizaciones..."
- **THEN** el sistema verifica actualizaciones inmediatamente
- **AND** independientemente de cuando fue la ultima verificacion automatica

### Requirement: Soporte de proxy durante verificacion y descarga
El sistema SHALL usar la configuracion de proxy definida en `SettingsManager` (host, puerto, tipo, usuario, password) al realizar peticiones HTTP a la API de GitHub y al descargar assets.

#### Scenario: Descarga a traves de proxy corporativo
- **WHEN** el usuario tiene configurado un proxy HTTP en SettingsManager
- **THEN** tanto `check_for_updates()` como `download_release()` usan el proxy configurado
- **AND** si el proxy requiere autenticacion, se usan las credenciales almacenadas
