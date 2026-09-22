"""Tests de integridad de renderizado de TaskTable (cambio corregir-renderizado-tabla-tareas).

Cubren la coherencia de filas bajo ordenación, la resolución de la tarea por ID,
la preservación de la ordenación activa, la barra de progreso mediante delegate
y el resaltado uniforme de prioridad.
"""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from app.widgets.task_table import TaskTable, ProgressBarDelegate


RED_INMEDIATA = QColor(200, 0, 0)
RED_URGENTE = QColor(180, 20, 20)
WHITE = QColor(255, 255, 255)


def _make_issue(issue_id, subject=None, priority="Normal", done_ratio=0,
                project_name="Proyecto", url=None, **extra):
    """Construye un dict de issue con todos los campos que consume TaskTable."""
    return {
        "id": issue_id,
        "subject": subject if subject is not None else f"Tarea {issue_id}",
        "due_date": extra.get("due_date", ""),
        "start_date": extra.get("start_date", ""),
        "status_name": extra.get("status_name", "Nueva"),
        "assigned_to_name": extra.get("assigned_to_name", ""),
        "done_ratio": done_ratio,
        "project_id": extra.get("project_id", 1),
        "project_name": project_name,
        "author_name": "",
        "tracker_name": extra.get("tracker_name", "Bug"),
        "priority_name": priority,
        "category_name": extra.get("category_name", ""),
        "url": url if url is not None else f"https://redmine.example.com/issues/{issue_id}",
        "description": "",
        "created_on": extra.get("created_on", ""),
        "updated_on": extra.get("updated_on", ""),
    }


class TestRowIntegrity:
    """1.1 Cada fila contiene datos coherentes de una única issue."""

    def test_rows_are_coherent_with_active_sort(self, qapp):
        table = TaskTable()
        issues = [
            _make_issue(3, subject="Charlie", priority="Baja"),
            _make_issue(1, subject="Alpha", priority="Alta"),
            _make_issue(2, subject="Bravo", priority="Normal"),
        ]
        table.sortItems(table.COL_ID, Qt.SortOrder.AscendingOrder)
        table.set_issues(issues)

        by_id = {i["id"]: i for i in issues}
        assert table.rowCount() == len(issues)
        ids = []
        for row in range(table.rowCount()):
            iid = int(table.item(row, table.COL_ID).data(Qt.ItemDataRole.DisplayRole))
            ids.append(iid)
            issue = by_id[iid]
            # La misma fila debe llevar título y prioridad de esa issue
            assert table.item(row, table.COL_TITLE).text() == issue["subject"]
            assert table.item(row, table.COL_PRIORITY).text() == issue["priority_name"]
        assert ids == sorted(ids)

    def test_reload_keeps_rows_coherent(self, qapp):
        table = TaskTable()
        table.sortItems(table.COL_ID, Qt.SortOrder.DescendingOrder)
        issues = [
            _make_issue(1, subject="Uno"),
            _make_issue(2, subject="Dos"),
            _make_issue(3, subject="Tres"),
        ]
        table.set_issues(issues)
        # Recargar (refresco) con la ordenación activa
        table.set_issues(issues)

        by_id = {i["id"]: i for i in issues}
        ids = []
        for row in range(table.rowCount()):
            iid = int(table.item(row, table.COL_ID).data(Qt.ItemDataRole.DisplayRole))
            ids.append(iid)
            assert table.item(row, table.COL_TITLE).text() == by_id[iid]["subject"]
        assert ids == sorted(ids, reverse=True)


class TestIssueResolutionById:
    """1.2 _issue_at_row resuelve la issue mostrada, no la de self._issues[row]."""

    def test_issue_at_row_matches_visible_row_not_insertion_index(self, qapp):
        table = TaskTable()
        issues = [_make_issue(3), _make_issue(1), _make_issue(2)]
        table.sortItems(table.COL_ID, Qt.SortOrder.AscendingOrder)
        table.set_issues(issues)

        for row in range(table.rowCount()):
            visible_id = int(
                table.item(row, table.COL_ID).data(Qt.ItemDataRole.DisplayRole)
            )
            assert table._issue_at_row(row)["id"] == visible_id
            assert table._issue_id_at_row(row) == visible_id

        # La fila ordenada 0 (id=1) no coincide con la inserción self._issues[0] (id=3)
        assert table._issue_at_row(0)["id"] == 1
        assert table._issues[0]["id"] == 3


class TestSortPreservation:
    """1.3 set_issues preserva la ordenación activa y no mezcla durante el poblado."""

    def test_set_issues_preserves_active_sort_indicator(self, qapp):
        table = TaskTable()
        table.sortItems(table.COL_ID, Qt.SortOrder.AscendingOrder)
        header = table.horizontalHeader()
        section = header.sortIndicatorSection()
        order = header.sortIndicatorOrder()

        table.set_issues([_make_issue(3), _make_issue(1), _make_issue(2)])

        assert header.sortIndicatorSection() == section
        assert header.sortIndicatorOrder() == order
        ids = [
            int(table.item(r, table.COL_ID).data(Qt.ItemDataRole.DisplayRole))
            for r in range(table.rowCount())
        ]
        assert ids == sorted(ids)

    def test_set_issues_does_not_corrupt_sorted_rows(self, qapp):
        table = TaskTable()
        table.sortItems(table.COL_TITLE, Qt.SortOrder.DescendingOrder)
        table.set_issues([
            _make_issue(10, subject="AAA"),
            _make_issue(20, subject="CCC"),
            _make_issue(30, subject="BBB"),
        ])
        titles = [table.item(r, table.COL_TITLE).text() for r in range(table.rowCount())]
        assert titles == sorted(titles, reverse=True)
        ids = [
            int(table.item(r, table.COL_ID).data(Qt.ItemDataRole.DisplayRole))
            for r in range(table.rowCount())
        ]
        assert ids == [20, 30, 10]


class TestProgressDelegate:
    """1.4 La columna Progreso usa delegate y entero en DisplayRole."""

    def test_progress_column_has_no_cell_widget(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(1, done_ratio=50), _make_issue(2, done_ratio=100)])
        for row in range(table.rowCount()):
            assert table.cellWidget(row, table.COL_PROGRESS) is None

    def test_progress_item_stores_integer_display_role(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(1, done_ratio=50), _make_issue(2, done_ratio=100)])
        values = []
        for row in range(table.rowCount()):
            item = table.item(row, table.COL_PROGRESS)
            assert item is not None
            value = item.data(Qt.ItemDataRole.DisplayRole)
            assert isinstance(value, int)
            values.append(value)
        assert sorted(values) == [50, 100]

    def test_progress_delegate_registered(self, qapp):
        table = TaskTable()
        delegate = table.itemDelegateForColumn(table.COL_PROGRESS)
        assert isinstance(delegate, ProgressBarDelegate)

    def test_progress_column_sorts_numerically(self, qapp):
        table = TaskTable()
        table.sortItems(table.COL_PROGRESS, Qt.SortOrder.AscendingOrder)
        table.set_issues([
            _make_issue(1, done_ratio=100),
            _make_issue(2, done_ratio=0),
            _make_issue(3, done_ratio=50),
        ])
        values = [
            table.item(r, table.COL_PROGRESS).data(Qt.ItemDataRole.DisplayRole)
            for r in range(table.rowCount())
        ]
        assert values == [0, 50, 100]


class TestPriorityHighlight:
    """1.5 Resaltado rojo en todas las celdas visibles, tras ordenar y recargar."""

    def _row_of(self, table, issue_id):
        for row in range(table.rowCount()):
            if table._issue_id_at_row(row) == issue_id:
                return row
        raise AssertionError(f"No se encontró la fila de la issue {issue_id}")

    def _assert_full_highlight(self, table, issue_id, expected_bg):
        row = self._row_of(table, issue_id)
        for col in range(table.columnCount()):
            if table.isColumnHidden(col):
                continue
            item = table.item(row, col)
            assert item is not None, f"fila {row}, columna {col} sin item"
            assert item.background().color() == expected_bg, (
                f"fila {row}, columna {col}: "
                f"{item.background().color().name()} != {expected_bg.name()}"
            )
            assert item.foreground().color() == WHITE, f"fila {row}, columna {col}"

    def test_highlight_covers_all_visible_cells_after_sort_and_reload(self, qapp):
        table = TaskTable()
        # Hacer visibles todas las columnas para cubrir Progreso y URL
        for col in range(table.columnCount()):
            table.setColumnHidden(col, False)

        issues = [
            _make_issue(1, subject="Normal", priority="Normal"),
            _make_issue(2, subject="Inmediata", priority="Inmediata"),
            _make_issue(3, subject="Urgente", priority="Urgente"),
        ]
        table.sortItems(table.COL_TITLE, Qt.SortOrder.AscendingOrder)
        table.set_issues(issues)

        self._assert_full_highlight(table, 2, RED_INMEDIATA)
        self._assert_full_highlight(table, 3, RED_URGENTE)

        # Segunda recarga: el resaltado debe seguir a la tarea
        table.set_issues(issues)
        self._assert_full_highlight(table, 2, RED_INMEDIATA)
        self._assert_full_highlight(table, 3, RED_URGENTE)

    def test_non_priority_rows_not_highlighted(self, qapp):
        table = TaskTable()
        issues = [_make_issue(1, priority="Normal")]
        table.set_issues(issues)
        row = self._row_of(table, 1)
        for col in range(table.columnCount()):
            if table.isColumnHidden(col):
                continue
            item = table.item(row, col)
            assert item.background().color() != RED_INMEDIATA
            assert item.background().color() != RED_URGENTE


class TestReloadResidues:
    """1.6 Recargar con menos issues no deja filas ni widgets residuales."""

    def test_reload_with_fewer_issues_leaves_no_residue(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(i) for i in range(1, 6)])
        assert table.rowCount() == 5

        table.set_issues([_make_issue(10), _make_issue(11)])
        assert table.rowCount() == 2
        assert len(table._issues) == 2

        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                assert table.cellWidget(row, col) is None
                assert table.item(row, col) is not None

        # No quedan items fuera del nuevo rango
        assert table.item(2, table.COL_ID) is None


class TestUrlCell:
    """5.1/5.2 Celda URL como item, abre URL en clic y no en doble clic."""

    def test_url_cell_is_item_with_tooltip(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(1)])
        item = table.item(0, table.COL_URL)
        assert item is not None
        assert item.toolTip() == "Abrir en Redmine"
        assert table.cellWidget(0, table.COL_URL) is None

    def test_click_url_emits_signal(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(7)])
        emitted = []
        table.tarea_abrir_url.connect(lambda iid, url: emitted.append((iid, url)))
        table._on_cell_clicked(0, table.COL_URL)
        assert emitted == [(7, "https://redmine.example.com/issues/7")]

    def test_click_non_url_does_not_emit(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(7)])
        emitted = []
        table.tarea_abrir_url.connect(lambda iid, url: emitted.append((iid, url)))
        table._on_cell_clicked(0, table.COL_TITLE)
        assert emitted == []

    def test_double_click_url_does_not_open_task_dialog(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(7)])
        emitted = []
        table.tarea_doble_click.connect(lambda iid: emitted.append(iid))
        table._on_double_click(0, table.COL_URL)
        assert emitted == []
