import pytest

from app.dialogs.assign_dialog import AssignDialog


class TestAssignDialog:
    @pytest.fixture
    def dialog(self, qapp):
        members = [(1, "Alice"), (2, "Bob"), (3, "Charlie")]
        return AssignDialog(issue_id=42, members=members, current_user_id=2)

    def test_notes_property_empty_by_default(self, dialog):
        """La propiedad notes debe devolver cadena vacía por defecto."""
        assert dialog.notes == ""

    def test_notes_property_with_text(self, dialog):
        """La propiedad notes debe devolver el texto introducido."""
        dialog._notes_edit.setPlainText("  mi comentario  ")
        assert dialog.notes == "mi comentario"

    def test_selected_user_id_returns_current_when_self_checked(self, dialog):
        """selected_user_id debe devolver current_user_id cuando 'Asignarme a mí' está marcado."""
        dialog._assign_self_cb.setChecked(True)
        assert dialog.selected_user_id == 2

    def test_selected_user_id_returns_selected_when_self_unchecked(self, dialog):
        """selected_user_id debe devolver el usuario seleccionado en el combo."""
        dialog._assign_self_cb.setChecked(False)
        dialog._user_combo.setCurrentIndex(0)  # Alice
        assert dialog.selected_user_id == 1

    def test_user_combo_disabled_when_self_checked(self, dialog):
        """El combo de usuarios debe estar deshabilitado cuando 'Asignarme a mí' está marcado."""
        dialog._assign_self_cb.setChecked(True)
        assert not dialog._user_combo.isEnabled()

    def test_user_combo_enabled_when_self_unchecked(self, dialog):
        """El combo de usuarios debe estar habilitado cuando 'Asignarme a mí' está desmarcado."""
        dialog._assign_self_cb.setChecked(False)
        assert dialog._user_combo.isEnabled()

    def test_user_combo_has_all_members(self, dialog):
        """El combo debe contener todos los miembros."""
        assert dialog._user_combo.count() == 3

    def test_user_combo_marks_current_user(self, dialog):
        """El usuario actual debe aparecer con '(yo)'."""
        items = [dialog._user_combo.itemText(i) for i in range(dialog._user_combo.count())]
        assert "Bob (yo)" in items
