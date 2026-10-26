"""Tests del diálogo de Configuración."""

from app.dialogs.settings_dialog import SettingsDialog
from app.services.settings_manager import SettingsManager


class TestCookieHelp:
    """La Cookie de sesión debe explicar su papel en campos personalizados."""

    def test_ayuda_y_tooltip_de_cookie_mencionan_campos_personalizados(self, qapp):
        dlg = SettingsDialog(SettingsManager())

        tooltip = dlg._cookie_edit.toolTip().lower()
        assert "campos personalizados" in tooltip
        assert "api key" in tooltip
        assert "administrador" in tooltip

        ayuda = dlg._redmine_info_label.text().lower()
        assert "cookie" in ayuda
        assert "campos personalizados" in ayuda
