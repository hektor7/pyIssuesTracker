from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QMainWindow, QDialog, QMessageBox

from app.dialogs.assign_dialog import AssignDialog
from app.dialogs.complete_dialog import CompleteDialog
from app.main_window import MainWindow
from app.services.redmine_client import RedmineValidationError


@pytest.fixture
def main_window(qapp):
    """Crea un MainWindow con métodos de setup mockeados."""
    with (
        patch.object(MainWindow, "_setup_ui"),
        patch.object(MainWindow, "_setup_menu"),
        patch.object(MainWindow, "_setup_tray"),
        patch.object(MainWindow, "_restore_window_state"),
    ):
        w = MainWindow()
        w._redmine = MagicMock()
        w._task_table = MagicMock()
        w._tray = MagicMock()
        w._filter_bar = MagicMock()
        w._cargar_issues = MagicMock()
        w._statuses = [(1, "Nueva"), (2, "Resuelta")]
        w._current_user_id = 2
        return w


class TestAsignarTarea:
    def _make_mock_dialog(self, selected_user_id: int, notes: str):
        """Crea un MagicMock que simula AssignDialog."""
        dlg = MagicMock(spec=AssignDialog)
        dlg.selected_user_id = selected_user_id
        dlg.notes = notes
        dlg.exec.return_value = QDialog.DialogCode.Accepted
        return dlg

    def _patch_assign_dialog(self, dlg_mock):
        """Parchea AssignDialog preservando DialogCode para comparaciones."""
        mock_class = MagicMock(spec=AssignDialog)
        mock_class.DialogCode = QDialog.DialogCode
        mock_class.return_value = dlg_mock
        return patch("app.main_window.AssignDialog", mock_class)

    def test_asignar_tarea_passes_notes(self, main_window):
        """_asignar_tarea debe pasar notes al redmine.assign_issue."""
        main_window._task_table.get_selected_issue_id.return_value = 42
        main_window._task_table.get_selected_row_data.return_value = {}

        dlg = self._make_mock_dialog(selected_user_id=7, notes="asignado con comentario")

        with self._patch_assign_dialog(dlg):
            main_window._asignar_tarea()

        main_window._redmine.assign_issue.assert_called_once_with(
            42, 7, notes="asignado con comentario"
        )

    def test_asignar_tarea_passes_no_notes(self, main_window):
        """_asignar_tarea debe pasar notes vacío si no hay comentario."""
        main_window._task_table.get_selected_issue_id.return_value = 42
        main_window._task_table.get_selected_row_data.return_value = {}

        dlg = self._make_mock_dialog(selected_user_id=3, notes="")

        with self._patch_assign_dialog(dlg):
            main_window._asignar_tarea()

        main_window._redmine.assign_issue.assert_called_once_with(
            42, 3, notes=""
        )


class TestCompletarTarea:
    def _make_mock_dialog(self, notes: str):
        """Crea un MagicMock que simula CompleteDialog."""
        dlg = MagicMock(spec=CompleteDialog)
        dlg.notes = notes
        dlg.exec.return_value = QDialog.DialogCode.Accepted
        return dlg

    def _patch_complete_dialog(self, dlg_mock):
        """Parchea CompleteDialog preservando DialogCode para comparaciones."""
        mock_class = MagicMock(spec=CompleteDialog)
        mock_class.DialogCode = QDialog.DialogCode
        mock_class.return_value = dlg_mock
        return patch("app.main_window.CompleteDialog", mock_class)

    def test_completar_tarea_passes_notes(self, main_window):
        """_completar_tarea debe pasar notes al redmine.complete_issue."""
        from datetime import date
        main_window._task_table.get_selected_issue_id.return_value = 42

        dlg = self._make_mock_dialog(notes="tarea completada")

        with self._patch_complete_dialog(dlg):
            main_window._completar_tarea()

        main_window._redmine.complete_issue.assert_called_once_with(
            42, done_ratio=100, status_id=2, notes="tarea completada",
            due_date=date.today().isoformat(),
        )

    def test_completar_tarea_passes_no_notes(self, main_window):
        """_completar_tarea debe pasar notes vacío si no hay comentario."""
        from datetime import date
        main_window._task_table.get_selected_issue_id.return_value = 42

        dlg = self._make_mock_dialog(notes="")

        with self._patch_complete_dialog(dlg):
            main_window._completar_tarea()

        main_window._redmine.complete_issue.assert_called_once_with(
            42, done_ratio=100, status_id=2, notes="",
            due_date=date.today().isoformat(),
        )


class TestCompletarTareaDueDate:
    """_completar_tarea debe pasar due_date con la fecha de hoy."""

    def test_completar_tarea_passes_today_as_due_date(self, main_window):
        """_completar_tarea debe pasar la fecha de hoy como due_date."""
        from datetime import date
        main_window._task_table.get_selected_issue_id.return_value = 42

        dlg = MagicMock(spec=CompleteDialog)
        dlg.notes = "tarea completada"
        dlg.exec.return_value = QDialog.DialogCode.Accepted

        mock_class = MagicMock(spec=CompleteDialog)
        mock_class.DialogCode = QDialog.DialogCode
        mock_class.return_value = dlg

        with patch("app.main_window.CompleteDialog", mock_class):
            main_window._completar_tarea()

        main_window._redmine.complete_issue.assert_called_once()
        call_kwargs = main_window._redmine.complete_issue.call_args.kwargs
        assert call_kwargs["due_date"] == date.today().isoformat()


class TestCompletarTareaSinDueDate:
    """_completar_tarea debe omitir due_date si el issue no tiene due_date."""

    def test_completar_tarea_sin_due_date_no_incluye_due_date(self, main_window):
        """_completar_tarea debe pasar due_date='' si el issue no tiene due_date."""
        main_window._task_table.get_selected_issue_id.return_value = 42
        main_window._task_table.get_selected_row_data.return_value = {}  # Sin due_date

        dlg = MagicMock(spec=CompleteDialog)
        dlg.notes = ""
        dlg.exec.return_value = QDialog.DialogCode.Accepted

        mock_class = MagicMock(spec=CompleteDialog)
        mock_class.DialogCode = QDialog.DialogCode
        mock_class.return_value = dlg

        with patch("app.main_window.CompleteDialog", mock_class):
            main_window._completar_tarea()

        main_window._redmine.complete_issue.assert_called_once()
        call_kwargs = main_window._redmine.complete_issue.call_args.kwargs
        assert call_kwargs["due_date"] == ""


class TestCompletarTareaResolvedStatus:
    """_completar_tarea debe manejar cuando resolved_status es None."""

    def test_completar_tarea_resolved_status_none_muestra_advertencia(self, main_window):
        """_completar_tarea debe mostrar advertencia si resolved_status es None."""
        # Sobrescribir _statuses para que NO incluya "Resuelta"/"Resolved"
        main_window._statuses = [(1, "Nueva"), (3, "En progreso")]
        main_window._task_table.get_selected_issue_id.return_value = 42

        dlg = MagicMock(spec=CompleteDialog)
        dlg.notes = ""
        dlg.exec.return_value = QDialog.DialogCode.Accepted

        mock_class = MagicMock(spec=CompleteDialog)
        mock_class.DialogCode = QDialog.DialogCode
        mock_class.return_value = dlg

        with (
            patch("app.main_window.CompleteDialog", mock_class),
            patch("app.main_window.QMessageBox") as mock_msgbox,
        ):
            main_window._completar_tarea()

        # Debe mostrar advertencia
        mock_msgbox.warning.assert_called_once()
        call_args = mock_msgbox.warning.call_args
        assert "No se puede completar" in call_args[0][1]

        # NO debe llamar a complete_issue
        main_window._redmine.complete_issue.assert_not_called()


# ================================================================
# Tests para manejo de RedmineValidationError en nueva/editar tarea
# ================================================================


class TestNuevaTareaValidationErrors:
    """Tests para manejo de RedmineValidationError en _nueva_tarea()."""

    @pytest.fixture
    def main_window(self, qapp):
        with (
            patch.object(MainWindow, "_setup_ui"),
            patch.object(MainWindow, "_setup_menu"),
            patch.object(MainWindow, "_setup_tray"),
            patch.object(MainWindow, "_restore_window_state"),
        ):
            w = MainWindow()
            w._redmine = MagicMock()
            w._task_table = MagicMock()
            w._filter_bar = MagicMock()
            w._filter_bar.selected_project_id = 0
            w._cargar_issues = MagicMock()
            w._projects = []
            w._trackers = []
            w._priorities = []
            w._statuses = []
            w._current_user_id = 1
            return w

    def test_nueva_tarea_catches_validation_error(self, main_window):
        """_nueva_tarea debe capturar RedmineValidationError y mostrar QMessageBox."""
        # Mock del diálogo que devuelve Accepted
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = QDialog.DialogCode.Accepted
        mock_dlg.project_id = 1
        mock_dlg.subject = "Test"
        mock_dlg.description = ""
        mock_dlg.tracker_id = 1
        mock_dlg.priority_id = 2
        mock_dlg.category_id = 0
        mock_dlg.assigned_to_id = 0
        mock_dlg.start_date = ""
        mock_dlg.due_date = ""
        mock_dlg.due_enabled = False
        mock_dlg.done_ratio = 0
        mock_dlg.upload_tokens = []

        main_window._redmine.create_issue.side_effect = RedmineValidationError(
            "Error", ["Asunto no puede estar vacío"]
        )

        with (
            patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td,
            patch("app.main_window.QMessageBox") as mock_msgbox,
        ):
            mock_td.DialogCode = QDialog.DialogCode
            main_window._nueva_tarea()
            mock_msgbox.critical.assert_called_once()
            call_args = mock_msgbox.critical.call_args
            assert "Error de validación" in call_args[0][1]
            assert "Asunto no puede estar vacío" in call_args[0][2]


class TestEditarTareaValidationErrors:
    """Tests para manejo de RedmineValidationError en _editar_tarea()."""

    @pytest.fixture
    def main_window(self, qapp):
        with (
            patch.object(MainWindow, "_setup_ui"),
            patch.object(MainWindow, "_setup_menu"),
            patch.object(MainWindow, "_setup_tray"),
            patch.object(MainWindow, "_restore_window_state"),
        ):
            w = MainWindow()
            w._redmine = MagicMock()
            w._task_table = MagicMock()
            w._filter_bar = MagicMock()
            w._cargar_issues = MagicMock()
            w._projects = []
            w._trackers = []
            w._priorities = []
            w._statuses = []
            w._current_user_id = 1
            return w

    def test_editar_tarea_catches_validation_error(self, main_window):
        """_editar_tarea debe capturar RedmineValidationError y mostrar QMessageBox."""
        # Mock de get_issue_with_journals
        main_window._redmine.get_issue_with_journals.return_value = {
            "id": 42,
            "subject": "Test",
            "description": "",
            "project": {"id": 1},
            "tracker": {"id": 1},
            "priority": {"id": 2},
            "category_id": 0,
            "start_date": "",
            "done_ratio": 0,
            "status": {"id": 1},
            "_journals": [],
            "_attachments": [],
        }
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []

        # Mock del diálogo que devuelve Accepted
        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = QDialog.DialogCode.Accepted
        mock_dlg.project_id = 1
        mock_dlg.subject = "Test updated"
        mock_dlg.description = ""
        mock_dlg.tracker_id = 1
        mock_dlg.priority_id = 2
        mock_dlg.category_id = 0
        mock_dlg.assigned_to_id = 0
        mock_dlg.start_date = ""
        mock_dlg.due_date = ""
        mock_dlg.due_enabled = False
        mock_dlg.done_ratio = 0
        mock_dlg.status_id = 1

        main_window._redmine.update_issue.side_effect = RedmineValidationError(
            "Error", ["Estado no válido"]
        )

        with (
            patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td,
            patch("app.main_window.QMessageBox") as mock_msgbox,
        ):
            mock_td.DialogCode = QDialog.DialogCode
            main_window._editar_tarea(42)
            mock_msgbox.critical.assert_called_once()
            call_args = mock_msgbox.critical.call_args
            assert "Error de validación" in call_args[0][1]
            assert "Estado no válido" in call_args[0][2]

    def test_editar_tarea_incluye_assigned_to_id(self, main_window):
        """_editar_tarea debe incluir assigned_to_id en task_data
        cuando el issue tiene assigned_to en la respuesta de la API."""
        main_window._redmine.get_issue_with_journals.return_value = {
            "id": 42,
            "subject": "Test",
            "description": "",
            "project": {"id": 1},
            "tracker": {"id": 1},
            "priority": {"id": 2},
            "category_id": 0,
            "assigned_to": {"id": 5, "name": "Juan"},
            "start_date": "",
            "due_date": "",
            "done_ratio": 0,
            "status": {"id": 1},
            "_journals": [],
            "_attachments": [],
        }
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []

        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = QDialog.DialogCode.Accepted

        with patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td:
            mock_td.DialogCode = QDialog.DialogCode
            main_window._editar_tarea(42)

        mock_td.assert_called_once()
        task_data = mock_td.call_args.kwargs["task_data"]
        assert task_data["assigned_to_id"] == 5

    def test_editar_tarea_sin_assigned_to_id(self, main_window):
        """_editar_tarea debe incluir assigned_to_id=0 en task_data
        cuando el issue NO tiene assigned_to en la respuesta de la API."""
        main_window._redmine.get_issue_with_journals.return_value = {
            "id": 42,
            "subject": "Test",
            "description": "",
            "project": {"id": 1},
            "tracker": {"id": 1},
            "priority": {"id": 2},
            "category_id": 0,
            # No hay clave "assigned_to"
            "start_date": "",
            "due_date": "",
            "done_ratio": 0,
            "status": {"id": 1},
            "_journals": [],
            "_attachments": [],
        }
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []

        mock_dlg = MagicMock()
        mock_dlg.exec.return_value = QDialog.DialogCode.Accepted

        with patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td:
            mock_td.DialogCode = QDialog.DialogCode
            main_window._editar_tarea(42)

        mock_td.assert_called_once()
        task_data = mock_td.call_args.kwargs["task_data"]
        assert task_data["assigned_to_id"] == 0
