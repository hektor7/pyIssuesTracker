"""Tests de registro en log de errores de operaciones clave (W3 / tarea 8.3).

Verifican que las operaciones clave de MainWindow registran a nivel ERROR
los RedmineError, RedmineValidationError, RedmineConnectionError y las
excepciones inesperadas, con contexto de operación (spec diagnostico-aplicacion
R3 y manejo-errores-api R4). También cubre el WARNING de delete_attachment (8.7).
"""

import logging
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QDialog

from app.main_window import MainWindow
from app.services.redmine_client import (
    RedmineError, RedmineValidationError, RedmineConnectionError,
    RedmineClient,
)


@pytest.fixture
def main_window(qapp):
    """MainWindow con setup mockeado y _redmine simulado (patrón del repo)."""
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


def _accepted_dialog(**overrides):
    """Diálogo de tarea aceptado con valores por defecto."""
    dlg = MagicMock()
    dlg.exec.return_value = QDialog.DialogCode.Accepted
    dlg.project_id = 5
    dlg.subject = "Test"
    dlg.description = ""
    dlg.tracker_id = 1
    dlg.priority_id = 2
    dlg.category_id = 0
    dlg.assigned_to_id = 0
    dlg.start_date = ""
    dlg.due_date = ""
    dlg.due_enabled = False
    dlg.done_ratio = 0
    dlg.upload_tokens = []
    dlg.pending_checklist_items = []
    for key, value in overrides.items():
        setattr(dlg, key, value)
    return dlg


def _setup_carga_issues(w):
    """Prepara el MainWindow para _cargar_issues (patrón TestCargarIssuesSaneadoYErrores)."""
    w._status_indicator = MagicMock()
    w._update_task_table_context = MagicMock()
    w._project_full_names = {}
    w._filter_bar.selected_project_ids = []
    w._filter_bar.selected_status = "open"
    w._filter_bar.selected_priority = 0
    w._filter_bar.selected_category = 0
    w._filter_bar.selected_date_from = None
    w._filter_bar.selected_date_to = None
    w._filter_bar.selected_assigned_to = []
    return w


class TestLogCargaIssues:
    """R3: un RedmineError en la carga de issues se registra a nivel ERROR."""

    def test_redmine_error_en_carga_registra_error(self, main_window, caplog):
        w = _setup_carga_issues(main_window)
        w._redmine.get_issues.side_effect = RedmineError("boom")

        with (
            patch("app.main_window.QMessageBox"),
            caplog.at_level(logging.ERROR, logger="app.main_window"),
        ):
            MainWindow._cargar_issues(w)

        assert any(
            r.levelno == logging.ERROR and "cargar issues" in r.getMessage()
            for r in caplog.records
        )


class TestLogNuevaTarea:
    """R3/R4: errores de validación, red y excepciones inesperadas en el alta."""

    def test_validation_error_en_alta_registra_error(self, main_window, caplog):
        mock_dlg = _accepted_dialog()
        main_window._redmine.create_issue.side_effect = RedmineValidationError(
            "Error", ["Asunto no puede estar vacío"]
        )

        with (
            patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td,
            patch("app.main_window.QMessageBox"),
            caplog.at_level(logging.ERROR, logger="app.main_window"),
        ):
            mock_td.DialogCode = QDialog.DialogCode
            main_window._nueva_tarea()

        assert any(
            r.levelno == logging.ERROR and "Validación" in r.getMessage()
            for r in caplog.records
        )

    def test_connection_error_en_alta_registra_error(self, main_window, caplog):
        mock_dlg = _accepted_dialog()
        main_window._redmine.create_issue.side_effect = RedmineConnectionError("sin red")

        with (
            patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td,
            patch("app.main_window.QMessageBox"),
            caplog.at_level(logging.ERROR, logger="app.main_window"),
        ):
            mock_td.DialogCode = QDialog.DialogCode
            main_window._nueva_tarea()

        assert any(
            r.levelno == logging.ERROR and "red" in r.getMessage().lower()
            for r in caplog.records
        )

    def test_excepcion_inesperada_en_alta_registra_error(self, main_window, caplog):
        mock_dlg = _accepted_dialog()
        main_window._redmine.create_issue.side_effect = RuntimeError("boom")

        with (
            patch("app.main_window.TaskDialog", return_value=mock_dlg) as mock_td,
            patch("app.main_window.QMessageBox"),
            caplog.at_level(logging.ERROR, logger="app.main_window"),
        ):
            mock_td.DialogCode = QDialog.DialogCode
            main_window._nueva_tarea()

        assert any(
            r.levelno == logging.ERROR and "inesperado" in r.getMessage()
            for r in caplog.records
        )


class TestLogDeleteAttachment:
    """8.7: delete_attachment registra un WARNING cuando no puede eliminar."""

    def test_delete_attachment_registra_warning_al_fallar(self, caplog):
        client = RedmineClient("https://redmine.example.com", "token")
        client._delete = MagicMock(side_effect=RedmineError("404"))

        with caplog.at_level(logging.WARNING, logger="app.services.redmine_client"):
            result = client.delete_attachment(11)

        assert result is False
        assert any(
            r.levelno == logging.WARNING and "adjunto" in r.getMessage()
            for r in caplog.records
        )