"""Ventana de depuración: muestra los mensajes de log en vivo.

Accesible desde `Ver > Registro de diagnóstico`. Es un QDialog NO modal que
consume la señal `mensaje_emitido` del `QtLogHandler` configurado por
`setup_logging()`, permite filtrar por nivel mínimo, limpiar, copiar y abrir
la carpeta del fichero de log. No bloquea el hilo de UI.
"""

import logging
import os
import re
import subprocess
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QComboBox,
    QLabel, QPushButton, QApplication,
)

from app.services.logging_config import get_log_path, get_qt_handler

_MAX_LINEAS = 5000


class DebugLogDialog(QDialog):
    """Diálogo no modal de registro de diagnóstico."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registro de diagnóstico")
        self.setMinimumSize(680, 440)
        self._level_filter: int = logging.INFO

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # --- Fila superior: selector de nivel mínimo ---
        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(QLabel("Nivel mínimo:"))
        self._level_combo = QComboBox()
        for nivel in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR):
            self._level_combo.addItem(logging.getLevelName(nivel), nivel)
        self._level_combo.setCurrentIndex(1)  # INFO por defecto
        self._level_combo.currentIndexChanged.connect(self._on_level_changed)
        top.addWidget(self._level_combo)
        top.addStretch()
        layout.addLayout(top)

        # --- Área de texto de solo lectura con límite de líneas ---
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setMaximumBlockCount(_MAX_LINEAS)
        layout.addWidget(self._text)

        # --- Botones ---
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        limpiar_btn = QPushButton("Limpiar")
        limpiar_btn.clicked.connect(self._limpiar)
        copiar_btn = QPushButton("Copiar")
        copiar_btn.clicked.connect(self._copiar)
        abrir_btn = QPushButton("Abrir carpeta del log")
        abrir_btn.clicked.connect(self._abrir_carpeta_log)
        buttons.addWidget(limpiar_btn)
        buttons.addWidget(copiar_btn)
        buttons.addWidget(abrir_btn)
        buttons.addStretch()
        layout.addLayout(buttons)

        # --- Conexión al QtLogHandler (mensajes en vivo) ---
        handler = get_qt_handler()
        if handler is not None:
            handler.mensaje_emitido.connect(self._append_message)

    # ================================================================
    # Mensajes en vivo
    # ================================================================

    def _append_message(self, mensaje: str):
        """Añade un mensaje formateado si su nivel supera el filtro vigente."""
        if self._nivel_de_mensaje(mensaje) >= self._level_filter:
            self._text.appendPlainText(mensaje)

    @staticmethod
    def _nivel_de_mensaje(mensaje: str) -> int:
        """Extrae el nivel del mensaje formateado '%(asctime)s %(levelname)s ...'."""
        m = re.match(r"^\S+ \S+ (\w+)", mensaje)
        if m:
            nivel = logging.getLevelName(m.group(1))
            if isinstance(nivel, int):
                return nivel
        return logging.INFO

    def _on_level_changed(self):
        self._level_filter = self._level_combo.currentData() or logging.DEBUG

    # ================================================================
    # Acciones
    # ================================================================

    def _limpiar(self):
        self._text.clear()

    def _copiar(self):
        QApplication.clipboard().setText(self._text.toPlainText())

    def _abrir_carpeta_log(self):
        """Abre la carpeta del fichero de log con el gestor de archivos del SO."""
        carpeta = str(get_log_path().parent)
        try:
            if sys.platform == "win32":
                os.startfile(carpeta)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", carpeta])
            else:
                subprocess.Popen(["xdg-open", carpeta])
        except Exception as e:
            logging.getLogger(__name__).warning(
                "No se pudo abrir la carpeta del log (%s): %s", carpeta, e
            )