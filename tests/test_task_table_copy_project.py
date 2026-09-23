"""Tests de la acción "Mover a otro proyecto" del menú contextual (BLOQUE 5).

Cubren la presencia de la acción en la rama genérica y la emisión de
`tarea_mover_proyecto` con el id de la tarea mostrada en la fila (resuelto por
rol, no por índice).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMenu

from app.widgets.task_table import TaskTable


def _make_issue(issue_id, subject=None):
    return {
        "id": issue_id,
        "subject": subject if subject is not None else f"Tarea {issue_id}",
        "due_date": "",
        "start_date": "",
        "status_name": "Nueva",
        "assigned_to_name": "",
        "done_ratio": 0,
        "project_id": 1,
        "project_name": "Proyecto",
        "author_name": "",
        "tracker_name": "Bug",
        "priority_name": "Normal",
        "category_name": "",
        "url": f"https://redmine.example.com/issues/{issue_id}",
        "description": "",
        "created_on": "",
        "updated_on": "",
    }


def _open_generic_menu(table, issue_id, monkeypatch):
    """Abre el menú contextual genérico de la fila de `issue_id` sin bloquear.

    Devuelve el QMenu capturado para inspeccionar/triggerear sus acciones.
    """
    captured = {}

    def fake_exec(self, *args, **kwargs):
        captured["menu"] = self
        return None

    monkeypatch.setattr(QMenu, "exec", fake_exec)

    row = table._row_for_issue_id(issue_id)
    assert row is not None
    monkeypatch.setattr(table, "rowAt", lambda y, r=row: r)
    monkeypatch.setattr(table, "columnAt", lambda x: table.COL_TITLE)

    table._show_context_menu(table.viewport().rect().center())
    return captured["menu"]


class TestMoveToAnotherProjectAction:
    def test_generic_menu_contains_move_action(self, qapp, monkeypatch):
        table = TaskTable()
        table.set_issues([_make_issue(3), _make_issue(1), _make_issue(2)])

        menu = _open_generic_menu(table, 3, monkeypatch)
        texts = [a.text() for a in menu.actions()]

        assert "Copiar URL" in texts
        assert "Mover a otro proyecto..." in texts
        assert "Abrir en Redmine" in texts
        # La acción de mover va tras el separador y antes de "Abrir en Redmine"
        assert texts.index("Mover a otro proyecto...") < texts.index("Abrir en Redmine")

    def test_move_action_emits_issue_id_of_row(self, qapp, monkeypatch):
        table = TaskTable()
        # Orden ascendente: la fila 0 es la issue 1, no la 3 insertada primero
        table.sortItems(table.COL_ID, Qt.SortOrder.AscendingOrder)
        table.set_issues([_make_issue(3), _make_issue(1), _make_issue(2)])

        emitted = []
        table.tarea_mover_proyecto.connect(lambda iid: emitted.append(iid))

        menu = _open_generic_menu(table, 3, monkeypatch)
        action = next(a for a in menu.actions() if a.text() == "Mover a otro proyecto...")
        action.trigger()

        # Se emite el id de la tarea de la fila (3), no el índice de inserción
        assert emitted == [3]


class TestContextMenuOutsideRow:
    """Un clic derecho fuera de cualquier fila no debe mostrar menú contextual."""

    def test_right_click_outside_row_shows_no_menu(self, qapp, monkeypatch):
        table = TaskTable()
        table.set_issues([_make_issue(3)])

        executed = []

        def fake_exec(self, *args, **kwargs):
            executed.append(self)
            return None

        monkeypatch.setattr(QMenu, "exec", fake_exec)
        # rowAt devuelve -1: el clic cae fuera de las filas de la tabla
        monkeypatch.setattr(table, "rowAt", lambda y: -1)
        monkeypatch.setattr(table, "columnAt", lambda x: table.COL_TITLE)

        table._show_context_menu(table.viewport().rect().center())

        assert executed == []
