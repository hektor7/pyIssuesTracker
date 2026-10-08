## 1. Corregir UpdateManager

- [x] 1.1 Modificar `check_for_updates()` para devolver `browser_download_url` del asset en lugar de `html_url` del release
- [x] 1.2 Añadir deteccion de plataforma con `sys.platform` y filtrado de assets (`.exe` para Windows, sin `.exe` para Linux)
- [x] 1.3 Si no hay asset compatible con la plataforma, devolver `available=False`
- [x] 1.4 Aumentar chunk_size de `download_release()` de 8KB a 64KB para descargas mas eficientes
- [x] 1.5 Añadir soporte para callback de progreso en `download_release()` (parametro `progress_callback: Callable[[int], None] | None`)

## 2. Crear DownloadWorker (QThread)

- [x] 2.1 Crear `app/services/download_worker.py` con clase `DownloadWorker(QObject)` que use `QThread`
- [x] 2.2 Emitir senales: `progress(int percent)`, `finished(bool success, str path)`, `error(str message)`
- [x] 2.3 Implementar `run()` que invoque `UpdateManager.download_release()` con el callback de progreso
- [x] 2.4 Soportar cancelacion via flag `_cancelled` y eliminar archivo parcial al cancelar

## 3. Crear UpdateDialog

- [x] 3.1 Crear `app/dialogs/update_dialog.py` con clase `UpdateDialog(QDialog)`
- [x] 3.2 Mostrar: version actual, nueva version, notas del release (primeros 500 chars, QTextEdit read-only con scroll)
- [x] 3.3 Incluir `QProgressBar` (oculta inicialmente, visible durante descarga)
- [x] 3.4 Boton "Descargar" que inicia el `DownloadWorker`, deshabilita el boton durante descarga
- [x] 3.5 Boton "Cancelar" / "Cerrar": cancela descarga si esta activa, cierra el dialogo si no
- [x] 3.6 Al finalizar descarga: mostrar ruta del archivo guardado, cambiar boton a "Cerrar"
- [x] 3.7 En caso de error: mostrar mensaje, permitir reintentar (reactivar boton "Descargar")

## 4. Integrar en MainWindow

- [x] 4.1 Instanciar `UpdateManager` en `MainWindow.__init__` pasando proxy URL desde `SettingsManager`
- [x] 4.2 Anadir item de menu "Buscar actualizaciones..." en el menu Archivo (debajo de "Conectar", con separador)
- [x] 4.3 Implementar metodo `_buscar_actualizaciones()` que llame a `check_for_updates()` y muestre `UpdateDialog` o `QMessageBox`
- [x] 4.4 Implementar verificacion automatica al iniciar en `_auto_connect()` o metodo dedicado:
  - Leer `update/last_check` de QSettings
  - Si han pasado >24h, ejecutar `check_for_updates()` en segundo plano
  - Si hay actualizacion, mostrar `UpdateDialog`
  - Actualizar `update/last_check` con `datetime.now().isoformat()`
- [x] 4.5 Asegurar que la verificacion automatica no bloquea el arranque (usar `QTimer.singleShot` con delay suficiente)

## 5. Tests

- [x] 5.1 Test unitario: `check_for_updates()` devuelve asset correcto segun `sys.platform` (mock de `httpx`)
- [x] 5.2 Test unitario: `check_for_updates()` devuelve `available=False` si no hay asset compatible
- [x] 5.3 Test unitario: `check_for_updates()` ignora prereleases y drafts
- [x] 5.4 Test unitario: `download_release()` llama al progress_callback con porcentajes correctos
- [x] 5.5 Test de integracion: `UpdateDialog` muestra informacion correcta con `UpdateInfo` falso
- [x] 5.6 Test de integracion: `MainWindow` muestra `UpdateDialog` al detectar actualizacion

## 6. Verificacion manual

- [x] 6.1 Ejecutar la app y verificar que "Buscar actualizaciones..." aparece en el menu Archivo
- [x] 6.2 Verificar que el dialogo de actualizacion se muestra correctamente con datos de prueba
- [x] 6.3 Verificar que la verificacion automatica no se ejecuta si ya se comprobo en las ultimas 24h
- [x] 6.4 Verificar que el progreso de descarga se muestra correctamente (con un archivo de prueba)
