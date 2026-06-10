"""Diálogo de actualización: muestra nueva versión, notas y progreso de descarga."""

import os
import tempfile
from urllib.parse import unquote, urlparse

from PyQt6.QtCore import QThread, Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit,
    QDialogButtonBox, QProgressBar, QPushButton,
)

from app import __version__
from app.services.download_worker import DownloadWorker


class _ButtonBox(QDialogButtonBox):
    """QDialogButtonBox con botones Descargar, Cancelar/Cerrar."""
    def __init__(self, has_update: bool, parent=None):
        super().__init__(parent)
        self._download_btn: QPushButton | None = None
        self._close_btn: QPushButton | None = None

        if has_update:
            self._download_btn = self.addButton(
                "&Descargar", QDialogButtonBox.ButtonRole.ActionRole
            )
            self._close_btn = self.addButton(
                "&Cancelar", QDialogButtonBox.ButtonRole.RejectRole
            )
        else:
            self._close_btn = self.addButton(
                "&Aceptar", QDialogButtonBox.ButtonRole.AcceptRole
            )

    @property
    def download_button(self) -> QPushButton | None:
        return self._download_btn

    @property
    def close_button(self) -> QPushButton | None:
        return self._close_btn


class UpdateDialog(QDialog):
    """Diálogo modal que muestra información de una actualización y permite descargarla.

    Args:
        update_info: UpdateInfo con datos de la nueva versión (o available=False).
        update_manager: UpdateManager para ejecutar la descarga.
        parent: Widget padre (opcional).
    """

    def __init__(self, update_info, update_manager, parent=None):
        super().__init__(parent)
        self._info = update_info
        self._update_manager = update_manager
        self._worker: DownloadWorker | None = None
        self._thread: QThread | None = None
        self._downloading = False

        self.setMinimumWidth(480)
        self.setMinimumHeight(350)

        if self._info.available:
            self.setWindowTitle("Actualización disponible")
        else:
            self.setWindowTitle("Sin actualizaciones")

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Versión actual
        layout.addWidget(QLabel(f"Versión actual: <b>{__version__}</b>"))

        # Nueva versión (solo si hay update)
        if self._info.available:
            layout.addWidget(QLabel(
                f"Nueva versión: <b>{self._info.version}</b>"
            ))

            # Notas del release
            notes_label = QLabel("Notas de la versión:")
            layout.addWidget(notes_label)

            self._notes_edit = QTextEdit()
            self._notes_edit.setReadOnly(True)
            self._notes_edit.setPlainText(self._info.notes)
            self._notes_edit.setMaximumHeight(200)
            layout.addWidget(self._notes_edit)
        else:
            # Sin actualización disponible
            layout.addWidget(QLabel(
                "No hay actualizaciones disponibles.\n"
                "Ya tienes la versión más reciente."
            ))

        # Barra de progreso
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setVisible(False)
        self._progress_bar.setTextVisible(True)
        layout.addWidget(self._progress_bar)

        # Label de estado (ruta del archivo o error)
        self._status_label = QLabel()
        self._status_label.setVisible(False)
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        # Botones
        self._buttons = _ButtonBox(self._info.available, self)
        if self._buttons.download_button:
            self._buttons.download_button.clicked.connect(self._on_descargar)
        self._buttons.rejected.connect(self._on_cancelar)
        if self._buttons.close_button:
            self._buttons.close_button.clicked.connect(self._on_cancelar)
        layout.addWidget(self._buttons)

    def _asset_name_from_url(self, url: str) -> str:
        """Extrae el nombre del archivo desde la URL de descarga."""
        path = urlparse(url).path
        name = os.path.basename(unquote(path))
        return name or "actualizacion"

    def _on_descargar(self):
        """Inicia la descarga en un QThread."""
        if self._downloading or not self._info.available:
            return

        asset_name = self._asset_name_from_url(self._info.url)
        dest_path = os.path.join(tempfile.gettempdir(), asset_name)

        # Deshabilitar botón de descarga
        if self._buttons.download_button:
            self._buttons.download_button.setEnabled(False)
        self._downloading = True
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._status_label.setVisible(False)

        # Crear worker y thread
        self._worker = DownloadWorker(
            self._update_manager, self._info.url, dest_path
        )
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)

        # Conectar señales
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_worker_error)
        self._thread.started.connect(self._worker.run)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _on_progress(self, percent: int):
        """Actualiza la barra de progreso."""
        if percent == -1:
            self._progress_bar.setRange(0, 0)  # Modo indeterminado
        else:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(percent)

    def _on_finished(self, success: bool, filepath: str):
        """Maneja la finalización de la descarga."""
        self._downloading = False
        self._progress_bar.setVisible(False)

        if success:
            self._status_label.setText(
                f"Archivo guardado en:\n{filepath}"
            )
            self._status_label.setVisible(True)
            # Cambiar botón Descargar por Cerrar
            if self._buttons.download_button:
                self._buttons.download_button.setVisible(False)
            if self._buttons.close_button:
                self._buttons.close_button.setText("&Cerrar")
        else:
            # Cancelado o fallido (la señal finished con False ya se emitió)
            self._status_label.setText("Descarga cancelada.")
            self._status_label.setVisible(True)
            if self._buttons.download_button:
                self._buttons.download_button.setEnabled(True)

        # Limpiar thread
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None

    def _on_worker_error(self, message: str):
        """Maneja errores del worker."""
        self._downloading = False
        self._progress_bar.setVisible(False)
        self._status_label.setText(f"Error: {message}")
        self._status_label.setVisible(True)
        if self._buttons.download_button:
            self._buttons.download_button.setEnabled(True)

        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None

    def _on_cancelar(self):
        """Cancela la descarga o cierra el diálogo."""
        if self._downloading and self._worker:
            self._worker.cancel()
            # El worker se encargará de limpiar y emitir finished
        else:
            self.reject()

    def closeEvent(self, event):
        """Asegura limpieza al cerrar el diálogo."""
        if self._downloading and self._worker:
            self._worker.cancel()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(1000)
        super().closeEvent(event)
