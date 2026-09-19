"""Tests para la columna Tracker en TaskTable."""

import pytest
from app.widgets.task_table import TaskTable


class TestTaskTableTrackerColumn:
    """Tests para la columna 'Tracker' en TaskTable."""

    def test_tracker_column_constant(self, qapp):
        """COL_TRACKER debe ser 1."""
        table = TaskTable()
        assert table.COL_TRACKER == 1

    def test_tracker_column_header(self, qapp):
        """La cabecera de COL_TRACKER debe ser 'Tracker'."""
        table = TaskTable()
        assert table.HEADERS[table.COL_TRACKER] == "Tracker"

    def test_tracker_column_shows_data(self, qapp):
        """La columna Tracker debe mostrar el tracker_name del issue."""
        table = TaskTable()
        issues = [
            {"id": 1, "subject": "Test", "due_date": "",
             "start_date": "", "status_name": "", "assigned_to_name": "",
             "done_ratio": 0, "project_id": 1, "project_name": "",
             "author_name": "", "tracker_name": "Bug", "priority_name": "",
             "url": "", "description": ""},
        ]
        table.set_issues(issues)
        item = table.item(0, table.COL_TRACKER)
        assert item is not None
        assert item.text() == "Bug"

    def test_tracker_column_empty_when_no_tracker(self, qapp):
        """Sin tracker_name, la celda debe estar vacía."""
        table = TaskTable()
        issues = [
            {"id": 1, "subject": "Test", "due_date": "",
             "start_date": "", "status_name": "", "assigned_to_name": "",
             "done_ratio": 0, "project_id": 1, "project_name": "",
             "author_name": "", "tracker_name": "", "priority_name": "",
             "url": "", "description": ""},
        ]
        table.set_issues(issues)
        item = table.item(0, table.COL_TRACKER)
        assert item is not None
        assert item.text() == ""

    def test_column_order(self, qapp):
        """Verificar orden correcto de todas las columnas."""
        table = TaskTable()
        assert table.COL_ID == 0
        assert table.COL_TRACKER == 1
        assert table.COL_PROJECT == 2
        assert table.COL_TITLE == 3
        assert table.COL_START_DATE == 4
        assert table.COL_DUE_DATE == 5
        assert table.COL_PRIORITY == 6
        assert table.COL_STATUS == 7
        assert table.COL_ASSIGNED_TO == 8
        assert table.COL_CATEGORY == 9
        assert table.COL_PROGRESS == 10
        assert table.COL_URL == 11
        assert table.COL_CREATED == 12
        assert table.COL_UPDATED == 13

    def test_new_columns_hidden_by_default(self, qapp):
        """Proyecto, Prioridad y Categoría deben estar ocultas por defecto."""
        table = TaskTable()
        assert table.isColumnHidden(table.COL_PROJECT)
        assert table.isColumnHidden(table.COL_PRIORITY)
        assert table.isColumnHidden(table.COL_CATEGORY)

    def test_project_column_shows_data(self, qapp):
        """La columna Proyecto debe mostrar el project_name del issue."""
        table = TaskTable()
        issues = [
            {"id": 1, "subject": "Test", "due_date": "", "start_date": "",
             "status_name": "", "assigned_to_name": "", "done_ratio": 0,
             "project_id": 1, "project_name": "Proyecto A", "author_name": "",
             "tracker_name": "", "priority_name": "", "category_name": "",
             "url": "", "description": ""},
        ]
        table.set_issues(issues)
        item = table.item(0, table.COL_PROJECT)
        assert item is not None
        assert item.text() == "Proyecto A"

    def test_category_column_shows_data(self, qapp):
        """La columna Categoría debe mostrar el category_name del issue."""
        table = TaskTable()
        issues = [
            {"id": 1, "subject": "Test", "due_date": "", "start_date": "",
             "status_name": "", "assigned_to_name": "", "done_ratio": 0,
             "project_id": 1, "project_name": "", "author_name": "",
             "tracker_name": "", "priority_name": "", "category_name": "Bugs",
             "url": "", "description": ""},
        ]
        table.set_issues(issues)
        item = table.item(0, table.COL_CATEGORY)
        assert item is not None
        assert item.text() == "Bugs"


class TestColumnVisibility:
    """Comportamiento de mostrar/ocultar columnas en TaskTable."""

    def test_default_visible_keys_exclude_hidden(self, qapp):
        table = TaskTable()
        keys = table.visible_column_keys()
        assert "project" not in keys
        assert "priority" not in keys
        assert "category" not in keys
        assert "id" in keys
        assert "title" in keys

    def test_apply_visible_column_keys(self, qapp):
        table = TaskTable()
        table.apply_visible_column_keys(["id", "project", "title"])
        assert not table.isColumnHidden(table.COL_ID)
        assert not table.isColumnHidden(table.COL_PROJECT)
        assert not table.isColumnHidden(table.COL_TITLE)
        assert table.isColumnHidden(table.COL_STATUS)

    def test_apply_empty_keeps_nothing_visible(self, qapp):
        table = TaskTable()
        table.apply_visible_column_keys([])
        assert table.isColumnHidden(table.COL_ID)

    def test_toggle_column_emits_signal(self, qapp):
        table = TaskTable()
        emitted = []
        table.columnas_cambiadas.connect(lambda: emitted.append(True))
        table._toggle_column(table.COL_PROJECT, True)
        assert emitted
        assert not table.isColumnHidden(table.COL_PROJECT)

    def test_menu_labels(self, qapp):
        """La URL debe tener etiqueta legible y el resto la cabecera."""
        table = TaskTable()
        assert table._column_label(table.COL_URL) == "Abrir en Redmine"
        assert table._column_label(table.COL_TITLE) == "Título"
