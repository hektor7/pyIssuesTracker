"""Worker para descargar actualizaciones en un hilo separado (QThread)."""

import os

from PyQt6.QtCore import QObject, pyqtSignal


class _CancelException(Exception):
    """Excepción interna para detener la descarga cuando el usuario cancela."""
    pass


class DownloadWorker(QObject):
    """Worker que descarga un asset en un QThread sin bloquear la UI.

    Señales:
        progress(int): Porcentaje de descarga (0-100) o -1 si indeterminado.
        finished(bool, str): (success, filepath) al terminar la descarga.
        error(str): Mensaje de error si falla la descarga.
    """

    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    error = pyqtSignal(str)

    def __init__(self, update_manager, url: str, dest_path: str, parent=None):
        super().__init__(parent)
        self._update_manager = update_manager
        self._url = url
        self._dest_path = dest_path
        self._cancelled = False

    def cancel(self):
        """Solicita la cancelación de la descarga en curso."""
        self._cancelled = True

    def _progress_callback(self, percent: int):
        """Callback interno que emite la señal de progreso y verifica cancelación."""
        self.progress.emit(percent)
        if self._cancelled:
            raise _CancelException()

    def run(self):
        """Ejecuta la descarga. Conectar a QThread.started."""
        try:
            success = self._update_manager.download_release(
                self._url,
                self._dest_path,
                progress_callback=self._progress_callback,
            )
        except _CancelException:
            # La excepción fue atrapada por download_release, pero la
            # incluimos por si en el futuro cambia la implementación.
            self._cleanup()
            self.finished.emit(False, self._dest_path)
            return
        except Exception as e:
            self._cleanup()
            self.error.emit(str(e))
            return

        if self._cancelled:
            self._cleanup()
            self.finished.emit(False, self._dest_path)
        elif success:
            self.finished.emit(True, self._dest_path)
        else:
            self.error.emit("Error durante la descarga.")

    def _cleanup(self):
        """Elimina el archivo parcial si existe."""
        if os.path.exists(self._dest_path):
            try:
                os.remove(self._dest_path)
            except OSError:
                pass
