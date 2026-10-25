"""Tests del widget MultiValueCombo (multiselección de valores de texto)."""

from PyQt6.QtCore import Qt

from app.widgets.multi_value_combo import MultiValueCombo


def test_set_items_and_set_selected_values(qapp):
    """2.1: set_items + set_selected_values deja marcado solo lo indicado."""
    combo = MultiValueCombo()
    combo.set_items(["A", "B"])
    combo.set_selected_values(["B"])

    assert combo.selected_values() == ["B"]


def test_summary_button_states(qapp):
    """2.3: vacío, valor único y "N seleccionados", con tooltip completo."""
    combo = MultiValueCombo()
    combo.resize(800, 40)
    combo.show()
    qapp.processEvents()
    combo.set_items(["A", "B", "C"])

    assert combo._button.text() == ""
    assert combo._button.toolTip() == ""

    combo.set_selected_values(["B"])
    assert combo._button.text() == "B"
    assert combo._button.toolTip() == "B"

    combo.set_selected_values(["A", "C"])
    assert combo._button.text() == "2 seleccionados"
    assert combo._button.toolTip() == "A, C"


def test_summary_single_long_value_is_elided(qapp):
    """2.3: un valor que no cabe se elide por la derecha y el tooltip es completo."""
    combo = MultiValueCombo()
    combo.resize(150, 40)
    combo.show()
    qapp.processEvents()
    largo = "Valor-muy-largo-" * 10
    combo.set_items([largo])
    combo.set_selected_values([largo])

    texto = combo._button.text()
    assert texto != largo
    assert texto.endswith("…")
    assert combo._button.toolTip() == largo


def test_search_filters_case_insensitive_without_changing_selection(qapp):
    """2.4: la búsqueda oculta las no coincidentes sin tocar la selección."""
    combo = MultiValueCombo()
    combo.set_items(["Alpha", "beta", "Gamma"])
    combo.set_selected_values(["beta"])

    combo._search_edit.setText("ALP")

    item_alpha, item_beta, item_gamma = (
        combo._list.item(i) for i in range(combo._list.count())
    )
    assert item_alpha.isHidden() is False
    assert item_beta.isHidden() is True
    assert item_gamma.isHidden() is True
    assert combo.selected_values() == ["beta"]


def test_search_is_cleared_on_open_and_close(qapp):
    """2.4: la búsqueda se vacía al abrir y al cerrar el popup."""
    combo = MultiValueCombo()
    combo.set_items(["A"])

    combo._search_edit.setText("zzz")
    combo._toggle_popup()
    assert combo._search_edit.text() == ""

    combo._search_edit.setText("zzz")
    combo._toggle_popup()
    assert combo._search_edit.text() == ""


def test_items_have_full_text_tooltip(qapp):
    """2.5: cada opción expone el texto completo en su tooltip y se elide."""
    combo = MultiValueCombo()
    largo = "x" * 120
    combo.set_items([largo, "B"])

    assert combo._list.item(0).toolTip() == largo
    assert combo._list.item(1).toolTip() == "B"
    # Configuración de elisión del popup: sin ajuste de línea, elisión derecha
    assert combo._list.textElideMode() == Qt.TextElideMode.ElideRight
    assert combo._list.wordWrap() is False


def test_set_items_preserves_previous_selection(qapp):
    """set_items conserva lo marcado que sigue existiendo y descarta el resto."""
    combo = MultiValueCombo()
    combo.set_items(["A", "B"])
    combo._list.item(1).setCheckState(Qt.CheckState.Checked)
    assert combo.selected_values() == ["B"]

    combo.set_items(["A", "B", "C"])
    assert combo.selected_values() == ["B"]

    combo.set_items(["A", "C"])
    assert combo.selected_values() == []


def test_no_options_disables_widget_with_help(qapp):
    """2.5: sin opciones el widget queda deshabilitado con texto de ayuda."""
    combo = MultiValueCombo()
    combo.set_items([])

    assert combo.isEnabled() is False
    assert combo._button.text() == "Sin opciones disponibles"

    combo.set_items(["A"])
    assert combo.isEnabled() is True


def test_check_state_is_single_source_of_truth(qapp):
    """2.7: marcar dos opciones con setCheckState conserva ambas marcas."""
    from PyQt6.QtWidgets import QAbstractItemView

    combo = MultiValueCombo()
    combo.set_items(["A", "B", "C"])

    combo._list.item(0).setCheckState(Qt.CheckState.Checked)
    combo._list.item(1).setCheckState(Qt.CheckState.Checked)

    assert combo.selected_values() == ["A", "B"]
    assert (
        combo._list.selectionMode()
        == QAbstractItemView.SelectionMode.NoSelection
    )


def test_popup_closes_on_hide_and_is_owned_by_combo(qapp):
    """2.9: el popup pertenece al combo y se oculta al ocultar el widget."""
    combo = MultiValueCombo()
    combo.set_items(["A"])
    combo.show()
    qapp.processEvents()

    combo._toggle_popup()
    combo._search_edit.setText("zzz")
    assert combo._popup.isVisible() is True

    combo.hide()

    assert combo._popup.isVisible() is False
    assert combo._popup.parent() is combo
    assert combo._search_edit.text() == ""


def test_popup_shows_options_when_expanded(qapp):
    """Al desplegar el popup se ven las opciones, ninguna oculta."""
    combo = MultiValueCombo()
    combo.set_items(["A", "B"])
    combo.show()
    qapp.processEvents()

    combo._toggle_popup()

    assert combo._popup.isVisible() is True
    assert combo._list.count() == 2
    for i in range(combo._list.count()):
        assert combo._list.item(i).isHidden() is False
