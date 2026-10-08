## Context

Actualmente el proyecto tiene un `UpdateManager` con dos métodos (`check_for_updates`, `download_release`) implementados pero desconectados de la UI. El CI/CD (`.github/workflows/release.yml`) genera binarios con PyInstaller para Windows (`.exe`) y Linux, y los publica como assets del release. El bug principal es que `check_for_updates()` devuelve `release["html_url"]` (página HTML del release) en lugar de `asset["browser_download_url"]` (URL directa del binario), por lo que la descarga nunca funcionaría aunque se conectara a la UI.

La app ya usa `httpx` para la API de Redmine y tiene soporte de proxy vía `SettingsManager`. La verificación de actualizaciones usará el mismo stack.

## Goals / Non-Goals

**Goals:**
- Corregir `UpdateManager` para que `check_for_updates()` devuelva la URL directa del asset binario correcto según plataforma (`.exe` en Windows, binario sin extensión en Linux).
- Conectar `UpdateManager` a la UI: ítem de menú "Buscar actualizaciones..." y verificación automática al iniciar con cooldown de 24h.
- Añadir diálogo de progreso de descarga con cancelación, mostrando notas de release.
- Soportar proxy corporativo (heredando la configuración existente de `SettingsManager`).

**Non-Goals:**
- No se implementa instalación automática (reemplazar el binario en ejecución requiere lógica adicional de reinicio que queda fuera de este cambio).
- No se modifica el CI/CD ni la generación de releases.
- No se añade soporte para macOS (el CI/CD actual solo builda Windows/Linux).

## Decisions

### 1. Detección de plataforma para filtrar assets

**Decisión**: Usar `sys.platform` (`"win32"` para Windows, `"linux"` para Linux) y filtrar assets del release por extensión: `.exe` para Windows, sin `.exe` para Linux.

**Alternativas consideradas**:
- `platform.system()`: más legible pero añade un import innecesario; `sys.platform` ya está disponible.
- Descargar siempre el `.exe`: incorrecto, los usuarios Linux necesitan el binario ELF.

### 2. Descarga asíncrona sin bloquear la UI

**Decisión**: Usar `QThread` con una clase `DownloadWorker` que emite señales `progress(int percent)`, `finished(bool success, str path)`, `error(str message)`. La descarga usa `httpx.Client.stream` con chunks de 64KB (más eficiente que los 8KB actuales para archivos grandes).

**Alternativas consideradas**:
- `asyncio` + `httpx.AsyncClient`: añade complejidad innecesaria; PyQt6 ya tiene su event loop y mezclar con asyncio requiere `qasync` como dependencia extra.
- `QNetworkAccessManager`: API de Qt para HTTP. Requiere reescribir todo el `UpdateManager` y no añade valor sobre `httpx` que ya funciona y está probado.

### 3. Diálogo de progreso

**Decisión**: Crear un `QDialog` simple (`UpdateDialog`) que muestra:
- Versión actual vs nueva versión.
- Notas del release (primeros 500 caracteres, scrollable).
- Barra de progreso con porcentaje.
- Botón "Cancelar" (deshabilita durante descarga, cierra si no hay descarga activa).
- Botón "Descargar" que inicia la descarga.

**Alternativas consideradas**:
- `QProgressDialog`: muy simple, no permite mostrar notas de release ni versión.
- `QMessageBox`: no soporta barra de progreso ni contenido enriquecido.

### 4. Auto-check al iniciar

**Decisión**: Verificar automáticamente al iniciar si han pasado más de 24h desde la última verificación (usando `KEY_LAST_UPDATE_CHECK` en QSettings). Si hay actualización, mostrar el `UpdateDialog`. Si no, no molestar al usuario.

**Alternativas consideradas**:
- Verificar siempre al iniciar: molesto si el usuario abre la app varias veces al día.
- No verificar automáticamente: el usuario podría no enterarse nunca de nuevas versiones.

### 5. Ubicación de descarga

**Decisión**: Descargar a un directorio temporal del sistema (`tempfile.gettempdir()`) con el nombre original del asset. Al finalizar, notificar al usuario la ruta donde se guardó.

**Alternativas consideradas**:
- Descargar al directorio de la app: requiere permisos de escritura que pueden no estar disponibles.
- Sobrescribir el binario en ejecución: no es posible en Windows (archivo bloqueado) ni fiable en Linux.

## Risks / Trade-offs

- **[Riesgo] Fallo de red / timeout durante la descarga**: La descarga de binarios PyInstaller (20-50MB) puede fallar en conexiones lentas. → Mitigación: timeout generoso (300s), reintento manual desde el diálogo, chunks de 64KB con progreso visible.
- **[Riesgo] El asset no existe para la plataforma actual**: Si el CI/CD falla para una plataforma, el asset no estará en el release. → Mitigación: `check_for_updates()` devuelve `available=False` si no encuentra asset para la plataforma; se muestra mensaje informativo.
- **[Riesgo] Falsos positivos en detección de plataforma**: Un usuario podría ejecutar la app con Wine en Linux y esperar el `.exe`. → Mitigación: fuera de scope; se detecta la plataforma real, no el emulador.
- **[Trade-off] Bloqueo de UI durante `check_for_updates()`**: La llamada a la API de GitHub es rápida (<1s típicamente) pero podría bloquear si hay problemas de red. → Mitigación: timeout de 15s (mismo que Redmine); si es necesario, migrar a QThread en iteración futura.

## Open Questions

- ¿Debería el diálogo ofrecer "Instalar y reiniciar" automáticamente? → No en esta iteración; se deja para un cambio futuro.
- ¿Debería permitirse configurar el canal (stable/prerelease)? → No en esta iteración; solo releases estables.
