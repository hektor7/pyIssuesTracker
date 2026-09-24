from unittest.mock import MagicMock, patch
from datetime import date
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QMainWindow, QDialog, QMessageBox

from app.dialogs.assign_dialog import AssignDialog
from app.dialogs.complete_dialog import CompleteDialog
from app.dialogs.report_dialog import ReportDialog
from app.dialogs.task_dialog import TaskDialog as RealTaskDialog
from app.main_window import MainWindow
from app.services.redmine_client import (
    RedmineError, RedmineValidationError, RedmineProject,
    RedmineIssue, RedmineJournal,
)
from app.services.report_generator import (
    ReportGenerator, REPORT_COLUMNS, REPORT_FIELDS, DEFAULT_FIELD_KEYS,
)
from app.widgets.toolbar import IssueToolbar


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
    """_completar_tarea intenta con due_date y reintenta sin él si falla."""

    def test_completar_tarea_intenta_con_due_date_primero(self, main_window):
        """_completar_tarea debe enviar due_date=today en el primer intento."""
        main_window._task_table.get_selected_issue_id.return_value = 42

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
        assert call_kwargs["due_date"] == date.today().isoformat()

    def test_completar_tarea_reintenta_sin_due_date_si_validation_error(self, main_window):
        """_completar_tarea debe reintentar sin due_date si Redmine rechaza el campo."""
        from app.services.redmine_client import RedmineValidationError

        main_window._task_table.get_selected_issue_id.return_value = 42

        dlg = MagicMock(spec=CompleteDialog)
        dlg.notes = ""
        dlg.exec.return_value = QDialog.DialogCode.Accepted

        # Primera llamada falla con validation error
        main_window._redmine.complete_issue.side_effect = [RedmineValidationError("due_date rechazado"), None]

        mock_class = MagicMock(spec=CompleteDialog)
        mock_class.DialogCode = QDialog.DialogCode
        mock_class.return_value = dlg

        with patch("app.main_window.CompleteDialog", mock_class):
            main_window._completar_tarea()

        # Se llamó dos veces: primero con due_date, segundo sin
        assert main_window._redmine.complete_issue.call_count == 2
        first_call_kwargs = main_window._redmine.complete_issue.call_args_list[0].kwargs
        second_call_kwargs = main_window._redmine.complete_issue.call_args_list[1].kwargs
        assert first_call_kwargs["due_date"] == date.today().isoformat()
        assert second_call_kwargs.get("due_date", "") == ""


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


class TestEditarTareaGuardaComentario:
    """Al confirmar la edición, el comentario pendiente debe guardarse como nota."""

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

    def _setup_issue(self, main_window):
        main_window._redmine.get_issue_with_journals.return_value = {
            "id": 42,
            "subject": "Test",
            "description": "",
            "project": {"id": 1},
            "tracker": {"id": 1},
            "priority": {"id": 2},
            "category_id": 0,
            "start_date": "",
            "due_date": "",
            "done_ratio": 0,
            "status": {"id": 1},
            "_journals": [],
            "_attachments": [],
        }
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []

    def test_editar_tarea_guarda_comentario_pendiente(self, main_window):
        """Si hay comentario pendiente, debe llamar a add_issue_note tras update_issue."""
        self._setup_issue(main_window)
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
        mock_dlg.status_id = 1
        mock_dlg.upload_tokens = []
        mock_dlg.pending_comment = "Nuevo comentario"
        mock_dlg.pending_checklist_items = []

        with patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td:
            mock_td.DialogCode = QDialog.DialogCode
            main_window._editar_tarea(42)

        main_window._redmine.add_issue_note.assert_called_once_with(42, "Nuevo comentario")

    def test_editar_tarea_sin_comentario_no_llama_add_note(self, main_window):
        """Sin comentario pendiente, no debe llamar a add_issue_note."""
        self._setup_issue(main_window)
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
        mock_dlg.status_id = 1
        mock_dlg.upload_tokens = []
        mock_dlg.pending_comment = ""

        with patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td:
            mock_td.DialogCode = QDialog.DialogCode
            main_window._editar_tarea(42)

        main_window._redmine.add_issue_note.assert_not_called()


class TestMultiProjectAgregacion:
    """La agregación de categorías y miembros debe unir y deduplicar proyectos."""

    def test_categorias_agregadas_y_deduplicadas(self, main_window):
        c1 = SimpleNamespace(id=1, name="Bug")
        c2 = SimpleNamespace(id=2, name="Feature")
        c3 = SimpleNamespace(id=3, name="Soporte")
        main_window._redmine.get_project_issue_categories.side_effect = [
            [c1, c2], [c2, c3],
        ]
        main_window._cargar_categorias_proyecto([10, 20])
        main_window._filter_bar.populate_categories.assert_called_once_with(
            [(1, "Bug"), (2, "Feature"), (3, "Soporte")]
        )
        main_window._redmine.get_project_issue_categories.assert_any_call(10)
        main_window._redmine.get_project_issue_categories.assert_any_call(20)

    def test_miembros_agregados_y_deduplicados(self, main_window):
        m1 = SimpleNamespace(user_id=1, user_name="Ana")
        m2 = SimpleNamespace(user_id=2, user_name="Luis")
        m3 = SimpleNamespace(user_id=1, user_name="Ana")
        main_window._redmine.get_project_memberships.side_effect = [[m1, m2], [m3]]
        main_window._cargar_miembros_proyecto([10, 20])
        main_window._filter_bar.populate_assignees.assert_called_once_with(
            [(1, "Ana"), (2, "Luis")]
        )

    def test_sin_proyectos_limpia_categorias(self, main_window):
        main_window._cargar_categorias_proyecto([])
        main_window._filter_bar.populate_categories.assert_called_once_with([])
        main_window._redmine.get_project_issue_categories.assert_not_called()

    def test_acepta_id_unico(self, main_window):
        c = SimpleNamespace(id=1, name="Bug")
        main_window._redmine.get_project_issue_categories.return_value = [c]
        main_window._cargar_categorias_proyecto(10)
        main_window._filter_bar.populate_categories.assert_called_once_with([(1, "Bug")])


class TestFiltroFijadoPersistencia:
    """Al activar 'Fijar filtro' debe persistir la lista de proyectos seleccionados."""

    @pytest.fixture(autouse=True)
    def _cleanup(self, main_window):
        yield
        s = main_window._settings._settings
        s.remove("filter/projects")
        s.remove("filter/fixed")

    def test_activar_fija_proyectos(self, main_window):
        main_window._filter_bar.selected_project_ids = [2, 3]
        main_window._on_filter_fixed_changed(True)
        assert main_window._settings.filter_fixed is True
        assert main_window._settings.filter_projects == [2, 3]

    def test_desactivar_no_borra_proyectos(self, main_window):
        main_window._settings.filter_projects = [5]
        main_window._on_filter_fixed_changed(False)
        assert main_window._settings.filter_fixed is False
        assert main_window._settings.filter_projects == [5]


class TestOnColumnasCambiadas:
    """Al cambiar columnas debe persistir la visibilidad y recargar datos."""

    @pytest.fixture(autouse=True)
    def _cleanup(self, main_window):
        yield
        main_window._settings._settings.remove("table/columns_visible")

    def test_persiste_y_recarga(self, main_window):
        main_window._task_table.visible_column_keys.return_value = ["id", "project", "title"]
        main_window._on_columnas_cambiadas()
        assert main_window._settings.visible_columns == ["id", "project", "title"]
        main_window._cargar_issues.assert_called_once()


class TestCopiarTareaOtroProyecto:
    """Flujo de copia a otro proyecto (tareas 5.3, 5.4, 7.2 y 7.3)."""

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
            w._projects = [(5, "Destino")]
            w._trackers = []
            w._priorities = []
            w._statuses = []
            w._current_user_id = 1
            return w

    def _issue(self):
        return {
            "id": 42,
            "subject": "Origen",
            "description": "linea1\nlinea2",
            "project": {"id": 1},
            "tracker": {"id": 1},
            "priority": {"id": 2},
            "status": {"id": 1},
            "_journals": [],
            "_attachments": [{"id": 11, "filename": "a.txt"}],
            "_custom_fields": {},
        }

    def test_cancelar_no_abre_task_dialog(self, main_window):
        with (
            patch("app.main_window.ProjectSelectDialog") as mock_sel,
            patch("app.main_window.TaskDialog") as mock_td,
        ):
            mock_sel.DialogCode = QDialog.DialogCode
            mock_sel.return_value.exec.return_value = QDialog.DialogCode.Rejected
            main_window._copiar_tarea_otro_proyecto(42)

        mock_td.assert_not_called()
        main_window._redmine.get_issue_with_journals.assert_not_called()

    def test_aceptar_abre_task_dialog_en_modo_copia(self, main_window):
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []

        with (
            patch("app.main_window.ProjectSelectDialog") as mock_sel,
            patch("app.main_window.TaskDialog") as mock_td,
        ):
            mock_sel.DialogCode = QDialog.DialogCode
            mock_sel.return_value.exec.return_value = QDialog.DialogCode.Accepted
            mock_sel.return_value.selected_project_id = 5
            mock_td.DialogCode = QDialog.DialogCode
            mock_td.return_value.exec.return_value = QDialog.DialogCode.Rejected
            main_window._copiar_tarea_otro_proyecto(42)

        main_window._redmine.get_issue_with_journals.assert_called_once_with(42)
        kwargs = mock_td.call_args.kwargs
        assert kwargs["default_project_id"] == 5
        assert kwargs["copy_from_issue_id"] == 42
        assert kwargs["copy_subject"] == "Origen"
        assert kwargs["copy_description"] == (
            "Tarea creada partiendo de la tarea #42\n\n"
            "> linea1\n> linea2"
        )
        assert kwargs["copy_attachments"] == [{"id": 11, "filename": "a.txt"}]
        # Categorías y miembros del destino se cargan antes de abrir el diálogo
        main_window._redmine.get_project_issue_categories.assert_called_once_with(5)
        main_window._redmine.get_project_memberships.assert_called_once_with(5)


class TestCopiarTareaCreacionEnDestino:
    """Creación real en el destino (tareas 7.4, 7.5 y 7.6).

    Verifica que al aceptar el diálogo de copia se descargan/resuben los adjuntos
    propuestos, se llama a create_issue con el project_id destino y uploads, que
    NUNCA se llama a update_issue sobre el id origen, y que un fallo al copiar
    adjuntos aborta la creación.
    """

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
            w._projects = [(5, "Destino")]
            w._trackers = []
            w._priorities = []
            w._statuses = []
            w._current_user_id = 1
            return w

    def _issue(self):
        return {
            "id": 42,
            "subject": "Origen",
            "description": "linea1\nlinea2",
            "project": {"id": 1},
            "tracker": {"id": 1},
            "priority": {"id": 2},
            "status": {"id": 1},
            "_journals": [],
            "_attachments": [{
                "id": 11,
                "filename": "a.txt",
                "content_url": "https://redmine.example.com/attachments/download/11",
            }],
            "_custom_fields": {},
        }

    def _accepted_copy_dialog(self, **overrides):
        dlg = MagicMock()
        dlg.exec.return_value = QDialog.DialogCode.Accepted
        dlg.project_id = 5
        dlg.subject = "Origen"
        dlg.description = "Tarea creada partiendo de la tarea #42\n\n> linea1\n> linea2"
        dlg.description_raw = "Tarea creada partiendo de la tarea #42\n\n> linea1\n> linea2"
        dlg.tracker_id = 1
        dlg.priority_id = 2
        dlg.category_id = 0
        dlg.assigned_to_id = 0
        dlg.start_date = ""
        dlg.due_date = ""
        dlg.due_enabled = False
        dlg.done_ratio = 0
        dlg.custom_fields = {}
        dlg.proposed_attachments = []
        dlg.upload_tokens = []
        dlg.pending_checklist_items = []
        for key, value in overrides.items():
            setattr(dlg, key, value)
        return dlg

    def _run_copy_flow(self, main_window, copy_dlg, extra_patches=()):
        from contextlib import ExitStack
        with ExitStack() as stack:
            mock_sel = stack.enter_context(patch("app.main_window.ProjectSelectDialog"))
            mock_td = stack.enter_context(
                patch("app.main_window.TaskDialog", return_value=copy_dlg)
            )
            # El código de producción usa TaskDialog._attachment_get; al mockear la
            # clase, restauramos el método estático real para leer filename/content_url.
            mock_td._attachment_get = RealTaskDialog._attachment_get
            for p in extra_patches:
                stack.enter_context(p)
            mock_sel.DialogCode = QDialog.DialogCode
            mock_sel.return_value.exec.return_value = QDialog.DialogCode.Accepted
            mock_sel.return_value.selected_project_id = 5
            mock_td.DialogCode = QDialog.DialogCode
            main_window._copiar_tarea_otro_proyecto(42)

    def test_crea_tarea_en_destino_con_uploads(self, main_window):
        """7.5: create_issue recibe project_id destino y los uploads de los adjuntos."""
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []
        main_window._redmine.download_attachment.return_value = None
        main_window._redmine.upload_file.return_value = {"upload": {"token": "tok-1"}}

        copy_dlg = self._accepted_copy_dialog(
            proposed_attachments=[{
                "id": 11,
                "filename": "a.txt",
                "content_url": "https://redmine.example.com/attachments/download/11",
            }]
        )
        self._run_copy_flow(main_window, copy_dlg)

        main_window._redmine.download_attachment.assert_called_once()
        main_window._redmine.upload_file.assert_called_once()
        main_window._redmine.create_issue.assert_called_once()
        kwargs = main_window._redmine.create_issue.call_args.kwargs
        assert kwargs["project_id"] == 5
        assert kwargs["uploads"] == [{
            "token": "tok-1",
            "filename": "a.txt",
            "content_type": "text/plain",
        }]
        main_window._cargar_issues.assert_called_once()

    def test_copia_conserva_espacios_extremos_de_la_descripcion(self, main_window):
        """R4: en modo copia, create_issue recibe el texto crudo con espacios exactos."""
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []

        copy_dlg = self._accepted_copy_dialog(
            description_raw="  Tarea creada partiendo de la tarea #42  ",
        )
        self._run_copy_flow(main_window, copy_dlg)

        kwargs = main_window._redmine.create_issue.call_args.kwargs
        assert kwargs["description"] == "  Tarea creada partiendo de la tarea #42  "

    def test_no_llama_update_issue_sobre_el_origen(self, main_window):
        """7.6: el flujo de copia nunca modifica la tarea origen."""
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []
        main_window._redmine.download_attachment.return_value = None
        main_window._redmine.upload_file.return_value = {"upload": {"token": "tok-1"}}

        copy_dlg = self._accepted_copy_dialog(
            proposed_attachments=[{
                "id": 11,
                "filename": "a.txt",
                "content_url": "https://redmine.example.com/attachments/download/11",
            }]
        )
        self._run_copy_flow(main_window, copy_dlg)

        main_window._redmine.update_issue.assert_not_called()

    def test_fallo_al_copiar_adjunto_aborta_creacion(self, main_window):
        """7.4: si falla la descarga de un adjunto, no se crea la tarea."""
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []
        main_window._redmine.download_attachment.side_effect = RedmineError("descarga fallida")

        copy_dlg = self._accepted_copy_dialog(
            proposed_attachments=[{
                "id": 11,
                "filename": "a.txt",
                "content_url": "https://redmine.example.com/attachments/download/11",
            }]
        )
        with patch("app.main_window.QMessageBox") as mock_msgbox:
            self._run_copy_flow(main_window, copy_dlg, extra_patches=())

        main_window._redmine.create_issue.assert_not_called()
        main_window._redmine.update_issue.assert_not_called()
        mock_msgbox.critical.assert_called_once()

    def test_directorio_temporal_se_limpia_aunque_falle(self, main_window):
        """7.4: el directorio temporal se limpia aunque falle la descarga."""
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []
        main_window._redmine.download_attachment.side_effect = RedmineError("descarga fallida")

        copy_dlg = self._accepted_copy_dialog(
            proposed_attachments=[{
                "id": 11,
                "filename": "a.txt",
                "content_url": "https://redmine.example.com/attachments/download/11",
            }]
        )
        with (
            patch("app.main_window.tempfile.TemporaryDirectory") as mock_tmp,
            patch("app.main_window.QMessageBox") as mock_msgbox,
        ):
            mock_tmp.return_value.__enter__.return_value = "/tmp/fake-copy"
            self._run_copy_flow(main_window, copy_dlg, extra_patches=())

        # El contexto se cierra (limpieza) aunque falle la descarga
        mock_tmp.return_value.__exit__.assert_called_once()
        main_window._redmine.create_issue.assert_not_called()

    def test_upload_tokens_del_dialogo_se_incluyen_en_uploads(self, main_window):
        """R2: los archivos nuevos del diálogo se adjuntan junto a la propuesta copiada."""
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []
        main_window._redmine.download_attachment.return_value = None
        main_window._redmine.upload_file.return_value = {"upload": {"token": "tok-1"}}

        copy_dlg = self._accepted_copy_dialog(
            upload_tokens=[{
                "token": "tok-nuevo",
                "filename": "nuevo.txt",
                "content_type": "text/plain",
            }],
            proposed_attachments=[{
                "id": 11,
                "filename": "a.txt",
                "content_url": "https://redmine.example.com/attachments/download/11",
            }],
        )
        self._run_copy_flow(main_window, copy_dlg)

        kwargs = main_window._redmine.create_issue.call_args.kwargs
        assert kwargs["uploads"] == [
            {"token": "tok-nuevo", "filename": "nuevo.txt", "content_type": "text/plain"},
            {"token": "tok-1", "filename": "a.txt", "content_type": "text/plain"},
        ]

    def test_pending_checklist_items_se_crean_tras_la_copia(self, main_window):
        """R2: los items pendientes del checklist se crean sobre la tarea creada."""
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []
        main_window._redmine.create_issue.return_value = {"issue": {"id": 99}}

        copy_dlg = self._accepted_copy_dialog(
            pending_checklist_items=["Item 1", "Item 2"],
        )
        self._run_copy_flow(main_window, copy_dlg)

        main_window._redmine.create_checklist_item.assert_any_call(99, "Item 1")
        main_window._redmine.create_checklist_item.assert_any_call(99, "Item 2")
        assert main_window._redmine.create_checklist_item.call_count == 2
        main_window._cargar_issues.assert_called_once()

    def test_fallo_parcial_checklist_muestra_warning(self, main_window):
        """R2: si falla algún item del checklist se avisa sin abortar la copia."""
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []
        main_window._redmine.create_issue.return_value = {"issue": {"id": 99}}
        main_window._redmine.create_checklist_item.side_effect = [None, RuntimeError("boom")]

        copy_dlg = self._accepted_copy_dialog(
            pending_checklist_items=["Item A", "Item B"],
        )
        with patch("app.main_window.QMessageBox") as mock_msgbox:
            self._run_copy_flow(main_window, copy_dlg)

        mock_msgbox.warning.assert_called_once()
        main_window._redmine.create_checklist_item.assert_any_call(99, "Item A")
        main_window._redmine.create_checklist_item.assert_any_call(99, "Item B")
        main_window._cargar_issues.assert_called_once()

    def test_adjuntos_mismo_filename_no_se_sobrescriben_en_tmp(self, main_window):
        """W3: dos adjuntos con el mismo filename se descargan a rutas temporales
        distintas (una por id) y se suben ambos sin sobrescribirse."""
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []
        main_window._redmine.download_attachment.return_value = None
        main_window._redmine.upload_file.side_effect = [
            {"upload": {"token": "tok-1"}},
            {"upload": {"token": "tok-2"}},
        ]

        copy_dlg = self._accepted_copy_dialog(
            proposed_attachments=[
                {
                    "id": 11,
                    "filename": "a.txt",
                    "content_url": "https://redmine.example.com/attachments/download/11",
                },
                {
                    "id": 22,
                    "filename": "a.txt",
                    "content_url": "https://redmine.example.com/attachments/download/22",
                },
            ]
        )
        self._run_copy_flow(main_window, copy_dlg)

        # Ambos adjuntos se descargan a rutas temporales distintas (una por id)
        assert main_window._redmine.download_attachment.call_count == 2
        dest_paths = [
            call.args[1]
            for call in main_window._redmine.download_attachment.call_args_list
        ]
        assert len(set(dest_paths)) == 2
        assert any("11_a.txt" in p for p in dest_paths)
        assert any("22_a.txt" in p for p in dest_paths)

        # Y ambos se suben (sin sobrescribirse) con su propio token
        assert main_window._redmine.upload_file.call_count == 2
        kwargs = main_window._redmine.create_issue.call_args.kwargs
        assert kwargs["uploads"] == [
            {"token": "tok-1", "filename": "a.txt", "content_type": "text/plain"},
            {"token": "tok-2", "filename": "a.txt", "content_type": "text/plain"},
        ]

    def test_descripcion_enviada_es_la_editada_por_el_usuario(self, main_window):
        """Lo enviado a create_issue es el texto final editado por el usuario."""
        main_window._redmine.get_issue_with_journals.return_value = self._issue()
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []

        copy_dlg = self._accepted_copy_dialog(
            description_raw="Texto editado por el usuario en el diálogo",
        )
        self._run_copy_flow(main_window, copy_dlg)

        kwargs = main_window._redmine.create_issue.call_args.kwargs
        assert kwargs["description"] == "Texto editado por el usuario en el diálogo"

    def test_copia_al_mismo_proyecto_crea_nueva_y_no_modifica_origen(self, main_window):
        """Copiar al mismo proyecto del origen crea una tarea nueva sin tocar el origen."""
        issue = self._issue()
        issue["project"] = {"id": 5}  # el origen pertenece al proyecto destino
        main_window._redmine.get_issue_with_journals.return_value = issue
        main_window._redmine.get_project_issue_categories.return_value = []
        main_window._redmine.get_project_memberships.return_value = []

        copy_dlg = self._accepted_copy_dialog()
        self._run_copy_flow(main_window, copy_dlg)

        # Se crea una tarea nueva en el proyecto 5 (create_issue)...
        kwargs = main_window._redmine.create_issue.call_args.kwargs
        assert kwargs["project_id"] == 5
        # ...y el origen nunca se modifica
        main_window._redmine.update_issue.assert_not_called()


class TestCustomFieldsEnviados:
    """custom_fields del diálogo se envía en _nueva_tarea y _editar_tarea."""

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

    def test_nueva_tarea_envia_custom_fields(self, main_window):
        """_nueva_tarea debe pasar custom_fields a create_issue."""
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
        mock_dlg.custom_fields = {1: "valor"}
        mock_dlg.pending_checklist_items = []

        with patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td:
            mock_td.DialogCode = QDialog.DialogCode
            main_window._nueva_tarea()

        kwargs = main_window._redmine.create_issue.call_args.kwargs
        assert kwargs["custom_fields"] == {1: "valor"}

    def test_editar_tarea_envia_custom_fields(self, main_window):
        """_editar_tarea debe pasar custom_fields a update_issue."""
        main_window._redmine.get_issue_with_journals.return_value = {
            "id": 42,
            "subject": "Test",
            "description": "",
            "project": {"id": 1},
            "tracker": {"id": 1},
            "priority": {"id": 2},
            "category_id": 0,
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
        mock_dlg.status_id = 1
        mock_dlg.upload_tokens = []
        mock_dlg.custom_fields = {2: "otro"}
        mock_dlg.pending_comment = ""

        with patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td:
            mock_td.DialogCode = QDialog.DialogCode
            main_window._editar_tarea(42)

        kwargs = main_window._redmine.update_issue.call_args.kwargs
        assert kwargs["custom_fields"] == {2: "otro"}


class TestCargarProyectosNombresCompletos:
    """_cargar_proyectos() debe usar el nombre completo del proyecto (D2)."""

    def test_cargar_proyectos_usa_nombre_completo_y_mapa_por_id(self, main_window):
        """_projects contiene el nombre completo y _project_full_names mapea id -> nombre."""
        w = main_window
        w._settings.filter_fixed = False
        projects = [
            RedmineProject(id=1, name="Raíz", identifier="raiz", parent_id=None, full_name="Raíz"),
            RedmineProject(id=2, name="Hijo", identifier="hijo", parent_id=1, full_name="Raíz > Hijo"),
        ]
        w._redmine.get_all_projects.return_value = projects

        w._cargar_proyectos()

        assert w._projects == [(1, "Raíz"), (2, "Raíz > Hijo")]
        assert w._project_full_names == {1: "Raíz", 2: "Raíz > Hijo"}
        # La jerarquía se mantiene igual que antes
        assert w._project_hierarchy == {1: None, 2: 1}
        w._filter_bar.populate_projects.assert_called_once_with(
            w._projects, w._project_hierarchy
        )

    def test_cargar_proyectos_fallback_a_name_si_full_name_vacio(self, main_window):
        """Si full_name está vacío, se usa p.name como nombre visible."""
        w = main_window
        w._settings.filter_fixed = False
        projects = [
            RedmineProject(id=1, name="Solo", identifier="solo", parent_id=None, full_name=""),
        ]
        w._redmine.get_all_projects.return_value = projects

        w._cargar_proyectos()

        assert w._projects == [(1, "Solo")]
        assert w._project_full_names == {1: "Solo"}


class TestCargarIssuesNombresCompletos:
    """_cargar_issues() debe usar el nombre completo y añadir priority_id (D3)."""

    def _setup(self, main_window):
        w = main_window
        w._status_indicator = MagicMock()
        w._update_task_table_context = MagicMock()
        w._project_full_names = {1: "Raíz > Hijo"}
        w._filter_bar.selected_project_ids = []
        w._filter_bar.selected_status = "open"
        w._filter_bar.selected_priority = 0
        w._filter_bar.selected_category = 0
        w._filter_bar.selected_date_from = None
        w._filter_bar.selected_date_to = None
        w._filter_bar.selected_assigned_to = []
        return w

    def _issue(self):
        return SimpleNamespace(
            id=42, subject="Tarea", description="", start_date="", due_date="",
            status_name="Abierta", status_id=1, done_ratio=0,
            project_id=1, project_name="Hijo",
            assigned_to_id=0, assigned_to_name="", author_name="",
            tracker_name="", priority_name="Alta", priority_id=4,
            category_name="", created_on="", updated_on="",
        )

    def test_cargar_issues_usa_nombre_completo_y_priority_id(self, main_window):
        """El dict pasado a set_issues lleva project_name completo y priority_id."""
        w = self._setup(main_window)
        w._redmine.get_issues.return_value = [self._issue()]

        MainWindow._cargar_issues(w)

        w._task_table.set_issues.assert_called_once()
        issues_dict = w._task_table.set_issues.call_args.args[0]
        assert issues_dict[0]["project_name"] == "Raíz > Hijo"
        assert issues_dict[0]["priority_id"] == 4

    def test_cargar_issues_fallback_a_project_name_si_no_hay_mapa(self, main_window):
        """Sin entrada en _project_full_names, se usa iss.project_name."""
        w = self._setup(main_window)
        w._project_full_names = {}
        w._redmine.get_issues.return_value = [self._issue()]

        MainWindow._cargar_issues(w)

        issues_dict = w._task_table.set_issues.call_args.args[0]
        assert issues_dict[0]["project_name"] == "Hijo"
        assert issues_dict[0]["priority_id"] == 4


class TestCargarPriorities:
    """W7: _cargar_priorities() debe propagar el catálogo a la tabla."""

    def test_cargar_priorities_llama_set_priorities_con_catalogo(self, main_window):
        """Con catálogo cargado, set_priorities recibe la lista (id, nombre)."""
        w = main_window
        w._redmine.get_issue_priorities.return_value = [
            SimpleNamespace(id=1, name="Baja"),
            SimpleNamespace(id=2, name="Normal"),
            SimpleNamespace(id=3, name="Alta"),
        ]

        w._cargar_priorities()

        w._task_table.set_priorities.assert_called_once_with(
            [(1, "Baja"), (2, "Normal"), (3, "Alta")]
        )
        w._filter_bar.populate_priorities.assert_called_once_with(
            [(1, "Baja"), (2, "Normal"), (3, "Alta")]
        )

    def test_cargar_priorities_error_llama_set_priorities_vacio(self, main_window):
        """Si la API falla, set_priorities se invoca igualmente con lista vacía."""
        w = main_window
        w._redmine.get_issue_priorities.side_effect = RedmineError("boom")

        w._cargar_priorities()

        w._task_table.set_priorities.assert_called_once_with([])
        w._filter_bar.populate_priorities.assert_not_called()


# ================================================================
# Tests del informe ODS (tarea 6.1 del cambio add-ods-report-export)
# ================================================================


class TestInformeToolbar:
    """Conexión del botón 'Informe' (tarea 6.1.1)."""

    def test_toolbar_emite_informe_clicked_al_disparar_la_accion(self, qapp):
        """La acción 'Informe' del IssueToolbar debe emitir informe_clicked."""
        toolbar = IssueToolbar()
        received = []
        toolbar.informe_clicked.connect(lambda: received.append(True))
        action = next(a for a in toolbar.actions() if a.text() == "Informe")
        action.trigger()
        assert received == [True]

    def test_toolbar_mantiene_acciones_existentes(self, qapp):
        """El toolbar conserva todas las acciones previas además de 'Informe'."""
        toolbar = IssueToolbar()
        texts = [a.text() for a in toolbar.actions()]
        for expected in ["Nuevo", "Editar", "Asignar", "Completada",
                         "Rechazar", "Refrescar", "Config", "Informe"]:
            assert expected in texts

    def test_main_window_conecta_informe_clicked_a_generar_informe(self, qapp):
        """En MainWindow, informe_clicked debe estar conectado a _generar_informe."""
        with (
            patch.object(MainWindow, "_setup_menu"),
            patch.object(MainWindow, "_setup_tray"),
            patch.object(MainWindow, "_restore_window_state"),
            patch.object(MainWindow, "_generar_informe") as mock_gen,
        ):
            w = MainWindow()  # _setup_ui real: crea el toolbar y conecta las señales
            w._redmine = MagicMock()
            w._task_table = MagicMock()
            w._tray = MagicMock()
            w._filter_bar = MagicMock()

            # Cadena completa: acción real del toolbar -> señal -> _generar_informe
            action = next(a for a in w._toolbar.actions() if a.text() == "Informe")
            action.trigger()
            mock_gen.assert_called_once()

            # La señal también puede emitirse directamente
            w._toolbar.informe_clicked.emit()
            assert mock_gen.call_count == 2


class TestGenerarInforme:
    """Flujo de _generar_informe (tareas 6.1.2 a 6.1.6)."""

    def _setup(self, main_window):
        """Prepara el MainWindow para el flujo del informe."""
        main_window._filter_bar.selected_project_ids = []
        main_window._project_full_names = {}

    def _issue(self, **overrides):
        """Crea un RedmineIssue real con valores por defecto."""
        defaults = dict(
            id=1, subject="Tarea de prueba", description="",
            start_date="2026-01-05", due_date="2026-01-20",
            status_name="Nueva", status_id=1, done_ratio=30,
            project_id=1, project_name="Proyecto A",
            assigned_to_id=2, assigned_to_name="Luis",
            author_id=1, author_name="Ana",
            created_on="2026-01-01T10:00:00Z",
            updated_on="2026-01-10T12:00:00Z",
            tracker_id=1, tracker_name="Tarea",
            priority_id=2, priority_name="Normal",
            category_id=0, category_name="",
        )
        defaults.update(overrides)
        return RedmineIssue(**defaults)

    def _make_report_dialog(self, **overrides):
        """Crea un MagicMock que simula ReportDialog aceptado."""
        dlg = MagicMock(spec=ReportDialog)
        dlg.exec.return_value = QDialog.DialogCode.Accepted
        dlg.selected_project_ids = []
        dlg.selected_user_ids = []
        dlg.selected_roles = ["creador", "actualizador", "participante"]
        dlg.selected_fields = DEFAULT_FIELD_KEYS
        dlg.created_from = None
        dlg.created_to = None
        for key, value in overrides.items():
            setattr(dlg, key, value)
        return dlg

    def _patch_report_dialog(self, dlg_mock):
        """Parchea ReportDialog preservando DialogCode para comparaciones."""
        mock_class = MagicMock(spec=ReportDialog)
        mock_class.DialogCode = QDialog.DialogCode
        mock_class.return_value = dlg_mock
        return patch("app.main_window.ReportDialog", mock_class)

    def test_sin_conexion_muestra_warning_y_no_abre_dialogo(self, main_window):
        """Con _redmine=None, _generar_informe avisa y no abre el diálogo."""
        main_window._redmine = None

        with (
            patch("app.main_window.ReportDialog") as mock_report_cls,
            patch("app.main_window.QMessageBox") as mock_msgbox,
        ):
            main_window._generar_informe()

        mock_msgbox.warning.assert_called_once()
        call_args = mock_msgbox.warning.call_args
        assert "Sin conexión" in call_args[0][1]
        mock_report_cls.assert_not_called()

    def test_cancelar_dialogo_no_consulta_ni_escribe(self, main_window):
        """Si el diálogo se cancela, no se consulta ni se escribe nada."""
        self._setup(main_window)
        dlg = self._make_report_dialog()
        dlg.exec.return_value = QDialog.DialogCode.Rejected

        with (
            self._patch_report_dialog(dlg),
            patch("app.main_window.QFileDialog.getSaveFileName") as mock_save,
            patch("app.main_window.ReportGenerator") as mock_gen_cls,
        ):
            main_window._generar_informe()

        main_window._redmine.get_issues.assert_not_called()
        mock_save.assert_not_called()
        mock_gen_cls.assert_not_called()

    def test_flujo_feliz_escribe_ods(self, main_window, tmp_path):
        """Flujo feliz: consulta con journals y rango, escribe el ODS y confirma."""
        self._setup(main_window)
        issue_con_journals = self._issue(
            id=1,
            journals=[RedmineJournal(id=1, user_id=3, user_name="Marta", notes="revisado")],
        )
        issue_sin_journals = self._issue(id=2, subject="Otra tarea")
        main_window._redmine.get_issues.return_value = [issue_con_journals, issue_sin_journals]

        dlg = self._make_report_dialog(
            selected_project_ids=[1],
            created_from="2026-01-01",
            created_to="2026-03-31",
        )
        path = str(tmp_path / "informe")  # sin extensión: debe añadirse .ods

        mock_gen_cls = MagicMock(spec=ReportGenerator)
        with (
            self._patch_report_dialog(dlg),
            patch("app.main_window.QFileDialog.getSaveFileName", return_value=(path, "")),
            patch("app.main_window.ReportGenerator", mock_gen_cls),
            patch("app.main_window.QMessageBox") as mock_msgbox,
        ):
            main_window._generar_informe()

        # (a) get_issues con journals y con el rango created_on del diálogo
        main_window._redmine.get_issues.assert_called_once_with(
            project_id=[1],
            status_filter="*",
            created_on_from="2026-01-01",
            created_on_to="2026-03-31",
            include_journals=True,
            current_user_id=2,
        )
        # (b) se escribe en la ruta con extensión .ods
        mock_gen_cls.assert_called_once_with(REPORT_COLUMNS, sheet_name="Informe")
        mock_gen_cls.return_value.write.assert_called_once_with(
            str(tmp_path / "informe.ods")
        )
        # (c) confirmación de éxito
        mock_msgbox.information.assert_called_once()
        call_args = mock_msgbox.information.call_args
        assert "Informe guardado" in call_args[0][2]

    def test_ruta_con_extension_ods_no_se_duplica(self, main_window, tmp_path):
        """Si la ruta ya termina en .ods, no se añade la extensión otra vez."""
        self._setup(main_window)
        main_window._redmine.get_issues.return_value = [self._issue()]
        dlg = self._make_report_dialog()
        path = str(tmp_path / "informe.ods")

        mock_gen_cls = MagicMock(spec=ReportGenerator)
        with (
            self._patch_report_dialog(dlg),
            patch("app.main_window.QFileDialog.getSaveFileName", return_value=(path, "")),
            patch("app.main_window.ReportGenerator", mock_gen_cls),
            patch("app.main_window.QMessageBox"),
        ):
            main_window._generar_informe()

        mock_gen_cls.return_value.write.assert_called_once_with(path)

    def test_sin_resultados_no_escribe_fichero(self, main_window):
        """Si ninguna tarea cumple el filtro de usuarios, avisa y no escribe."""
        self._setup(main_window)
        # El usuario 999 no participa en la tarea -> no cumple el filtro
        main_window._redmine.get_issues.return_value = [self._issue()]
        dlg = self._make_report_dialog(
            selected_user_ids=[999],
            selected_roles=["creador"],
        )

        with (
            self._patch_report_dialog(dlg),
            patch("app.main_window.QFileDialog.getSaveFileName") as mock_save,
            patch("app.main_window.ReportGenerator") as mock_gen_cls,
            patch("app.main_window.QMessageBox") as mock_msgbox,
        ):
            main_window._generar_informe()

        mock_msgbox.information.assert_called_once()
        call_args = mock_msgbox.information.call_args
        assert "Sin resultados" in call_args[0][1]
        mock_save.assert_not_called()
        mock_gen_cls.assert_not_called()

    def test_error_de_consulta_muestra_critical(self, main_window):
        """Si get_issues lanza RedmineError, se muestra critical y no se escribe."""
        self._setup(main_window)
        main_window._redmine.get_issues.side_effect = RedmineError("boom")
        dlg = self._make_report_dialog()

        with (
            self._patch_report_dialog(dlg),
            patch("app.main_window.QFileDialog.getSaveFileName") as mock_save,
            patch("app.main_window.ReportGenerator") as mock_gen_cls,
            patch("app.main_window.QMessageBox") as mock_msgbox,
        ):
            main_window._generar_informe()

        mock_msgbox.critical.assert_called_once()
        call_args = mock_msgbox.critical.call_args
        assert "No se pudieron obtener las tareas" in call_args[0][2]
        mock_save.assert_not_called()
        mock_gen_cls.assert_not_called()

    def test_error_de_escritura_muestra_critical(self, main_window, tmp_path):
        """Si write() lanza OSError, se muestra critical y no information."""
        self._setup(main_window)
        main_window._redmine.get_issues.return_value = [self._issue()]
        dlg = self._make_report_dialog()
        path = str(tmp_path / "informe.ods")

        mock_gen_cls = MagicMock(spec=ReportGenerator)
        mock_gen_cls.return_value.write.side_effect = OSError("disk full")
        with (
            self._patch_report_dialog(dlg),
            patch("app.main_window.QFileDialog.getSaveFileName", return_value=(path, "")),
            patch("app.main_window.ReportGenerator", mock_gen_cls),
            patch("app.main_window.QMessageBox") as mock_msgbox,
            patch("app.main_window.QApplication.setOverrideCursor"),
            patch("app.main_window.QApplication.restoreOverrideCursor") as mock_restore,
        ):
            main_window._generar_informe()

        mock_msgbox.critical.assert_called_once()
        call_args = mock_msgbox.critical.call_args
        assert "No se pudo generar el informe" in call_args[0][2]
        mock_msgbox.information.assert_not_called()
        mock_restore.assert_called_once()

    def test_pasa_proyectos_preseleccionados_al_dialogo(self, main_window):
        """Los proyectos preseleccionados del filtro se pasan al ReportDialog."""
        self._setup(main_window)
        main_window._filter_bar.selected_project_ids = [1, 2]
        dlg = self._make_report_dialog()
        dlg.exec.return_value = QDialog.DialogCode.Rejected

        with self._patch_report_dialog(dlg) as mock_report_cls:
            main_window._generar_informe()

        mock_report_cls.assert_called_once()
        args = mock_report_cls.call_args
        assert args[0][2] == [1, 2]

    def test_generar_informe_usa_solo_las_etiquetas_de_los_campos_marcados(
        self, main_window, tmp_path
    ):
        """ReportGenerator recibe solo las etiquetas de los campos marcados."""
        self._setup(main_window)
        main_window._redmine.get_issues.return_value = [self._issue()]
        dlg = self._make_report_dialog(
            selected_fields=["id", "titulo", "url", "comentarios"],
        )
        path = str(tmp_path / "informe.ods")

        mock_gen_cls = MagicMock(spec=ReportGenerator)
        with (
            self._patch_report_dialog(dlg),
            patch("app.main_window.QFileDialog.getSaveFileName", return_value=(path, "")),
            patch("app.main_window.ReportGenerator", mock_gen_cls),
            patch("app.main_window.QMessageBox"),
        ):
            main_window._generar_informe()

        mock_gen_cls.assert_called_once_with(
            ["ID", "Título", "URL", "Comentarios"], sheet_name="Informe"
        )
        # Las filas añadidas están alineadas con las claves marcadas
        rows_added = [
            call.args[0]
            for call in mock_gen_cls.return_value.add_row.call_args_list
        ]
        assert len(rows_added) == 1
        assert len(rows_added[0]) == 4

    def test_pasa_custom_fields_al_dialogo(self, main_window):
        """_generar_informe pasa la unión de campos personalizados al ReportDialog."""
        self._setup(main_window)
        main_window._projects = [(1, "Proyecto A")]
        main_window._redmine.get_project_custom_fields.return_value = [
            SimpleNamespace(id=7, name="Cliente"),
        ]
        dlg = self._make_report_dialog()
        dlg.exec.return_value = QDialog.DialogCode.Rejected

        with self._patch_report_dialog(dlg) as mock_report_cls:
            main_window._generar_informe()

        mock_report_cls.assert_called_once()
        kwargs = mock_report_cls.call_args.kwargs
        assert kwargs["custom_fields"] == [(7, "Cliente")]

    def test_columnas_incluyen_campo_personalizado_seleccionado(self, main_window, tmp_path):
        """ReportGenerator recibe la etiqueta del campo personalizado marcado."""
        self._setup(main_window)
        main_window._projects = [(1, "Proyecto A")]
        main_window._redmine.get_project_custom_fields.return_value = [
            SimpleNamespace(id=7, name="Cliente"),
        ]
        main_window._redmine.get_issues.return_value = [self._issue()]
        dlg = self._make_report_dialog(
            selected_fields=["id", "cf_7"],
        )
        path = str(tmp_path / "informe.ods")

        mock_gen_cls = MagicMock(spec=ReportGenerator)
        with (
            self._patch_report_dialog(dlg),
            patch("app.main_window.QFileDialog.getSaveFileName", return_value=(path, "")),
            patch("app.main_window.ReportGenerator", mock_gen_cls),
            patch("app.main_window.QMessageBox"),
        ):
            main_window._generar_informe()

        mock_gen_cls.assert_called_once_with(["ID", "Cliente"], sheet_name="Informe")

    def test_campo_personalizado_no_seleccionado_no_aparece_en_columnas(
        self, main_window, tmp_path
    ):
        """Si selected_fields no incluye cf_7, la columna del campo personalizado no aparece."""
        self._setup(main_window)
        main_window._projects = [(1, "Proyecto A")]
        main_window._redmine.get_project_custom_fields.return_value = [
            SimpleNamespace(id=7, name="Cliente"),
        ]
        main_window._redmine.get_issues.return_value = [self._issue()]
        dlg = self._make_report_dialog(
            selected_fields=["id", "titulo"],  # sin cf_7
        )
        path = str(tmp_path / "informe.ods")

        mock_gen_cls = MagicMock(spec=ReportGenerator)
        with (
            self._patch_report_dialog(dlg),
            patch("app.main_window.QFileDialog.getSaveFileName", return_value=(path, "")),
            patch("app.main_window.ReportGenerator", mock_gen_cls),
            patch("app.main_window.QMessageBox"),
        ):
            main_window._generar_informe()

        columns = mock_gen_cls.call_args.args[0]
        assert "Cliente" not in columns
        assert columns == ["ID", "Título"]

    def test_por_defecto_sin_columnas_personalizadas(self, main_window, tmp_path):
        """Con los 17 campos estándar y sin cf_, las columnas son exactamente REPORT_COLUMNS."""
        self._setup(main_window)
        main_window._projects = [(1, "Proyecto A")]
        main_window._redmine.get_project_custom_fields.return_value = [
            SimpleNamespace(id=7, name="Cliente"),
        ]
        main_window._redmine.get_issues.return_value = [self._issue()]
        dlg = self._make_report_dialog()  # selected_fields = DEFAULT_FIELD_KEYS (17)
        path = str(tmp_path / "informe.ods")

        mock_gen_cls = MagicMock(spec=ReportGenerator)
        with (
            self._patch_report_dialog(dlg),
            patch("app.main_window.QFileDialog.getSaveFileName", return_value=(path, "")),
            patch("app.main_window.ReportGenerator", mock_gen_cls),
            patch("app.main_window.QMessageBox"),
        ):
            main_window._generar_informe()

        mock_gen_cls.assert_called_once_with(REPORT_COLUMNS, sheet_name="Informe")


class TestComposeReportRows:
    """Tests unitarios de _compose_report_rows (tarea 6.1.7)."""

    def _issue(self, **overrides):
        """Crea un RedmineIssue real con valores por defecto."""
        defaults = dict(
            id=1, subject="Tarea de prueba", description="",
            start_date="2026-01-05", due_date="2026-01-20",
            status_name="Nueva", status_id=1, done_ratio=30,
            project_id=1, project_name="Proyecto A",
            assigned_to_id=2, assigned_to_name="Luis",
            author_id=1, author_name="Ana",
            created_on="2026-01-01T10:00:00Z",
            updated_on="2026-01-10T12:00:00Z",
            tracker_id=1, tracker_name="Tarea",
            priority_id=2, priority_name="Normal",
            category_id=0, category_name="",
        )
        defaults.update(overrides)
        return RedmineIssue(**defaults)

    def test_alinea_con_report_columns(self, main_window):
        """Cada fila debe tener tantos valores como campos por defecto, en orden."""
        main_window._project_full_names = {1: "Proyecto A"}
        iss = self._issue()
        rows = main_window._compose_report_rows([iss], DEFAULT_FIELD_KEYS)
        assert len(rows) == 1
        row = rows[0]
        assert len(row) == len(REPORT_COLUMNS)
        assert row[0] == 1                      # ID
        assert row[1] == "Proyecto A"           # Proyecto (nombre completo)
        assert row[2] == "Tarea"                # Tracker
        assert row[3] == "Tarea de prueba"      # Título
        assert row[4] == "Nueva"                # Estado
        assert row[5] == "Normal"               # Prioridad
        assert row[6] == "Luis"                 # Asignado a
        assert row[7] == "Ana"                  # Creado por
        assert row[11] == 30                    # % Progreso
        assert row[12] == ""                    # Categoría
        assert row[14] == "Ana, Luis"           # Usuarios implicados

    def test_convierte_fechas_iso_a_date(self, main_window):
        """Las fechas ISO se convierten a datetime.date; las vacías quedan como ''."""
        main_window._project_full_names = {}
        iss = self._issue(
            created_on="2026-01-01T10:00:00Z",
            start_date="2026-01-05",
            due_date="",
            updated_on="2026-01-10T12:30:00Z",
        )
        row = main_window._compose_report_rows([iss], DEFAULT_FIELD_KEYS)[0]
        assert row[8] == date(2026, 1, 1)    # Fecha de creación
        assert row[9] == date(2026, 1, 5)    # Fecha de inicio
        assert row[10] == ""                 # Fecha de fin vacía
        assert row[13] == date(2026, 1, 10)  # Última modificación

    def test_progreso_numerico(self, main_window):
        """El % Progreso debe ser numérico (int)."""
        main_window._project_full_names = {}
        iss = self._issue(done_ratio=75)
        row = main_window._compose_report_rows([iss], DEFAULT_FIELD_KEYS)[0]
        assert row[11] == 75
        assert isinstance(row[11], int)

    def test_usuarios_implicados_sin_duplicados(self, main_window):
        """La lista de usuarios implicados no repite nombres y se une con ', '."""
        main_window._project_full_names = {}
        iss = RedmineIssue(
            id=1, subject="T",
            author_id=1, author_name="Ana",
            assigned_to_id=2, assigned_to_name="Luis",
            journals=[
                RedmineJournal(id=1, user_id=1, user_name="Ana", notes="comentario"),
                RedmineJournal(id=2, user_id=3, user_name="Marta", notes=""),
            ],
        )
        row = main_window._compose_report_rows([iss], DEFAULT_FIELD_KEYS)[0]
        assert row[14] == "Ana, Luis, Marta"

    def test_subconjunto_de_campos_produce_filas_alineadas(self, main_window):
        """Con un subconjunto de claves, cada fila tiene un valor por clave en orden."""
        main_window._project_full_names = {1: "Proyecto A"}
        iss = self._issue()
        field_keys = ["id", "titulo", "estado", "progreso"]
        rows = main_window._compose_report_rows([iss], field_keys)
        assert len(rows) == 1
        assert rows[0] == [1, "Tarea de prueba", "Nueva", 30]

    def test_url_correcta(self, main_window):
        """El campo url es la URL absoluta {redmine_url}/issues/{id}."""
        main_window._project_full_names = {}
        main_window._settings.redmine_url = "https://redmine.example.com"
        iss = self._issue(id=42)
        row = main_window._compose_report_rows([iss], ["url"])[0]
        assert row[0] == "https://redmine.example.com/issues/42"

    def test_url_correcta_con_slash_final(self, main_window):
        """La URL se construye igual si redmine_url termina en '/'."""
        main_window._project_full_names = {}
        main_window._settings.redmine_url = "https://redmine.example.com/"
        iss = self._issue(id=7)
        row = main_window._compose_report_rows([iss], ["url"])[0]
        assert row[0] == "https://redmine.example.com/issues/7"

    def test_comentarios_formateados_con_autor_y_fecha_hora(self, main_window):
        """Los comentarios se formatean '[DD/MM/YYYY HH:MM] Autor: texto' y se unen con \\n."""
        main_window._project_full_names = {}
        iss = RedmineIssue(
            id=1, subject="T",
            journals=[
                RedmineJournal(
                    id=1, user_id=3, user_name="Marta",
                    notes="revisado", created_on="2026-01-05T10:30:00Z",
                ),
                RedmineJournal(
                    id=2, user_id=4, user_name="Luis",
                    notes="ok", created_on="2026-01-06T09:15:00Z",
                ),
            ],
        )
        row = main_window._compose_report_rows([iss], ["comentarios"])[0]
        assert row[0] == (
            "[05/01/2026 10:30] Marta: revisado\n"
            "[06/01/2026 09:15] Luis: ok"
        )

    def test_comentarios_vacios_sin_journals(self, main_window):
        """Sin journals, la celda de comentarios es una cadena vacía."""
        main_window._project_full_names = {}
        iss = RedmineIssue(id=1, subject="T", journals=[])
        row = main_window._compose_report_rows([iss], ["comentarios"])[0]
        assert row[0] == ""

    def test_comentarios_ignora_journals_sin_notas(self, main_window):
        """Los journals sin notas (o solo espacios) no cuentan como comentarios."""
        main_window._project_full_names = {}
        iss = RedmineIssue(
            id=1, subject="T",
            journals=[
                RedmineJournal(
                    id=1, user_id=3, user_name="Marta",
                    notes="", created_on="2026-01-05T10:30:00Z",
                ),
                RedmineJournal(
                    id=2, user_id=4, user_name="Luis",
                    notes="   ", created_on="2026-01-06T09:15:00Z",
                ),
            ],
        )
        row = main_window._compose_report_rows([iss], ["comentarios"])[0]
        assert row[0] == ""

    def test_comentario_sin_hora_muestra_solo_fecha(self, main_window):
        """Si el timestamp solo tiene fecha, el comentario muestra '[DD/MM/YYYY]'."""
        main_window._project_full_names = {}
        iss = RedmineIssue(
            id=1, subject="T",
            journals=[
                RedmineJournal(
                    id=1, user_id=3, user_name="Marta",
                    notes="sin hora", created_on="2026-02-10",
                ),
            ],
        )
        row = main_window._compose_report_rows([iss], ["comentarios"])[0]
        assert row[0] == "[10/02/2026] Marta: sin hora"


class TestReportCustomFields:
    """Recolección y unión de campos personalizados (cambio informe-campos-personalizados)."""

    def test_union_sin_duplicados_ordenada_por_nombre(self, main_window):
        """_report_custom_fields une los campos de todos los proyectos, dedupe por id y ordena por nombre."""
        main_window._projects = [(1, "Proyecto A"), (2, "Proyecto B")]
        cf1 = SimpleNamespace(id=7, name="Cliente")
        cf2 = SimpleNamespace(id=9, name="Sprint")
        cf3 = SimpleNamespace(id=7, name="Cliente")  # duplicado en otro proyecto
        main_window._redmine.get_project_custom_fields.side_effect = [
            [cf1, cf2], [cf3],
        ]
        result = main_window._report_custom_fields()
        assert result == [(7, "Cliente"), (9, "Sprint")]
        main_window._redmine.get_project_custom_fields.assert_any_call(1)
        main_window._redmine.get_project_custom_fields.assert_any_call(2)

    def test_ignora_proyecto_que_falla(self, main_window):
        """Si un proyecto lanza RedmineError, se ignora y el resto se devuelve."""
        main_window._projects = [(1, "Proyecto A"), (2, "Proyecto B")]
        cf = SimpleNamespace(id=9, name="Sprint")
        main_window._redmine.get_project_custom_fields.side_effect = [
            RedmineError("boom"), [cf],
        ]
        result = main_window._report_custom_fields()
        assert result == [(9, "Sprint")]

    def test_sin_redmine_devuelve_vacio(self, main_window):
        """Sin conexión, _report_custom_fields devuelve []."""
        main_window._redmine = None
        assert main_window._report_custom_fields() == []

    def test_ordena_por_nombre_case_insensitive(self, main_window):
        """El orden es por nombre sin distinguir mayúsculas."""
        main_window._projects = [(1, "Proyecto A")]
        cf1 = SimpleNamespace(id=1, name="zeta")
        cf2 = SimpleNamespace(id=2, name="Alfa")
        main_window._redmine.get_project_custom_fields.return_value = [cf1, cf2]
        result = main_window._report_custom_fields()
        assert result == [(2, "Alfa"), (1, "zeta")]

    def test_for_projects_filtra_por_proyecto(self, main_window):
        """_report_custom_fields_for_projects([1]) devuelve solo los campos del proyecto 1."""
        main_window._projects = [(1, "Proyecto A"), (2, "Proyecto B")]
        cf1 = SimpleNamespace(id=7, name="Cliente")
        cf2 = SimpleNamespace(id=9, name="Sprint")
        main_window._redmine.get_project_custom_fields.side_effect = [
            [cf1], [cf2],
        ]
        result = main_window._report_custom_fields_for_projects([1])
        assert result == [(7, "Cliente")]
        main_window._redmine.get_project_custom_fields.assert_called_once_with(1)

    def test_for_projects_sin_ids_usa_todos(self, main_window):
        """None o lista vacía usan todos los proyectos cargados."""
        main_window._projects = [(1, "Proyecto A"), (2, "Proyecto B")]
        cf1 = SimpleNamespace(id=7, name="Cliente")
        cf2 = SimpleNamespace(id=9, name="Sprint")
        main_window._redmine.get_project_custom_fields.side_effect = [
            [cf1], [cf2],
        ]
        assert main_window._report_custom_fields_for_projects(None) == [
            (7, "Cliente"), (9, "Sprint"),
        ]
        main_window._redmine.get_project_custom_fields.reset_mock()
        main_window._redmine.get_project_custom_fields.side_effect = [
            [cf1], [cf2],
        ]
        assert main_window._report_custom_fields_for_projects([]) == [
            (7, "Cliente"), (9, "Sprint"),
        ]

    def test_for_projects_ignora_ids_vacios(self, main_window):
        """Los ids falsy (0, None) se descartan antes de consultar."""
        main_window._projects = [(1, "Proyecto A")]
        cf1 = SimpleNamespace(id=7, name="Cliente")
        main_window._redmine.get_project_custom_fields.return_value = [cf1]
        result = main_window._report_custom_fields_for_projects([0, None, 1])
        assert result == [(7, "Cliente")]
        main_window._redmine.get_project_custom_fields.assert_called_once_with(1)

    def test_for_projects_sin_redmine_devuelve_vacio(self, main_window):
        """Sin conexión, _report_custom_fields_for_projects devuelve []."""
        main_window._redmine = None
        assert main_window._report_custom_fields_for_projects([1]) == []

    def test_valor_escalar(self, main_window):
        """cf_7 devuelve el valor escalar del campo 7."""
        iss = RedmineIssue(id=1, subject="T", custom_fields={7: "ACME"})
        assert main_window._report_field_value(iss, "cf_7") == "ACME"

    def test_valor_lista_unida_por_coma(self, main_window):
        """Un campo multivalor se une con ', '."""
        iss = RedmineIssue(id=1, subject="T", custom_fields={7: ["A", "B"]})
        assert main_window._report_field_value(iss, "cf_7") == "A, B"

    def test_valor_ausente_devuelve_vacio(self, main_window):
        """Sin el campo, la celda queda vacía."""
        iss = RedmineIssue(id=1, subject="T", custom_fields={})
        assert main_window._report_field_value(iss, "cf_7") == ""

    def test_valor_none_o_vacio_devuelve_vacio(self, main_window):
        """None o cadena vacía se formatean como celda vacía."""
        iss = RedmineIssue(id=1, subject="T", custom_fields={7: None})
        assert main_window._report_field_value(iss, "cf_7") == ""
        iss2 = RedmineIssue(id=1, subject="T", custom_fields={7: ""})
        assert main_window._report_field_value(iss2, "cf_7") == ""

    def test_lista_con_vacios_ignora_vacios(self, main_window):
        """Los elementos vacíos de una lista multivalor se ignoran."""
        iss = RedmineIssue(id=1, subject="T", custom_fields={7: ["A", "", "B"]})
        assert main_window._report_field_value(iss, "cf_7") == "A, B"
