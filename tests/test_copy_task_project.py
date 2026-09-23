"""Tests del modo copia de TaskDialog (BLOQUE 6).

Verifican que en modo copia el diálogo es de alta con datos precargados, que los
adjuntos del origen se muestran como propuesta y que el botón "−" NUNCA borra en
el servidor, mientras que el modo edición normal mantiene el borrado remoto.
"""

from unittest.mock import MagicMock

from PyQt6.QtWidgets import QMessageBox, QPushButton

from app.dialogs.task_dialog import TaskDialog
from app.main_window import MainWindow


def _make_attachment(att_id, filename):
    return {
        "id": att_id,
        "filename": filename,
        "filesize": 100,
        "created_on": "2026-01-01",
        "content_url": f"https://redmine.example.com/attachments/download/{att_id}",
    }


def _delete_button_for(dialog, attachment_id) -> QPushButton:
    """Localiza el botón '−' del frame de un adjunto por su attachment_id."""
    for i in range(dialog._attachments_layout.count()):
        widget = dialog._attachments_layout.itemAt(i).widget()
        if widget and widget.property("attachment_id") == attachment_id:
            for btn in widget.findChildren(QPushButton):
                if btn.text() == "−":
                    return btn
    raise AssertionError(f"No se encontró el botón '−' del adjunto {attachment_id}")


class TestCopyModeSetup:
    def test_copy_mode_is_creation_with_prefilled_fields(self, qapp):
        dlg = TaskDialog(
            projects=[(5, "Destino")],
            default_project_id=5,
            redmine_client=MagicMock(),
            copy_from_issue_id=42,
            copy_subject="Revisar despliegue",
            copy_description="Tarea creada partiendo de la tarea #42",
        )

        assert dlg._copy_mode is True
        assert dlg._is_edit is False
        assert dlg.windowTitle() == "Nueva tarea"
        assert dlg.project_id == 5
        assert dlg.subject == "Revisar despliegue"
        assert dlg.description == "Tarea creada partiendo de la tarea #42"

    def test_description_raw_preserves_leading_trailing_spaces(self, qapp):
        """R4: description_raw devuelve el texto crudo sin strip (flujo de copia)."""
        dlg = TaskDialog(
            redmine_client=MagicMock(),
            copy_from_issue_id=42,
            copy_description="  texto con espacios  ",
        )

        assert dlg.description_raw == "  texto con espacios  "
        # description (resto de flujos) mantiene el strip para no romper nada
        assert dlg.description == "texto con espacios"

    def test_non_copy_dialog_not_in_copy_mode(self, qapp):
        dlg = TaskDialog()
        assert dlg._copy_mode is False

    def test_proposed_attachments_shown(self, qapp):
        attachments = [_make_attachment(11, "a.txt"), _make_attachment(22, "b.txt")]
        dlg = TaskDialog(
            redmine_client=MagicMock(),
            copy_from_issue_id=42,
            copy_attachments=attachments,
        )

        assert [a["id"] for a in dlg.proposed_attachments] == [11, 22]
        assert dlg._attachments_group.isVisible() or not dlg.isVisible()
        # Hay un frame por adjunto propuesto
        assert dlg._attachments_layout.count() == 2


class TestCopyModeRemoveProposalIsNonDestructive:
    def test_remove_proposed_attachment_does_not_delete_on_server(self, qapp):
        redmine = MagicMock()
        attachments = [_make_attachment(11, "a.txt"), _make_attachment(22, "b.txt")]
        dlg = TaskDialog(
            redmine_client=redmine,
            copy_from_issue_id=42,
            copy_attachments=attachments,
        )

        dlg._on_remove_proposed_attachment(11)

        assert [a["id"] for a in dlg.proposed_attachments] == [22]
        redmine.delete_attachment.assert_not_called()

    def test_minus_button_in_copy_mode_removes_from_proposal_only(self, qapp):
        redmine = MagicMock()
        attachments = [_make_attachment(11, "a.txt"), _make_attachment(22, "b.txt")]
        dlg = TaskDialog(
            redmine_client=redmine,
            copy_from_issue_id=42,
            copy_attachments=attachments,
        )

        _delete_button_for(dlg, 11).click()

        assert [a["id"] for a in dlg.proposed_attachments] == [22]
        redmine.delete_attachment.assert_not_called()

    def test_remove_proposed_attachment_with_id_zero_does_not_wipe_proposal(self, qapp):
        """S3: un id 0 (improbable) no debe eliminar toda la propuesta."""
        redmine = MagicMock()
        attachments = [
            {"id": 0, "filename": "a.txt", "content_url": "https://redmine.example.com/attachments/download/0"},
            _make_attachment(22, "b.txt"),
        ]
        dlg = TaskDialog(
            redmine_client=redmine,
            copy_from_issue_id=42,
            copy_attachments=attachments,
        )

        dlg._on_remove_proposed_attachment(0)

        assert [a["id"] for a in dlg.proposed_attachments] == [0, 22]
        redmine.delete_attachment.assert_not_called()


class TestCopyModeMissingDestinationAttributes:
    """El modo copia no falla si el destino no tiene tracker/prioridad/categoría."""

    def test_copy_dialog_survives_missing_attributes(self, qapp):
        """Sin categorías/miembros/campos en el destino, el diálogo se construye igual."""
        redmine = MagicMock()
        redmine.get_project_issue_categories.return_value = []
        redmine.get_project_memberships.return_value = []
        redmine.get_project_custom_fields.return_value = []

        dlg = TaskDialog(
            projects=[(5, "Destino")],
            default_project_id=5,
            redmine_client=redmine,
            copy_from_issue_id=42,
            copy_subject="Origen",
            copy_description="Tarea creada partiendo de la tarea #42",
        )

        # El diálogo se construye sin fallar y con valores por defecto válidos
        assert dlg.project_id == 5
        assert dlg.tracker_id == 1
        assert dlg.priority_id == 2
        assert dlg.category_id == 0
        assert dlg.custom_fields == {}

    def test_copy_dialog_survives_loading_errors(self, qapp):
        """Si la carga de categorías/miembros/campos del destino falla, no rompe el diálogo."""
        redmine = MagicMock()
        redmine.get_project_issue_categories.side_effect = RuntimeError("API caída")
        redmine.get_project_memberships.side_effect = RuntimeError("API caída")
        redmine.get_project_custom_fields.side_effect = RuntimeError("API caída")

        dlg = TaskDialog(
            projects=[(5, "Destino")],
            default_project_id=5,
            redmine_client=redmine,
            copy_from_issue_id=42,
            copy_subject="Origen",
            copy_description="Tarea creada partiendo de la tarea #42",
        )

        assert dlg.project_id == 5
        assert dlg.category_id == 0
        assert dlg.custom_fields == {}


class TestEditModeStillDeletesOnServer:
    def test_minus_button_in_edit_mode_calls_delete_attachment(self, qapp, monkeypatch):
        redmine = MagicMock()
        redmine.delete_attachment.return_value = True
        monkeypatch.setattr(
            QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes
        )
        task_data = {
            "id": 7,
            "project_id": 1,
            "tracker_id": 1,
            "priority_id": 2,
            "status_id": 1,
            "subject": "Existente",
            "description": "",
            "attachments": [_make_attachment(11, "a.txt")],
        }
        dlg = TaskDialog(redmine_client=redmine, task_data=task_data)

        _delete_button_for(dlg, 11).click()

        redmine.delete_attachment.assert_called_once_with(11)


class TestComposeCopiedDescription:
    """La descripción copiada cita el origen en blockquote (D2 / tarea 7.1)."""

    def test_multiline_description_quotes_each_line(self):
        result = MainWindow._compose_copied_description(42, "linea1\nlinea2")

        assert result == (
            "Tarea creada partiendo de la tarea #42\n\n"
            "> linea1\n> linea2"
        )

    def test_empty_description_only_header(self):
        result = MainWindow._compose_copied_description(42, "")

        assert result == "Tarea creada partiendo de la tarea #42"

    def test_blank_description_only_header(self):
        result = MainWindow._compose_copied_description(7, "   \n  ")

        assert result == "Tarea creada partiendo de la tarea #7"
