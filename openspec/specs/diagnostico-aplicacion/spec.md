## Purpose

Dotar a PyIssuesTracker de un sistema de logging a fichero y de una ventana de depuración que hagan visibles los errores hoy silenciados, sin exponer secretos.

## Requirements

### Requirement: Registro de sucesos a fichero
La aplicación SHALL registrar sus sucesos en un fichero de log rotativo ubicado en la carpeta de configuración del usuario, con marca de tiempo, nivel y módulo de origen, en niveles configurables, registrando al menos los niveles WARNING y ERROR de la aplicación.

#### Scenario: Arranque con logging configurado
- **WHEN** la aplicación arranca
- **THEN** se crea (si no existe) y se abre el fichero de log en la carpeta de configuración del usuario
- **AND** las entradas incluyen marca de tiempo, nivel y módulo

#### Scenario: Rotación del fichero de log
- **WHEN** el fichero de log alcanza el tamaño máximo configurado
- **THEN** el `RotatingFileHandler` rota el fichero y conserva el número de backups configurado

#### Scenario: Registro de un error de la aplicación
- **WHEN** la aplicación captura un error en una operación clave
- **THEN** se escribe una entrada de nivel ERROR con contexto en el fichero de log

### Requirement: Ocultación de secretos
El log SHALL NOT contener la API key de Redmine ni credenciales de autenticación.

#### Scenario: Mensaje con API key
- **WHEN** se intenta registrar un mensaje que incluye la cabecera `X-Redmine-API-Key` o el valor de la API key
- **THEN** el valor del secreto no aparece en el fichero de log

### Requirement: Registro de todo error capturado en operaciones clave
Todo `RedmineError` o excepción inesperada capturada en operaciones clave (carga de issues, alta/edición de tarea, filtros e informes) SHALL registrarse al menos en nivel ERROR con contexto (operación, proyecto(s) implicados y parámetros relevantes).

#### Scenario: Error de carga de issues
- **WHEN** la carga de issues lanza `RedmineError`
- **THEN** se registra un ERROR con la operación, los proyectos implicados y el mensaje de la API

#### Scenario: Excepción inesperada en operación clave
- **WHEN** una operación clave lanza una excepción no prevista
- **THEN** se registra un ERROR con el tipo de excepción y el contexto de la operación

### Requirement: Ventana de depuración
La aplicación SHALL ofrecer una ventana de depuración accesible desde `Ver > Registro de diagnóstico` que muestre los mensajes en vivo, permita filtrar por nivel, limpiar, copiar y abrir el fichero/carpeta de log, sin bloquear el hilo de UI.

#### Scenario: Apertura de la ventana de depuración
- **WHEN** el usuario selecciona `Ver > Registro de diagnóstico`
- **THEN** se abre una ventana que muestra los mensajes de log en vivo

#### Scenario: Filtro por nivel
- **WHEN** el usuario selecciona un nivel mínimo en la ventana de depuración
- **THEN** solo se muestran los mensajes de ese nivel o superior

#### Scenario: Acciones de la ventana de depuración
- **WHEN** el usuario pulsa Limpiar, Copiar o Abrir carpeta de log
- **THEN** la ventana se limpia, copia el contenido al portapapeles o abre la carpeta/fichero de log, respectivamente

#### Scenario: Registro sin bloquear la UI
- **WHEN** la aplicación escribe una entrada de log mientras la UI está activa
- **THEN** el registro no bloquea el hilo de UI