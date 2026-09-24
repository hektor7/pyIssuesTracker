"""Tests del ReportDialog (tarea 4.1 del cambio add-ods-report-export).

Cubre: construcción del diálogo, precarga de proyectos preseleccionados,
lectura de las propiedades de filtros, roles por defecto y validación
del rango de fechas de creación.
"""
from unittest.mock import patch

import pytest
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QDialog

from app.dialogs.report_dialog import ReportDialog


PROJECTS = [(1, "Proyecto A"), (2, "Proyecto B"), (3, "Proyecto C")]
USERS = [(10, "Ana"), (11, "Luis"), (12, "Marta")]


@pytest.fixture
def dialog(qapp):
    """Crea un ReportDialog con proyectos y usuarios de ejemplo."""
    return ReportDialog(PROJECTS, USERS, parent=None)


class TestConstruccion:
    """(a) Construcción del diálogo con proyectos y usuarios."""

    def test_se_crea_con_proyectos_y_usuarios(self, dialog):
        """El diálogo se construye sin errores y expone las propiedades."""
        assert dialog.windowTitle() == "Generar informe"
        assert dialog.selected_project_ids == []
        assert dialog.selected_user_ids == []
        assert dialog.selected_roles == ["creador", "actualizador", "participante"]

    def test_usuarios_cargados_en_el_combo(self, dialog):
        """El MultiSelectCombo de usuarios contiene los usuarios pasados."""
        items = dialog._users_combo._items
        assert items == USERS

    def test_proyectos_cargados_en_el_combo(self, dialog):
        """El MultiSelectCombo de proyectos contiene los proyectos pasados."""
        items = dialog._projects_combo._items
        assert items == PROJECTS

    def test_roles_marcados_por_defecto(self, dialog):
        """Los tres checkboxes de rol están marcados por defecto."""
        for cb in dialog._roles_checkboxes.values():
            assert cb.isChecked()


class TestPrecargaProyectos:
    """(b) Precarga de proyectos preseleccionados."""

    def test_preselecciona_proyectos(self, qapp):
        """Si se pasan preselected_project_ids, quedan seleccionados."""
        dlg = ReportDialog(PROJECTS, USERS, preselected_project_ids=[1, 3], parent=None)
        assert dlg.selected_project_ids == [1, 3]

    def test_sin_preseleccion_todos(self, dialog):
        """Sin preselección, la selección de proyectos es 'Todos' ([])."""
        assert dialog.selected_project_ids == []


class TestFechasCreacion:
    """(c) created_from/created_to: None por defecto e ISO al activar."""

    def test_none_por_defecto(self, dialog):
        """Con los checkboxes desactivados, las fechas son None."""
        assert dialog.created_from is None
        assert dialog.created_to is None

    def test_iso_al_activar_desde(self, dialog):
        """Al activar el checkbox 'desde' se devuelve la fecha en ISO."""
        dialog._from_check.setChecked(True)
        dialog._from_date.setDate(QDate(2026, 1, 1))
        assert dialog.created_from == "2026-01-01"

    def test_iso_al_activar_hasta(self, dialog):
        """Al activar el checkbox 'hasta' se devuelve la fecha en ISO."""
        dialog._to_check.setChecked(True)
        dialog._to_date.setDate(QDate(2026, 3, 31))
        assert dialog.created_to == "2026-03-31"

    def test_desactivar_checkbox_vuelve_a_none(self, dialog):
        """Al desactivar el checkbox, la fecha vuelve a None."""
        dialog._from_check.setChecked(True)
        dialog._from_date.setDate(QDate(2026, 1, 1))
        dialog._from_check.setChecked(False)
        assert dialog.created_from is None


class TestRoles:
    """(d) selected_roles por defecto contiene los tres roles."""

    def test_roles_por_defecto(self, dialog):
        assert set(dialog.selected_roles) == {"creador", "actualizador", "participante"}

    def test_roles_filtrados_al_desmarcar(self, dialog):
        """Al desmarcar un rol, deja de aparecer en selected_roles."""
        dialog._roles_checkboxes["creador"].setChecked(False)
        assert "creador" not in dialog.selected_roles
        assert set(dialog.selected_roles) == {"actualizador", "participante"}


class TestValidacionRoles:
    """(e2) Sin roles marcados, accept() avisa y no acepta el diálogo."""

    def test_sin_roles_no_acepta(self, dialog):
        """Si se desmarcan los tres roles, accept() muestra warning y no acepta."""
        for cb in dialog._roles_checkboxes.values():
            cb.setChecked(False)

        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()

        mock_warning.assert_called_once()
        assert dialog.result() != QDialog.DialogCode.Accepted

    def test_con_al_menos_un_rol_acepta(self, dialog):
        """Con al menos un rol marcado, accept() acepta sin warning."""
        dialog._roles_checkboxes["creador"].setChecked(False)
        dialog._roles_checkboxes["actualizador"].setChecked(False)

        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()

        mock_warning.assert_not_called()
        assert dialog.result() == QDialog.DialogCode.Accepted


class TestValidacionRango:
    """(e) Un rango inválido impide aceptar el diálogo."""

    def test_rango_invalido_no_acepta(self, dialog):
        """Si desde > hasta, accept() muestra warning y no acepta."""
        dialog._from_check.setChecked(True)
        dialog._to_check.setChecked(True)
        dialog._from_date.setDate(QDate(2026, 5, 1))
        dialog._to_date.setDate(QDate(2026, 1, 1))

        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()

        mock_warning.assert_called_once()
        assert dialog.result() != QDialog.DialogCode.Accepted

    def test_rango_valido_acepta(self, dialog):
        """Si desde <= hasta, accept() acepta sin warning."""
        dialog._from_check.setChecked(True)
        dialog._to_check.setChecked(True)
        dialog._from_date.setDate(QDate(2026, 1, 1))
        dialog._to_date.setDate(QDate(2026, 3, 31))

        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()

        mock_warning.assert_not_called()
        assert dialog.result() == QDialog.DialogCode.Accepted


class TestSeleccionTodos:
    """(f) selected_project_ids/selected_user_ids devuelven [] con 'Todos'."""

    def test_proyectos_todos_devuelve_vacio(self, dialog):
        assert dialog.selected_project_ids == []

    def test_usuarios_todos_devuelve_vacio(self, dialog):
        assert dialog.selected_user_ids == []

    def test_seleccionar_usuarios_devuelve_ids(self, dialog):
        """Al seleccionar usuarios concretos se devuelven sus IDs."""
        dialog._users_combo.set_selected_ids([10, 12])
        assert dialog.selected_user_ids == [10, 12]

    def test_seleccionar_proyectos_devuelve_ids(self, dialog):
        """Al seleccionar proyectos concretos se devuelven sus IDs."""
        dialog._projects_combo.set_selected_ids([2])
        assert dialog.selected_project_ids == [2]