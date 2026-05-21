from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QStyle


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
            QStyle.StandardPixmap.SP_ComputerIcon
        )
        self._tray.setIcon(icon)

    def _setup_menu(self):
        menu = QMenu()
        style = QApplication.style()

        action_show = QAction(style.standardIcon(QStyle.StandardPixmap.SP_TitleBarNormalButton),
                             "Mostrar ventana", menu)
        action_show.triggered.connect(self.mostrar_ventana.emit)
        menu.addAction(action_show)

        action_connect = QAction(style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload),
                                "Reconectar", menu)
        action_connect.triggered.connect(self.conectar.emit)
        menu.addAction(action_connect)

        menu.addSeparator()

        action_exit = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton),
                             "Salir", menu)
        action_exit.triggered.connect(self.salir.emit)
        menu.addAction(action_exit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.mostrar_ventana.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.mostrar_ventana.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            pass

    def notify(self, title: str, message: str, duration_ms: int = 5000):
        if self._tray.supportsMessages():
            self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, duration_ms)

    def set_icon_connected(self, connected: bool):
        style = QApplication.style()
        if connected:
            icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        else:
            icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton)
        self._tray.setIcon(icon)

    def hide(self):
        self._tray.hide()
