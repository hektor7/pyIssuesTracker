"""Tests para _populate_members en TaskDialog."""

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QDialog

from app.dialogs.task_dialog import TaskDialog


class TestPopulateMembers:
    """Tests para el orden de miembros en TaskDialog._populate_members."""

    @pytest.fixture
    def dialog(self, qapp):
        """Crea un TaskDialog con current_user_id=2."""
        dlg = TaskDialog(current_user_id=2)
        return dlg

    def test_current_user_first(self, dialog):
        """El usuario actual debe aparecer primero en la lista (después de 'Sin asignar')."""
        members = [(1, "Alice"), (2, "Bob"), (3, "Charlie")]
        dialog._populate_members(members)
        # Índice 0 = "(Sin asignar)", Índice 1 = usuario actual
        assert dialog._assigned_combo.itemText(0) == "(Sin asignar)"
        assert dialog._assigned_combo.itemText(1) == "Bob"

    def test_other_members_sorted_alphabetically(self, dialog):
        """Los demás miembros deben ordenarse alfabéticamente."""
        members = [(1, "Charlie"), (2, "Bob"), (3, "Alice")]
        dialog._populate_members(members)
        # Índice 0 = "(Sin asignar)", Índice 1 = Bob (actual), resto alfabético
        assert dialog._assigned_combo.itemText(0) == "(Sin asignar)"
        assert dialog._assigned_combo.itemText(1) == "Bob"
        assert dialog._assigned_combo.itemText(2) == "Alice"
        assert dialog._assigned_combo.itemText(3) == "Charlie"

    def test_current_user_not_in_members(self, dialog):
        """Si el usuario actual no está en miembros, solo orden alfabético."""
        members = [(1, "Charlie"), (5, "Alice")]
        dialog._populate_members(members)
        assert dialog._assigned_combo.itemText(0) == "(Sin asignar)"
        assert dialog._assigned_combo.itemText(1) == "Alice"
        assert dialog._assigned_combo.itemText(2) == "Charlie"

    def test_empty_members_list(self, dialog):
        """Lista vacía de miembros solo muestra '(Sin asignar)'."""
        dialog._populate_members([])
        assert dialog._assigned_combo.count() == 1
        assert dialog._assigned_combo.itemText(0) == "(Sin asignar)"

    def test_no_current_user_id(self, qapp):
        """Sin current_user_id, todos los miembros en orden alfabético."""
        dlg = TaskDialog(current_user_id=None)
        members = [(1, "Charlie"), (2, "Alice"), (3, "Bob")]
        dlg._populate_members(members)
        assert dlg._assigned_combo.itemText(0) == "(Sin asignar)"
        assert dlg._assigned_combo.itemText(1) == "Alice"
        assert dlg._assigned_combo.itemText(2) == "Bob"
        assert dlg._assigned_combo.itemText(3) == "Charlie"
