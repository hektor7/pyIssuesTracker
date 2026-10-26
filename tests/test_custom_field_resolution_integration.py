"""Integración de la resolución de campos personalizados con TaskDialog.

Usa un `RedmineClient` real con `_get`/`_get_text` mockeados para recorrer
la cascada completa (pertenencia → admin → HTML) hasta el widget del diálogo.
"""

from unittest.mock import MagicMock

from PyQt6.QtWidgets import QComboBox, QLabel, QLineEdit

from app.dialogs.task_dialog import TaskDialog
from app.services.redmine_client import (
    RedmineAuthError,
    RedmineClient,
    RedmineCustomField,
    RedmineError,
)
from app.widgets.multi_value_combo import TEXTO_SIN_OPCIONES, MultiValueCombo


def _membership(*entries):
    """Respuesta de pertenencia con solo id y nombre (Redmine real)."""
    return {
        "project": {
            "issue_custom_fields": [
                {"id": cf_id, "name": name} for cf_id, name in entries
            ]
        }
    }


def _admin_def(cf_id, name, *, field_format="string", multiple=False,
               possible_values=None, is_required=False, default_value=""):
    """Entrada de `/custom_fields.json`."""
    return {
        "id": cf_id,
        "name": name,
        "customized_type": "issue",
        "field_format": field_format,
        "multiple": multiple,
        "possible_values": possible_values if possible_values is not None else [],
        "is_required": is_required,
        "default_value": default_value,
        "visible": True,
        "editable": True,
    }


def _select_html(cf_id, options, *, multiple=False):
    """Formulario HTML mínimo con un select reconocible."""
    sufijo = "[]" if multiple else ""
    atributo = ' multiple="multiple"' if multiple else ""
    opciones = "".join(
        f'<option value="{valor}">{valor}</option>' for valor in options
    )
    return (
        f'<select name="issue[custom_field_values][{cf_id}]{sufijo}"{atributo}>'
        f'<option value=""></option>{opciones}</select>'
    )


def _client(*, membership, admin_responses, html="", session_cookie=""):
    """Cliente real con HTTP mockeado para todas las llamadas del diálogo."""
    client = RedmineClient(
        "https://redmine.example.com",
        "token",
        session_cookie=session_cookie,
    )
    respuestas = list(admin_responses)
    estado = {"indice": 0}

    def fake_get(path, params=None):
        if path == "/custom_fields.json":
            indice = estado["indice"]
            estado["indice"] += 1
            if indice >= len(respuestas):
                raise AssertionError("Petición inesperada a /custom_fields.json")
            respuesta = respuestas[indice]
            if isinstance(respuesta, Exception):
                raise respuesta
            return respuesta
        if path == "/projects/1.json":
            include = (params or {}).get("include")
            if include == "trackers":
                return {"project": {"trackers": [{"id": 1, "name": "Bug"}]}}
            return membership
        if path == "/projects/1/issue_categories.json":
            return {"issue_categories": []}
        if path == "/projects/1/memberships.json":
            return {"memberships": []}
        raise AssertionError(f"Ruta inesperada: {path}")

    client._get = MagicMock(side_effect=fake_get)
    client._get_text = MagicMock(return_value=html)
    return client


def _dialog(client):
    return TaskDialog(
        projects=[(1, "Proyecto")],
        default_project_id=1,
        redmine_client=client,
    )


def _mock_field(cf_id, name, *, fmt="string", **kwargs):
    return RedmineCustomField(id=cf_id, name=name, field_format=fmt, **kwargs)


def _dialog_with_fields(fields, task_data=None):
    redmine = MagicMock()
    redmine.get_project_custom_fields.return_value = fields
    return TaskDialog(
        projects=[(1, "Proyecto")],
        default_project_id=1,
        redmine_client=redmine,
        task_data=task_data,
    )


def _edit_task_data(custom_fields):
    return {
        "id": 9,
        "project_id": 1,
        "tracker_id": 1,
        "priority_id": 2,
        "status_id": 1,
        "subject": "Tarea existente",
        "description": "",
        "custom_fields": custom_fields,
    }


class TestListaResuelta:
    """5.1–5.6: la resolución llega al widget correcto."""

    def test_lista_resuelta_por_admin_se_renderiza_como_combo(self, qapp):
        client = _client(
            membership=_membership((3, "Severidad")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(
                        3,
                        "Severidad",
                        field_format="list",
                        possible_values=["Baja", "Alta"],
                    )
                ]
            }],
        )

        dlg = _dialog(client)

        combo = dlg._custom_field_widgets[3]["widget"]
        assert isinstance(combo, QComboBox)
        assert [
            combo.itemText(i) for i in range(combo.count())
        ] == ["", "Baja", "Alta"]
        assert combo.isEnabled() is True

    def test_lista_resuelta_por_html_se_renderiza_como_combo(self, qapp):
        client = _client(
            membership=_membership((3, "Severidad")),
            admin_responses=[
                RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)
            ],
            html=_select_html(3, ["Baja", "Alta"]),
            session_cookie="session=x",
        )

        dlg = _dialog(client)

        combo = dlg._custom_field_widgets[3]["widget"]
        assert isinstance(combo, QComboBox)
        assert [
            combo.itemText(i) for i in range(combo.count())
        ] == ["", "Baja", "Alta"]
        assert dlg._custom_field_widgets[3]["field"].definition_source == "html"

    def test_multiple_resuelto_se_renderiza_como_multivalue(self, qapp):
        client = _client(
            membership=_membership((4, "Etiquetas")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(
                        4,
                        "Etiquetas",
                        field_format="list",
                        multiple=True,
                        possible_values=["Rojo", "Verde"],
                    )
                ]
            }],
        )

        dlg = _dialog(client)

        widget = dlg._custom_field_widgets[4]["widget"]
        assert isinstance(widget, MultiValueCombo)
        assert widget._list.count() == 2
        assert [
            widget._list.item(i).text() for i in range(widget._list.count())
        ] == ["Rojo", "Verde"]


class TestFallbacksDialogo:
    """5.7–5.8: comportamiento ya especificado de los fallbacks."""

    def test_definicion_no_resoluble_sigue_siendo_qlineedit(self, qapp):
        client = _client(
            membership=_membership((3, "Libre")),
            admin_responses=[
                RedmineError("Error HTTP 500", status_code=500)
            ],
        )

        dlg = _dialog(client)

        widget = dlg._custom_field_widgets[3]["widget"]
        assert isinstance(widget, QLineEdit)
        assert dlg._custom_field_widgets[3]["field"].definition_source == "none"

    def test_lista_conocida_sin_opciones_muestra_combo_deshabilitado(self, qapp):
        client = _client(
            membership=_membership((3, "Lista")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(
                        3,
                        "Lista",
                        field_format="list",
                        possible_values=[],
                    )
                ]
            }],
        )

        dlg = _dialog(client)

        combo = dlg._custom_field_widgets[3]["widget"]
        assert isinstance(combo, QComboBox)
        assert combo.isEnabled() is False
        assert combo.count() == 1
        assert combo.itemText(0) == TEXTO_SIN_OPCIONES


class TestPayload:
    """5.9–5.10: el payload no cambia si la resolución no aporta nada nuevo."""

    def test_payload_sin_informacion_nueva_no_cambia(self, qapp):
        fields = [
            _mock_field(
                3, "Lista", fmt="list", possible_values=["A", "B"],
                definition_source="admin",
            ),
            _mock_field(
                4, "Multiple", fmt="list", multiple=True,
                possible_values=["X", "Y"], definition_source="admin",
            ),
            _mock_field(
                5, "Libre", fmt="", definition_source="none",
                degraded_reason="sin Cookie de sesión",
            ),
        ]
        dlg = _dialog_with_fields(fields)

        combo = dlg._custom_field_widgets[3]["widget"]
        combo.setCurrentIndex(combo.findData("A"))
        dlg._custom_field_widgets[4]["widget"].set_selected_values(["X"])
        dlg._custom_field_widgets[5]["widget"].setText("texto libre")

        assert dlg.custom_fields == {
            3: "A",
            4: ["X"],
            5: "texto libre",
        }

    def test_aceptar_sin_cambios_conserva_representables_y_omite_no_representables(
        self, qapp
    ):
        """El list simple no representable se omite; el múltiple se conserva."""
        fields = [
            _mock_field(
                3, "Representable", fmt="list", possible_values=["A", "B"],
                definition_source="admin",
            ),
            _mock_field(
                4, "No representable", fmt="list", possible_values=["A", "B"],
                definition_source="admin",
            ),
            _mock_field(
                5, "Multiple no representable", fmt="list", multiple=True,
                possible_values=["A", "B"], definition_source="admin",
            ),
            _mock_field(
                6, "Libre", fmt="", definition_source="none",
                degraded_reason="sin Cookie de sesión",
            ),
        ]
        dlg = _dialog_with_fields(
            fields,
            task_data=_edit_task_data({
                3: "A",
                4: "Z",
                5: ["Z"],
                6: "valor previo",
            }),
        )

        # El list simple "Z" no se puede inyectar y se omite (no se borra en
        # Redmine). El múltiple inyecta "Z" y lo conserva en el payload.
        assert dlg.custom_fields == {
            3: "A",
            5: ["Z"],
            6: "valor previo",
        }


class TestDefinicionAdmin:
    """5.11–5.16: obligatoriedad y valor por defecto de la definición."""

    def test_is_required_de_la_definicion_muestra_asterisco(self, qapp):
        client = _client(
            membership=_membership((3, "Severidad")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(
                        3,
                        "Severidad",
                        field_format="list",
                        possible_values=["Baja", "Alta"],
                        is_required=True,
                    )
                ]
            }],
        )

        dlg = _dialog(client)

        widget = dlg._custom_field_widgets[3]["widget"]
        etiqueta = dlg._custom_fields_form.labelForField(widget)
        assert "*" in etiqueta.text()

    def test_default_value_de_la_definicion_se_aplica_en_alta(self, qapp):
        client = _client(
            membership=_membership((3, "Severidad")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(
                        3,
                        "Severidad",
                        field_format="list",
                        possible_values=["Baja", "Alta"],
                        default_value="Baja",
                    )
                ]
            }],
        )

        dlg = _dialog(client)

        combo = dlg._custom_field_widgets[3]["widget"]
        assert combo.currentData() == "Baja"
        assert dlg.custom_fields == {3: "Baja"}

    def test_html_no_anade_asterisco_ni_default_distintos(self, qapp):
        client = _client(
            membership=_membership((3, "Severidad")),
            admin_responses=[
                RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)
            ],
            html=_select_html(3, ["Baja", "Alta"]),
            session_cookie="session=x",
        )

        dlg = _dialog(client)

        campo = dlg._custom_field_widgets[3]["field"]
        widget = dlg._custom_field_widgets[3]["widget"]
        etiqueta = dlg._custom_fields_form.labelForField(widget)

        assert campo.definition_source == "html"
        assert campo.is_required is False
        assert campo.default_value == ""
        assert "*" not in etiqueta.text()
        # Sin valor previo ni default, el campo vacío no se envía.
        assert 3 not in dlg.custom_fields


class TestAvisoDegradacion:
    """5.17–5.20: aviso visible cuando algún campo queda sin definición."""

    def test_aviso_visible_cuando_hay_campos_sin_definicion(self, qapp):
        client = _client(
            membership=_membership((3, "Libre")),
            admin_responses=[
                RedmineError("Error HTTP 500", status_code=500)
            ],
        )

        dlg = _dialog(client)

        aviso = dlg._custom_fields_notice
        assert aviso.isVisibleTo(dlg) is True
        texto = aviso.text().lower()
        for palabra in (
            "cookie",
            "ajustes",
            "api key de administrador",
            "texto libre",
        ):
            assert palabra in texto

        avisos = [
            etiqueta
            for etiqueta in dlg._custom_fields_group.findChildren(QLabel)
            if "no se pudieron obtener los tipos" in etiqueta.text().lower()
        ]
        assert len(avisos) == 1
        # Es un aviso discreto embebido, no un diálogo modal.
        assert aviso.isWindow() is False

    def test_sin_aviso_cuando_todo_se_resuelve_o_no_hay_campos(self, qapp):
        client_resuelto = _client(
            membership=_membership((3, "Resuelto")),
            admin_responses=[{
                "custom_fields": [_admin_def(3, "Resuelto", field_format="string")]
            }],
        )
        dlg_resuelto = _dialog(client_resuelto)
        assert dlg_resuelto._custom_fields_notice.isVisibleTo(dlg_resuelto) is False

        client_vacio = _client(
            membership={"project": {"issue_custom_fields": []}},
            admin_responses=[],
        )
        dlg_vacio = _dialog(client_vacio)
        assert dlg_vacio._custom_fields_group.isVisibleTo(dlg_vacio) is False
        assert dlg_vacio._custom_fields_notice.isVisibleTo(dlg_vacio) is False

    def test_aviso_unico_con_varios_campos_degradados(self, qapp):
        client = _client(
            membership=_membership((3, "Uno"), (4, "Dos"), (5, "Tres")),
            admin_responses=[
                RedmineError("Error HTTP 500", status_code=500)
            ],
        )

        dlg = _dialog(client)

        assert dlg._custom_fields_notice.isVisibleTo(dlg) is True
        avisos = [
            etiqueta
            for etiqueta in dlg._custom_fields_group.findChildren(QLabel)
            if "no se pudieron obtener los tipos" in etiqueta.text().lower()
        ]
        assert len(avisos) == 1

    def test_aviso_se_limpia_al_cambiar_de_proyecto(self, qapp):
        degradado = _mock_field(
            3, "Degradado", fmt="", definition_source="none",
            degraded_reason="sin Cookie de sesión",
        )
        resuelto = _mock_field(
            4, "Resuelto", fmt="string", definition_source="admin",
        )
        redmine = MagicMock()
        redmine.get_project_custom_fields.side_effect = (
            lambda pid: [degradado] if pid == 1 else [resuelto]
        )
        dlg = TaskDialog(
            projects=[(1, "P1"), (2, "P2")],
            default_project_id=1,
            redmine_client=redmine,
        )
        assert dlg._custom_fields_notice.isVisibleTo(dlg) is True

        dlg._project_combo.setCurrentIndex(1)

        assert dlg._custom_fields_notice.isVisibleTo(dlg) is False

    def test_multiple_resuelto_por_html_se_renderiza_como_multivalue(self, qapp):
        """7.3: un select multiple del HTML llega como MultiValueCombo."""
        client = _client(
            membership=_membership((4, "Etiquetas")),
            admin_responses=[
                RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)
            ],
            html=_select_html(4, ["Rojo", "Verde"], multiple=True),
            session_cookie="session=x",
        )

        dlg = _dialog(client)

        campo = dlg._custom_field_widgets[4]["field"]
        widget = dlg._custom_field_widgets[4]["widget"]
        assert isinstance(widget, MultiValueCombo)
        assert [
            widget._list.item(i).text() for i in range(widget._list.count())
        ] == ["Rojo", "Verde"]
        assert campo.definition_source == "html"
        assert campo.multiple is True

    def test_fallo_de_pertenencia_oculta_grupo_y_aviso(self, qapp):
        """R5-S3: si falla la pertenencia, grupo y aviso quedan ocultos."""
        redmine = MagicMock()
        redmine.get_project_custom_fields.side_effect = RedmineError(
            "sin acceso al proyecto"
        )

        dlg = TaskDialog(
            projects=[(1, "Proyecto")],
            default_project_id=1,
            redmine_client=redmine,
        )

        assert dlg._custom_fields_group.isVisibleTo(dlg) is False
        assert dlg._custom_fields_notice.isVisibleTo(dlg) is False
