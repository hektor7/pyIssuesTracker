"""Tests para las mejoras de filtros, columnas y checklist (cambio mejoras-filtros-y-checklist)."""

import sys
from datetime import date, timedelta

import pytest
from PyQt6.QtCore import Qt, QEvent
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
from app.widgets.filter_bar import FilterBar


class TestFilterBarMultiProject:
    """El filtro de proyecto debe soportar selección múltiple."""

    def test_default_all_projects(self, qapp):
        fb = FilterBar()
        fb.populate_projects([(1, "Proyecto A"), (2, "Proyecto B")])
        assert fb.selected_project_ids == []

    def test_select_multiple_projects(self, qapp):
        fb = FilterBar()
        fb.populate_projects([(1, "Proyecto A"), (2, "Proyecto B"), (3, "Proyecto C")])
        fb.select_projects([2, 3])
        assert fb.selected_project_ids == [2, 3]
        assert fb.selected_project_id == 2  # primero seleccionado

    def test_select_projects_zero_resets_to_all(self, qapp):
        fb = FilterBar()
        fb.populate_projects([(1, "A"), (2, "B")])
        fb.select_projects([0])
        assert fb.selected_project_ids == []

    def test_select_projects_empty_resets_to_all(self, qapp):
        fb = FilterBar()
        fb.populate_projects([(1, "A"), (2, "B")])
        fb.select_projects([])
        assert fb.selected_project_ids == []

    def test_signal_emits_list(self, qapp):
        fb = FilterBar()
        fb.populate_projects([(1, "A"), (2, "B"), (3, "C")])
        received = []
        fb.proyecto_cambiado.connect(lambda ids: received.append(ids))
        fb.select_projects([1, 3])
        assert received and received[-1] == [1, 3]


class TestFilterBarNombresCompletos:
    """populate_projects debe usar el nombre recibido sin indentación (D8)."""

    def test_populate_projects_no_anade_indentacion(self, qapp):
        """El nombre completo se muestra tal cual, sin espacios de indentación añadidos."""
        fb = FilterBar()
        fb.populate_projects([(1, "Padre > Hijo")], hierarchy={1: 2, 2: None})

        combo = fb._project_combo
        texto = None
        for i in range(combo._list.count()):
            if combo._list.item(i).data(Qt.ItemDataRole.UserRole) == 1:
                texto = combo._list.item(i).text()
                break
        assert texto == "Padre > Hijo"
        assert not texto.startswith(" ")


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
# MultiSelectCombo — búsqueda por texto (cambio mejoras-generacion-informes)
# ──────────────────────────────────────────────────────────────────────


class TestMultiSelectComboBusqueda:
    """Búsqueda por texto en el popup del MultiSelectCombo (tareas 1.1-1.4)."""

    def test_popup_incluye_campo_de_busqueda(self, qapp):
        combo = MultiSelectCombo()
        assert hasattr(combo, "_search_edit")
        assert combo._search_edit.placeholderText() == "Buscar..."
        assert combo._search_edit.parent() is combo._popup

    def test_filtrado_por_subcadena_case_insensitive(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana"), (2, "Luis"), (3, "Andrea")])
        combo._apply_filter("an")
        visibles = [
            combo._list.item(i).text()
            for i in range(combo._list.count())
            if not combo._list.item(i).isHidden()
        ]
        assert "Ana" in visibles
        assert "Andrea" in visibles
        assert "Luis" not in visibles

    def test_filtrado_preserva_seleccion(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana"), (2, "Luis")])
        combo.set_selected_ids([1, 2])
        combo._apply_filter("an")
        assert combo.selected_ids() == [1, 2]
        for i in range(combo._list.count()):
            item = combo._list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == 2:
                assert item.checkState() == Qt.CheckState.Checked

    def test_vaciar_filtro_restaura_todos(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana"), (2, "Luis")])
        combo.set_selected_ids([1, 2])
        combo._apply_filter("an")
        combo._apply_filter("")
        for i in range(combo._list.count()):
            assert not combo._list.item(i).isHidden()
        assert combo.selected_ids() == [1, 2]

    def test_opciones_fijas_nunca_se_ocultan(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([
            (MultiSelectCombo.ALL, "Todos"),
            (MultiSelectCombo.NONE, "Sin asignar"),
            (MultiSelectCombo.ME, "Asignado a mí"),
        ])
        combo.set_items([(1, "Ana")])
        combo._apply_filter("zzz")
        for i in range(combo._list.count()):
            item = combo._list.item(i)
            iid = item.data(Qt.ItemDataRole.UserRole)
            if iid in (MultiSelectCombo.ALL, MultiSelectCombo.NONE, MultiSelectCombo.ME):
                assert not item.isHidden()
            else:
                assert item.isHidden()


class TestMultiSelectComboTooltips:
    """Tooltips en ítems y botón del MultiSelectCombo (tareas 1.5-1.6)."""

    def test_items_tienen_tooltip_con_su_texto(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana"), (2, "Luis")])
        for i in range(combo._list.count()):
            item = combo._list.item(i)
            assert item.toolTip() == item.text()

    def test_boton_tooltip_con_seleccion_unica(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana"), (2, "Luis")])
        combo.set_selected_ids([1])
        assert combo._button.text() == "Ana"
        assert combo._button.toolTip() == "Ana"

    def test_boton_tooltip_vacio_con_todos(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana")])
        assert combo._button.text() == "Todos"
        assert combo._button.toolTip() == ""

    def test_boton_tooltip_vacio_con_multiseleccion(self, qapp):
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana"), (2, "Luis")])
        combo.set_selected_ids([1, 2])
        assert combo._button.text() == "2 seleccionados"
        assert combo._button.toolTip() == ""


class TestFilterBarTooltipProyecto:
    """Integración: FilterBar.populate_projects expone el nombre completo en el tooltip (tarea 1.7)."""

    def test_tooltip_nombre_completo_en_item(self, qapp):
        fb = FilterBar()
        fb.populate_projects([(1, "Padre > Hijo muy largo")])
        combo = fb._project_combo
        item = None
        for i in range(combo._list.count()):
            if combo._list.item(i).data(Qt.ItemDataRole.UserRole) == 1:
                item = combo._list.item(i)
                break
        assert item is not None
        assert item.toolTip() == "Padre > Hijo muy largo"


class TestMultiSelectComboCierrePopup:
    """Cierre del popup por clic fuera: limpia búsqueda y resetea _popup_open (tarea 14.1)."""

    def test_cierre_popup_por_clic_fuera_vacia_busqueda_y_resetea(self, qapp):
        """Al ocultarse el popup (clic fuera), se vacía la búsqueda y _popup_open=False."""
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana"), (2, "Luis")])
        combo._toggle_popup()  # abre
        assert combo._popup_open is True
        combo._search_edit.setText("an")
        # Simular el cierre por clic fuera: el popup recibe un evento Hide
        combo._popup.hide()
        assert combo._search_edit.text() == ""
        assert combo._popup_open is False

    def test_cierre_popup_por_clic_fuera_permite_reabrir_con_un_clic(self, qapp):
        """Tras el cierre por clic fuera, un clic en el botón vuelve a abrir el popup."""
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana")])
        combo._toggle_popup()
        combo._popup.hide()  # clic fuera
        assert combo._popup_open is False
        combo._toggle_popup()  # segundo clic: debe ABRIR
        assert combo._popup_open is True

    def test_event_filter_hide_vacia_busqueda(self, qapp):
        """El event filter del popup responde a QEvent.Type.Hide."""
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana")])
        combo._toggle_popup()
        combo._search_edit.setText("an")
        combo.eventFilter(combo._popup, QEvent(QEvent.Type.Hide))
        assert combo._search_edit.text() == ""
        assert combo._popup_open is False


class TestMultiSelectComboFallbackBoton:
    """Fallback de _update_button_text con ids fuera de la lista (tarea 14.4)."""

    def test_boton_fallback_con_id_fuera_de_la_lista(self, qapp):
        """Con una selección única cuyo id no está en la lista, el botón muestra el id y tooltip vacío."""
        combo = MultiSelectCombo()
        combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        combo.set_items([(1, "Ana")])
        combo.set_selected_ids([999])  # id no presente en items ni fixed
        assert combo._button.text() == "999"
        assert combo._button.toolTip() == ""

    def test_boton_busca_nombre_en_opciones_fijas(self, qapp):
        """Con selección única de una opción fija, el botón muestra su nombre y tooltip."""
        combo = MultiSelectCombo()
        combo.set_fixed_options([
            (MultiSelectCombo.ALL, "Todos"),
            (MultiSelectCombo.NONE, "Sin asignar"),
        ])
        combo.set_items([(1, "Ana")])
        combo.set_selected_ids([MultiSelectCombo.NONE])
        assert combo._button.text() == "Sin asignar"
        assert combo._button.toolTip() == "Sin asignar"


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
