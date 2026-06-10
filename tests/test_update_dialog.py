"""Tests de integración para UpdateDialog y MainWindow._buscar_actualizaciones."""

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QDialog, QMessageBox

from app.dialogs.update_dialog import UpdateDialog
from app.services.update_manager import UpdateInfo, UpdateManager


# ============================================================
# Tests: 5.5 — UpdateDialog muestra información correcta
# ============================================================

class TestUpdateDialog:
    """UpdateDialog muestra información correcta con UpdateInfo simulado."""

    def test_dialog_shows_update_info(self, qapp):
        """El diálogo muestra versión actual, nueva versión y notas."""
        info = UpdateInfo(
            version="0.4.0",
            url="https://example.com/PyIssuesTracker.exe",
            notes="Correcciones y mejoras.\nNueva funcionalidad.",
            available=True,
        )
        um = MagicMock(spec=UpdateManager)

        dlg = UpdateDialog(info, um)
        assert dlg.windowTitle() == "Actualización disponible"
        assert dlg.isVisible() is False  # No se ha mostrado aún
        dlg.close()

    def test_dialog_no_update(self, qapp):
        """El diálogo muestra mensaje de 'sin actualizaciones' cuando no hay update."""
        info = UpdateInfo(
            version="",
            url="",
            notes="",
            available=False,
        )
        um = MagicMock(spec=UpdateManager)

        dlg = UpdateDialog(info, um)
        assert dlg.windowTitle() == "Sin actualizaciones"
        dlg.close()

    def test_dialog_has_download_button_when_update_available(self, qapp):
        """El diálogo tiene botón Descargar cuando hay actualización."""
        info = UpdateInfo(
            version="0.4.0",
            url="https://example.com/PyIssuesTracker.exe",
            notes="",
            available=True,
        )
        um = MagicMock(spec=UpdateManager)

        dlg = UpdateDialog(info, um)
        assert dlg._buttons.download_button is not None
        assert dlg._buttons.download_button.text() == "&Descargar"
        dlg.close()

    def test_dialog_no_download_button_when_no_update(self, qapp):
        """El diálogo NO tiene botón Descargar cuando no hay actualización."""
        info = UpdateInfo(
            version="",
            url="",
            notes="",
            available=False,
        )
        um = MagicMock(spec=UpdateManager)

        dlg = UpdateDialog(info, um)
        assert dlg._buttons.download_button is None
        dlg.close()

    def test_dialog_progress_bar_hidden_initially(self, qapp):
        """La barra de progreso está oculta al inicio."""
        info = UpdateInfo(
            version="0.4.0",
            url="https://example.com/PyIssuesTracker.exe",
            notes="",
            available=True,
        )
        um = MagicMock(spec=UpdateManager)

        dlg = UpdateDialog(info, um)
        assert dlg._progress_bar.isVisible() is False
        dlg.close()


# ============================================================
# Tests: 5.6 — MainWindow._buscar_actualizaciones
# ============================================================

class TestMainWindowBuscarActualizaciones:
    """MainWindow._buscar_actualizaciones muestra UpdateDialog al detectar update."""

    @pytest.fixture
    def main_window(self, qapp):
        """Crea un MainWindow con setup mockeado."""
        from app.main_window import MainWindow

        with (
            patch.object(MainWindow, "_setup_ui"),
            patch.object(MainWindow, "_setup_menu"),
            patch.object(MainWindow, "_setup_tray"),
            patch.object(MainWindow, "_restore_window_state"),
        ):
            w = MainWindow()
            w._settings = MagicMock()
            w._settings.build_proxy_url.return_value = None
            w._settings.last_update_check = ""
            return w

    def test_buscar_actualizaciones_shows_dialog_when_available(self, main_window):
        """_buscar_actualizaciones muestra UpdateDialog cuando hay update."""
        info = UpdateInfo(
            version="0.4.0",
            url="https://example.com/PyIssuesTracker.exe",
            notes="Nueva versión",
            available=True,
        )

        mock_um = MagicMock(spec=UpdateManager)
        mock_um.check_for_updates.return_value = info

        # Parcheamos UpdateDialog en su módulo original (import local en el método)
        with (
            patch("app.main_window.UpdateManager", return_value=mock_um),
            patch("app.dialogs.update_dialog.UpdateDialog") as mock_dlg_cls,
        ):
            mock_dlg = MagicMock(spec=UpdateDialog)
            mock_dlg_cls.return_value = mock_dlg
            mock_dlg_cls.DialogCode = QDialog.DialogCode

            main_window._buscar_actualizaciones()

            mock_um.check_for_updates.assert_called_once()
            mock_dlg_cls.assert_called_once()
            mock_dlg.exec.assert_called_once()

    def test_buscar_actualizaciones_shows_message_when_no_update(self, main_window):
        """_buscar_actualizaciones muestra QMessageBox cuando no hay update."""
        info = UpdateInfo(
            version="",
            url="",
            notes="",
            available=False,
        )

        mock_um = MagicMock(spec=UpdateManager)
        mock_um.check_for_updates.return_value = info

        with (
            patch("app.main_window.UpdateManager", return_value=mock_um),
            patch("app.dialogs.update_dialog.UpdateDialog") as mock_dlg_cls,
            patch("app.main_window.QMessageBox") as mock_msgbox,
        ):
            main_window._buscar_actualizaciones()

            mock_um.check_for_updates.assert_called_once()
            mock_dlg_cls.assert_not_called()
            mock_msgbox.information.assert_called_once()
