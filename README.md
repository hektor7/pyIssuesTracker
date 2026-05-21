# PyIssuesTracker

Cliente de escritorio multiplataforma para Redmine. Gestiona tus tareas desde una aplicación nativa con soporte para bandeja del sistema, notificaciones, proxy corporativo y entornos con autenticación SSO.

## Requisitos

- **Python 3.9 o superior**
- **Linux**: `libxcb-cursor0` (en Debian/Ubuntu/Mint: `sudo apt install libxcb-cursor0`)
- **Windows 10/11**: sin dependencias adicionales del sistema

## Instalación y ejecución

Clona el repositorio y ejecuta el lanzador correspondiente. El lanzador detecta Python, crea un entorno virtual, instala las dependencias y arranca la aplicación automáticamente.

### Linux

```bash
git clone <repositorio>
cd pyIssuesTracker
chmod +x launcher.sh
./launcher.sh
```

### Windows

Doble clic en `launcher.bat`.

La primera ejecución tarda un poco más porque instala las dependencias. Las siguientes van directas.

Para integrar la aplicación en el menú del sistema en Linux:

```bash
cp pyissuestracker.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

## Configuración

Para usar la aplicación necesitas una **API key de Redmine**. Se obtiene en tu perfil de Redmine: _Mi cuenta → Mostrar API key_.

Abre la configuración desde el menú **Archivo → Configuración** (o botón **Config** en la barra de herramientas) y completa los siguientes campos:

### Pestaña Redmine

| Campo | Descripción |
|---|---|
| URL del servidor | Dirección completa de tu instancia Redmine |
| API Key | Tu clave de acceso a la API REST de Redmine |
| Cookie | Header de cookies del navegador (necesario si Redmine está tras un SSO) |
| Headers extra | Cabeceras HTTP adicionales que necesite el proxy SSO |

### Pestaña Proxy

Si tu equipo sale a Internet a través de un proxy corporativo, actívalo aquí. Soporta HTTP, HTTPS y SOCKS5 con autenticación opcional. Cuando el proxy está activo, aparece el indicador **PROXY** en la barra de estado.

### Pestaña Apariencia

Elige entre los temas disponibles: claro, oscuro, y variantes Fusion. El cambio se aplica al reiniciar.

## Redmine detrás de un portal SSO

Si tu instancia de Redmine está protegida por un portal de autenticación corporativo (SSO), la API key por sí sola no será suficiente. La aplicación mostrará un mensaje indicando que se detectó el SSO y necesitas proporcionar credenciales de sesión adicionales.

### Cómo obtener las cookies del navegador

1. Abre Redmine en tu navegador e inicia sesión normalmente a través del portal SSO
2. Abre las herramientas de desarrollo: pulsa **F12**
3. Ve a la pestaña **Network** (Red)
4. Recarga la página con **F5**
5. Busca en la lista cualquier petición dirigida al servidor Redmine y haz clic en ella
6. En el panel de detalle, ve a la sección **Request Headers** (Cabeceras de la petición)
7. Busca la línea **Cookie:** y copia **todo su valor** — es una línea larga que contiene todas las cookies de sesión necesarias, por ejemplo:

   ```
   JSESSIONID=abc123; _redmine_session=xyz789; SSO_TOKEN=qwerty
   ```

8. Pega ese valor completo en el campo **Cookie** de la configuración de la aplicación

### Headers extra

En la misma sección **Request Headers** de las DevTools puedes encontrar otras cabeceras que el SSO requiera, como tokens de autorización o cabeceras personalizadas. Si ves algo como:

```
Authorization: Bearer abcdef123456
X-Custom-Auth: valor
```

Cópialas en el campo **Headers extra** respetando el formato `Clave: Valor` (una por línea).

### Verificar que funciona

Tras configurar las cookies y headers, ve a **Archivo → Conectar** (o pulsa `Ctrl+R`). El indicador LED en la barra inferior se pondrá verde si la conexión es correcta.

## Funcionalidades

### Barra de herramientas

| Botón | Acción |
|---|---|
| **Nuevo** | Crear una nueva tarea en el proyecto seleccionado |
| **Editar** | Modificar la tarea seleccionada (también con doble clic) |
| **Asignar** | Asignar la tarea a ti mismo (por defecto) o a otro miembro del proyecto |
| **Completada** | Marcar como completada: 100% de progreso, estado resuelta y fecha de fin a hoy |
| **Rechazar** | Rechazar la tarea cambiando su estado y añadiendo un comentario con el motivo |
| **Refrescar** | Recargar la lista de tareas desde Redmine |
| **Config** | Abrir la ventana de configuración |

### Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl + ,` | Abrir configuración |
| `Ctrl + R` | Reconectar a Redmine |
| `Ctrl + Q` | Salir de la aplicación |

### Filtros

- **Proyecto**: despliega todos los proyectos visibles. Escribe para buscar por nombre y pulsa Enter para seleccionar
- **Fijar filtro**: al marcar esta casilla, el proyecto seleccionado se mantiene al reiniciar la aplicación
- **Estado**: filtra por tareas abiertas (por defecto), cerradas o todas

### Tabla de tareas

| Columna | Descripción |
|---|---|
| ID | Identificador de la tarea |
| Título | Al pasar el cursor se muestra la descripción completa, tracker, autor y asignado |
| Fecha inicio | Fecha de comienzo de la tarea |
| Estado | Estado actual |
| Progreso % | Porcentaje completado (verde si es 100%, amarillo si está en progreso) |
| 🔗 | Botón para abrir la tarea directamente en el navegador |

### Bandeja del sistema

La aplicación se minimiza a la bandeja del sistema. Haz clic derecho para:

- **Mostrar ventana**: restaurar la aplicación
- **Reconectar**: reintentar la conexión a Redmine
- **Salir**: cerrar la aplicación completamente

Las notificaciones emergentes informan de eventos como conexión exitosa, tareas completadas o rechazadas.

### Indicador de estado

El LED en la barra inferior muestra el estado de la conexión:

- **Verde**: conectado a Redmine
- **Rojo**: sin conexión o error
- **Naranja parpadeante**: intentando conectar
- **PROXY** (azul): usando proxy para las conexiones salientes

## Temas

La aplicación incluye cuatro temas:

- **Predeterminado**: tema nativo del sistema
- **Oscuro**: paleta oscura personalizada
- **Fusion Claro**: tema Fusion de Qt con colores claros
- **Fusion Oscuro**: tema Fusion con paleta oscura

Se cambian desde **Configuración → Apariencia**.

## Auto-actualización

La aplicación puede verificar si hay nuevas versiones disponibles en GitHub. El gestor de actualizaciones compara la versión local con la última release publicada y permite descargar e instalar la nueva versión.

## Desarrollo

### Dependencias

```
PyQt6 >= 6.4
httpx >= 0.24
packaging >= 21.0
```

### Estructura del proyecto

```
pyIssuesTracker/
├── main.py                    # Punto de entrada, temas
├── launcher.sh / launcher.bat # Lanzadores auto-instalables
├── app/
│   ├── main_window.py         # Ventana principal
│   ├── tray_icon.py           # Icono de bandeja y notificaciones
│   ├── widgets/               # Componentes de interfaz
│   │   ├── status_indicator.py  # LED de estado
│   │   ├── toolbar.py           # Barra de herramientas
│   │   ├── filter_bar.py        # Filtros de proyecto y estado
│   │   └── task_table.py        # Tabla de tareas
│   ├── dialogs/               # Ventanas de diálogo
│   │   ├── settings_dialog.py   # Configuración (3 pestañas)
│   │   ├── task_dialog.py       # Crear/editar tarea
│   │   ├── assign_dialog.py     # Asignar tarea
│   │   └── reject_dialog.py     # Rechazar tarea
│   ├── services/              # Lógica de negocio
│   │   ├── settings_manager.py  # Persistencia con QSettings
│   │   ├── redmine_client.py    # Cliente de la API de Redmine
│   │   └── update_manager.py    # Verificación de versiones en GitHub
│   └── utils/
│       └── constants.py         # Claves de configuración y valores por defecto
└── pyproject.toml             # Configuración del paquete Python
```
