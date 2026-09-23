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

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QLineEdit

from app.dialogs.task_dialog import TaskDialog
from app.services.redmine_client import RedmineCustomField


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
        selected = [
            w[5]["widget"].item(i).text()
            for i in range(w[5]["widget"].count())
            if w[5]["widget"].item(i).isSelected()
        ]
        assert selected == ["x", "y"]

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
        w[8]["widget"].item(0).setSelected(True)
        w[8]["widget"].item(2).setSelected(True)

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