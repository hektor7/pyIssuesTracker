import pytest

from app.dialogs.complete_dialog import CompleteDialog


class TestCompleteDialog:
    @pytest.fixture
    def dialog(self, qapp):
        return CompleteDialog(issue_id=42)

    def test_notes_property_empty_by_default(self, dialog):
        """La propiedad notes debe devolver cadena vacía por defecto."""
        assert dialog.notes == ""

    def test_notes_property_with_text(self, dialog):
        """La propiedad notes debe devolver el texto introducido."""
        dialog._notes_edit.setPlainText("  mi comentario  ")
        assert dialog.notes == "mi comentario"
