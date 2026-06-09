import sys
import os
import ctypes
import ctypes.util

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication

from app import __version__, __app_name__
from app.main_window import MainWindow
from app.services.settings_manager import SettingsManager


def _check_system_dependencies():
    """Verifica que las librerías de sistema necesarias estén instaladas (solo Linux)."""
    if sys.platform != "linux":
        return

    required_libs = {
        "libxcb-cursor.so.0": {
            "name": "libxcb-cursor0 / xcb-util-cursor",
            "purpose": "Qt6 la necesita para funcionar en Linux (plugin de plataforma xcb).",
            "packages": {
                "debian": "sudo apt-get install libxcb-cursor0",
                "arch": "sudo pacman -S xcb-util-cursor",
                "fedora": "sudo dnf install xcb-util-cursor",
            },
        },
    }

    missing = []
    for soname, info in required_libs.items():
        path = ctypes.util.find_library(soname.replace(".so.0", "").replace(".so", ""))
        if path is None:
            # fallback: intentar cargar directamente
            try:
                ctypes.CDLL(soname)
            except OSError:
                missing.append((soname, info))

    if missing:
        print("\n" + "=" * 62, file=sys.stderr)
        print(" ERROR: Faltan librerías del sistema necesarias para ejecutar la aplicación",
              file=sys.stderr)
        print("=" * 62, file=sys.stderr)
        for soname, info in missing:
            print(f"\n  Librería: {soname}", file=sys.stderr)
            print(f"  Paquete:  {info['name']}", file=sys.stderr)
            print(f"  Motivo:   {info['purpose']}", file=sys.stderr)
            print(f"\n  Instálala con uno de estos comandos según tu distribución:",
                  file=sys.stderr)
            for distro, cmd in info["packages"].items():
                print(f"    [{distro:7}]  {cmd}", file=sys.stderr)
        print("\n" + "=" * 62, file=sys.stderr)
        sys.exit(1)


def _apply_theme(app: QApplication, theme_key: str):
    if theme_key == "dark":
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        pal.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        pal.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        pal.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        pal.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        pal.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        pal.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        pal.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        pal.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        app.setPalette(pal)
        app.setStyleSheet(
            "QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }"
        )
    elif theme_key == "fusion_light":
        app.setStyle("Fusion")
        app.setPalette(app.style().standardPalette())
    elif theme_key == "fusion_dark":
        app.setStyle("Fusion")
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window, QColor(45, 45, 45))
        pal.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        pal.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
        pal.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        pal.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        pal.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        pal.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        pal.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        pal.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        pal.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        app.setPalette(pal)
        app.setStyleSheet(
            "QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }"
        )
    else:
        app.setStyle("Fusion" if theme_key.startswith("fusion") else app.style().objectName())


def main():
    _check_system_dependencies()
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("pyissuestracker")
    app.setQuitOnLastWindowClosed(False)

    settings = SettingsManager()
    _apply_theme(app, settings.theme)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
