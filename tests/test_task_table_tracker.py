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
        assert table.COL_TITLE == 2
        assert table.COL_START_DATE == 3
        assert table.COL_DUE_DATE == 4
        assert table.COL_STATUS == 5
        assert table.COL_ASSIGNED_TO == 6
        assert table.COL_PROGRESS == 7
        assert table.COL_URL == 8
