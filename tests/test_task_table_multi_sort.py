"""Tests de ordenación múltiple y orden semántico de prioridad en TaskTable
(cambio nombre-completo-proyecto-y-doble-ordenacion, Fase B).

Cubren: dos criterios simultáneos (primario + secundario), reglas de
interacción del clic en cabecera, estabilidad, preservación tras set_issues,
indicadores internos del encabezado y orden semántico de la columna Prioridad.
"""

import pytest
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QImage, QPainter

from app.widgets.task_table import TaskTable, MultiSortHeaderView

ASC = Qt.SortOrder.AscendingOrder
DESC = Qt.SortOrder.DescendingOrder

# Catálogo de Redmine: Baja, Normal, Alta, Urgente, Inmediata (de menor a mayor)
REDMINE_PRIORITIES = [
    (1, "Baja"),
    (2, "Normal"),
    (3, "Alta"),
    (4, "Urgente"),
    (5, "Inmediata"),
]


def _make_issue(issue_id, subject=None, priority="Normal", priority_id=None,
                status="Nueva", **extra):
    """Construye un dict de issue con todos los campos que consume TaskTable."""
    return {
        "id": issue_id,
        "subject": subject if subject is not None else f"Tarea {issue_id}",
        "due_date": extra.get("due_date", ""),
        "start_date": extra.get("start_date", ""),
        "status_name": status,
        "assigned_to_name": extra.get("assigned_to_name", ""),
        "done_ratio": extra.get("done_ratio", 0),
        "project_id": extra.get("project_id", 1),
        "project_name": extra.get("project_name", "Proyecto"),
        "author_name": "",
        "tracker_name": extra.get("tracker_name", "Bug"),
        "priority_name": priority,
        "priority_id": priority_id,
        "category_name": extra.get("category_name", ""),
        "url": f"https://redmine.example.com/issues/{issue_id}",
        "description": "",
        "created_on": extra.get("created_on", ""),
        "updated_on": extra.get("updated_on", ""),
    }


def _row_ids(table):
    """Devuelve la lista de ids de issue en el orden visual de las filas."""
    return [
        int(table.item(r, table.COL_ID).data(Qt.ItemDataRole.DisplayRole))
        for r in range(table.rowCount())
    ]


class TestMultiSortTwoCriteria:
    """7.1 Ordenación por dos criterios: el secundario desempata dentro del primario."""

    def test_secondary_sorts_within_primary(self, qapp):
        table = TaskTable()
        table.set_priorities(REDMINE_PRIORITIES)
        table.set_issues([
            _make_issue(1, priority="Baja", priority_id=1, status="Nueva"),
            _make_issue(2, priority="Inmediata", priority_id=5, status="Nueva"),
            _make_issue(3, priority="Alta", priority_id=3, status="Cerrada"),
            _make_issue(4, priority="Urgente", priority_id=4, status="Cerrada"),
            _make_issue(5, priority="Normal", priority_id=2, status="En curso"),
        ])

        # Prioridad primaria y, tras el clic en Estado, Estado pasa a primario
        # y Prioridad a secundario (regla D5).
        table._on_header_clicked(table.COL_PRIORITY)
        table._on_header_clicked(table.COL_STATUS)

        header = table.horizontalHeader()
        assert header.sort_keys == [
            (table.COL_STATUS, ASC),
            (table.COL_PRIORITY, ASC),
        ]

        # Estados alfabéticos: Cerrada, En curso, Nueva.
        # Dentro de cada estado, prioridad de mayor a menor (rango asc):
        #   Cerrada: Urgente(4), Alta(3); En curso: Normal(5); Nueva: Inmediata(2), Baja(1)
        assert _row_ids(table) == [4, 3, 5, 2, 1]

    def test_primary_desc_secondary_asc(self, qapp):
        table = TaskTable()
        table.set_priorities(REDMINE_PRIORITIES)
        table.set_issues([
            _make_issue(1, priority="Baja", priority_id=1, status="Nueva"),
            _make_issue(2, priority="Inmediata", priority_id=5, status="Nueva"),
            _make_issue(3, priority="Alta", priority_id=3, status="Cerrada"),
            _make_issue(4, priority="Urgente", priority_id=4, status="Cerrada"),
        ])

        table._on_header_clicked(table.COL_PRIORITY)  # Prioridad asc
        table._on_header_clicked(table.COL_STATUS)    # Estado primario asc + Prioridad sec
        table._on_header_clicked(table.COL_STATUS)    # Estado -> desc

        header = table.horizontalHeader()
        assert header.sort_keys == [
            (table.COL_STATUS, DESC),
            (table.COL_PRIORITY, ASC),
        ]

        # Estados desc: Nueva, Cerrada. Dentro de cada uno, prioridad asc.
        assert _row_ids(table) == [2, 1, 4, 3]


class TestHeaderClickRules:
    """7.1 Reglas de interacción del clic en la cabecera."""

    def test_first_click_sets_primary_ascending(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(1)])
        table._on_header_clicked(table.COL_STATUS)
        assert table.horizontalHeader().sort_keys == [(table.COL_STATUS, ASC)]

    def test_second_click_on_other_column_adds_secondary(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(1)])
        table._on_header_clicked(table.COL_STATUS)
        table._on_header_clicked(table.COL_PRIORITY)
        # D5: la columna nueva pasa a primario y la anterior a secundario
        assert table.horizontalHeader().sort_keys == [
            (table.COL_PRIORITY, ASC),
            (table.COL_STATUS, ASC),
        ]

    def test_click_on_primary_toggles_direction_keeps_secondary(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(1)])
        table._on_header_clicked(table.COL_STATUS)
        table._on_header_clicked(table.COL_PRIORITY)
        table._on_header_clicked(table.COL_PRIORITY)
        assert table.horizontalHeader().sort_keys == [
            (table.COL_PRIORITY, DESC),
            (table.COL_STATUS, ASC),
        ]

    def test_click_on_secondary_promotes_it_and_demotes_primary(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(1)])
        table._on_header_clicked(table.COL_STATUS)      # Estado asc
        table._on_header_clicked(table.COL_PRIORITY)    # Prioridad primario asc
        table._on_header_clicked(table.COL_PRIORITY)    # Prioridad -> desc
        table._on_header_clicked(table.COL_STATUS)      # Estado (secundario) -> primario
        assert table.horizontalHeader().sort_keys == [
            (table.COL_STATUS, ASC),
            (table.COL_PRIORITY, DESC),
        ]

    def test_click_on_third_column_reorders(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(1)])
        table._on_header_clicked(table.COL_STATUS)
        table._on_header_clicked(table.COL_PRIORITY)
        table._on_header_clicked(table.COL_ASSIGNED_TO)
        assert table.horizontalHeader().sort_keys == [
            (table.COL_ASSIGNED_TO, ASC),
            (table.COL_PRIORITY, ASC),
        ]

    def test_click_on_url_is_ignored(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(1)])
        table._on_header_clicked(table.COL_STATUS)
        table._on_header_clicked(table.COL_URL)
        assert table.horizontalHeader().sort_keys == [(table.COL_STATUS, ASC)]


class TestSortStability:
    """7.1 La ordenación es estable: empates conservan el orden relativo previo."""

    def test_equal_keys_keep_insertion_order(self, qapp):
        table = TaskTable()
        table.set_priorities(REDMINE_PRIORITIES)
        table.set_issues([
            _make_issue(1, priority="Normal", priority_id=2, status="Nueva"),
            _make_issue(2, priority="Normal", priority_id=2, status="Nueva"),
            _make_issue(3, priority="Normal", priority_id=2, status="Nueva"),
        ])
        table._on_header_clicked(table.COL_STATUS)
        table._on_header_clicked(table.COL_PRIORITY)
        # Mismo estado y misma prioridad: se conserva el orden de inserción
        assert _row_ids(table) == [1, 2, 3]


class TestSortPreservationAfterSetIssues:
    """7.1 set_issues preserva los dos criterios y sus direcciones."""

    def test_two_criteria_preserved_after_reload(self, qapp):
        table = TaskTable()
        table.set_priorities(REDMINE_PRIORITIES)
        table.set_issues([
            _make_issue(1, priority="Baja", priority_id=1, status="Nueva"),
            _make_issue(2, priority="Inmediata", priority_id=5, status="Nueva"),
            _make_issue(3, priority="Alta", priority_id=3, status="Cerrada"),
            _make_issue(4, priority="Urgente", priority_id=4, status="Cerrada"),
        ])
        table._on_header_clicked(table.COL_PRIORITY)  # Prioridad primaria
        table._on_header_clicked(table.COL_STATUS)    # Estado primario + Prioridad secundaria
        table.set_issues([
            _make_issue(1, priority="Baja", priority_id=1, status="Nueva"),
            _make_issue(2, priority="Inmediata", priority_id=5, status="Nueva"),
            _make_issue(3, priority="Alta", priority_id=3, status="Cerrada"),
            _make_issue(4, priority="Urgente", priority_id=4, status="Cerrada"),
        ])

        header = table.horizontalHeader()
        assert header.sort_keys == [
            (table.COL_STATUS, ASC),
            (table.COL_PRIORITY, ASC),
        ]
        assert _row_ids(table) == [4, 3, 2, 1]

    def test_sort_indicator_synced_after_reload(self, qapp):
        table = TaskTable()
        table.sortItems(table.COL_ID, ASC)
        header = table.horizontalHeader()
        section = header.sortIndicatorSection()
        order = header.sortIndicatorOrder()
        table.set_issues([_make_issue(3), _make_issue(1), _make_issue(2)])
        assert header.sortIndicatorSection() == section
        assert header.sortIndicatorOrder() == order
        assert _row_ids(table) == [1, 2, 3]


class TestSortIndicators:
    """7.1 Indicadores: estado interno sort_keys y renderizado sin excepción."""

    def test_header_is_multisort(self, qapp):
        table = TaskTable()
        assert isinstance(table.horizontalHeader(), MultiSortHeaderView)

    def test_sort_keys_empty_by_default(self, qapp):
        table = TaskTable()
        assert table.horizontalHeader().sort_keys == []

    def test_set_sort_keys_updates_state(self, qapp):
        table = TaskTable()
        header = table.horizontalHeader()
        header.set_sort_keys([(table.COL_STATUS, ASC), (table.COL_PRIORITY, DESC)])
        assert header.sort_keys == [
            (table.COL_STATUS, ASC),
            (table.COL_PRIORITY, DESC),
        ]

    def test_paint_section_renders_without_error(self, qapp):
        table = TaskTable()
        table.set_issues([_make_issue(1)])
        table._on_header_clicked(table.COL_STATUS)
        table._on_header_clicked(table.COL_PRIORITY)
        header = table.horizontalHeader()

        img = QImage(800, 40, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.white)
        painter = QPainter(img)
        try:
            # Primario, secundario y una columna sin criterio
            header.paintSection(painter, QRect(0, 0, 120, 40), table.COL_STATUS)
            header.paintSection(painter, QRect(0, 0, 120, 40), table.COL_PRIORITY)
            header.paintSection(painter, QRect(0, 0, 120, 40), table.COL_TITLE)
        finally:
            painter.end()


class TestPrioritySemanticOrder:
    """7.2 La columna Prioridad ordena por el orden semántico de Redmine."""

    def test_first_click_orders_high_to_low(self, qapp):
        table = TaskTable()
        table.set_priorities(REDMINE_PRIORITIES)
        table.set_issues([
            _make_issue(1, priority="Baja", priority_id=1),
            _make_issue(2, priority="Normal", priority_id=2),
            _make_issue(3, priority="Alta", priority_id=3),
            _make_issue(4, priority="Urgente", priority_id=4),
            _make_issue(5, priority="Inmediata", priority_id=5),
        ])
        table._on_header_clicked(table.COL_PRIORITY)

        priorities = [
            table.item(r, table.COL_PRIORITY).text()
            for r in range(table.rowCount())
        ]
        assert priorities == ["Inmediata", "Urgente", "Alta", "Normal", "Baja"]

    def test_second_click_reverses_order(self, qapp):
        table = TaskTable()
        table.set_priorities(REDMINE_PRIORITIES)
        table.set_issues([
            _make_issue(1, priority="Baja", priority_id=1),
            _make_issue(2, priority="Normal", priority_id=2),
            _make_issue(3, priority="Alta", priority_id=3),
            _make_issue(4, priority="Urgente", priority_id=4),
            _make_issue(5, priority="Inmediata", priority_id=5),
        ])
        table._on_header_clicked(table.COL_PRIORITY)
        table._on_header_clicked(table.COL_PRIORITY)

        priorities = [
            table.item(r, table.COL_PRIORITY).text()
            for r in range(table.rowCount())
        ]
        assert priorities == ["Baja", "Normal", "Alta", "Urgente", "Inmediata"]

    def test_not_alphabetic(self, qapp):
        table = TaskTable()
        table.set_issues([
            _make_issue(1, priority="Alta"),
            _make_issue(2, priority="Inmediata"),
            _make_issue(3, priority="Normal"),
        ])
        table._on_header_clicked(table.COL_PRIORITY)

        priorities = [
            table.item(r, table.COL_PRIORITY).text()
            for r in range(table.rowCount())
        ]
        # No alfabético (Alta, Inmediata, Normal) sino semántico
        assert priorities == ["Inmediata", "Alta", "Normal"]

    def test_uses_redmine_catalog(self, qapp):
        table = TaskTable()
        table.set_priorities(REDMINE_PRIORITIES)
        table.set_issues([
            _make_issue(1, priority="Baja", priority_id=1),
            _make_issue(2, priority="Inmediata", priority_id=5),
            _make_issue(3, priority="Alta", priority_id=3),
        ])
        table._on_header_clicked(table.COL_PRIORITY)
        # La última del catálogo (Inmediata) es la de mayor rango
        assert _row_ids(table) == [2, 3, 1]

    def test_priority_rank_role_stored(self, qapp):
        table = TaskTable()
        table.set_priorities(REDMINE_PRIORITIES)
        table.set_issues([
            _make_issue(1, priority="Baja", priority_id=1),
            _make_issue(2, priority="Inmediata", priority_id=5),
        ])
        ranks = {
            table._issue_id_at_row(r): table.item(r, table.COL_PRIORITY).data(
                TaskTable.PRIORITY_RANK_ROLE
            )
            for r in range(table.rowCount())
        }
        assert ranks[1] == 4  # Baja: última del catálogo invertido
        assert ranks[2] == 0  # Inmediata: mayor prioridad


class TestSortAllColumns:
    """W5: ordenación por todas las columnas restantes (Asc y Desc).

    Fechas (ISO) y fecha/hora (ISO) se ordenan cronológicamente por su string
    ISO; los campos de texto se ordenan alfabéticamente case-insensitive.
    """

    # (columna, campo de la issue, valores en orden de inserción no ordenado)
    COLUMN_CASES = [
        (TaskTable.COL_START_DATE, "start_date",
         ["2026-01-10", "2026-01-02", "2026-01-15"]),
        (TaskTable.COL_DUE_DATE, "due_date",
         ["2026-03-01", "2026-02-01", "2026-04-01"]),
        (TaskTable.COL_TRACKER, "tracker_name",
         ["Bug", "Feature", "Soporte"]),
        (TaskTable.COL_STATUS, "status_name",
         ["Nueva", "Cerrada", "En curso"]),
        (TaskTable.COL_ASSIGNED_TO, "assigned_to_name",
         ["Ana", "Luis", "Bea"]),
        (TaskTable.COL_CATEGORY, "category_name",
         ["Zeta", "Alfa", "Beta"]),
        (TaskTable.COL_CREATED, "created_on",
         ["2026-01-01T10:00:00Z", "2025-12-01T10:00:00Z", "2026-02-01T10:00:00Z"]),
        (TaskTable.COL_UPDATED, "updated_on",
         ["2026-05-01T10:00:00Z", "2026-04-01T10:00:00Z", "2026-06-01T10:00:00Z"]),
    ]

    @staticmethod
    def _issue_for_field(iid, field, value):
        if field == "status_name":
            return _make_issue(iid, status=value)
        return _make_issue(iid, **{field: value})

    @pytest.mark.parametrize("order", [ASC, DESC])
    @pytest.mark.parametrize("col,field,values", COLUMN_CASES)
    def test_sort_column(self, qapp, col, field, values, order):
        table = TaskTable()
        table.set_issues([
            self._issue_for_field(1, field, values[0]),
            self._issue_for_field(2, field, values[1]),
            self._issue_for_field(3, field, values[2]),
        ])

        table.sortItems(col, order)

        keyed = sorted(
            zip([1, 2, 3], values), key=lambda t: str(t[1]).casefold()
        )
        expected = [iid for iid, _ in keyed]
        if order == DESC:
            expected = list(reversed(expected))
        assert _row_ids(table) == expected

    def test_sort_url_is_ignored(self, qapp):
        """La columna URL no es ordenable: sortItems no cambia el orden."""
        table = TaskTable()
        table.set_issues([_make_issue(2), _make_issue(1)])
        table.sortItems(table.COL_URL, ASC)
        assert table.horizontalHeader().sort_keys == []
        assert _row_ids(table) == [2, 1]


class TestSortTriangleSpecs:
    """W8: el helper sort_triangle_specs expone color y orientación de forma determinista."""

    @staticmethod
    def _table_with_keys(qapp, keys):
        table = TaskTable()
        table.set_issues([_make_issue(1)])
        table.horizontalHeader().set_sort_keys(keys)
        return table

    def test_primary_ascending_color_and_tip_up(self, qapp):
        table = self._table_with_keys(qapp, [(TaskTable.COL_STATUS, ASC)])
        header = table.horizontalHeader()
        rect = QRect(0, 0, 120, 40)
        specs = header.sort_triangle_specs(rect, TaskTable.COL_STATUS)

        assert len(specs) == 1
        points, color, ascending = specs[0]
        assert color == MultiSortHeaderView.COLOR_PRIMARY
        assert color.name() == "#2e7d32"
        assert ascending is True
        # Punta arriba: el vértice superior (y mínimo) es único y menor que la base
        ys = [p.y() for p in points]
        assert ys.count(min(ys)) == 1
        assert min(ys) < max(ys)

    def test_secondary_uses_secondary_color(self, qapp):
        table = self._table_with_keys(
            qapp, [(TaskTable.COL_STATUS, ASC), (TaskTable.COL_PRIORITY, ASC)]
        )
        header = table.horizontalHeader()
        rect = QRect(0, 0, 120, 40)
        specs = header.sort_triangle_specs(rect, TaskTable.COL_PRIORITY)

        assert len(specs) == 1
        _points, color, _ascending = specs[0]
        assert color == MultiSortHeaderView.COLOR_SECONDARY
        assert color.name() == "#81c784"

    def test_descending_tip_down(self, qapp):
        table = self._table_with_keys(qapp, [(TaskTable.COL_STATUS, DESC)])
        header = table.horizontalHeader()
        rect = QRect(0, 0, 120, 40)
        specs = header.sort_triangle_specs(rect, TaskTable.COL_STATUS)

        assert len(specs) == 1
        points, _color, ascending = specs[0]
        assert ascending is False
        # Punta abajo: el vértice inferior (y máximo) es único y mayor que la base
        ys = [p.y() for p in points]
        assert ys.count(max(ys)) == 1
        assert max(ys) > min(ys)

    def test_polygons_inside_section_rect(self, qapp):
        table = self._table_with_keys(
            qapp, [(TaskTable.COL_STATUS, ASC), (TaskTable.COL_PRIORITY, DESC)]
        )
        header = table.horizontalHeader()
        rect = QRect(0, 0, 120, 40)
        for col in (TaskTable.COL_STATUS, TaskTable.COL_PRIORITY):
            for points, _color, _asc in header.sort_triangle_specs(rect, col):
                assert len(points) == 3
                for p in points:
                    assert rect.contains(p), f"punto {p} fuera de {rect}"

    def test_no_specs_for_unsorted_column(self, qapp):
        table = self._table_with_keys(qapp, [(TaskTable.COL_STATUS, ASC)])
        header = table.horizontalHeader()
        rect = QRect(0, 0, 120, 40)
        assert header.sort_triangle_specs(rect, TaskTable.COL_TITLE) == []