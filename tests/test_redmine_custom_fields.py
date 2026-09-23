"""Tests TDD para campos personalizados en RedmineClient.

Cubren:
- Obtención de campos personalizados de un proyecto.
- Parseo de valores en RedmineIssue y en get_issue_with_journals.
- Serialización en create_issue / update_issue.
"""

from unittest.mock import MagicMock

import pytest

from app.services.redmine_client import (
    RedmineClient,
    RedmineCustomField,
    RedmineIssue,
)


@pytest.fixture
def client():
    c = RedmineClient("https://redmine.example.com", "token")
    c._get = MagicMock()
    c._post = MagicMock()
    c._put = MagicMock()
    return c


class TestGetProjectCustomFields:
    """get_project_custom_fields(project_id)."""

    def test_get_project_custom_fields_maps_entries(self, client):
        """Hace GET /projects/7.json?include=issue_custom_fields y mapea entradas."""
        client._get.return_value = {
            "project": {
                "issue_custom_fields": [
                    {
                        "id": 3,
                        "name": "Severidad",
                        "field_format": "list",
                        "is_required": True,
                        "multiple": False,
                        "possible_values": ["Baja", "Alta"],
                        "default_value": "Baja",
                        "visible": True,
                        "editable": True,
                    },
                    {
                        "id": 4,
                        "name": "Notas extra",
                        "field_format": "text",
                    },
                ]
            }
        }

        fields = client.get_project_custom_fields(7)

        client._get.assert_called_once_with(
            "/projects/7.json", params={"include": "issue_custom_fields"}
        )
        assert len(fields) == 2
        assert isinstance(fields[0], RedmineCustomField)
        assert fields[0].id == 3
        assert fields[0].name == "Severidad"
        assert fields[0].field_format == "list"
        assert fields[0].is_required is True
        assert fields[0].multiple is False
        assert fields[0].possible_values == ["Baja", "Alta"]
        assert fields[0].default_value == "Baja"
        assert fields[0].visible is True
        assert fields[0].editable is True
        # Valores por defecto razonables en entradas incompletas
        assert fields[1].field_format == "text"
        assert fields[1].is_required is False
        assert fields[1].multiple is False
        assert fields[1].possible_values == []
        assert fields[1].default_value == ""

    def test_project_without_custom_fields_returns_empty(self, client):
        """Proyecto sin issue_custom_fields devuelve lista vacía sin excepción."""
        client._get.return_value = {"project": {"id": 7, "name": "Proyecto"}}
        assert client.get_project_custom_fields(7) == []

    def test_project_with_empty_custom_fields_returns_empty(self, client):
        """issue_custom_fields vacío devuelve lista vacía."""
        client._get.return_value = {"project": {"issue_custom_fields": []}}
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
