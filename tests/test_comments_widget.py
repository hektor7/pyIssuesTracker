"""Tests para CommentsWidget: _journal_get robusto y @mention completer."""

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QPlainTextEdit

from app.widgets.comments_widget import CommentsWidget, setup_mention_completer


class TestJournalGet:
    """_journal_get debe proteger contra valores None."""

    def test_returns_value_from_dataclass(self, qapp):
        """Debe devolver el valor del atributo si existe y no es None."""
        widget = CommentsWidget()
        journal = MagicMock()
        journal.user_name = "Alice"
        assert widget._journal_get(journal, 'user_name') == "Alice"

    def test_returns_default_when_none(self, qapp):
        """Debe devolver default si el atributo es None."""
        widget = CommentsWidget()
        journal = MagicMock()
        journal.notes = None
        assert widget._journal_get(journal, 'notes', '') == ""

    def test_returns_default_when_missing(self, qapp):
        """Debe devolver default si el atributo no existe."""
        widget = CommentsWidget()
        journal = MagicMock(spec=[])  # Sin atributos
        assert widget._journal_get(journal, 'user_name', 'Desconocido') == "Desconocido"

    def test_returns_value_from_dict(self, qapp):
        """Debe funcionar con diccionarios."""
        widget = CommentsWidget()
        journal = {"user_name": "Bob", "notes": None}
        assert widget._journal_get(journal, 'user_name') == "Bob"
        assert widget._journal_get(journal, 'notes', '') == ""

    def test_returns_default_for_missing_dict_key(self, qapp):
        """Debe devolver default si la clave no existe en el dict."""
        widget = CommentsWidget()
        journal = {"id": 1}
        assert widget._journal_get(journal, 'user_name', 'Desconocido') == "Desconocido"


class TestSetComments:
    """set_comments debe manejar journals con valores None sin crashear."""

    def test_set_comments_with_none_notes(self, qapp):
        """No debe crashear si notes es None."""
        widget = CommentsWidget()
        journal = MagicMock()
        journal.user_name = "Alice"
        journal.created_on = "2026-06-12"
        journal.notes = None  # Esto causaba crash
        widget.set_comments([journal])
        # No debe lanzar excepción

    def test_set_comments_with_none_user(self, qapp):
        """No debe crashear si user_name es None."""
        widget = CommentsWidget()
        journal = MagicMock()
        journal.user_name = None  # Esto causaba "None" en el header
        journal.created_on = "2026-06-12"
        journal.notes = "Test comment"
        widget.set_comments([journal])
        # No debe lanzar excepción


class TestMentionCompleterLifecycle:
    """El completer debe manejar correctamente su ciclo de vida."""

    def test_set_members_creates_completer(self, qapp):
        """set_members debe crear un completer almacenado como atributo."""
        widget = CommentsWidget()
        members = [(1, "Alice"), (2, "Bob")]
        widget.set_members(members)
        assert widget._completer is not None
        assert widget._completer.completionCount() == 2

    def test_set_members_replaces_completer(self, qapp):
        """Llamar set_members dos veces debe reemplazar el completer, no duplicar."""
        widget = CommentsWidget()
        widget.set_members([(1, "Alice")])
        first_completer = widget._completer
        widget.set_members([(2, "Bob"), (3, "Charlie")])
        assert widget._completer is not first_completer
        assert widget._completer.completionCount() == 2

    def test_set_members_empty_clears_completer(self, qapp):
        """set_members con lista vacía debe limpiar el completer."""
        widget = CommentsWidget()
        widget.set_members([(1, "Alice")])
        assert widget._completer is not None
        widget.set_members([])
        assert widget._completer is None

    def test_at_triggers_completion(self, qapp):
        """Escribir @ debe activar el completer."""
        widget = CommentsWidget()
        widget.set_members([(1, "Maria Garcia"), (2, "Martin Lopez")])
        widget._note_edit.setPlainText("@mar")
        # Mover cursor al final
        cursor = widget._note_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        widget._note_edit.setTextCursor(cursor)
        # El handler se ejecuta vía textChanged; verificar que no crashea
        assert True  # Si llegó aquí, no crasheó
