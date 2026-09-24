"""Tests del nombre completo de proyecto en el listado y el tooltip (W1).

Cubre que dos issues de proyectos homónimos (mismo nombre de hoja bajo
distintos padres) muestran cada una su nombre completo en la columna
Proyecto y en el tooltip del título, sin confundirse entre sí.
"""

from PyQt6.QtCore import Qt

from app.widgets.task_table import TaskTable


def _make_issue(issue_id, project_name, subject=None, **extra):
    """Construye un dict de issue con los campos que consume TaskTable."""
    return {
        "id": issue_id,
        "subject": subject if subject is not None else f"Tarea {issue_id}",
        "due_date": extra.get("due_date", ""),
        "start_date": extra.get("start_date", ""),
        "status_name": extra.get("status_name", "Nueva"),
        "assigned_to_name": extra.get("assigned_to_name", ""),
        "done_ratio": extra.get("done_ratio", 0),
        "project_id": extra.get("project_id", issue_id),
        "project_name": project_name,
        "author_name": "",
        "tracker_name": extra.get("tracker_name", "Bug"),
        "priority_name": extra.get("priority_name", "Normal"),
        "priority_id": extra.get("priority_id", 2),
        "category_name": extra.get("category_name", ""),
        "url": f"https://redmine.example.com/issues/{issue_id}",
        "description": "",
        "created_on": extra.get("created_on", ""),
        "updated_on": extra.get("updated_on", ""),
    }


class TestProjectNameHomonyms:
    """W1: dos proyectos homónimos se distinguen por su nombre completo."""

    def test_project_column_shows_full_name_per_row(self, qapp):
        table = TaskTable()
        table.set_issues([
            _make_issue(1, "Proyecto padre 1 > Soporte"),
            _make_issue(2, "Proyecto padre 2 > Soporte"),
        ])

        # Cada fila muestra el nombre completo de SU proyecto
        assert table.item(0, table.COL_PROJECT).text() == "Proyecto padre 1 > Soporte"
        assert table.item(1, table.COL_PROJECT).text() == "Proyecto padre 2 > Soporte"

    def test_title_tooltip_contains_full_project_name_per_row(self, qapp):
        table = TaskTable()
        table.set_issues([
            _make_issue(1, "Proyecto padre 1 > Soporte", subject="Incidente A"),
            _make_issue(2, "Proyecto padre 2 > Soporte", subject="Incidente B"),
        ])

        tooltip_1 = table.item(0, table.COL_TITLE).toolTip()
        tooltip_2 = table.item(1, table.COL_TITLE).toolTip()

        # El tooltip de cada fila contiene el nombre completo de su proyecto
        assert "Proyecto padre 1 > Soporte" in tooltip_1
        assert "Proyecto padre 2 > Soporte" in tooltip_2
        # Y no el del otro (se distinguen ambos)
        assert "Proyecto padre 2 > Soporte" not in tooltip_1
        assert "Proyecto padre 1 > Soporte" not in tooltip_2

    def test_full_names_survive_sorting(self, qapp):
        """Tras ordenar, cada fila conserva el nombre completo de su proyecto."""
        table = TaskTable()
        table.set_issues([
            _make_issue(1, "Proyecto padre 1 > Soporte"),
            _make_issue(2, "Proyecto padre 2 > Soporte"),
        ])
        table.sortItems(table.COL_ID, Qt.SortOrder.DescendingOrder)

        by_id = {
            table._issue_id_at_row(r): table.item(r, table.COL_PROJECT).text()
            for r in range(table.rowCount())
        }
        assert by_id[1] == "Proyecto padre 1 > Soporte"
        assert by_id[2] == "Proyecto padre 2 > Soporte"