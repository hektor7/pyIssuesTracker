from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QMainWindow, QDialog

from app.dialogs.assign_dialog import AssignDialog
from app.dialogs.complete_dialog import CompleteDialog
from app.main_window import MainWindow


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
        main_window._task_table.get_selected_issue_id.return_value = 42

        dlg = self._make_mock_dialog(notes="tarea completada")

        with self._patch_complete_dialog(dlg):
            main_window._completar_tarea()

        main_window._redmine.complete_issue.assert_called_once_with(
            42, done_ratio=100, status_id=2, notes="tarea completada"
        )

    def test_completar_tarea_passes_no_notes(self, main_window):
        """_completar_tarea debe pasar notes vacío si no hay comentario."""
        main_window._task_table.get_selected_issue_id.return_value = 42

        dlg = self._make_mock_dialog(notes="")

        with self._patch_complete_dialog(dlg):
            main_window._completar_tarea()

        main_window._redmine.complete_issue.assert_called_once_with(
            42, done_ratio=100, status_id=2, notes=""
        )
