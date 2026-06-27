"""Tests para las mejoras de filtros, columnas y checklist (cambio mejoras-filtros-y-checklist)."""

import sys
from datetime import date, timedelta

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QTableWidgetItem

from app.utils.dates import iso_datetime_to_display, iso_to_display, display_to_iso
from app.widgets.task_table import DateSortItem


# ──────────────────────────────────────────────────────────────────────
# iso_datetime_to_display
# ──────────────────────────────────────────────────────────────────────

class TestIsoDatetimeToDisplay:
    """Verifica el formateo de timestamps ISO 8601 a DD/MM/YY HH:MM."""

    def test_full_utc(self):
        assert iso_datetime_to_display("2026-06-26T14:45:00Z") == "26/06/26 14:45"

    def test_with_timezone(self):
        assert iso_datetime_to_display("2026-06-15T09:30:00+02:00") == "15/06/26 09:30"

    def test_with_negative_timezone(self):
        assert iso_datetime_to_display("2026-12-31T23:59:59-05:00") == "31/12/26 23:59"

    def test_date_only_no_time(self):
        assert iso_datetime_to_display("2026-06-15") == "15/06/26"

    def test_empty_string(self):
        assert iso_datetime_to_display("") == ""

    def test_whitespace_only(self):
        assert iso_datetime_to_display("   ") == ""

    def test_midnight_utc(self):
        assert iso_datetime_to_display("2026-01-01T00:00:00Z") == "01/01/26 00:00"

    def test_end_of_year(self):
        assert iso_datetime_to_display("2026-12-31T23:59:59Z") == "31/12/26 23:59"

    def test_space_separator(self):
        assert iso_datetime_to_display("2026-06-26 14:45:00") == "26/06/26 14:45"

    def test_milliseconds(self):
        assert iso_datetime_to_display("2026-06-26T14:45:00.123Z") == "26/06/26 14:45"

    def test_unparseable_returns_original(self):
        result = iso_datetime_to_display("not-a-date")
        assert result == "not-a-date"


# ──────────────────────────────────────────────────────────────────────
# DateSortItem — ordenación cronológica
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def qapp():
    """QApplication compartida para tests de widgets."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestDateSortItem:
    """Verifica que DateSortItem ordena fechas cronológicamente (ISO) y no lexicográficamente."""

    def test_january_before_june(self, qapp):
        a = DateSortItem("2026-01-15", "15/01/26")
        b = DateSortItem("2026-06-26", "26/06/26")
        assert a < b   # cronológico: enero < junio
        assert not (b < a)

    def test_with_time_component(self, qapp):
        a = DateSortItem("2026-06-26T10:00:00Z", "26/06/26 10:00")
        b = DateSortItem("2026-06-26T14:00:00Z", "26/06/26 14:00")
        # Mismo día, distinta hora → orden ISO correcto
        assert a < b

    def test_different_years(self, qapp):
        a = DateSortItem("2025-12-31", "31/12/25")
        b = DateSortItem("2026-01-01", "01/01/26")
        assert a < b  # 2025 < 2026

    def test_lexicographic_would_be_wrong(self, qapp):
        """Con QTableWidgetItem normal, '01/02/26' < '15/01/26' (febrero < enero).
        DateSortItem debe corregir esto usando la ISO."""
        a = DateSortItem("2026-02-01", "01/02/26")
        b = DateSortItem("2026-01-15", "15/01/26")
        # Lexicográfico: "01/02/26" < "15/01/26" → febrero antes que enero (mal)
        # Cronológico (ISO): "2026-02-01" > "2026-01-15" → febrero después de enero (bien)
        assert not (a < b)
        assert b < a

    def test_empty_falls_back_to_text_comparison(self, qapp):
        a = DateSortItem("", "")
        b = DateSortItem("2026-06-26", "26/06/26")
        # Item vacío: sin ISO → usa texto ("" < "26/06/26")
        assert a < b

    def test_same_date_equal(self, qapp):
        a = DateSortItem("2026-06-26", "26/06/26")
        b = DateSortItem("2026-06-26", "26/06/26")
        assert not (a < b)
        assert not (b < a)

    def test_iso_role_stored(self, qapp):
        item = DateSortItem("2026-06-26T14:45:00Z", "26/06/26 14:45")
        assert item.data(DateSortItem.ISO_ROLE) == "2026-06-26T14:45:00Z"

    def test_empty_iso_no_role_stored(self, qapp):
        item = DateSortItem("", "")
        assert item.data(DateSortItem.ISO_ROLE) is None


# ──────────────────────────────────────────────────────────────────────
# Funciones de fechas existentes (regresión)
# ──────────────────────────────────────────────────────────────────────

class TestExistingDateFunctions:
    """Verifica que iso_to_display y display_to_iso siguen funcionando."""

    def test_iso_to_display_normal(self):
        assert iso_to_display("2026-06-26") == "26/06/2026"

    def test_iso_to_display_empty(self):
        assert iso_to_display("") == ""

    def test_display_to_iso_normal(self):
        assert display_to_iso("26/06/2026") == "2026-06-26"

    def test_display_to_iso_empty(self):
        assert display_to_iso("") == ""


# ──────────────────────────────────────────────────────────────────────
# MultiSelectCombo
# ──────────────────────────────────────────────────────────────────────

from app.widgets.multi_select_combo import MultiSelectCombo


class TestMultiSelectCombo:
    """Verifica el widget de multiselección con checkboxes."""

    def test_initial_state_all_selected(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([
            (MultiSelectCombo.ALL, "Todos"),
            (MultiSelectCombo.NONE, "Sin asignar"),
            (MultiSelectCombo.ME, "Asignado a mí"),
        ])
        # Por defecto, "Todos" debería estar seleccionado
        ids = combo.selected_ids()
        assert MultiSelectCombo.ALL in ids
        assert combo._button.text() == "Todos"

    def test_select_single_item_deselects_all(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([
            (MultiSelectCombo.ALL, "Todos"),
        ])
        combo.set_items([(5, "Ana"), (8, "Carlos")])
        # Simular selección: marcar Ana (id=5)
        combo.set_selected_ids([5])
        ids = combo.selected_ids()
        assert 5 in ids
        assert MultiSelectCombo.ALL not in ids
        assert combo._button.text() == "Ana"

    def test_multiple_selection_shows_count(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(5, "Ana"), (8, "Carlos"), (12, "Beatriz")])
        combo.set_selected_ids([5, 8])
        assert combo._button.text() == "2 seleccionados"

    def test_deselecting_all_resets_to_todos(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(5, "Ana")])
        combo.set_selected_ids([5])
        assert 5 in combo.selected_ids()
        # Desmarcar todo → volver a "Todos"
        combo.set_selected_ids([])
        assert MultiSelectCombo.ALL in combo.selected_ids()

    def test_fixed_options_preserved(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([
            (MultiSelectCombo.ALL, "Todos"),
            (MultiSelectCombo.NONE, "Sin asignar"),
        ])
        combo.set_items([(5, "Ana")])
        # Verificar que los items fijos y dinámicos están en la lista
        all_ids = []
        for i in range(combo._list.count()):
            all_ids.append(combo._list.item(i).data(Qt.ItemDataRole.UserRole))
        assert MultiSelectCombo.ALL in all_ids
        assert MultiSelectCombo.NONE in all_ids
        assert 5 in all_ids

    def test_signal_emitted_on_change(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(5, "Ana")])

        received = []
        combo.seleccion_cambiada.connect(lambda ids: received.append(ids))

        combo.set_selected_ids([5])
        assert len(received) == 1
        assert 5 in received[0]


# ──────────────────────────────────────────────────────────────────────
# Checklist mode — regresión en _is_edit
# ──────────────────────────────────────────────────────────────────────

from app.dialogs.task_dialog import TaskDialog
from app.widgets.checklist_widget import ChecklistWidget


class TestChecklistCreateMode:
    """Verifica que el checklist funciona en modo creación."""

    def test_checklist_widget_set_item_checked(self, qapp):
        """set_item_checked no debe emitir señal."""
        widget = ChecklistWidget()
        widget.set_items([
            {"id": 1, "subject": "Test item", "is_done": False, "position": 1}
        ])

        toggled = []
        widget.item_toggled.connect(lambda iid, checked: toggled.append((iid, checked)))

        widget.set_item_checked(1, True)
        # No debe haberse emitido señal
        assert len(toggled) == 0

    def test_pending_checklist_items_property(self):
        """La propiedad pending_checklist_items debe existir y ser una lista."""
        dlg = TaskDialog()
        assert hasattr(dlg, 'pending_checklist_items')
        assert isinstance(dlg.pending_checklist_items, list)
        assert len(dlg.pending_checklist_items) == 0
