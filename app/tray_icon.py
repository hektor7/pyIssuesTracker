from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


class TrayManager(QObject):
    mostrar_ventana = pyqtSignal()
    salir = pyqtSignal()
    conectar = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("PyIssuesTracker")
        self._setup_icon()
        self._setup_menu()
        self._tray.show()

    def _setup_icon(self):
        icon = QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_ComputerIcon
        )
        self._tray.setIcon(icon)

    def _setup_menu(self):
        menu = QMenu()

        action_show = QAction("Mostrar ventana")
        action_show.triggered.connect(self.mostrar_ventana.emit)
        menu.addAction(action_show)

        action_connect = QAction("Reconectar")
        action_connect.triggered.connect(self.conectar.emit)
        menu.addAction(action_connect)

        menu.addSeparator()

        action_exit = QAction("Salir")
        action_exit.triggered.connect(self.salir.emit)
        menu.addAction(action_exit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.mostrar_ventana.emit()

    def notify(self, title: str, message: str, duration_ms: int = 5000):
        if self._tray.supportsMessages():
            self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, duration_ms)

    def set_icon_connected(self, connected: bool):
        style = QApplication.style()
        if connected:
            icon = style.standardIcon(style.StandardPixmap.SP_DialogApplyButton)
        else:
            icon = style.standardIcon(style.StandardPixmap.SP_DialogCancelButton)
        self._tray.setIcon(icon)

    def hide(self):
        self._tray.hide()
