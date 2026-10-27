"""Tests de la sección "Campos personalizados" del TaskDialog (BLOQUE 3).

Cubren:
- Sección oculta cuando el proyecto no tiene campos personalizados.
- Sección visible con un control por campo y situada antes del grupo Comentarios.
- Recarga de la sección al cambiar de proyecto.
- Precarga de los valores actuales del issue en modo edición.
- Serialización del valor por field_format (string/text/int/float/date/bool/list/multiple).
- Ocultación de la sección si la carga falla (sin romper el diálogo).
"""

from unittest.mock import MagicMock

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDoubleSpinBox,
    QFrame,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
)

from app.dialogs.task_dialog import TaskDialog
from app.services.redmine_client import RedmineCustomField
from app.widgets.multi_value_combo import MultiValueCombo


def _field(cf_id, name, fmt, **kwargs):
    """Construye un RedmineCustomField con valores por defecto razonables."""
    return RedmineCustomField(id=cf_id, name=name, field_format=fmt, **kwargs)


def _make_dialog(redmine, fields, projects=None, default_project_id=1, task_data=None):
    """Crea un TaskDialog con el cliente mockeado y los campos dados.

    En modo creación usa default_project_id para disparar la carga; en modo
    edición el proyecto se toma de task_data.
    """
    redmine.get_project_custom_fields.return_value = fields
    return TaskDialog(
        projects=projects or [(1, "Proyecto")],
        default_project_id=default_project_id,
        redmine_client=redmine,
        task_data=task_data,
    )


def _edit_task_data(custom_fields: dict | None = None):
    """task_data mínimo de un issue en modo edición."""
    return {
        "id": 9,
        "project_id": 1,
        "tracker_id": 1,
        "priority_id": 2,
        "status_id": 1,
        "subject": "Tarea existente",
        "description": "",
        "custom_fields": custom_fields or {},
    }


class TestSectionVisibility:
    """La sección se oculta sin campos y se muestra con campos."""

    def test_section_hidden_when_project_has_no_fields(self, qapp):
        redmine = MagicMock()
        dlg = _make_dialog(redmine, [])

        assert dlg._custom_fields_group.isVisibleTo(dlg) is False
        assert dlg._custom_field_widgets == {}

    def test_section_visible_with_fields(self, qapp):
        redmine = MagicMock()
        fields = [
            _field(1, "Texto", "string"),
            _field(2, "Lista", "list", possible_values=["A", "B"]),
        ]
        dlg = _make_dialog(redmine, fields)

        assert dlg._custom_fields_group.isVisibleTo(dlg) is True
        assert set(dlg._custom_field_widgets) == {1, 2}
        # Un control por campo definido en el proyecto
        assert dlg._custom_fields_form.rowCount() == 2

    def test_section_before_comments_group(self, qapp):
        """La sección aparece antes del grupo Comentarios en el scroll."""
        redmine = MagicMock()
        dlg = _make_dialog(redmine, [_field(1, "Texto", "string")])

        layout = dlg._custom_fields_group.parentWidget().layout()
        assert layout.indexOf(dlg._custom_fields_group) < layout.indexOf(dlg._comments_group)

    def test_section_hidden_when_load_fails(self, qapp):
        """Si la carga falla, la sección se oculta sin romper el diálogo."""
        redmine = MagicMock()
        redmine.get_project_custom_fields.side_effect = RuntimeError("API caída")
        dlg = _make_dialog(redmine, [])

        assert dlg._custom_fields_group.isVisibleTo(dlg) is False


class TestReloadOnProjectChange:
    """La sección se recarga al cambiar de proyecto."""

    def test_reloads_fields_of_new_project(self, qapp):
        redmine = MagicMock()

        def fields_for(pid):
            if pid == 1:
                return [_field(1, "Campo P1", "string")]
            return [_field(2, "Campo P2", "string")]

        redmine.get_project_custom_fields.side_effect = fields_for
        dlg = TaskDialog(
            projects=[(1, "P1"), (2, "P2")],
            default_project_id=1,
            redmine_client=redmine,
        )

        assert set(dlg._custom_field_widgets) == {1}

        # Cambiar al proyecto 2: se recargan los campos del nuevo proyecto
        dlg._project_combo.setCurrentIndex(1)

        assert set(dlg._custom_field_widgets) == {2}
        assert dlg._custom_fields_group.isVisibleTo(dlg) is True

    def test_hides_when_new_project_has_no_fields(self, qapp):
        redmine = MagicMock()

        def fields_for(pid):
            if pid == 1:
                return [_field(1, "Campo P1", "string")]
            return []

        redmine.get_project_custom_fields.side_effect = fields_for
        dlg = TaskDialog(
            projects=[(1, "P1"), (2, "P2")],
            default_project_id=1,
            redmine_client=redmine,
        )
        assert dlg._custom_fields_group.isVisibleTo(dlg) is True

        dlg._project_combo.setCurrentIndex(1)

        assert dlg._custom_fields_group.isVisibleTo(dlg) is False
        assert dlg._custom_field_widgets == {}


class TestEditModePreload:
    """En modo edición los controles muestran los valores actuales del issue."""

    def test_preloads_current_values(self, qapp):
        redmine = MagicMock()
        fields = [
            _field(1, "Texto", "string"),
            _field(2, "Lista", "list", possible_values=["Baja", "Alta"]),
            _field(3, "Bool", "bool"),
            _field(4, "Fecha", "date"),
            _field(5, "Multi", "list", multiple=True, possible_values=["x", "y"]),
        ]
        dlg = _make_dialog(
            redmine,
            fields,
            task_data=_edit_task_data({1: "hola", 2: "Alta", 3: "1", 4: "2026-05-01", 5: ["x", "y"]}),
        )

        w = dlg._custom_field_widgets
        assert w[1]["widget"].text() == "hola"
        assert w[2]["widget"].currentData() == "Alta"
        assert w[3]["widget"].isChecked() is True
        # Fecha: checkbox "Sin valor" desmarcado y fecha fijada
        assert w[4]["extra"].isChecked() is False
        assert w[4]["widget"].date().toString("yyyy-MM-dd") == "2026-05-01"
        assert w[5]["widget"].selected_values() == ["x", "y"]

    def test_default_value_applied_when_no_previous_value(self, qapp):
        redmine = MagicMock()
        fields = [
            _field(1, "Lista", "list", possible_values=["Baja", "Alta"], default_value="Baja"),
            _field(2, "Texto", "string", default_value="por defecto"),
        ]
        dlg = _make_dialog(redmine, fields)

        w = dlg._custom_field_widgets
        assert w[1]["widget"].currentData() == "Baja"
        assert w[2]["widget"].text() == "por defecto"


class TestSerialization:
    """La propiedad custom_fields serializa cada valor según su field_format."""

    def test_serializes_by_field_format(self, qapp):
        redmine = MagicMock()
        fields = [
            _field(1, "Texto", "string"),
            _field(2, "Largo", "text"),
            _field(3, "Entero", "int"),
            _field(4, "Decimal", "float"),
            _field(5, "Fecha", "date"),
            _field(6, "Booleano", "bool"),
            _field(7, "Lista", "list", possible_values=["Baja", "Alta"]),
            _field(8, "Multi", "list", multiple=True, possible_values=["x", "y", "z"]),
        ]
        dlg = _make_dialog(redmine, fields)

        w = dlg._custom_field_widgets

        # Tipos de control por field_format (granularidad de la verificación)
        assert isinstance(w[1]["widget"], QLineEdit)
        assert isinstance(w[2]["widget"], QPlainTextEdit)
        assert isinstance(w[3]["widget"], QSpinBox)
        assert w[3]["widget"].minimum() == -2147483648
        assert w[3]["widget"].maximum() == 2147483647
        assert isinstance(w[4]["widget"], QDoubleSpinBox)
        assert w[4]["widget"].decimals() == 4
        assert w[4]["widget"].minimum() == -1e12
        assert w[4]["widget"].maximum() == 1e12
        assert isinstance(w[5]["widget"], QDateEdit)
        assert isinstance(w[6]["widget"], QCheckBox)

        w[1]["widget"].setText("hola")
        w[2]["widget"].setPlainText("notas")
        w[3]["widget"].setValue(42)
        w[4]["widget"].setValue(3.5)
        w[5]["extra"].setChecked(False)
        w[5]["widget"].setDate(QDate(2026, 5, 1))
        w[6]["widget"].setChecked(True)
        w[7]["widget"].setCurrentIndex(w[7]["widget"].findData("Alta"))
        w[8]["widget"].set_selected_values(["x", "z"])

        result = dlg.custom_fields
        assert result[1] == "hola"
        assert result[2] == "notas"
        assert result[3] == "42"
        assert result[4] == "3.5"
        assert result[5] == "2026-05-01"
        assert result[6] == "1"
        assert result[7] == "Alta"
        assert result[8] == ["x", "z"]

    def test_bool_without_previous_value_not_required_omitted(self, qapp):
        """R3: un bool sin valor previo y no obligatorio se omite del payload."""
        redmine = MagicMock()
        dlg = _make_dialog(redmine, [_field(1, "Bool", "bool")])

        dlg._custom_field_widgets[1]["widget"].setChecked(False)

        assert dlg.custom_fields == {}

    def test_bool_without_previous_value_required_sends_zero(self, qapp):
        """R3: un bool sin valor previo pero obligatorio se envía como "0"."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Bool", "bool", is_required=True)],
        )

        dlg._custom_field_widgets[1]["widget"].setChecked(False)

        assert dlg.custom_fields == {1: "0"}

    def test_bool_with_previous_value_serializes_checked_state(self, qapp):
        """R3: un bool con valor previo se envía "1"/"0" según el checkbox."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Bool", "bool")],
            task_data=_edit_task_data({1: "1"}),
        )

        # Con valor previo y desmarcado -> "0"
        dlg._custom_field_widgets[1]["widget"].setChecked(False)
        assert dlg.custom_fields == {1: "0"}

        # Con valor previo y marcado -> "1"
        dlg._custom_field_widgets[1]["widget"].setChecked(True)
        assert dlg.custom_fields == {1: "1"}

    def test_date_without_value_serializes_empty(self, qapp):
        redmine = MagicMock()
        dlg = _make_dialog(redmine, [_field(1, "Fecha", "date")])

        # "Sin valor" marcado por defecto
        assert dlg.custom_fields == {}

    def test_empty_fields_omitted_unless_previously_set(self, qapp):
        """Vacíos sin valor previo se omiten; con valor previo se envían con ''."""
        redmine = MagicMock()
        fields = [_field(1, "Texto", "string"), _field(2, "Otro", "string")]
        dlg = _make_dialog(redmine, fields)

        # Sin valores previos: los campos vacíos no se incluyen
        assert dlg.custom_fields == {}

        # En edición con valor previo: vaciar el campo lo incluye con ""
        dlg2 = _make_dialog(
            redmine,
            fields,
            task_data=_edit_task_data({1: "valor previo"}),
        )
        dlg2._custom_field_widgets[1]["widget"].setText("")

        assert dlg2.custom_fields == {1: ""}

    def test_int_with_previous_zero_serializes_as_zero(self, qapp):
        """R1: un int con valor previo 0 se envía como "0", no como ''."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Entero", "int")],
            task_data=_edit_task_data({1: 0}),
        )

        assert dlg.custom_fields == {1: "0"}

    def test_float_with_previous_zero_serializes_as_zero(self, qapp):
        """R1: un float con valor previo 0.0 se envía como "0.0", no como ''."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Decimal", "float")],
            task_data=_edit_task_data({1: 0.0}),
        )

        assert dlg.custom_fields == {1: "0.0"}

    def test_numeric_without_previous_value_omitted(self, qapp):
        """R1: un campo numérico sin valor previo y en 0 se omite."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Entero", "int"), _field(2, "Decimal", "float")],
        )

        assert dlg.custom_fields == {}


class TestUnsupportedFieldFormat:
    """Un field_format no contemplado cae al fallback de texto libre sin fallar."""

    def test_unsupported_format_falls_back_to_line_edit(self, qapp):
        redmine = MagicMock()
        dlg = _make_dialog(redmine, [_field(1, "Enlace", "link")])

        w = dlg._custom_field_widgets[1]
        assert w["kind"] == "string"
        assert isinstance(w["widget"], QLineEdit)

        # El fallback serializa como texto libre
        w["widget"].setText("https://ejemplo.com")
        assert dlg.custom_fields == {1: "https://ejemplo.com"}

    def test_multiple_takes_precedence_over_unsupported_format(self, qapp):
        """multiple manda sobre field_format: formato no soportado + multiple."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Enlace", "link", multiple=True, possible_values=["a", "b"])],
        )

        entry = dlg._custom_field_widgets[1]
        assert entry["kind"] == "multiple"
        assert isinstance(entry["widget"], MultiValueCombo)


class TestRequiredFieldLabel:
    """Un campo obligatorio (is_required) se marca visualmente en la etiqueta."""

    def test_required_field_label_has_asterisk_suffix(self, qapp):
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [
                _field(1, "Obligatorio", "string", is_required=True),
                _field(2, "Opcional", "string"),
            ],
        )

        label_required = dlg._custom_fields_form.labelForField(
            dlg._custom_field_widgets[1]["widget"]
        )
        label_optional = dlg._custom_fields_form.labelForField(
            dlg._custom_field_widgets[2]["widget"]
        )

        assert label_required.text() == "Obligatorio *:"
        assert label_optional.text() == "Opcional:"

    def test_required_multiple_field_label_has_asterisk_suffix(self, qapp):
        """Un campo de valor múltiple obligatorio también lleva el sufijo " *:"."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [
                _field(
                    1, "Obligatorio", "list", multiple=True,
                    is_required=True, possible_values=["a"],
                ),
            ],
        )

        widget = dlg._custom_field_widgets[1]["widget"]
        label = dlg._custom_fields_form.labelForField(widget)

        assert label.text() == "Obligatorio *:"


class TestMultipleFieldWidget:
    """El campo de valor múltiple se construye con MultiValueCombo."""

    def test_multiple_field_uses_multi_value_combo(self, qapp):
        """3.1: kind "multiple" y widget MultiValueCombo con las opciones."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Multi", "list", multiple=True, possible_values=["A", "B"])],
        )

        entry = dlg._custom_field_widgets[1]
        assert entry["kind"] == "multiple"
        assert isinstance(entry["widget"], MultiValueCombo)
        assert entry["widget"].selected_values() == []
        # Las possible_values se materializan como items marcables
        assert entry["widget"]._list.count() == 2
        for i in range(entry["widget"]._list.count()):
            item = entry["widget"]._list.item(i)
            assert item.flags() & Qt.ItemFlag.ItemIsUserCheckable
            assert item.text() == ["A", "B"][i]


def test_multiple_preloads_previous_values(qapp):
    """3.3: en edición se precargan los valores previos del campo múltiple."""
    redmine = MagicMock()
    dlg = _make_dialog(
        redmine,
        [_field(5, "Multi", "list", multiple=True, possible_values=["x", "y"])],
        task_data=_edit_task_data({5: ["x", "y"]}),
    )

    entry = dlg._custom_field_widgets[5]
    assert entry["widget"].selected_values() == ["x", "y"]


def test_multiple_serializes_selected_values(qapp):
    """3.4: serializa list[str] y [] al vaciar un campo con valor previo."""
    redmine = MagicMock()
    fields = [
        _field(8, "Multi", "list", multiple=True, possible_values=["x", "y", "z"])
    ]

    dlg = _make_dialog(redmine, fields)
    dlg._custom_field_widgets[8]["widget"].set_selected_values(["x", "z"])
    assert dlg.custom_fields == {8: ["x", "z"]}

    dlg2 = _make_dialog(redmine, fields, task_data=_edit_task_data({8: ["x"]}))
    dlg2._custom_field_widgets[8]["widget"].set_selected_values([])
    assert dlg2.custom_fields == {8: []}


def test_multiple_default_value_applied_without_previous(qapp):
    """3.5: sin valor previo se aplica default_value al campo múltiple."""
    redmine = MagicMock()
    dlg = _make_dialog(
        redmine,
        [_field(
            5, "Multi", "list", multiple=True,
            possible_values=["x", "y"], default_value="x",
        )],
    )

    assert dlg._custom_field_widgets[5]["widget"].selected_values() == ["x"]


class TestSimpleListCombo:
    """El QComboBox de lista simple elide y expone tooltips completos."""

    def test_list_combo_has_min_width_elision_and_tooltips(self, qapp):
        """4.1: ancho mínimo, elisión por la derecha y tooltip por opción."""
        redmine = MagicMock()
        largo = "Valor-muy-largo-" * 10
        dlg = _make_dialog(
            redmine,
            [_field(7, "Lista", "list", possible_values=[largo, "Alta"])],
        )

        combo = dlg._custom_field_widgets[7]["widget"]
        assert combo.minimumContentsLength() == 20
        assert combo.minimumWidth() == 200
        assert combo.view().textElideMode() == Qt.TextElideMode.ElideRight
        assert combo.itemData(1, Qt.ItemDataRole.ToolTipRole) == largo
        assert combo.itemData(2, Qt.ItemDataRole.ToolTipRole) == "Alta"


def test_list_without_options_disabled_with_help(qapp):
    """4.3: sin possible_values el combo se deshabilita; el previo se preserva."""
    redmine = MagicMock()
    fields = [_field(7, "Lista", "list", possible_values=[])]

    dlg = _make_dialog(redmine, fields)
    combo = dlg._custom_field_widgets[7]["widget"]
    assert combo.isEnabled() is False
    assert combo.currentText() == "Sin opciones disponibles"
    assert dlg.custom_fields == {}

    dlg2 = _make_dialog(
        redmine, fields, task_data=_edit_task_data({7: "Antigua"})
    )
    assert dlg2._custom_field_widgets[7]["widget"].isEnabled() is False
    # El control no puede representar el valor previo: se omite del payload
    # para que Redmine conserve el valor en lugar de borrarlo.
    assert dlg2.custom_fields == {}


def test_multiple_without_options_disabled_and_preserves_previous_value(qapp):
    """4.5: sin possible_values el multiselector se deshabilita; previo preservado."""
    redmine = MagicMock()
    fields = [_field(8, "Multi", "list", multiple=True, possible_values=[])]

    dlg = _make_dialog(redmine, fields)
    widget = dlg._custom_field_widgets[8]["widget"]
    assert widget.isEnabled() is False
    assert widget._button.text() == "Sin opciones disponibles"
    assert dlg.custom_fields == {}

    dlg2 = _make_dialog(
        redmine, fields, task_data=_edit_task_data({8: ["x"]})
    )
    assert dlg2._custom_field_widgets[8]["widget"].isEnabled() is False
    # El valor previo no es representable: se omite para no borrarlo en Redmine.
    assert dlg2.custom_fields == {}


def test_list_previous_value_outside_options_is_preserved(qapp):
    """El valor previo fuera de possible_values se omite y no se borra."""
    redmine = MagicMock()
    dlg = _make_dialog(
        redmine,
        [_field(7, "Lista", "list", possible_values=["Baja", "Alta"])],
        task_data=_edit_task_data({7: "Antigua"}),
    )

    assert dlg._custom_field_widgets[7]["widget"].currentData() in (None, "")
    assert dlg.custom_fields == {}


def test_multiple_previous_value_partially_representable_preserves_unknown(qapp):
    """El valor previo no representable se inyecta como opción y se conserva."""
    redmine = MagicMock()
    dlg = _make_dialog(
        redmine,
        [_field(8, "Multi", "list", multiple=True, possible_values=["x", "y"])],
        task_data=_edit_task_data({8: ["x", "z"]}),
    )

    widget = dlg._custom_field_widgets[8]["widget"]
    # "z" no está en possible_values, pero se inyecta marcado para no perderlo.
    textos = [
        widget._list.item(i).text() for i in range(widget._list.count())
    ]
    assert "z" in textos
    assert widget.selected_values() == ["x", "z"]
    assert dlg.custom_fields == {8: ["x", "z"]}


def test_multiple_uncheck_injected_previous_value_removes_it(qapp):
    """Desmarcar explícitamente el valor inyectado sí lo elimina del payload."""
    redmine = MagicMock()
    dlg = _make_dialog(
        redmine,
        [_field(8, "Multi", "list", multiple=True, possible_values=["x", "y"])],
        task_data=_edit_task_data({8: ["x", "z"]}),
    )

    widget = dlg._custom_field_widgets[8]["widget"]
    for i in range(widget._list.count()):
        item = widget._list.item(i)
        if item.text() == "z":
            item.setCheckState(Qt.CheckState.Unchecked)

    assert dlg.custom_fields == {8: ["x"]}


def test_reload_rebuilds_multiselector_without_open_popups(qapp):
    """5.3: recargar al cambiar de proyecto no deja popups abiertos."""
    redmine = MagicMock()

    def fields_for(pid):
        if pid == 1:
            return [_field(1, "Multi", "list", multiple=True, possible_values=["x"])]
        return [_field(2, "Multi", "list", multiple=True, possible_values=["y"])]

    redmine.get_project_custom_fields.side_effect = fields_for
    dlg = TaskDialog(
        projects=[(1, "P1"), (2, "P2")],
        default_project_id=1,
        redmine_client=redmine,
    )

    combo = dlg._custom_field_widgets[1]["widget"]
    combo.show()
    qapp.processEvents()
    combo._toggle_popup()
    assert combo._popup.isVisible() is True

    combo.hide()
    assert combo._popup.isVisible() is False
    assert combo._popup.parent() is combo

    dlg._project_combo.setCurrentIndex(1)

    nuevo = dlg._custom_field_widgets[2]["widget"]
    assert nuevo._popup.isVisible() is False
    assert nuevo._popup.parent() is nuevo


def test_project_change_with_open_popup_leaves_no_visible_popup(qapp):
    """5.3: cambiar de proyecto con el popup abierto (sin hide) no deja popups."""
    from PyQt6 import sip

    def visible_popups():
        return {
            w
            for w in qapp.topLevelWidgets()
            if isinstance(w, QFrame)
            and w.isVisible()
            and bool(w.windowFlags() & Qt.WindowType.Popup)
        }

    redmine = MagicMock()

    def fields_for(pid):
        if pid == 1:
            return [_field(1, "Multi", "list", multiple=True, possible_values=["x"])]
        return [_field(2, "Multi", "list", multiple=True, possible_values=["y"])]

    redmine.get_project_custom_fields.side_effect = fields_for
    dlg = TaskDialog(
        projects=[(1, "P1"), (2, "P2")],
        default_project_id=1,
        redmine_client=redmine,
    )

    popups_antes = visible_popups()
    combo = dlg._custom_field_widgets[1]["widget"]
    popup = combo._popup
    combo.show()
    qapp.processEvents()
    combo._toggle_popup()
    assert popup.isVisible() is True

    # Sin llamar a combo.hide(): la recarga de campos destruye el combo antiguo
    dlg._project_combo.setCurrentIndex(1)
    qapp.processEvents()

    # El combo/popup antiguo puede haberse destruido ya: evitar RuntimeError
    if not sip.isdeleted(combo):
        assert combo.isVisible() is False
    if not sip.isdeleted(popup):
        assert popup.isVisible() is False
    assert visible_popups() == popups_antes

    nuevo = dlg._custom_field_widgets[2]["widget"]
    assert nuevo._popup.isVisible() is False


class TestFallbackTextPreviousList:
    """Renderizado legible y round-trip de listas en el fallback de texto."""

    def test_fallback_string_renders_previous_list_without_repr(self, qapp):
        """2.1: un QLineEdit muestra los elementos unidos por ', ' sin repr."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Libre", "")],
            task_data=_edit_task_data(
                {1: ["Petición de mejora / usabilidad", "Otra"]}
            ),
        )

        entry = dlg._custom_field_widgets[1]
        assert isinstance(entry["widget"], QLineEdit)
        texto = entry["widget"].text()
        assert texto == "Petición de mejora / usabilidad, Otra"
        assert "[" not in texto
        assert "]" not in texto
        assert "'" not in texto

    def test_fallback_text_renders_previous_list_without_repr(self, qapp):
        """2.1: un QPlainTextEdit muestra los elementos unidos por ', ' sin repr."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Largo", "text")],
            task_data=_edit_task_data(
                {1: ["Petición de mejora / usabilidad", "Otra"]}
            ),
        )

        entry = dlg._custom_field_widgets[1]
        assert isinstance(entry["widget"], QPlainTextEdit)
        texto = entry["widget"].toPlainText()
        assert texto == "Petición de mejora / usabilidad, Otra"
        assert "[" not in texto
        assert "]" not in texto
        assert "'" not in texto

    def test_render_previous_list_omits_empty_and_none_items(self, qapp):
        """2.3: None y "" no generan separadores vacíos ni alteran el orden."""
        redmine = MagicMock()
        dlg = _make_dialog(redmine, [_field(1, "Libre", "")])

        assert dlg._render_previous_text(
            [None, "A", "", "B", None]
        ) == "A, B"
        assert dlg._render_previous_text([None, ""]) == ""
        assert dlg._render_previous_text("escalar") == "escalar"

    def test_fallback_string_accept_unchanged_resends_original_list(self, qapp):
        """3.1: aceptar sin cambios reenvía la lista original en QLineEdit."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Libre", "")],
            task_data=_edit_task_data({1: ["A", "B"]}),
        )

        assert dlg.custom_fields == {1: ["A", "B"]}

    def test_fallback_text_accept_unchanged_resends_original_list(self, qapp):
        """3.1: aceptar sin cambios reenvía la lista original en QPlainTextEdit."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Largo", "text")],
            task_data=_edit_task_data({1: ["A", "B"]}),
        )

        assert dlg.custom_fields == {1: ["A", "B"]}

    def test_fallback_string_unchanged_list_with_spaces_preserves_elements(self, qapp):
        """3.2: el texto crudo sin strip conserva los espacios de los elementos."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Libre", "")],
            task_data=_edit_task_data({1: [" A", "B"]}),
        )

        assert dlg._custom_field_widgets[1]["widget"].text() == " A, B"
        assert dlg.custom_fields == {1: [" A", "B"]}

    def test_fallback_string_edited_resends_single_item_list(self, qapp):
        """3.4: editar el texto envía una lista de un elemento."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Libre", "")],
            task_data=_edit_task_data({1: ["A", "B"]}),
        )

        dlg._custom_field_widgets[1]["widget"].setText("Solo este")

        assert dlg.custom_fields == {1: ["Solo este"]}

    def test_fallback_string_cleared_resends_empty_list_not_empty_string(self, qapp):
        """3.6: vaciar un campo con previo lista envía [] y nunca ""."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Libre", "")],
            task_data=_edit_task_data({1: ["A", "B"]}),
        )

        dlg._custom_field_widgets[1]["widget"].setText("")

        assert dlg.custom_fields == {1: []}
        assert dlg.custom_fields != {1: ""}

    def test_fallback_string_commas_are_single_item(self, qapp):
        """3.8: las comas editadas no separan elementos (limitación de D2).

        Se parte de un previo distinto de "A, B": si el previo fuese ["A", "B"],
        el texto editado "A, B" coincidiría con el render sin cambios y D2 lo
        trataría como aceptación sin modificar (no es observable una edición).
        """
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Libre", "")],
            task_data=_edit_task_data({1: ["Original"]}),
        )

        dlg._custom_field_widgets[1]["widget"].setText("A, B")

        assert dlg.custom_fields == {1: ["A, B"]}


class TestSimpleListPreviousList:
    """Lista simple con valor previo en forma de lista (D3)."""

    def test_list_kind_with_single_valid_previous_list_selects_value(self, qapp):
        """4.1: una lista de un elemento válido se selecciona y se envía escalar."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(7, "Lista", "list", possible_values=["A", "B"])],
            task_data=_edit_task_data({7: ["A"]}),
        )

        entry = dlg._custom_field_widgets[7]
        assert entry["widget"].currentData() == "A"
        assert not entry.get("previo_no_representable")
        assert dlg.custom_fields == {7: "A"}

    def test_list_kind_with_non_representable_previous_list_is_omitted(self, qapp):
        """4.3: varios elementos o un único inválido se omiten del payload."""
        redmine = MagicMock()
        fields = [_field(7, "Lista", "list", possible_values=["A", "B"])]

        dlg_multi = _make_dialog(
            redmine, fields, task_data=_edit_task_data({7: ["A", "B"]})
        )
        entry_multi = dlg_multi._custom_field_widgets[7]
        assert entry_multi.get("previo_no_representable") is True
        assert dlg_multi.custom_fields == {}

        dlg_invalido = _make_dialog(
            redmine, fields, task_data=_edit_task_data({7: ["Z"]})
        )
        entry_invalido = dlg_invalido._custom_field_widgets[7]
        assert entry_invalido.get("previo_no_representable") is True
        assert dlg_invalido.custom_fields == {}

    def test_no_representable_with_non_empty_serialized_value_is_omitted(self, qapp):
        """4.5: la marca omite el campo aunque el control tenga valor no vacío."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [
                _field(7, "Lista", "list", possible_values=["A", "B"]),
                _field(8, "Multi", "list", multiple=True, possible_values=["A", "B"]),
            ],
            task_data=_edit_task_data({7: ["Z"]}),
        )

        # Un list no representable que ahora tiene una opción válida seleccionada.
        combo = dlg._custom_field_widgets[7]["widget"]
        combo.setCurrentIndex(combo.findData("A"))
        assert dlg._custom_field_widgets[7]["previo_no_representable"] is True

        # Un multiple marcado explícitamente (p. ej. sin opciones) con valor.
        dlg._custom_field_widgets[8]["previo_no_representable"] = True
        dlg._custom_field_widgets[8]["widget"].set_selected_values(["A"])

        assert dlg.custom_fields == {}

    def test_list_without_options_previous_value_is_omitted(self, qapp):
        """4.7: list sin possible_values con previo se marca y se omite."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(7, "Lista", "list", possible_values=[])],
            task_data=_edit_task_data({7: "Antigua"}),
        )

        assert dlg._custom_field_widgets[7]["previo_no_representable"] is True
        assert dlg.custom_fields == {}

    def test_multiple_without_options_previous_value_is_omitted(self, qapp):
        """4.7: multiple sin possible_values con previo se marca y se omite."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(8, "Multi", "list", multiple=True, possible_values=[])],
            task_data=_edit_task_data({8: ["x"]}),
        )

        assert dlg._custom_field_widgets[8]["previo_no_representable"] is True
        assert dlg.custom_fields == {}

    def test_multiple_with_injectable_values_is_not_marked_not_representable(
        self, qapp
    ):
        """4.8: un multiple con opciones inyecta los ausentes y los envía."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(8, "Multi", "list", multiple=True, possible_values=["x", "y"])],
            task_data=_edit_task_data({8: ["x", "z"]}),
        )

        assert not dlg._custom_field_widgets[8].get("previo_no_representable")
        assert dlg.custom_fields == {8: ["x", "z"]}


class TestRegresionesMultivalor:
    """Caracterización: no se reinterpretan strings ni se rompen los múltiples."""

    def test_string_with_brackets_is_treated_as_text(self, qapp):
        """5.1: una cadena con corchetes es texto legítimo, no una lista."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Libre", "")],
            task_data=_edit_task_data({1: "['A']"}),
        )

        assert dlg._custom_field_widgets[1]["widget"].text() == "['A']"
        assert dlg.custom_fields == {1: "['A']"}

    def test_plain_string_previous_value_still_roundtrips(self, qapp):
        """6.1: un string escalar se muestra y se reenvía sin cambios."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Corto", "string"), _field(2, "Largo", "text")],
            task_data=_edit_task_data({1: "hola", 2: "notas\nlargas"}),
        )

        assert dlg._custom_field_widgets[1]["widget"].text() == "hola"
        assert dlg._custom_field_widgets[2]["widget"].toPlainText() == "notas\nlargas"
        assert dlg.custom_fields == {1: "hola", 2: "notas\nlargas"}

    def test_representable_multiple_still_sends_full_list(self, qapp):
        """6.2: un multiple representable mantiene render, inyección y payload."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(8, "Multi", "list", multiple=True, possible_values=["x", "y"])],
            task_data=_edit_task_data({8: ["x", "y"]}),
        )

        assert not dlg._custom_field_widgets[8].get("previo_no_representable")
        assert dlg._custom_field_widgets[8]["widget"].selected_values() == ["x", "y"]
        assert dlg.custom_fields == {8: ["x", "y"]}


class TestObservacionesVerificacion:
    """Observaciones surgidas en la verificación del cambio."""

    def test_edit_matching_previous_render_is_treated_as_unchanged(self, qapp):
        """8.1: una edición indistinguible del render reenvía la lista original."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(1, "Libre", "")],
            task_data=_edit_task_data({1: ["A", "B"]}),
        )

        # Texto idéntico al render sin cambios: no hay forma de observar una
        # edición, así que D2 lo trata como aceptación sin modificar.
        dlg._custom_field_widgets[1]["widget"].setText("A, B")

        assert dlg.custom_fields == {1: ["A", "B"]}
        assert dlg.custom_fields != {1: ["A, B"]}

    def test_multiple_with_empty_or_none_previous_keeps_valid_values(self, qapp):
        """8.2: "" y None no marcan el multiple como no representable."""
        redmine = MagicMock()
        dlg = _make_dialog(
            redmine,
            [_field(8, "Multi", "list", multiple=True, possible_values=["A", "B"])],
            task_data=_edit_task_data({8: ["A", "", None, "B"]}),
        )

        entry = dlg._custom_field_widgets[8]
        assert not entry.get("previo_no_representable")
        assert entry["widget"].selected_values() == ["A", "B"]
        assert dlg.custom_fields == {8: ["A", "B"]}


def test_multiple_long_options_elide_and_keep_full_tooltip(qapp):
    """9.5: el selector múltiple elide por la derecha y conserva el tooltip."""
    redmine = MagicMock()
    largo = "Etiqueta-muy-larga-" * 8
    dlg = _make_dialog(
        redmine,
        [_field(1, "Multi", "list", multiple=True, possible_values=[largo, "Corta"])],
    )

    widget = dlg._custom_field_widgets[1]["widget"]
    assert widget._list.textElideMode() == Qt.TextElideMode.ElideRight
    assert widget._list.item(0).text() == largo
    assert widget._list.item(0).toolTip() == largo
    assert widget._list.item(1).toolTip() == "Corta"

    metrics = QFontMetrics(widget._list.font())
    elided = metrics.elidedText(largo, Qt.TextElideMode.ElideRight, 40)
    assert "…" in elided
    assert len(elided) < len(largo)


def test_multiple_uncheck_all_injected_values_sends_empty_list(qapp):
    """9.6: desmarcar todos los valores (incluido el inyectado) envía []."""
    redmine = MagicMock()
    dlg = _make_dialog(
        redmine,
        [_field(8, "Multi", "list", multiple=True, possible_values=["x", "y"])],
        task_data=_edit_task_data({8: ["x", "z"]}),
    )

    widget = dlg._custom_field_widgets[8]["widget"]
    for i in range(widget._list.count()):
        widget._list.item(i).setCheckState(Qt.CheckState.Unchecked)

    assert dlg.custom_fields == {8: []}
    assert dlg.custom_fields != {8: ""}
