"""Tests TDD para campos personalizados en RedmineClient.

Cubren:
- Obtención de campos personalizados de un proyecto.
- Parseo de valores en RedmineIssue y en get_issue_with_journals.
- Serialización en create_issue / update_issue.
"""

import logging
from unittest.mock import MagicMock, call

import pytest

from app.services.redmine_client import (
    RedmineClient,
    RedmineCustomField,
    RedmineError,
    RedmineIssue,
    RedmineAuthError,
    RedmineConnectionError,
    RedmineSSOError,
)


@pytest.fixture
def client():
    c = RedmineClient("https://redmine.example.com", "token")
    c._get = MagicMock()
    c._get_text = MagicMock()
    c._post = MagicMock()
    c._put = MagicMock()
    return c


@pytest.fixture
def cookie_client(client):
    """Cliente con Cookie de sesión configurada (necesaria para el HTML)."""
    client._session_cookie = "redmine_session=abc123"
    return client


def _membership(*entries):
    """Respuesta de pertenencia con solo id y nombre (como Redmine real)."""
    return {
        "project": {
            "issue_custom_fields": [
                {"id": cf_id, "name": name} for cf_id, name in entries
            ]
        }
    }


def _admin_def(cf_id, name, *, customized_type="issue", field_format="string",
               multiple=False, possible_values=None, is_required=False,
               default_value="", visible=True, editable=True):
    """Entrada de definición tal y como la devuelve /custom_fields.json."""
    return {
        "id": cf_id,
        "name": name,
        "customized_type": customized_type,
        "field_format": field_format,
        "multiple": multiple,
        "possible_values": possible_values if possible_values is not None else [],
        "is_required": is_required,
        "default_value": default_value,
        "visible": visible,
        "editable": editable,
    }


def _route(client, membership, admin_responses):
    """Enruta `_get` entre la pertenencia y las páginas de definiciones.

    Cada elemento de `admin_responses` puede ser un dict (respuesta) o una
    excepción que se lanzará al pedir `/custom_fields.json`.
    """
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
        if path.startswith("/projects/"):
            if isinstance(membership, Exception):
                raise membership
            return membership
        raise AssertionError(f"Ruta inesperada: {path}")

    client._get.side_effect = fake_get
    return fake_get


def _route_projects(client, memberships, admin_responses):
    """Como `_route`, pero con una pertenencia distinta por id de proyecto."""
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
        if path.startswith("/projects/"):
            project_id = int(path.split("/")[2].split(".")[0])
            pertenencia = memberships[project_id]
            if isinstance(pertenencia, Exception):
                raise pertenencia
            return pertenencia
        raise AssertionError(f"Ruta inesperada: {path}")

    client._get.side_effect = fake_get
    return fake_get


def _select_html(cf_id, options, *, multiple=False):
    """Formulario HTML mínimo con un select de campo personalizado."""
    sufijo = "[]" if multiple else ""
    atributo = ' multiple="multiple"' if multiple else ""
    opciones = "".join(
        f'<option value="{valor}">{valor}</option>' for valor in options
    )
    return (
        f'<select name="issue[custom_field_values][{cf_id}]{sufijo}"{atributo}>'
        f'<option value=""></option>{opciones}</select>'
    )


class TestGetProjectCustomFields:
    """get_project_custom_fields(project_id): pertenencia + definiciones."""

    def test_maps_entries_using_admin_definitions(self, client):
        """La definición completa procede de /custom_fields.json."""
        _route(
            client,
            membership=_membership((3, "Severidad"), (4, "Notas extra")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(4, "Notas extra (admin)", field_format="text"),
                    _admin_def(
                        3,
                        "Severidad (admin)",
                        field_format="list",
                        possible_values=["Baja", "Alta"],
                        is_required=True,
                        default_value="Baja",
                    ),
                ]
            }],
        )

        fields = client.get_project_custom_fields(7)

        assert [f.id for f in fields] == [3, 4]
        assert isinstance(fields[0], RedmineCustomField)
        assert fields[0].name == "Severidad"
        assert fields[0].field_format == "list"
        assert fields[0].is_required is True
        assert fields[0].multiple is False
        assert fields[0].possible_values == ["Baja", "Alta"]
        assert fields[0].default_value == "Baja"
        assert fields[1].name == "Notas extra"
        assert fields[1].field_format == "text"

    def test_claves_extra_de_la_pertenencia_se_ignoran(self, client):
        """Claves de definición en la pertenencia no se usan (solo id/nombre)."""
        pertenencia = {
            "project": {
                "issue_custom_fields": [{
                    "id": 3,
                    "name": "Severidad",
                    "field_format": "text",
                    "multiple": True,
                    "possible_values": ["Falso"],
                    "is_required": False,
                }]
            }
        }
        _route(
            client,
            membership=pertenencia,
            admin_responses=[{
                "custom_fields": [
                    _admin_def(
                        3,
                        "Severidad admin",
                        field_format="list",
                        possible_values=["Baja", "Alta"],
                        is_required=True,
                    )
                ]
            }],
        )

        campo = client.get_project_custom_fields(7)[0]

        assert campo.field_format == "list"
        assert campo.multiple is False
        assert campo.possible_values == ["Baja", "Alta"]
        assert campo.is_required is True

    def test_nombre_de_la_pertenencia_prevalece(self, client):
        """El nombre visible del proyecto manda sobre el de la definición."""
        _route(
            client,
            membership=_membership((3, "Nombre del proyecto")),
            admin_responses=[{
                "custom_fields": [_admin_def(3, "Nombre de administrador")]
            }],
        )

        assert client.get_project_custom_fields(7)[0].name == "Nombre del proyecto"

    def test_orden_de_la_pertenencia_se_preserva(self, client):
        """El orden de salida es el de la pertenencia, no el de la API."""
        _route(
            client,
            membership=_membership((4, "Cuarto"), (3, "Tercero")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(3, "Tercero admin"),
                    _admin_def(4, "Cuarto admin"),
                ]
            }],
        )

        assert [f.id for f in client.get_project_custom_fields(7)] == [4, 3]

    def test_project_without_custom_fields_returns_empty(self, client):
        """Proyecto sin issue_custom_fields devuelve lista vacía sin excepción."""
        _route(
            client,
            membership={"project": {"id": 7, "name": "Proyecto"}},
            admin_responses=[],
        )
        assert client.get_project_custom_fields(7) == []

    def test_project_with_empty_custom_fields_returns_empty(self, client):
        """issue_custom_fields vacío devuelve lista vacía."""
        _route(
            client,
            membership={"project": {"issue_custom_fields": []}},
            admin_responses=[],
        )
        assert client.get_project_custom_fields(7) == []


class TestParseCustomFields:
    """Parseo de custom_fields en _issue_from_json."""

    def test_issue_from_json_parses_custom_fields(self):
        """custom_fields se convierte en dict id -> valor."""
        issue = RedmineClient._issue_from_json({
            "id": 1,
            "subject": "T",
            "custom_fields": [
                {"id": 3, "value": "Alta"},
                {"id": 4, "value": "texto"},
            ],
        })
        assert isinstance(issue, RedmineIssue)
        assert issue.custom_fields == {3: "Alta", 4: "texto"}

    def test_issue_from_json_parses_multiple_value(self):
        """Un valor múltiple (lista) se conserva como lista."""
        issue = RedmineClient._issue_from_json({
            "id": 1,
            "subject": "T",
            "custom_fields": [{"id": 5, "value": ["x", "y"]}],
        })
        assert issue.custom_fields == {5: ["x", "y"]}

    def test_issue_from_json_without_custom_fields(self):
        """Ausencia de la clave custom_fields devuelve dict vacío."""
        issue = RedmineClient._issue_from_json({"id": 1, "subject": "T"})
        assert issue.custom_fields == {}


class TestGetIssueWithJournalsCustomFields:
    """get_issue_with_journals incluye _custom_fields."""

    def test_includes_custom_fields(self, client):
        client._get.return_value = {
            "issue": {
                "id": 42,
                "subject": "T",
                "custom_fields": [{"id": 3, "value": "Alta"}],
            }
        }
        data = client.get_issue_with_journals(42)
        assert data["_custom_fields"] == {3: "Alta"}

    def test_without_custom_fields(self, client):
        client._get.return_value = {"issue": {"id": 42, "subject": "T"}}
        data = client.get_issue_with_journals(42)
        assert data["_custom_fields"] == {}


class TestCreateIssueCustomFields:
    """create_issue serializa custom_fields."""

    def test_create_issue_serializes_custom_fields(self, client):
        client._post.return_value = {}
        client.create_issue(
            project_id=1,
            subject="T",
            custom_fields={3: "A", 4: ["x", "y"]},
        )
        args, _kwargs = client._post.call_args
        assert args[0] == "/issues.json"
        assert args[1]["issue"]["custom_fields"] == [
            {"id": 3, "value": "A"},
            {"id": 4, "value": ["x", "y"]},
        ]

    def test_create_issue_without_custom_fields_omits_key(self, client):
        client._post.return_value = {}
        client.create_issue(project_id=1, subject="T")
        args, _kwargs = client._post.call_args
        assert "custom_fields" not in args[1]["issue"]

    def test_create_issue_omits_none_values(self, client):
        """S4: las entradas con valor None no se envían en custom_fields."""
        client._post.return_value = {}
        client.create_issue(
            project_id=1,
            subject="T",
            custom_fields={3: "A", 4: None, 5: "B"},
        )
        args, _kwargs = client._post.call_args
        assert args[1]["issue"]["custom_fields"] == [
            {"id": 3, "value": "A"},
            {"id": 5, "value": "B"},
        ]

    def test_create_issue_with_empty_dict_omits_key(self, client):
        client._post.return_value = {}
        client.create_issue(project_id=1, subject="T", custom_fields={})
        args, _kwargs = client._post.call_args
        assert "custom_fields" not in args[1]["issue"]


class TestUpdateIssueCustomFields:
    """update_issue serializa custom_fields."""

    def test_update_issue_serializes_custom_fields(self, client):
        client._put.return_value = {}
        client.update_issue(42, custom_fields={3: "Baja"})
        client._put.assert_called_once_with(
            "/issues/42.json",
            {"issue": {"custom_fields": [{"id": 3, "value": "Baja"}]}},
        )

    def test_update_issue_allows_clearing_with_empty_string(self, client):
        """Un valor "" se incluye para permitir limpiar el campo."""
        client._put.return_value = {}
        client.update_issue(42, custom_fields={3: ""})
        client._put.assert_called_once_with(
            "/issues/42.json",
            {"issue": {"custom_fields": [{"id": 3, "value": ""}]}},
        )

    def test_update_issue_without_custom_fields_omits_key(self, client):
        client._put.return_value = {}
        client.update_issue(42, subject="Nuevo")
        client._put.assert_called_once_with(
            "/issues/42.json", {"issue": {"subject": "Nuevo"}}
        )

    def test_update_issue_with_empty_dict_omits_key(self, client):
        client._put.return_value = {}
        client.update_issue(42, subject="Nuevo", custom_fields={})
        client._put.assert_called_once_with(
            "/issues/42.json", {"issue": {"subject": "Nuevo"}}
        )


class TestFiltradoDefiniciones:
    """4.3: solo definiciones de incidencia y de ids del proyecto."""

    def test_filtra_por_customized_type_issue(self, client):
        """Solo se consideran definiciones con customized_type == "issue"."""
        _route(
            client,
            membership=_membership((3, "Tercero"), (4, "Cuarto")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(3, "Tercero", customized_type="issue"),
                    _admin_def(4, "Cuarto", customized_type="project"),
                ]
            }],
        )

        definiciones = client._fetch_custom_field_definitions()

        assert set(definiciones) == {3}

    def test_filtra_por_ids_de_la_pertenencia(self, client):
        """Una definición de incidencia ajena al proyecto no se devuelve."""
        _route(
            client,
            membership=_membership((3, "Tercero")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(3, "Tercero"),
                    _admin_def(4, "Ajeno al proyecto"),
                ]
            }],
        )

        campos = client.get_project_custom_fields(7)

        assert [cf.id for cf in campos] == [3]


class TestNormalizacionPossibleValues:
    """4.5: `possible_values` acepta objetos {value,label} y cadenas."""

    def test_normaliza_possible_values_en_objetos_y_cadenas(self, client):
        _route(
            client,
            membership=_membership((3, "Campo")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(
                        3,
                        "Campo",
                        field_format="list",
                        possible_values=[
                            {"value": "Baja", "label": "Baja"},
                            {"value": "Alta", "label": "Alta"},
                            "Media",
                            {"value": "Nula"},
                        ],
                    )
                ]
            }],
        )

        definiciones = client._fetch_custom_field_definitions()

        assert definiciones[3].possible_values == [
            "Baja", "Alta", "Media", "Nula"
        ]


class TestPaginacionDefiniciones:
    """4.7: paginación defensiva de /custom_fields.json."""

    def test_pagina_definiciones_con_total_count_mayor_que_la_pagina(self, client):
        _route(
            client,
            membership=_membership((3, "A"), (4, "B"), (5, "C")),
            admin_responses=[
                {
                    "custom_fields": [_admin_def(3, "A")],
                    "total_count": 3,
                },
                {
                    "custom_fields": [_admin_def(4, "B"), _admin_def(5, "C")],
                },
            ],
        )

        definiciones = client._fetch_custom_field_definitions()

        assert set(definiciones) == {3, 4, 5}
        llamadas = client._get.call_args_list
        assert llamadas[0] == call("/custom_fields.json")
        assert llamadas[1].kwargs["params"]["offset"] == 1
        assert "limit" in llamadas[1].kwargs["params"]

    def test_sin_total_count_no_pagina(self, client):
        _route(
            client,
            membership=_membership((3, "A")),
            admin_responses=[{"custom_fields": [_admin_def(3, "A")]}],
        )
        assert set(client._fetch_custom_field_definitions()) == {3}
        client._get.assert_called_once_with("/custom_fields.json")

        client._get.reset_mock()
        _route(
            client,
            membership=_membership((3, "A")),
            admin_responses=[{
                "custom_fields": [_admin_def(3, "A")],
                "total_count": "muchos",
            }],
        )
        assert set(client._fetch_custom_field_definitions()) == {3}
        client._get.assert_called_once_with("/custom_fields.json")


class TestFallbackHTMLAdminAuth:
    """4.9: 401/403 en la API de definiciones activan el formulario HTML."""

    def test_403_en_api_de_definiciones_usa_formulario_html(self, cookie_client):
        _route(
            cookie_client,
            membership=_membership((3, "Severidad")),
            admin_responses=[
                RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)
            ],
        )
        cookie_client._get_text.return_value = _select_html(3, ["Baja", "Alta"])

        campos = cookie_client.get_project_custom_fields(7)

        assert [cf.id for cf in campos] == [3]
        assert campos[0].field_format == "list"
        assert campos[0].possible_values == ["Baja", "Alta"]
        cookie_client._get_text.assert_called_once_with(
            "/projects/7/issues/new"
        )

    def test_401_en_api_de_definiciones_usa_formulario_html(self, cookie_client):
        _route(
            cookie_client,
            membership=_membership((3, "Severidad")),
            admin_responses=[
                RedmineAuthError("API key no válida (HTTP 401)", status_code=401)
            ],
        )
        cookie_client._get_text.return_value = _select_html(3, ["Baja", "Alta"])

        campos = cookie_client.get_project_custom_fields(7)

        assert campos[0].field_format == "list"
        assert campos[0].possible_values == ["Baja", "Alta"]
        cookie_client._get_text.assert_called_once_with(
            "/projects/7/issues/new"
        )


class TestFallbackHTMLAdminOtrosErrores:
    """4.11: 404 y 500 en la API también activan el formulario HTML."""

    def test_404_en_api_de_definiciones_usa_formulario_html(self, cookie_client):
        _route(
            cookie_client,
            membership=_membership((3, "Severidad")),
            admin_responses=[
                RedmineError(
                    "Recurso no encontrado: /custom_fields.json",
                    status_code=404,
                )
            ],
        )
        cookie_client._get_text.return_value = _select_html(3, ["Baja", "Alta"])

        campos = cookie_client.get_project_custom_fields(7)

        assert campos[0].field_format == "list"
        assert campos[0].possible_values == ["Baja", "Alta"]

    def test_500_en_api_de_definiciones_usa_formulario_html(self, cookie_client):
        _route(
            cookie_client,
            membership=_membership((3, "Severidad")),
            admin_responses=[
                RedmineError("Error HTTP 500 en /custom_fields.json", status_code=500)
            ],
        )
        cookie_client._get_text.return_value = _select_html(3, ["Baja", "Alta"])

        campos = cookie_client.get_project_custom_fields(7)

        assert campos[0].field_format == "list"
        assert campos[0].possible_values == ["Baja", "Alta"]


class TestFallbackHTMLAdminConexion:
    """4.13: timeout y error de conexión también degradan al formulario HTML."""

    def test_timeout_en_api_de_definiciones_usa_formulario_html(self, cookie_client):
        _route(
            cookie_client,
            membership=_membership((3, "Severidad")),
            admin_responses=[
                RedmineConnectionError("Timeout al conectar al servidor Redmine")
            ],
        )
        cookie_client._get_text.return_value = _select_html(3, ["Baja", "Alta"])

        campos = cookie_client.get_project_custom_fields(7)

        assert campos[0].field_format == "list"
        assert campos[0].possible_values == ["Baja", "Alta"]

    def test_error_de_conexion_en_api_de_definiciones_usa_formulario_html(
        self, cookie_client
    ):
        _route(
            cookie_client,
            membership=_membership((3, "Severidad")),
            admin_responses=[
                RedmineConnectionError(
                    "No se pudo conectar al servidor Redmine: boom"
                )
            ],
        )
        cookie_client._get_text.return_value = _select_html(3, ["Baja", "Alta"])

        campos = cookie_client.get_project_custom_fields(7)

        assert campos[0].field_format == "list"
        assert campos[0].possible_values == ["Baja", "Alta"]


class TestDegradacionSinCookie:
    """4.15: sin Cookie no se pide el formulario y el campo degrada a texto."""

    def test_sin_cookie_no_pide_formulario_y_degrada_a_texto(
        self, client, caplog
    ):
        _route(
            client,
            membership=_membership((3, "Severidad")),
            admin_responses=[
                RedmineError("Error HTTP 500 en /custom_fields.json", status_code=500)
            ],
        )

        with caplog.at_level(logging.WARNING):
            campos = client.get_project_custom_fields(7)

        client._get_text.assert_not_called()
        assert len(campos) == 1
        campo = campos[0]
        assert campo.id == 3
        assert campo.name == "Severidad"
        assert campo.field_format == ""
        assert campo.multiple is False
        assert campo.possible_values == []
        assert campo.definition_source == "none"
        assert "Cookie" in campo.degraded_reason
        assert "Cookie" in caplog.text


class TestDefinicionesParciales:
    """4.17: la API de administrador puede cubrir solo parte de los ids."""

    def test_definiciones_parciales_se_completan_con_html(self, cookie_client):
        _route(
            cookie_client,
            membership=_membership((3, "Tercero"), (4, "Cuarto")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(
                        3,
                        "Tercero",
                        field_format="list",
                        possible_values=["Baja", "Alta"],
                    )
                ]
            }],
        )
        cookie_client._get_text.return_value = _select_html(4, ["Uno", "Dos"])

        campos = cookie_client.get_project_custom_fields(7)

        assert [cf.id for cf in campos] == [3, 4]
        assert campos[0].field_format == "list"
        assert campos[0].possible_values == ["Baja", "Alta"]
        assert campos[0].definition_source == "admin"
        assert campos[1].field_format == "list"
        assert campos[1].possible_values == ["Uno", "Dos"]
        assert campos[1].definition_source == "html"
        cookie_client._get_text.assert_called_once_with("/projects/7/issues/new")


class TestFormularioSinCampo:
    """4.19: un campo ausente del formulario degrada solo a ese campo."""

    def test_formulario_sin_el_campo_degrada_solo_ese_campo(
        self, cookie_client, caplog
    ):
        _route(
            cookie_client,
            membership=_membership((3, "Tercero"), (4, "Cuarto")),
            admin_responses=[
                RedmineError("Error HTTP 500 en /custom_fields.json", status_code=500)
            ],
        )
        cookie_client._get_text.return_value = _select_html(3, ["Uno", "Dos"])

        with caplog.at_level(logging.WARNING):
            campos = cookie_client.get_project_custom_fields(7)

        assert campos[0].id == 3
        assert campos[0].field_format == "list"
        assert campos[0].definition_source == "html"
        assert campos[1].id == 4
        assert campos[1].field_format == ""
        assert campos[1].definition_source == "none"
        assert "formulario" in campos[1].degraded_reason.lower()
        assert "Cuarto" in caplog.text


class TestFallosHTMLSinExcepcion:
    """4.21: los fallos del HTML degradan sin propagar excepciones."""

    def test_redireccion_a_login_degrada_sin_excepcion(
        self, cookie_client, caplog
    ):
        _route(
            cookie_client,
            membership=_membership((3, "Tercero")),
            admin_responses=[
                RedmineError("Error HTTP 500 en /custom_fields.json", status_code=500)
            ],
        )
        cookie_client._get_text.side_effect = RedmineSSOError(
            "Redireccion inesperada [302] en '/projects/7/issues/new'.",
            location="/login",
        )

        with caplog.at_level(logging.WARNING):
            campos = cookie_client.get_project_custom_fields(7)

        assert campos[0].definition_source == "none"
        assert "Cookie" in campos[0].degraded_reason
        assert cookie_client._issue_form_auth_failure is not None

    def test_html_sin_controles_degrada_sin_excepcion(
        self, cookie_client, caplog
    ):
        _route(
            cookie_client,
            membership=_membership((3, "Tercero")),
            admin_responses=[
                RedmineError("Error HTTP 500 en /custom_fields.json", status_code=500)
            ],
        )
        cookie_client._get_text.return_value = (
            '<html><body><form id="new_issue"></form></body></html>'
        )

        with caplog.at_level(logging.WARNING):
            campos = cookie_client.get_project_custom_fields(7)

        assert campos[0].definition_source == "none"
        assert "controles" in campos[0].degraded_reason
        # Un 200 válido sin controles NO fija el fallo global de autenticación.
        assert cookie_client._issue_form_auth_failure is None


class TestPertenencia:
    """4.23: el fallo de la pertenencia se propaga y no se cachea."""

    def test_fallo_de_pertenencia_se_propaga_como_redmine_error(self, client):
        _route(
            client,
            membership=RedmineError("sin acceso al proyecto"),
            admin_responses=[],
        )

        with pytest.raises(RedmineError):
            client.get_project_custom_fields(7)
        assert 7 not in client._project_custom_fields

        with pytest.raises(RedmineError):
            client.get_project_custom_fields(7)


class TestProyectoSinCampos:
    """4.25: sin pertenencia no se consultan definiciones ni HTML."""

    def test_proyecto_sin_campos_no_consulta_definiciones(self, client):
        _route(
            client,
            membership={"project": {"issue_custom_fields": []}},
            admin_responses=[],
        )

        assert client.get_project_custom_fields(7) == []
        client._get.assert_called_once_with(
            "/projects/7.json", params={"include": "issue_custom_fields"}
        )
        client._get_text.assert_not_called()


class TestCachePorProyecto:
    """4.27: la segunda llamada del mismo proyecto no repite peticiones."""

    def test_cache_por_proyecto_no_repite_peticiones(self, client):
        _route(
            client,
            membership=_membership((3, "Tercero")),
            admin_responses=[{"custom_fields": [_admin_def(3, "Tercero")]}],
        )

        primera = client.get_project_custom_fields(7)
        assert client._get.call_count == 2

        segunda = client.get_project_custom_fields(7)
        assert client._get.call_count == 2
        assert segunda == primera


class TestCacheGlobalDefiniciones:
    """4.29: las definiciones de administrador se piden una sola vez."""

    def test_cache_global_de_definiciones_entre_proyectos(self, client):
        memberships = {
            pid: _membership((3, "Tercero")) for pid in (1, 2, 3)
        }
        llamadas = {"admin": 0}

        def fake_get(path, params=None):
            if path == "/custom_fields.json":
                llamadas["admin"] += 1
                return {"custom_fields": [_admin_def(3, "Tercero")]}
            project_id = int(path.split("/")[2].split(".")[0])
            return memberships[project_id]

        client._get.side_effect = fake_get

        for pid in (1, 2, 3):
            assert [cf.id for cf in client.get_project_custom_fields(pid)] == [3]

        assert llamadas["admin"] == 1


class TestCacheNegativaAdmin:
    """4.31: los fallos de administrador y la ausencia de Cookie se memorizan."""

    def test_403_memorizado_entre_proyectos(self, cookie_client):
        memberships = {
            1: _membership((3, "Tercero")),
            2: _membership((4, "Cuarto")),
        }
        _route_projects(
            cookie_client,
            memberships,
            [RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)],
        )
        html_por_ruta = {
            "/projects/1/issues/new": _select_html(3, ["Uno"]),
            "/projects/2/issues/new": _select_html(4, ["Dos"]),
        }
        cookie_client._get_text.side_effect = lambda path: html_por_ruta[path]

        primero = cookie_client.get_project_custom_fields(1)
        segundo = cookie_client.get_project_custom_fields(2)

        assert primero[0].possible_values == ["Uno"]
        assert segundo[0].possible_values == ["Dos"]
        # Una sola llamada a /custom_fields.json y una por proyecto al HTML.
        assert cookie_client._get_text.call_count == 2

    def test_ausencia_de_cookie_memorizada(self, client):
        memberships = {
            1: _membership((3, "Tercero")),
            2: _membership((4, "Cuarto")),
        }
        _route_projects(
            client,
            memberships,
            [RedmineError("Error HTTP 500", status_code=500)],
        )

        primero = client.get_project_custom_fields(1)
        segundo = client.get_project_custom_fields(2)

        assert primero[0].definition_source == "none"
        assert segundo[0].definition_source == "none"
        client._get_text.assert_not_called()


class TestCacheNegativaHTML:
    """4.33: solo los fallos de autenticación del HTML se memorizan global."""

    def test_fallo_de_login_html_memorizado_globalmente(self, cookie_client):
        memberships = {
            1: _membership((3, "Tercero")),
            2: _membership((4, "Cuarto")),
        }
        _route_projects(
            cookie_client,
            memberships,
            [RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)],
        )
        cookie_client._get_text.side_effect = RedmineSSOError(
            "Redireccion inesperada [302] en '/projects/1/issues/new'.",
            location="/login",
        )

        primero = cookie_client.get_project_custom_fields(1)
        segundo = cookie_client.get_project_custom_fields(2)

        assert primero[0].definition_source == "none"
        assert segundo[0].definition_source == "none"
        assert cookie_client._get_text.call_count == 1
        assert cookie_client._issue_form_auth_failure is not None

    def test_redireccion_benigna_no_marca_fallo_global(self, cookie_client):
        """W1: una redirección no-login degrada solo ese proyecto."""
        memberships = {
            1: _membership((3, "Tercero")),
            2: _membership((4, "Cuarto")),
        }
        _route_projects(
            cookie_client,
            memberships,
            [RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)],
        )

        def fake_html(path):
            if path == "/projects/1/issues/new":
                raise RedmineSSOError(
                    "Redireccion inesperada [302] en '/projects/1/issues/new'.",
                    location="/projects/1/issues/new/",
                )
            return _select_html(4, ["Uno", "Dos"])

        cookie_client._get_text.side_effect = fake_html

        primero = cookie_client.get_project_custom_fields(1)
        segundo = cookie_client.get_project_custom_fields(2)

        assert primero[0].definition_source == "none"
        assert "redirecci" in primero[0].degraded_reason.lower()
        assert cookie_client._issue_form_auth_failure is None
        assert segundo[0].definition_source == "html"
        assert segundo[0].possible_values == ["Uno", "Dos"]
        assert cookie_client._get_text.call_count == 2

    @pytest.mark.parametrize("status", [401, 403])
    def test_401_403_en_html_marcan_fallo_global(self, cookie_client, status):
        """W1: 401/403 del formulario fijan la caché negativa global."""
        memberships = {
            1: _membership((3, "Tercero")),
            2: _membership((4, "Cuarto")),
        }
        _route_projects(
            cookie_client,
            memberships,
            [RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)],
        )
        cookie_client._get_text.side_effect = RedmineAuthError(
            f"Acceso denegado (HTTP {status})", status_code=status
        )

        primero = cookie_client.get_project_custom_fields(1)
        segundo = cookie_client.get_project_custom_fields(2)

        assert primero[0].definition_source == "none"
        assert segundo[0].definition_source == "none"
        assert cookie_client._get_text.call_count == 1
        assert cookie_client._issue_form_auth_failure is not None

    def test_pagina_de_login_200_memorizada_globalmente(self, cookie_client):
        memberships = {
            1: _membership((3, "Tercero")),
            2: _membership((4, "Cuarto")),
        }
        _route_projects(
            cookie_client,
            memberships,
            [RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)],
        )
        cookie_client._get_text.return_value = (
            '<html><body><form id="login-form">'
            '<input type="text" name="username">'
            '<input type="password" name="password">'
            "</form></body></html>"
        )

        primero = cookie_client.get_project_custom_fields(1)
        segundo = cookie_client.get_project_custom_fields(2)

        assert primero[0].definition_source == "none"
        assert segundo[0].definition_source == "none"
        assert cookie_client._get_text.call_count == 1
        assert cookie_client._issue_form_auth_failure is not None

    def test_formulario_valido_sin_controles_del_proyecto_a_no_impide_resolver_b_por_html(
        self, cookie_client
    ):
        memberships = {
            1: _membership((3, "Tercero")),
            2: _membership((4, "Cuarto")),
        }
        _route_projects(
            cookie_client,
            memberships,
            [RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)],
        )
        html_por_ruta = {
            "/projects/1/issues/new": (
                '<html><body><form id="new_issue"></form></body></html>'
            ),
            "/projects/2/issues/new": _select_html(4, ["Uno", "Dos"]),
        }
        cookie_client._get_text.side_effect = lambda path: html_por_ruta[path]

        primero = cookie_client.get_project_custom_fields(1)
        segundo = cookie_client.get_project_custom_fields(2)

        assert primero[0].definition_source == "none"
        assert cookie_client._issue_form_auth_failure is None
        assert segundo[0].definition_source == "html"
        assert segundo[0].possible_values == ["Uno", "Dos"]
        assert cookie_client._get_text.call_count == 2


class TestInformeODS:
    """4.35: el recorrido de N proyectos hace como máximo una petición fallida."""

    def test_informe_ods_con_n_proyectos_hace_como_maximo_una_peticion_html_fallida(
        self, cookie_client
    ):
        memberships = {
            1: _membership((3, "Tercero")),
            2: _membership((4, "Cuarto")),
            3: _membership((5, "Quinto")),
        }
        _route_projects(
            cookie_client,
            memberships,
            [RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)],
        )
        cookie_client._get_text.side_effect = RedmineSSOError(
            "Redireccion inesperada [302] en '/login'."
        )

        resultados = {
            pid: cookie_client.get_project_custom_fields(pid) for pid in (1, 2, 3)
        }

        assert all(r[0].definition_source == "none" for r in resultados.values())
        assert cookie_client._get_text.call_count == 1


class TestLimpiezaCache:
    """4.37: clear_custom_field_cache fuerza recarga y olvida el fallo global."""

    def test_clear_custom_field_cache_fuerza_recarga_y_olvida_fallo_html(
        self, cookie_client
    ):
        memberships = {1: _membership((3, "Tercero"))}
        _route_projects(
            cookie_client,
            memberships,
            [
                RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403),
                RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403),
            ],
        )
        cookie_client._get_text.side_effect = RedmineSSOError(
            "Redireccion inesperada [302] en '/projects/1/issues/new'.",
            location="/login",
        )

        antes = cookie_client.get_project_custom_fields(1)
        assert antes[0].definition_source == "none"
        assert cookie_client._get_text.call_count == 1

        cookie_client._get_text.side_effect = None
        cookie_client._get_text.return_value = _select_html(3, ["Uno", "Dos"])
        cookie_client.clear_custom_field_cache()

        despues = cookie_client.get_project_custom_fields(1)

        assert despues[0].definition_source == "html"
        assert despues[0].possible_values == ["Uno", "Dos"]
        assert cookie_client._get_text.call_count == 2


class TestAislamientoCache:
    """4.39: cada cliente tiene su propia caché (no hay caché de módulo)."""

    def test_cliente_nuevo_no_comparte_cache(self):
        primero = RedmineClient("https://redmine.example.com", "token")
        primero._get = MagicMock()
        primero._get_text = MagicMock()
        _route(
            primero,
            membership=_membership((3, "Tercero")),
            admin_responses=[{"custom_fields": [_admin_def(3, "Tercero")]}],
        )
        primero.get_project_custom_fields(7)
        assert primero._get.call_count == 2

        segundo = RedmineClient("https://redmine.example.com", "token")
        segundo._get = MagicMock()
        segundo._get_text = MagicMock()
        _route(
            segundo,
            membership=_membership((3, "Tercero")),
            admin_responses=[{"custom_fields": [_admin_def(3, "Tercero")]}],
        )
        segundo.get_project_custom_fields(7)
        assert segundo._get.call_count == 2


class TestCopiaResultado:
    """4.41: mutar la lista devuelta no altera la caché interna."""

    def test_resultado_modificado_no_contamina_la_cache(self, client):
        _route(
            client,
            membership=_membership((3, "Tercero")),
            admin_responses=[{"custom_fields": [_admin_def(3, "Tercero")]}],
        )

        primera = client.get_project_custom_fields(7)
        primera.clear()

        segunda = client.get_project_custom_fields(7)
        assert [cf.id for cf in segunda] == [3]


class TestDefinitionSource:
    """4.43: origen de cada definición y motivo solo en la degradación."""

    def test_definition_source_admin_html_none_y_degraded_reason(
        self, cookie_client
    ):
        _route(
            cookie_client,
            membership=_membership(
                (3, "Tercero"), (4, "Cuarto"), (5, "Quinto")
            ),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(3, "Tercero", field_format="list",
                               possible_values=["Baja", "Alta"])
                ]
            }],
        )
        cookie_client._get_text.return_value = _select_html(4, ["Uno", "Dos"])

        campos = cookie_client.get_project_custom_fields(7)

        assert [cf.definition_source for cf in campos] == [
            "admin", "html", "none"
        ]
        assert campos[0].degraded_reason == ""
        assert campos[1].degraded_reason == ""
        assert campos[2].degraded_reason != ""


class _HttpResp:
    """Respuesta HTTP mínima para ejercitar el `_get` real."""

    def __init__(self, *, status_code=200, payload=None, text="", json_error=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = {}
        self._json_error = json_error

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._payload


class TestRespuesta200NoJSON:
    """7.2: un 200 con HTML en `/custom_fields.json` degrada al formulario."""

    def test_200_html_en_definiciones_usa_formulario_html(self):
        client = RedmineClient(
            "https://redmine.example.com",
            "token",
            session_cookie="redmine_session=abc",
        )
        respuestas = {
            ("/projects/1.json", "issue_custom_fields"): _HttpResp(
                payload=_membership((3, "Severidad"))
            ),
            ("/custom_fields.json", None): _HttpResp(
                text="<html><body>SSO</body></html>",
                json_error=ValueError("Expecting value: line 1 column 1"),
            ),
            ("/projects/1/issues/new", None): _HttpResp(
                text=_select_html(3, ["Baja", "Alta"])
            ),
        }

        def fake_get(path, params=None):
            include = (params or {}).get("include")
            return respuestas[(path, include)]

        mock_http = MagicMock()
        mock_http.get.side_effect = fake_get
        client._client = mock_http

        campos = client.get_project_custom_fields(1)

        assert [cf.id for cf in campos] == [3]
        assert campos[0].field_format == "list"
        assert campos[0].possible_values == ["Baja", "Alta"]
        assert campos[0].definition_source == "html"


class TestCopiaProfundaResultado:
    """W2: mutar los objetos devueltos no debe contaminar la caché."""

    def test_resultado_modificado_profundamente_no_contamina_la_cache(self, client):
        _route(
            client,
            membership=_membership((3, "Tercero")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(
                        3,
                        "Tercero",
                        field_format="list",
                        possible_values=["A", "B"],
                    )
                ]
            }],
        )

        primera = client.get_project_custom_fields(7)
        primera[0].name = "MUTADO"
        primera[0].possible_values.append("MUTADO")

        segunda = client.get_project_custom_fields(7)

        assert segunda[0].name == "Tercero"
        assert segunda[0].possible_values == ["A", "B"]


class TestVisibleEditable:
    """R1-S5/R1-S6: la vía admin conserva visible/editable; la HTML usa defaults."""

    def test_admin_conserva_visible_y_editable(self, client):
        _route(
            client,
            membership=_membership((3, "Tercero")),
            admin_responses=[{
                "custom_fields": [
                    _admin_def(
                        3,
                        "Tercero",
                        field_format="list",
                        possible_values=["A", "B"],
                        visible=False,
                        editable=False,
                    )
                ]
            }],
        )

        campo = client.get_project_custom_fields(7)[0]

        assert campo.visible is False
        assert campo.editable is False

    def test_html_deja_visible_y_editable_en_true(self, cookie_client):
        _route(
            cookie_client,
            membership=_membership((3, "Tercero")),
            admin_responses=[
                RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)
            ],
        )
        cookie_client._get_text.return_value = _select_html(3, ["A", "B"])

        campo = cookie_client.get_project_custom_fields(7)[0]

        assert campo.definition_source == "html"
        assert campo.visible is True
        assert campo.editable is True
        assert campo.is_required is False
        assert campo.default_value == ""


class TestPaginacionTopeYParada:
    """R1-S13: tope de 20 páginas y parada en página vacía."""

    def test_tope_de_20_paginas_si_el_endpoint_ignora_offset(self, client):
        pagina = {
            "custom_fields": [_admin_def(3, "Tercero")],
            "total_count": 1000,
        }
        _route(
            client,
            membership=_membership((3, "Tercero")),
            admin_responses=[pagina] * 20,
        )

        definiciones = client._fetch_custom_field_definitions()

        assert set(definiciones) == {3}
        assert client._get.call_count == 20

    def test_todo_en_una_pagina_y_segunda_vacia_no_repite(self, client):
        _route(
            client,
            membership=_membership((3, "Tercero"), (4, "Cuarto")),
            admin_responses=[
                {
                    "custom_fields": [
                        _admin_def(3, "Tercero"),
                        _admin_def(4, "Cuarto"),
                    ],
                    "total_count": 100,
                },
                {"custom_fields": []},
            ],
        )

        definiciones = client._fetch_custom_field_definitions()

        assert set(definiciones) == {3, 4}
        assert client._get.call_count == 2


class TestWarningDegradacion:
    """R1-S23/R4-S4: el warning identifica el campo y no filtra secretos."""

    def test_warning_incluye_ids_y_no_filtra_secretos(self, caplog):
        client = RedmineClient(
            "https://redmine.example.com",
            "APIKEY_SECRETA",
            session_cookie="COOKIE_SECRETA",
        )
        client._get = MagicMock()
        client._get_text = MagicMock()
        _route(
            client,
            membership=_membership((3, "Tercero")),
            admin_responses=[
                RedmineError("Error HTTP 500", status_code=500)
            ],
        )
        client._get_text.side_effect = RedmineSSOError(
            "Redireccion inesperada [302] en '/projects/7/issues/new'.",
            location="/login",
        )

        with caplog.at_level(logging.WARNING):
            campos = client.get_project_custom_fields(7)

        assert campos[0].definition_source == "none"
        texto = caplog.text
        assert "proyecto=7" in texto
        assert "campo=3" in texto
        assert "Tercero" in texto
        assert "APIKEY_SECRETA" not in texto
        assert "COOKIE_SECRETA" not in texto


class TestPertenenciaRobustez:
    """8.9: una respuesta inválida de pertenencia no lanza AttributeError."""

    def test_project_no_dict_lanza_redmine_error(self, client):
        _route(
            client,
            membership={"project": "no-es-un-dict"},
            admin_responses=[],
        )

        with pytest.raises(RedmineError) as exc_info:
            client.get_project_custom_fields(7)

        assert "Respuesta inválida" in str(exc_info.value)
