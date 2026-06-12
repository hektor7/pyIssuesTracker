from unittest.mock import MagicMock, patch, mock_open

import pytest

from app.services.redmine_client import (
    RedmineClient, RedmineAttachment, RedmineIssue,
    RedmineValidationError, RedmineError, RedmineProject,
)


@pytest.fixture
def client():
    c = RedmineClient("https://redmine.example.com", "token")
    c._put = MagicMock()
    return c


class TestAssignIssue:
    def test_assign_issue_without_notes(self, client):
        """assign_issue sin notas debe pasar solo assigned_to_id."""
        client.assign_issue(issue_id=42, user_id=7)
        client._put.assert_called_once_with(
            "/issues/42.json", {"issue": {"assigned_to_id": 7}}
        )

    def test_assign_issue_with_notes(self, client):
        """assign_issue con notas debe pasar assigned_to_id y notes."""
        client.assign_issue(issue_id=42, user_id=7, notes="test notes")
        client._put.assert_called_once_with(
            "/issues/42.json",
            {"issue": {"assigned_to_id": 7, "notes": "test notes"}},
        )


class TestCompleteIssue:
    def test_complete_issue_without_notes(self, client):
        """complete_issue sin notas debe pasar done_ratio y opcionalmente status_id."""
        client.complete_issue(issue_id=42, done_ratio=100, status_id=5)
        client._put.assert_called_once_with(
            "/issues/42.json",
            {"issue": {"done_ratio": 100, "status_id": 5}},
        )

    def test_complete_issue_with_notes(self, client):
        """complete_issue con notas debe pasar done_ratio, status_id y notes."""
        client.complete_issue(issue_id=42, done_ratio=100, status_id=5, notes="issue done")
        client._put.assert_called_once_with(
            "/issues/42.json",
            {"issue": {"done_ratio": 100, "status_id": 5, "notes": "issue done"}},
        )

    def test_complete_issue_with_notes_default_done_ratio(self, client):
        """complete_issue con notas y sin status_id."""
        client.complete_issue(issue_id=42, notes="completed")
        client._put.assert_called_once_with(
            "/issues/42.json",
            {"issue": {"done_ratio": 100, "notes": "completed"}},
        )

    def test_complete_issue_with_due_date(self, client):
        """complete_issue con due_date debe pasar el campo due_date."""
        client.complete_issue(issue_id=42, done_ratio=100, status_id=5, due_date="2026-06-12")
        client._put.assert_called_once_with(
            "/issues/42.json",
            {"issue": {"done_ratio": 100, "status_id": 5, "due_date": "2026-06-12"}},
        )


class TestParseAttachments:
    """Tests para parseo de attachments desde respuestas JSON."""

    def test_parse_attachments_from_issue(self, client):
        """_parse_attachments debe convertir JSON a lista de RedmineAttachment."""
        raw = [
            {
                "id": 1,
                "filename": "doc.pdf",
                "filesize": 204800,
                "content_type": "application/pdf",
                "content_url": "https://redmine.example.com/attachments/download/1/doc.pdf",
                "description": "Informe final",
                "author": {"id": 5, "name": "Juan Perez"},
                "created_on": "2026-06-01T10:30:00Z",
            }
        ]
        result = client._parse_attachments(raw)
        assert len(result) == 1
        att = result[0]
        assert att.id == 1
        assert att.filename == "doc.pdf"
        assert att.filesize == 204800
        assert att.content_type == "application/pdf"
        assert att.content_url == "https://redmine.example.com/attachments/download/1/doc.pdf"
        assert att.description == "Informe final"
        assert att.author_name == "Juan Perez"
        assert att.created_on == "2026-06-01T10:30:00Z"

    def test_parse_empty_attachments(self, client):
        """Lista vacia debe devolver lista vacia."""
        result = client._parse_attachments([])
        assert result == []

    def test_parse_attachments_missing_fields(self, client):
        """Campos ausentes deben usar valores por defecto."""
        raw = [{"id": 1, "filename": "doc.txt"}]
        result = client._parse_attachments(raw)
        att = result[0]
        assert att.filesize == 0
        assert att.content_type == ""
        assert att.content_url == ""


class TestDownloadAttachment:
    """Tests para la descarga de attachments."""

    def test_download_attachment_writes_chunks(self, client):
        """download_attachment debe escribir los chunks al archivo destino."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_bytes = MagicMock(return_value=[b"chunk1", b"chunk2"])

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_response)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_stream_ctx)
        mock_client.close = MagicMock()

        mock_open_file = mock_open()

        with patch.object(client, "_build_client", return_value=mock_client), \
             patch("builtins.open", mock_open_file):
            client.download_attachment("https://example.com/file.pdf", "/tmp/file.pdf")

        mock_client.stream.assert_called_once_with("GET", "https://example.com/file.pdf")
        mock_response.raise_for_status.assert_called_once()
        mock_open_file.assert_called_once_with("/tmp/file.pdf", "wb")
        handle = mock_open_file()
        handle.write.assert_any_call(b"chunk1")
        handle.write.assert_any_call(b"chunk2")


# ================================================================
# Tests para RedmineValidationError
# ================================================================


class TestRedmineValidationError:
    """Tests para la clase de excepción RedmineValidationError."""

    def test_validation_error_has_errors_list(self):
        """RedmineValidationError debe almacenar lista de errores."""
        err = RedmineValidationError("msg", ["error1", "error2"])
        assert err.errors == ["error1", "error2"]
        assert str(err) == "msg"

    def test_validation_error_default_empty_errors(self):
        """Sin errors, debe tener lista vacía."""
        err = RedmineValidationError("msg")
        assert err.errors == []

    def test_validation_error_is_redmine_error(self):
        """RedmineValidationError debe heredar de RedmineError."""
        err = RedmineValidationError("msg")
        assert isinstance(err, RedmineError)


class TestExtractValidationErrors:
    """Tests para _extract_validation_errors()."""

    @pytest.fixture
    def client(self):
        return RedmineClient("https://redmine.example.com", "token")

    def test_extracts_errors_from_json(self, client):
        """Extrae lista de errores del JSON de respuesta."""
        resp = MagicMock()
        resp.status_code = 422
        resp.json.return_value = {"errors": ["Asunto no puede estar vacío", "Proyecto es obligatorio"]}
        errors = client._extract_validation_errors(resp)
        assert errors == ["Asunto no puede estar vacío", "Proyecto es obligatorio"]

    def test_returns_generic_message_when_no_json(self, client):
        """Si no hay JSON válido, devuelve mensaje genérico."""
        resp = MagicMock()
        resp.status_code = 422
        resp.json.side_effect = Exception("no json")
        errors = client._extract_validation_errors(resp)
        assert errors == ["Error HTTP 422"]

    def test_returns_generic_message_when_no_errors_key(self, client):
        """Si el JSON no tiene clave 'errors', devuelve mensaje genérico."""
        resp = MagicMock()
        resp.status_code = 422
        resp.json.return_value = {"message": "something wrong"}
        errors = client._extract_validation_errors(resp)
        assert errors == ["Error HTTP 422"]

    def test_handles_errors_as_string(self, client):
        """Si errors es un string en vez de lista, lo envuelve."""
        resp = MagicMock()
        resp.status_code = 422
        resp.json.return_value = {"errors": "single error message"}
        errors = client._extract_validation_errors(resp)
        assert errors == ["single error message"]


class TestPostValidationErrors:
    """Tests para _post() con HTTP 422."""

    @pytest.fixture
    def client(self):
        c = RedmineClient("https://redmine.example.com", "token")
        return c

    def test_post_raises_validation_error_on_422(self, client):
        """_post() debe lanzar RedmineValidationError en HTTP 422."""
        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.json.return_value = {"errors": ["Subject is required"]}

        mock_http_client = MagicMock()
        mock_http_client.post.return_value = mock_resp

        with patch.object(client, "_build_client", return_value=mock_http_client):
            client._client = mock_http_client  # Forzar uso del mock
            with pytest.raises(RedmineValidationError) as exc_info:
                client._post("/issues.json", {"issue": {}})
            assert exc_info.value.errors == ["Subject is required"]

    def test_post_raises_auth_error_on_401(self, client):
        """_post() debe lanzar RedmineAuthError en HTTP 401."""
        from app.services.redmine_client import RedmineAuthError
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        mock_http_client = MagicMock()
        mock_http_client.post.return_value = mock_resp

        with patch.object(client, "_build_client", return_value=mock_http_client):
            client._client = mock_http_client
            with pytest.raises(RedmineAuthError):
                client._post("/issues.json", {"issue": {}})


class TestPutValidationErrors:
    """Tests para _put() con HTTP 422."""

    @pytest.fixture
    def client(self):
        return RedmineClient("https://redmine.example.com", "token")

    def test_put_raises_validation_error_on_422(self, client):
        """_put() debe lanzar RedmineValidationError en HTTP 422."""
        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.json.return_value = {"errors": ["Status is invalid"]}

        mock_http_client = MagicMock()
        mock_http_client.put.return_value = mock_resp

        with patch.object(client, "_build_client", return_value=mock_http_client):
            client._client = mock_http_client
            with pytest.raises(RedmineValidationError) as exc_info:
                client._put("/issues/1.json", {"issue": {}})
            assert exc_info.value.errors == ["Status is invalid"]


class TestGetErrorHandling:
    """Tests para _get() con errores HTTP."""

    @pytest.fixture
    def client(self):
        return RedmineClient("https://redmine.example.com", "token")

    def test_get_includes_error_body_in_message(self, client):
        """_get() debe incluir errores del JSON en el mensaje de error."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.json.return_value = {"errors": ["Internal server error"]}

        mock_http_client = MagicMock()
        mock_http_client.get.return_value = mock_resp

        with patch.object(client, "_build_client", return_value=mock_http_client):
            client._client = mock_http_client
            with pytest.raises(RedmineError) as exc_info:
                client._get("/issues.json")
            assert "Internal server error" in str(exc_info.value)

    def test_get_raises_on_404(self, client):
        """_get() debe lanzar RedmineError en HTTP 404."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        mock_http_client = MagicMock()
        mock_http_client.get.return_value = mock_resp

        with patch.object(client, "_build_client", return_value=mock_http_client):
            client._client = mock_http_client
            with pytest.raises(RedmineError, match="Recurso no encontrado"):
                client._get("/issues/999.json")


class TestGetProjects:
    """Tests para get_projects() con paginación."""

    @pytest.fixture
    def client(self):
        c = RedmineClient("https://redmine.example.com", "token")
        c._get = MagicMock()
        return c

    def test_get_projects_passes_offset_and_limit(self, client):
        """get_projects() debe pasar offset y limit como parámetros."""
        client._get.return_value = {"projects": []}
        client.get_projects(offset=50, limit=25)
        client._get.assert_called_once_with("/projects.json", params={"limit": 25, "offset": 50})

    def test_get_projects_parses_response(self, client):
        """get_projects() debe parsear la respuesta en RedmineProject."""
        client._get.return_value = {
            "projects": [
                {"id": 1, "name": "Project A", "identifier": "proj-a"},
                {"id": 2, "name": "Project B", "identifier": "proj-b", "parent": {"id": 1}},
            ]
        }
        projects = client.get_projects()
        assert len(projects) == 2
        assert projects[0].id == 1
        assert projects[0].name == "Project A"
        assert projects[0].parent_id is None
        assert projects[1].parent_id == 1


class TestGetAllProjects:
    """Tests para get_all_projects()."""

    @pytest.fixture
    def client(self):
        c = RedmineClient("https://redmine.example.com", "token")
        return c

    def test_get_all_projects_single_page(self, client):
        """Con menos de 100 proyectos, debe hacer una sola llamada."""
        projects = [RedmineProject(id=i, name=f"P{i}", identifier=f"p{i}", parent_id=None) for i in range(5)]

        with patch.object(client, "get_projects", side_effect=[projects, []]) as mock_get:
            result = client.get_all_projects()
            assert len(result) == 5
            assert mock_get.call_count == 2  # Primera llamada + segunda vacía

    def test_get_all_projects_multiple_pages(self, client):
        """Con múltiples páginas, debe iterar hasta recibir lista vacía."""
        page1 = [RedmineProject(id=i, name=f"P{i}", identifier=f"p{i}", parent_id=None) for i in range(100)]
        page2 = [RedmineProject(id=i, name=f"P{i}", identifier=f"p{i}", parent_id=None) for i in range(100, 150)]

        with patch.object(client, "get_projects", side_effect=[page1, page2, []]) as mock_get:
            result = client.get_all_projects()
            assert len(result) == 150
            assert mock_get.call_count == 3

    def test_get_all_projects_sorts_alphabetically(self, client):
        """Los proyectos deben ordenarse alfabéticamente."""
        projects = [
            RedmineProject(id=1, name="Zebra", identifier="z", parent_id=None),
            RedmineProject(id=2, name="Alpha", identifier="a", parent_id=None),
            RedmineProject(id=3, name="Middle", identifier="m", parent_id=None),
        ]

        with patch.object(client, "get_projects", side_effect=[projects, []]):
            result = client.get_all_projects()
            assert [p.name for p in result] == ["Alpha", "Middle", "Zebra"]

    def test_get_all_projects_respects_max_pages(self, client):
        """No debe exceder 20 páginas (límite de seguridad)."""
        page = [RedmineProject(id=i, name=f"P{i}", identifier=f"p{i}", parent_id=None) for i in range(100)]

        # Siempre devuelve 100 proyectos (nunca lista vacía)
        with patch.object(client, "get_projects", return_value=page) as mock_get:
            result = client.get_all_projects()
            assert mock_get.call_count == 20  # Máximo 20 páginas
            assert len(result) == 2000  # 20 * 100


class TestGetCurrentUserId:
    """Tests para get_current_user_id()."""

    @pytest.fixture
    def client(self):
        c = RedmineClient("https://redmine.example.com", "token")
        return c

    def test_get_current_user_id_fetches_from_api(self, client):
        """Primera llamada debe obtener el ID de la API."""
        client._get = MagicMock(return_value={"user": {"id": 42}})
        result = client.get_current_user_id()
        assert result == 42
        client._get.assert_called_once_with("/users/current.json")

    def test_get_current_user_id_uses_cache(self, client):
        """Segunda llamada debe usar caché sin llamar a la API."""
        client._get = MagicMock(return_value={"user": {"id": 42}})
        client.get_current_user_id()  # Primera llamada
        client._get.reset_mock()

        result = client.get_current_user_id()  # Segunda llamada
        assert result == 42
        client._get.assert_not_called()  # No debe llamar a la API
