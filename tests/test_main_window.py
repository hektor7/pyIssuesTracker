from unittest.mock import MagicMock, patch
from datetime import date
from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QMainWindow, QDialog, QMessageBox

from app.dialogs.assign_dialog import AssignDialog
from app.dialogs.complete_dialog import CompleteDialog
from app.dialogs.task_dialog import TaskDialog as RealTaskDialog
from app.main_window import MainWindow
from app.services.redmine_client import RedmineError, RedmineValidationError, RedmineProject


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
