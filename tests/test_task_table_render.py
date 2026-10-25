"""Tests de integridad de renderizado de TaskTable (cambio corregir-renderizado-tabla-tareas).

Cubren la coherencia de filas bajo ordenación, la resolución de la tarea por ID,
la preservación de la ordenación activa, la barra de progreso mediante delegate
y el resaltado uniforme de prioridad.
"""

import pytest
from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import (
    QBrush, QColor, QImage, QPainter, QPalette, QStandardItem, QStandardItemModel,
)
from PyQt6.QtWidgets import QStyleOptionViewItem

from app.widgets.task_table import TaskTable, ProgressBarDelegate


BG_INMEDIATA = QColor(139, 0, 0)
BG_URGENTE = QColor(200, 0, 0)
BG_ALTA = QColor(198, 81, 0)
WHITE = QColor(255, 255, 255)
BLACK = QColor(0, 0, 0)

TEXT_DARK = QColor("#333333")
TRACK_WHITE = QColor("#ffffff")
CHUNK_EMPTY = QColor("#bdbdbd")
CHUNK_PRIORITY = QColor("#ff9800")
CHUNK_PARTIAL = QColor("#f57c00")
CHUNK_DONE = QColor("#2e7d32")

CELL_WIDTH = 120
CELL_HEIGHT = 28
BAR_RECT = QRect(4, 5, CELL_WIDTH - 8, CELL_HEIGHT - 10)


def _relative_luminance(color: QColor) -> float:
    """Luminancia relativa WCAG de un color sRGB (0.0 = negro, 1.0 = blanco)."""
    def _channel(value: int) -> float:
        c = value / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    return (
        0.2126 * _channel(color.red())
        + 0.7152 * _channel(color.green())
        + 0.0722 * _channel(color.blue())
    )


def _contrast_ratio(a: QColor, b: QColor) -> float:
    """Ratio de contraste WCAG entre dos colores (1.0:1 a 21.0:1)."""
    lum_a = _relative_luminance(a)
    lum_b = _relative_luminance(b)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def _make_progress_index(done_ratio: int, priority_bg: QColor | None = None):
    """Devuelve (modelo, índice) con DisplayRole y BackgroundRole del delegate.

    El modelo se devuelve para mantenerlo vivo: un QModelIndex no es dueño de su
    modelo y quedaría inválido en cuanto saliera de ámbito.
    """
    model = QStandardItemModel()
    item = QStandardItem()
    item.setData(int(done_ratio), Qt.ItemDataRole.DisplayRole)
    if priority_bg is not None:
        item.setBackground(QBrush(priority_bg))
    model.appendRow(item)
    return model, model.index(0, 0)


def _render_progress(index, text_palette: QColor) -> QImage:
    """Pinta ProgressBarDelegate sobre un QImage aislado y devuelve la imagen.

    Se prefiere a `viewport().grab()` porque no muta el tema global de la app (que
    contaminaría otros tests), no depende del tamaño de la tabla ni de
    `visualRect`, y reproduce de forma determinista el bug de tema oscuro:
    `QPalette.Text` blanco sobre la pista blanca del delegate.
    """
    image = QImage(CELL_WIDTH, CELL_HEIGHT, QImage.Format.Format_RGB32)
    image.fill(QColor("#ffffff"))
    painter = QPainter(image)
    option = QStyleOptionViewItem()
    option.rect = QRect(0, 0, CELL_WIDTH, CELL_HEIGHT)
    option.palette = QPalette()
    option.palette.setColor(QPalette.ColorRole.Text, text_palette)
    option.palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    option.backgroundBrush = QBrush(QColor("#ffffff"))
    ProgressBarDelegate().paint(painter, option, index)
    painter.end()
    return image


def _count_color(image: QImage, rect: QRect, expected: QColor, tolerance: int = 12) -> int:
    """Cuenta píxeles de `rect` dentro de ±tolerance por canal respecto a expected.

    Comparar con tolerancia y umbral (no igualdad en coordenadas fijas) evita
    que el antialiasing o el DPI rompan el test.
    """
    count = 0
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            color = image.pixelColor(x, y)
            if (
                abs(color.red() - expected.red()) <= tolerance
                and abs(color.green() - expected.green()) <= tolerance
                and abs(color.blue() - expected.blue()) <= tolerance
            ):
                count += 1
    return count


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


class TestProgressBarInPriorityRows:
    """barra-progreso: pista blanca y chunk naranja en filas resaltadas.

    Renderiza la tabla a un QImage en modo offscreen y muestrea píxeles del
    rectángulo real de la celda de progreso (`visualRect`), sin coordenadas
    hardcodeadas. `visualRect` funciona en offscreen: devuelve coordenadas
    relativas al viewport, por eso se captura `table.viewport().grab()`.
    """

    TRACK_WHITE = (255, 255, 255)
    CHUNK_PRIORITY = (255, 152, 0)
    CHUNK_EMPTY = (189, 189, 189)

    @staticmethod
    def _render(table, qapp):
        table.resize(900, 200)
        table.show()
        qapp.processEvents()
        return table.viewport().grab().toImage()

    @staticmethod
    def _progress_bar_rect(table, row=0):
        cell = table.visualRect(table.model().index(row, table.COL_PROGRESS))
        assert cell.isValid(), "visualRect no devolvió un rectángulo válido en offscreen"
        assert cell.width() > 20 and cell.height() > 10, cell
        # Mismo ajuste interno que aplica ProgressBarDelegate.paint
        return cell.adjusted(4, 5, -4, -5)

    @staticmethod
    def _rgb(image, x, y):
        color = image.pixelColor(int(x), int(y))
        return (color.red(), color.green(), color.blue())

    @pytest.mark.parametrize(
        ("priority", "done_ratio", "expected_track", "expected_chunk"),
        [
            ("Urgente", 30, (255, 255, 255), (255, 152, 0)),
            ("Inmediata", 30, (255, 255, 255), (255, 152, 0)),
            ("Alta", 30, (255, 255, 255), (255, 152, 0)),
            ("Alta", 0, (255, 255, 255), None),
        ],
    )
    def test_track_and_chunk_use_priority_palette(
        self, qapp, priority, done_ratio, expected_track, expected_chunk
    ):
        table = TaskTable()
        table.set_issues([_make_issue(1, priority=priority, done_ratio=done_ratio)])
        image = self._render(table, qapp)
        bar = self._progress_bar_rect(table)
        y = bar.center().y()

        # Pista: al 75 % del ancho queda fuera del chunk (30 %) y del texto centrado
        track_x = bar.x() + int(bar.width() * 0.75)
        assert self._rgb(image, track_x, y) == expected_track

        left_x = bar.x() + max(3, int(bar.width() * 0.10))
        if expected_chunk is not None:
            # Chunk: dentro del tramo relleno pintado con CHUNK_PRIORITY
            assert self._rgb(image, left_x, y) == expected_chunk
        else:
            # Sin chunk: la pista es blanca, no el gris CHUNK_EMPTY de "vacía"
            assert self._rgb(image, left_x, y) == expected_track
            assert self._rgb(image, left_x, y) != self.CHUNK_EMPTY
            # Se muestrea por encima del glifo central: con el texto ya visible,
            # el píxel justo del centro puede ser antialiasing del porcentaje.
            upper = self._rgb(image, bar.center().x(), bar.y() + 2)
            assert upper == expected_track
            assert upper != self.CHUNK_EMPTY

        table.close()

    @pytest.mark.parametrize("priority", ["Urgente", "Inmediata", "Alta"])
    def test_painted_percentage_text_contrasts_in_priority_rows(self, qapp, priority):
        """Valida el color realmente pintado, no el rol foreground del item.

        `item.foreground()` sigue siendo blanco por el resaltado de prioridad,
        pero eso no prueba legibilidad: el texto se dibuja sobre la pista blanca.
        """
        priority_bg = {"Urgente": BG_URGENTE, "Inmediata": BG_INMEDIATA, "Alta": BG_ALTA}[priority]
        model, index = _make_progress_index(30, priority_bg)
        image = _render_progress(index, text_palette=BLACK)
        assert _count_color(image, BAR_RECT, TEXT_DARK) >= 5
        del model


class TestProgressTextLegibility:
    """Legibilidad del porcentaje según el relleno real (contraste WCAG).

    El color del texto debe elegirse por contraste contra el relleno subyacente,
    no por prioridad ni por `QPalette.Text`. Los tests de render pintan el
    delegate directamente sobre un QImage para aislar el caso.
    """

    @pytest.mark.parametrize(
        ("fill", "expected"),
        [
            ("#ffffff", "#333333"),
            ("#bdbdbd", "#333333"),
            ("#ff9800", "#333333"),
            ("#f57c00", "#333333"),
            ("#2e7d32", "#ffffff"),
        ],
    )
    def test_text_color_for_fill_table(self, qapp, fill, expected):
        color = ProgressBarDelegate._text_color_for(QColor(fill))
        assert color.name().lower() == expected

    def test_relative_luminance_extremes_and_known_value(self, qapp):
        assert ProgressBarDelegate._relative_luminance(QColor("#ffffff")) == pytest.approx(1.0)
        assert ProgressBarDelegate._relative_luminance(QColor("#000000")) == pytest.approx(0.0)
        assert ProgressBarDelegate._relative_luminance(QColor("#8b0000")) == pytest.approx(
            0.0549, abs=0.002
        )

    def test_dark_theme_normal_row_renders_dark_percentage(self, qapp):
        """Tema oscuro (Text blanco), prioridad Normal, 30 %: el texto debe ser oscuro."""
        model, index = _make_progress_index(30, None)
        image = _render_progress(index, text_palette=WHITE)
        assert _count_color(image, BAR_RECT, TEXT_DARK) >= 5
        del model

    @pytest.mark.parametrize("priority", ["Alta", "Urgente", "Inmediata"])
    def test_priority_rows_render_dark_percentage_on_light_track(self, qapp, priority):
        """Tema claro, filas con prioridad y 30 %: texto oscuro sobre la pista."""
        priority_bg = {"Alta": BG_ALTA, "Urgente": BG_URGENTE, "Inmediata": BG_INMEDIATA}[priority]
        model, index = _make_progress_index(30, priority_bg)
        image = _render_progress(index, text_palette=BLACK)
        assert _count_color(image, BAR_RECT, TEXT_DARK) >= 5
        del model

    def test_full_progress_renders_white_percentage_over_green_chunk(self, qapp):
        """Al 100 % el texto cae sobre el tramo verde y debe ser blanco.

        Se usa tema claro (Text negro) para que la implementación antigua pinte
        el texto oscuro y el test falle en rojo.
        """
        model, index = _make_progress_index(100, None)
        image = _render_progress(index, text_palette=BLACK)
        # Interior del tramo relleno, evitando el borde y la pista exterior
        chunk_inner = QRect(
            BAR_RECT.x() + 3,
            BAR_RECT.y() + 2,
            BAR_RECT.width() - 6,
            BAR_RECT.height() - 4,
        )
        assert _count_color(image, chunk_inner, WHITE) >= 5
        del model

    @pytest.mark.parametrize("theme", ["claro", "oscuro"])
    @pytest.mark.parametrize("priority", ["Alta", "Urgente", "Inmediata", "Normal", "Baja"])
    @pytest.mark.parametrize("done_ratio", [0, 30, 100])
    def test_text_color_never_matches_its_fill(self, qapp, theme, priority, done_ratio):
        """Invariante: el color elegido siempre contrasta ≥ 4.5:1 con su relleno."""
        priority_bg = {
            "Alta": BG_ALTA,
            "Urgente": BG_URGENTE,
            "Inmediata": BG_INMEDIATA,
        }.get(priority)

        track_color = TRACK_WHITE if (priority_bg is not None or done_ratio > 0) else CHUNK_EMPTY
        fills = [track_color]
        if done_ratio > 0:
            if priority_bg is not None:
                fills.append(CHUNK_PRIORITY)
            elif done_ratio == 100:
                fills.append(CHUNK_DONE)
            else:
                fills.append(CHUNK_PARTIAL)

        for fill in fills:
            text_color = ProgressBarDelegate._text_color_for(fill)
            assert _contrast_ratio(text_color, fill) >= 4.5, (
                f"tema={theme} prioridad={priority} done_ratio={done_ratio} "
                f"relleno={fill.name()} texto={text_color.name()}"
            )


class TestPriorityHighlight:
    """1.5 Resaltado rojo en todas las celdas visibles, tras ordenar y recargar."""

    def _row_of(self, table, issue_id):
        for row in range(table.rowCount()):
            if table._issue_id_at_row(row) == issue_id:
                return row
        raise AssertionError(f"No se encontró la fila de la issue {issue_id}")

    def _row_bg(self, table, issue_id):
        """Fondo aplicado a la fila de una issue (columna Título, siempre visible)."""
        row = self._row_of(table, issue_id)
        return table.item(row, table.COL_TITLE).background().color()

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
            _make_issue(4, subject="Alta", priority="Alta"),
        ]
        table.sortItems(table.COL_TITLE, Qt.SortOrder.AscendingOrder)
        table.set_issues(issues)

        self._assert_full_highlight(table, 2, BG_INMEDIATA)
        self._assert_full_highlight(table, 3, BG_URGENTE)
        self._assert_full_highlight(table, 4, BG_ALTA)

        # Segunda recarga: el resaltado debe seguir a la tarea
        table.set_issues(issues)
        self._assert_full_highlight(table, 2, BG_INMEDIATA)
        self._assert_full_highlight(table, 3, BG_URGENTE)
        self._assert_full_highlight(table, 4, BG_ALTA)

        # S1: reordenar DESPUÉS de poblar. Se ordena por Título descendente
        # (las fechas están vacías y no reordenarían nada) para forzar un
        # cambio real de filas y comprobar que el resaltado sigue a la tarea.
        order_before = [table._issue_id_at_row(row) for row in range(table.rowCount())]
        table.sortItems(table.COL_TITLE, Qt.SortOrder.DescendingOrder)
        order_after = [table._issue_id_at_row(row) for row in range(table.rowCount())]
        assert order_after == list(reversed(order_before))
        self._assert_full_highlight(table, 2, BG_INMEDIATA)
        self._assert_full_highlight(table, 3, BG_URGENTE)
        self._assert_full_highlight(table, 4, BG_ALTA)

    def test_three_levels_distinct_and_decreasing_luminance(self, qapp):
        table = TaskTable()
        issues = [
            _make_issue(1, priority="Alta"),
            _make_issue(2, priority="Urgente"),
            _make_issue(3, priority="Inmediata"),
        ]
        table.set_issues(issues)

        alta = self._row_bg(table, 1)
        urgente = self._row_bg(table, 2)
        inmediata = self._row_bg(table, 3)

        assert alta == BG_ALTA
        assert urgente == BG_URGENTE
        assert inmediata == BG_INMEDIATA
        assert len({alta.rgb(), urgente.rgb(), inmediata.rgb()}) == 3

        lum_alta = _relative_luminance(alta)
        lum_urgente = _relative_luminance(urgente)
        lum_inmediata = _relative_luminance(inmediata)
        assert lum_alta > lum_urgente > lum_inmediata

    def test_english_aliases_match_spanish_backgrounds(self, qapp):
        table = TaskTable()
        issues = [
            _make_issue(1, priority="Alta"),
            _make_issue(2, priority="High"),
            _make_issue(3, priority="Urgente"),
            _make_issue(4, priority="Urgent"),
            _make_issue(5, priority="Inmediata"),
            _make_issue(6, priority="Immediate"),
        ]
        table.set_issues(issues)

        assert self._row_bg(table, 2) == self._row_bg(table, 1) == BG_ALTA
        assert self._row_bg(table, 4) == self._row_bg(table, 3) == BG_URGENTE
        assert self._row_bg(table, 6) == self._row_bg(table, 5) == BG_INMEDIATA

    def test_non_priority_rows_not_highlighted(self, qapp):
        table = TaskTable()
        issues = [
            _make_issue(1, priority="Normal"),
            _make_issue(2, priority="Baja"),
            _make_issue(3, priority="Low"),
            # Prioridades fuera del resaltado: valores arbitrarios/custom
            _make_issue(4, priority="Crítica"),
            _make_issue(5, priority="Minor"),
        ]
        table.set_issues(issues)
        for issue_id in (1, 2, 3, 4, 5):
            row = self._row_of(table, issue_id)
            for col in range(table.columnCount()):
                if table.isColumnHidden(col):
                    continue
                color = table.item(row, col).background().color()
                assert color != BG_ALTA
                assert color != BG_URGENTE
                assert color != BG_INMEDIATA
                # S2: no se fuerza texto blanco en filas sin prioridad
                assert table.item(row, col).foreground().color() != WHITE


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
