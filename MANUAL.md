# Manual de Usuario — PyIssuesTracker v0.3.16

Cliente de escritorio multiplataforma para Redmine. Gestiona tus tareas desde una aplicacion nativa con soporte para bandeja del sistema, notificaciones, proxy corporativo y entornos con autenticacion SSO.

---

## Indice

1. [Requisitos del sistema](#1-requisitos-del-sistema)
2. [Instalacion y ejecucion](#2-instalacion-y-ejecucion)
3. [Primera configuracion](#3-primera-configuracion)
   - [3.1 Pestana Redmine](#31-pestana-redmine)
   - [3.2 Pestana Proxy](#32-pestana-proxy)
   - [3.3 Pestana Apariencia](#33-pestana-apariencia)
4. [Conexion a Redmine detras de SSO](#4-conexion-a-redmine-detras-de-sso)
5. [Interfaz principal](#5-interfaz-principal)
   - [5.1 Barra de herramientas](#51-barra-de-herramientas)
   - [5.2 Barra de filtros](#52-barra-de-filtros)
   - [5.3 Tabla de tareas](#53-tabla-de-tareas)
   - [5.4 Indicador de estado](#54-indicador-de-estado)
6. [Crear y editar tareas](#6-crear-y-editar-tareas)
   - [6.1 Dialogo de tarea](#61-dialogo-de-tarea)
   - [6.2 Menciones @usuario](#62-menciones-usuario)
   - [6.3 Adjuntos](#63-adjuntos)
7. [Acciones rapidas sobre tareas](#7-acciones-rapidas-sobre-tareas)
   - [7.1 Asignar tarea](#71-asignar-tarea)
   - [7.2 Completar tarea](#72-completar-tarea)
   - [7.3 Rechazar tarea](#73-rechazar-tarea)
8. [Menus contextuales](#8-menus-contextuales)
   - [8.1 Menu de progreso](#81-menu-de-progreso)
   - [8.2 Menu de estado](#82-menu-de-estado)
   - [8.3 Menu de asignacion](#83-menu-de-asignacion)
   - [8.4 Menu de fecha fin](#84-menu-de-fecha-fin)
9. [Filtros avanzados](#9-filtros-avanzados)
   - [9.1 Filtro de texto](#91-filtro-de-texto)
   - [9.2 Filtro por prioridad y categoria](#92-filtro-por-prioridad-y-categoria)
   - [9.3 Filtro por fecha](#93-filtro-por-fecha)
   - [9.4 Filtro de proyecto persistente](#94-filtro-de-proyecto-persistente)
10. [Ordenacion de la tabla](#10-ordenacion-de-la-tabla)
11. [Notificaciones de bandeja](#11-notificaciones-de-bandeja)
12. [Auto-actualizacion](#12-auto-actualizacion)
13. [Atajos de teclado](#13-atajos-de-teclado)
14. [Temas visuales](#14-temas-visuales)
15. [Solucion de problemas](#15-solucion-de-problemas)

---

## 1. Requisitos del sistema

- **Python 3.9 o superior**
- **Linux**: `libxcb-cursor0` (en Debian/Ubuntu/Mint: `sudo apt install libxcb-cursor0`)
- **Windows 10/11**: sin dependencias adicionales

---

## 2. Instalacion y ejecucion

El proyecto incluye lanzadores que detectan Python, crean un entorno virtual, instalan las dependencias y arrancan la aplicacion automaticamente.

### Linux

```bash
git clone <repositorio>
cd pyIssuesTracker
chmod +x launcher.sh
./launcher.sh
```

### Windows

Doble clic en `launcher.bat`.

> La primera ejecucion tarda un poco mas porque instala las dependencias. Las siguientes arrancan directamente.

### Integracion en el menu del sistema (Linux)

```bash
cp pyissuestracker.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

---

## 3. Primera configuracion

Para usar la aplicacion necesitas una **API key de Redmine**. Se obtiene en tu perfil de Redmine: _Mi cuenta -> Mostrar API key_.

Abre la configuracion desde el menu **Archivo -> Configuracion** (o boton **Config** en la barra de herramientas).

### 3.1 Pestana Redmine

| Campo | Descripcion |
|---|---|
| **URL del servidor** | Direccion completa de tu instancia Redmine (ej. `https://redmine.mi-empresa.com`) |
| **API Key** | Tu clave de acceso a la API REST de Redmine |
| **Cookie** | Header de cookies del navegador (solo si Redmine esta tras un SSO) |
| **Headers extra** | Cabeceras HTTP adicionales que requiera el proxy SSO (formato `Clave: Valor`, una por linea) |

### 3.2 Pestana Proxy

Si tu equipo sale a Internet a traves de un proxy corporativo, activa esta pestana:

| Campo | Descripcion |
|---|---|
| **Tipo** | HTTP, HTTPS o SOCKS5 |
| **Host / Puerto** | Direccion y puerto del servidor proxy |
| **Usuario / Contrasena** | Credenciales de autenticacion (opcional) |

Cuando el proxy esta activo, aparece el indicador **PROXY** en azul en la barra de estado inferior.

### 3.3 Pestana Apariencia

Elige entre los cuatro temas disponibles. El cambio se aplica al reiniciar la aplicacion.

---

## 4. Conexion a Redmine detras de SSO

Si tu instancia de Redmine esta protegida por un portal SSO (Azure AD, Okta, Keycloak...), la API key por si sola no bastara. La aplicacion detecta esta situacion y muestra un mensaje indicando que necesitas credenciales de sesion adicionales.

### Como obtener las cookies del navegador

1. Abre Redmine en tu navegador e inicia sesion normalmente a traves del portal SSO
2. Pulsa **F12** para abrir las herramientas de desarrollo
3. Ve a la pestana **Network** (Red)
4. Recarga la pagina con **F5**
5. Busca cualquier peticion dirigida al servidor Redmine y haz clic en ella
6. En el panel de detalle, busca **Request Headers**
7. Localiza la linea **Cookie:** y copia **todo su valor**, por ejemplo:

   ```
   JSESSIONID=abc123; _redmine_session=xyz789; SSO_TOKEN=qwerty
   ```

8. Pega ese valor completo en el campo **Cookie** de la configuracion

### Headers extra

En la misma seccion **Request Headers** pueden aparecer cabeceras adicionales requeridas por el SSO:

```
Authorization: Bearer abcdef123456
X-Custom-Auth: valor
```

Copia estas lineas en el campo **Headers extra** respetando el formato `Clave: Valor` (una por linea).

### Verificar la conexion

Tras configurar las cookies y headers, ve a **Archivo -> Conectar** (o pulsa `Ctrl+R`). El LED en la barra inferior se pondra **verde** si la conexion es correcta.

---

## 5. Interfaz principal

La ventana principal se organiza en cuatro zonas:

```
+-----------------------------------------+
|  Barra de herramientas (iconos)         |
+-----------------------------------------+
|  Barra de filtros (proyecto, estado...) |
+-----------------------------------------+
|  Tabla de tareas (columnas)             |
+-----------------------------------------+
|  Barra de estado (LED + indicadores)    |
+-----------------------------------------+
```

### 5.1 Barra de herramientas

| Boton | Accion |
|---|---|
| **Nuevo** | Crear una nueva tarea en el proyecto seleccionado |
| **Editar** | Modificar la tarea seleccionada (tambien con doble clic) |
| **Asignar** | Asignar la tarea a ti mismo (por defecto) o a otro miembro |
| **Completada** | Marcar como completada: 100% de progreso, estado "Resuelta" y fecha de fin a hoy |
| **Rechazar** | Rechazar la tarea cambiando su estado y anadiendo un comentario |
| **Refrescar** | Recargar la lista de tareas desde Redmine |
| **Config** | Abrir la ventana de configuracion |

### 5.2 Barra de filtros

La barra de filtros permite acotar las tareas visibles mediante varios criterios, organizados en dos filas.

**Fila superior:**

| Filtro | Descripcion |
|---|---|
| **Proyecto** | Combo desplegable con todos los proyectos visibles. Escribe para buscar por nombre y pulsa Enter para seleccionar |
| **Fijar filtro** | Al marcar esta casilla, el proyecto seleccionado se mantiene al reiniciar la aplicacion |
| **Estado** | Filtra por tareas abiertas (por defecto), cerradas o todas |
| **Asignado a** | Filtra por "Cualquiera", "Sin asignar", "Asignadas a mi" o un miembro concreto |
| **Prioridad** | Permite buscar y seleccionar una prioridad especifica |
| **Categoria** | Permite buscar y seleccionar una categoria del proyecto |

**Fila inferior:**

| Filtro | Descripcion |
|---|---|
| **Buscar** | Campo de texto que filtra en tiempo real por coincidencia parcial en el titulo |
| **Fecha** | Filtro por fecha de fin con presets: Hoy, Ayer, Esta semana, Semana pasada, Este mes, Mes pasado, o Rango personalizado |

### 5.3 Tabla de tareas

| Columna | Descripcion |
|---|---|
| **ID** | Identificador de la tarea en Redmine |
| **Tracker** | Tipo de tarea (Bug, Feature, Soporte...) |
| **Titulo** | Al pasar el cursor se muestra un tooltip con la descripcion completa, tracker, autor y persona asignada |
| **Fecha inicio** | Fecha de comienzo de la tarea |
| **Fecha fin** | Fecha limite. Se puede editar con doble clic |
| **Estado** | Estado actual del flujo de trabajo |
| **Progreso %** | Barra de progreso visual: verde (100%), naranja (parcial), gris (0%) |
| **Asignado a** | Persona responsable de la tarea |
| **Link** | Boton para abrir la tarea directamente en Redmine en el navegador |

Las filas con prioridad **Inmediata** aparecen con fondo rojo intenso y las de prioridad **Urgente** con un rojo mas suave.

### 5.4 Indicador de estado

El LED en la esquina inferior derecha muestra el estado de la conexion:

| Estado | Significado |
|---|---|
| Verde | Conectado correctamente a Redmine |
| Rojo | Sin conexion o error |
| Naranja parpadeante | Intentando conectar |
| PROXY (azul) | Usando proxy para las conexiones salientes |

---

## 6. Crear y editar tareas

### 6.1 Dialogo de tarea

Pulsa **Nuevo** o haz doble clic en una tarea existente para abrir el dialogo. Los campos disponibles son:

| Campo | Descripcion |
|---|---|
| **Proyecto** | Proyecto al que pertenece la tarea |
| **Tracker** | Tipo de tarea. Se puede buscar por nombre |
| **Asunto** | Titulo de la tarea |
| **Descripcion** | Texto completo con soporte para menciones @usuario |
| **Prioridad** | Nivel de prioridad |
| **Categoria** | Categoria dentro del proyecto |
| **Asignado a** | Persona responsable. Se muestra "(Sin asignar)" por defecto |
| **Fecha inicio** | Fecha de comienzo |
| **Fecha fin** | Fecha limite (con casilla para habilitar/deshabilitar) |
| **Estado** | Estado del flujo de trabajo (solo en edicion) |
| **Progreso %** | Porcentaje completado (slider + campo numerico) |

Al editar una tarea existente (**Editar** o doble clic), todos los campos se precargan con los valores actuales, incluida la persona asignada.

### 6.2 Menciones @usuario

En los campos **Descripcion** y **Comentarios**, escribe `@` seguido de letras para que aparezca un popup con los miembros del proyecto cuyo nombre coincide. El popup muestra hasta 5 sugerencias y se cierra con la tecla **Escape**.

### 6.3 Adjuntos

Al crear o editar una tarea, puedes adjuntar archivos. Los adjuntos subidos se muestran en el dialogo con su nombre, tamano y fecha. Puedes descargar cualquier adjunto haciendo clic en el y seleccionando la carpeta de destino.

---

## 7. Acciones rapidas sobre tareas

### 7.1 Asignar tarea

Pulsa el boton **Asignar** para abrir el dialogo de asignacion:

- **Asignar a**: combo con busqueda por teclado. El usuario autenticado aparece en primera posicion tras "(Sin asignar)". El resto de miembros se ordenan alfabeticamente
- **Comentario**: campo multilinea opcional que se anade como nota en la tarea

### 7.2 Completar tarea

Pulsa **Completada** para abrir el dialogo de finalizacion:

- **Comentario**: nota opcional que se anade al historial de la tarea
- Al confirmar, la tarea se marca con 100% de progreso y estado "Resuelta"
- La aplicacion intenta establecer la fecha de fin a hoy. Si Redmine rechaza el campo `due_date` (HTTP 422), reintenta automaticamente sin el
- Si no existe un estado de tipo "Resuelta" en el servidor, se muestra una advertencia y no se envia la peticion

### 7.3 Rechazar tarea

Pulsa **Rechazar** para abrir el dialogo de rechazo:

- Selecciona el estado de rechazo y escribe el motivo
- La tarea se actualiza al estado seleccionado y se anade el comentario como nota

---

## 8. Menus contextuales

### 8.1 Menu de progreso

**Clic derecho** sobre la barra de progreso de cualquier tarea:

- Opciones: **0%, 20%, 40%, 60%, 80%, 100%**
- El valor actual aparece marcado
- Al seleccionar un valor se pide confirmacion antes de actualizar
- Si Redmine rechaza el cambio (HTTP 422), se muestra el detalle de los errores de validacion

### 8.2 Menu de estado

**Clic derecho** sobre la columna **Estado** de una tarea:

- Muestra todos los estados disponibles en el servidor Redmine
- El estado actual aparece resaltado
- Al seleccionar un nuevo estado se pide confirmacion
- Si el estado no esta permitido por el workflow del tracker, Redmine devuelve HTTP 422 y la aplicacion muestra un mensaje descriptivo explicando la causa probable

### 8.3 Menu de asignacion

**Clic derecho** sobre la columna **Asignado a**:

- Opcion **"Asignarme a mi"**: asigna la tarea al usuario autenticado
- **Personas frecuentes**: lista con las ultimas 5 personas a las que has asignado tareas
- Al seleccionar se pide confirmacion antes de asignar
- Las personas frecuentes se guardan automaticamente entre sesiones

### 8.4 Menu de fecha fin

**Clic derecho** sobre la columna **Fecha fin**:

- **Limpiar fecha**: elimina la fecha fin de la tarea
- **Copiar URL**: copia al portapapeles el enlace directo a la tarea en Redmine
- **Abrir en Redmine**: abre la tarea en el navegador

---

## 9. Filtros avanzados

### 9.1 Filtro de texto

El campo **Buscar** en la segunda fila de filtros permite filtrar tareas en tiempo real. Escribe cualquier texto y la tabla se actualizara mostrando solo las tareas cuyo titulo contenga ese texto (sin distinguir mayusculas/minusculas).

### 9.2 Filtro por prioridad y categoria

Los combos de **Prioridad** y **Categoria** son buscables por teclado: empieza a escribir y el combo filtrara las opciones que contengan el texto introducido.

### 9.3 Filtro por fecha

El combo **Fecha** filtra por la fecha de fin (`due_date`):

| Preset | Rango |
|---|---|
| **Hoy** | Tareas con fecha fin = hoy |
| **Ayer** | Tareas con fecha fin = ayer |
| **Esta semana** | Fecha fin entre lunes y domingo de esta semana |
| **Semana pasada** | Fecha fin entre lunes y domingo de la semana anterior |
| **Este mes** | Fecha fin dentro del mes actual |
| **Mes pasado** | Fecha fin dentro del mes anterior |
| **Rango personalizado** | Muestra dos selectores de fecha para elegir desde/hasta |

La seleccion de fecha se guarda y se mantiene al reiniciar la aplicacion.

### 9.4 Filtro de proyecto persistente

Marca la casilla **Fijar filtro** para que el proyecto seleccionado se conserve al cerrar y reabrir la aplicacion.

---

## 10. Ordenacion de la tabla

Haz clic en la cabecera de cualquier columna para ordenar la tabla por ese criterio. Un segundo clic invierte el orden (ascendente <-> descendente). Una flecha indica la direccion actual.

| Columnas | Tipo de ordenacion |
|---|---|
| ID, Progreso % | Numerica |
| Tracker, Titulo, Estado, Asignado a | Alfabetica |
| Fecha inicio, Fecha fin | Cronologica |

---

## 11. Notificaciones de bandeja

La aplicacion puede mostrar notificaciones emergentes cuando se detectan cambios en las tareas.

### Configuracion de notificaciones

Accede desde **Archivo -> Configuracion -> Notificaciones**:

| Opcion | Descripcion |
|---|---|
| **Activar notificaciones** | Habilita/deshabilita globalmente |
| **Proyectos suscritos** | Lista de proyectos para los que se reciben notificaciones |
| **Solo mis tareas** | Si se activa, solo notifica cambios en tareas asignadas al usuario actual |
| **Intervalo de consulta** | Frecuencia con la que se consulta Redmine por cambios (1-60 minutos). Por defecto: 5 min |

### Menu de bandeja

Clic derecho sobre el icono de la aplicacion en la bandeja del sistema:

- **Mostrar ventana**: restaura la aplicacion
- **Reconectar**: reintenta la conexion a Redmine
- **Salir**: cierra la aplicacion completamente

---

## 12. Auto-actualizacion

La aplicacion verifica automaticamente si hay nuevas versiones disponibles en GitHub Releases.

- **Verificacion automatica**: se ejecuta al iniciar, con un cooldown de 24 horas entre comprobaciones
- **Verificacion manual**: **Ayuda -> Buscar actualizaciones**
- **Descarga**: si hay una version nueva, se muestra un dialogo con el changelog. La descarga incluye barra de progreso y boton de cancelar
- **Proxy**: el gestor de actualizaciones respeta la configuracion de proxy definida en **Configuracion -> Proxy**

---

## 13. Atajos de teclado

| Atajo | Accion |
|---|---|
| `Ctrl + ,` | Abrir configuracion |
| `Ctrl + R` | Reconectar a Redmine |
| `Ctrl + Q` | Salir de la aplicacion |

---

## 14. Temas visuales

La aplicacion incluye cuatro temas, configurables desde **Configuracion -> Apariencia**:

| Tema | Descripcion |
|---|---|
| **Predeterminado (Claro)** | Tema nativo del sistema operativo |
| **Oscuro** | Paleta oscura personalizada |
| **Fusion Claro** | Tema Fusion de Qt con colores claros |
| **Fusion Oscuro** | Tema Fusion con paleta oscura |

El cambio de tema se aplica al reiniciar la aplicacion.

---

## 15. Solucion de problemas

### No puedo conectar a Redmine

1. Verifica que la **URL del servidor** sea correcta y accesible desde tu red
2. Comprueba que la **API key** es valida (_Mi cuenta -> Mostrar API key_ en Redmine)
3. Si el LED se queda en naranja parpadeante, puede ser un problema de timeout. Revisa si necesitas configurar un **proxy** en la pestana correspondiente
4. Si Redmine esta tras un **SSO**, asegurate de haber copiado correctamente las cookies del navegador (ver [seccion 4](#4-conexion-a-redmine-detras-de-sso))

### Error HTTP 422 al cambiar estado o progreso

Redmine rechaza la operacion porque el estado o progreso seleccionado no esta permitido en el workflow del tracker de esa tarea. La aplicacion muestra un mensaje descriptivo con los errores devueltos por la API.

### Error HTTP 422 al completar una tarea

La aplicacion intenta completar la tarea incluyendo la fecha actual como `due_date`. Si Redmine rechaza este campo, la aplicacion reintenta automaticamente sin el. Si aun asi falla, se muestra un dialogo con las causas probables (estado no valido para el tracker, transicion no permitida, etc.).

### El boton "Completada" muestra "No se encontro un estado 'Resuelta'"

El servidor Redmine no tiene configurado un estado de tipo "Resuelta" (o "Resolved"). Contacta con el administrador de Redmine para que anada este estado al workflow.

### No se muestran todos los proyectos

La aplicacion carga los proyectos de forma paginada hasta un maximo de seguridad de 2000 proyectos (20 paginas). Si tu instancia tiene mas, contacta con el administrador.

### La aplicacion no arranca en Linux

Asegurate de tener instalada la dependencia del sistema `libxcb-cursor0`:

```bash
sudo apt install libxcb-cursor0
```

---

*Manual generado a partir de la documentacion OpenSpec del proyecto. Ultima actualizacion: junio 2026.*
