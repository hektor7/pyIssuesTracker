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
from PyQt6.QtWidgets import QFrame, QLineEdit

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
