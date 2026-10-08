## Why

El gestor de actualizaciones `UpdateManager` está implementado (verifica releases en GitHub, descarga binarios), pero nunca se conectó a la UI. Además, tiene un bug crítico: `check_for_updates()` devuelve la URL de la página HTML del release en lugar de la URL del asset binario, lo que hace que `download_release()` descargue HTML en vez del `.exe`. El CI/CD ya genera y publica los binarios (Windows `.exe` y Linux) en cada release, así que la infraestructura está lista; solo falta cablear y corregir el lado cliente.

## What Changes

- **Corregir** `UpdateManager.check_for_updates()` para que devuelva la URL del asset binario correcto según la plataforma (`.exe` en Windows, binario sin extensión en Linux).
- **Conectar** `UpdateManager` a la UI: añadir acción "Buscar actualizaciones..." en el menú Archivo y verificación automática al iniciar (con cooldown configurable).
- **Añadir** un diálogo de progreso de descarga con cancelación.
- **Notificar** al usuario cuando haya una nueva versión disponible, mostrando versión, notas de release, y opción de descargar.
- **Gestionar** correctamente el proxy corporativo (ya configurado en SettingsManager) durante la descarga.

## Capabilities

### New Capabilities

- `actualizacion-automatica`: Verificación de nuevas versiones desde GitHub Releases, descarga del binario correcto según plataforma (Windows `.exe` / Linux), con diálogo de progreso y notificación al usuario.

### Modified Capabilities

<!-- Ninguna spec existente modifica sus requisitos -->

## Impact

- **`app/services/update_manager.py`**: corregir `check_for_updates()` (devolver `browser_download_url` del asset, no `html_url` del release); filtrar assets por plataforma (`.exe` en Windows, binario Linux en Linux).
- **`app/main_window.py`**: instanciar `UpdateManager`, añadir item de menú "Buscar actualizaciones...", verificación automática al iniciar con cooldown.
- **Nuevo `app/dialogs/update_dialog.py`**: diálogo para mostrar progreso de descarga, notas de release, y confirmación de instalación.
- **`app/utils/constants.py`**: añadir constantes para cooldown de verificación y prefijos de assets por plataforma.
- **`app/services/settings_manager.py`**: posiblemente añadir getter para proxy URL.
