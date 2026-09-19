from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from PyQt6.QtCore import QSettings

from app.services.settings_manager import SettingsManager


@pytest.fixture
def settings():
    """Fixture que crea un SettingsManager con organización única para tests."""
    return SettingsManager()


class TestNotificationsProperties:
    """Tests para las propiedades de notificaciones en SettingsManager."""

    @pytest.fixture(autouse=True)
    def _cleanup(self):
        """Resetea las claves de notificaciones antes y despues de cada test."""
        s = SettingsManager()
        s.notifications_enabled = True
        s.notifications_projects = []
        s.notifications_assigned_only = False
        s.poll_interval_minutes = 5
        yield
        # Dejar tambien limpio para futuras sesiones
        s2 = SettingsManager()
        s2.notifications_enabled = True
        s2.notifications_projects = []
        s2.notifications_assigned_only = False
        s2.poll_interval_minutes = 5

    def test_defaults(self, settings):
        """Los valores por defecto deben ser los esperados."""
        assert settings.notifications_enabled is True
        assert settings.notifications_projects == []
        assert settings.notifications_assigned_only is False
        assert settings.poll_interval_minutes == 5

    def test_enabled_persists(self, settings):
        """notifications_enabled debe persistir correctamente."""
        settings.notifications_enabled = False
        # Nueva instancia (misma org/app) debe leer el valor persistido
        s2 = SettingsManager()
        assert s2.notifications_enabled is False

    def test_projects_list_roundtrip(self, settings):
        """notifications_projects debe persistir lista de IDs."""
        settings.notifications_projects = [1, 2, 3]
        s2 = SettingsManager()
        assert s2.notifications_projects == [1, 2, 3]

    def test_projects_empty_list_roundtrip(self, settings):
        """Lista vacía debe persistir correctamente (sin IDs basura)."""
        settings.notifications_projects = [1, 2]
        settings.notifications_projects = []
        s2 = SettingsManager()
        assert s2.notifications_projects == []

    def test_assigned_only_persists(self, settings):
        """notifications_assigned_only debe persistir."""
        settings.notifications_assigned_only = True
        s2 = SettingsManager()
        assert s2.notifications_assigned_only is True

    def test_poll_interval_persists(self, settings):
        """poll_interval_minutes debe persistir."""
        settings.poll_interval_minutes = 10
        s2 = SettingsManager()
        assert s2.poll_interval_minutes == 10

    def test_poll_interval_clamped_low(self, settings):
        """Valores por debajo de 1 deben ser clampados a 1."""
        settings.poll_interval_minutes = 0
        s2 = SettingsManager()
        assert s2.poll_interval_minutes == 1

    def test_poll_interval_clamped_high(self, settings):
        """Valores por encima de 60 deben ser clampados a 60."""
        settings.poll_interval_minutes = 120
        s2 = SettingsManager()
        assert s2.poll_interval_minutes == 60

    def test_poll_interval_invalid_defaults_to_5(self, settings):
        """Valor no numérico en QSettings debe devolver default 5."""
        settings._settings.setValue("notifications/poll_interval", "abc")
        s2 = SettingsManager()
        assert s2.poll_interval_minutes == 5


class TestFilterProjects:
    """Tests para la lista de proyectos filtrados y su migración legacy."""

    @pytest.fixture(autouse=True)
    def _cleanup(self):
        """Limpia las claves de filtro de proyecto antes y despues de cada test."""
        s = SettingsManager()
        s._settings.remove("filter/projects")
        s._settings.remove("filter/project_id")
        s._settings.remove("filter/project_name")
        yield
        s2 = SettingsManager()
        s2._settings.remove("filter/projects")
        s2._settings.remove("filter/project_id")
        s2._settings.remove("filter/project_name")

    def test_default_empty(self, settings):
        assert settings.filter_projects == []

    def test_roundtrip(self, settings):
        settings.filter_projects = [1, 2, 3]
        s2 = SettingsManager()
        assert s2.filter_projects == [1, 2, 3]

    def test_empty_list_roundtrip(self, settings):
        settings.filter_projects = [1, 2]
        settings.filter_projects = []
        s2 = SettingsManager()
        assert s2.filter_projects == []

    def test_migration_from_legacy(self, settings):
        """Sin clave lista, debe migrar desde filter/project_id."""
        settings.filter_project_id = 5
        s2 = SettingsManager()
        assert s2.filter_projects == [5]

    def test_legacy_zero_means_empty(self, settings):
        settings.filter_project_id = 0
        s2 = SettingsManager()
        assert s2.filter_projects == []


class TestVisibleColumns:
    """Tests para la persistencia de la visibilidad de columnas."""

    @pytest.fixture(autouse=True)
    def _cleanup(self):
        s = SettingsManager()
        s._settings.remove("table/columns_visible")
        yield
        s2 = SettingsManager()
        s2._settings.remove("table/columns_visible")

    def test_unset_returns_none(self, settings):
        assert settings.visible_columns is None

    def test_roundtrip(self, settings):
        settings.visible_columns = ["id", "title", "project"]
        s2 = SettingsManager()
        assert s2.visible_columns == ["id", "title", "project"]

    def test_empty_list_roundtrip(self, settings):
        settings.visible_columns = ["id"]
        settings.visible_columns = []
        s2 = SettingsManager()
        assert s2.visible_columns == []
