from unittest.mock import MagicMock, patch, mock_open

import pytest

from app.services.redmine_client import (
    RedmineClient, RedmineAttachment, RedmineIssue, RedmineJournal,
    RedmineValidationError, RedmineError, RedmineProject,
)


@pytest.fixture
def client():
    c = RedmineClient("https://redmine.example.com", "token")
    c._put = MagicMock()
    return c


class TestUpdateIssue:
    def test_update_issue_without_uploads(self, client):
        """update_issue sin uploads no debe incluir el campo uploads."""
        client.update_issue(issue_id=42, subject="Nuevo asunto")
        client._put.assert_called_once_with(
            "/issues/42.json", {"issue": {"subject": "Nuevo asunto"}}
        )

    def test_update_issue_with_uploads_inside_issue(self, client):
        """update_issue con uploads debe enviarlos dentro del objeto issue."""
        uploads = [{"token": "abc123", "filename": "doc.pdf", "content_type": "application/pdf"}]
        client.update_issue(issue_id=42, subject="Nuevo asunto", uploads=uploads)
        client._put.assert_called_once_with(
            "/issues/42.json",
            {"issue": {"subject": "Nuevo asunto", "uploads": uploads}},
        )

    def test_update_issue_with_only_uploads(self, client):
        """update_issue solo con uploads debe enviarlos dentro del objeto issue."""
        uploads = [{"token": "tok", "filename": "f.txt", "content_type": "text/plain"}]
        client.update_issue(issue_id=42, uploads=uploads)
        client._put.assert_called_once_with(
            "/issues/42.json", {"issue": {"uploads": uploads}}
        )


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


class TestGetIssuesMultiProject:
    """get_issues debe soportar una lista de proyectos fusionando resultados."""

    @staticmethod
    def _issue_json(iid, project_id, updated_on):
        return {
            "id": iid,
            "subject": f"Issue {iid}",
            "project": {"id": project_id, "name": f"Proyecto {project_id}"},
            "status": {"id": 1, "name": "Abierta"},
            "updated_on": updated_on,
        }

    def test_single_int_project(self, client):
        """Un único proyecto como int se pasa directamente a la API."""
        client._get = MagicMock(return_value={"issues": []})
        client.get_issues(project_id=5)
        client._get.assert_called_once()
        _, kwargs = client._get.call_args
        assert kwargs["params"]["project_id"] == 5

    def test_list_of_one_scales_to_int(self, client):
        """Una lista con un solo proyecto debe escalarse a int."""
        client._get = MagicMock(return_value={"issues": []})
        client.get_issues(project_id=[5])
        client._get.assert_called_once()
        _, kwargs = client._get.call_args
        assert kwargs["params"]["project_id"] == 5

    def test_empty_list_means_no_project_filter(self, client):
        """Una lista vacía no debe filtrar por proyecto."""
        client._get = MagicMock(return_value={"issues": []})
        client.get_issues(project_id=[])
        client._get.assert_called_once()
        _, kwargs = client._get.call_args
        assert "project_id" not in kwargs["params"]

    def test_multiple_projects_merge_and_dedupe(self, client):
        """Con varios proyectos hace una llamada por proyecto y fusiona sin duplicados."""
        p1 = [self._issue_json(1, 1, "2026-09-01T10:00:00Z"),
              self._issue_json(2, 1, "2026-09-02T10:00:00Z")]
        p2 = [self._issue_json(2, 1, "2026-09-02T10:00:00Z"),  # duplicado
              self._issue_json(3, 2, "2026-09-03T10:00:00Z")]
        client._get = MagicMock(side_effect=[{"issues": p1}, {"issues": p2}])

        result = client.get_issues(project_id=[1, 2])

        assert client._get.call_count == 2
        ids = [iss.id for iss in result]
        assert ids == [3, 2, 1]  # orden por updated_on desc, sin duplicados

    def test_multiple_projects_pass_project_id_per_call(self, client):
        """Cada llamada debe incluir el project_id correspondiente."""
        client._get = MagicMock(return_value={"issues": []})
        client.get_issues(project_id=[1, 2, 3])
        pids = [call.kwargs["params"]["project_id"] for call in client._get.call_args_list]
        assert pids == [1, 2, 3]

    def test_multiple_projects_with_client_side_assigned_filter(self, client):
        """El filtro client-side de asignados debe aplicarse tras fusionar proyectos."""
        p1 = [self._issue_json(1, 1, "2026-09-01T10:00:00Z"),
              {"id": 2, "subject": "I2", "project": {"id": 1, "name": "P1"},
               "status": {"id": 1, "name": "Abierta"}, "updated_on": "2026-09-02T10:00:00Z",
               "assigned_to": {"id": 7, "name": "Ana"}}]
        p2 = [{"id": 3, "subject": "I3", "project": {"id": 2, "name": "P2"},
               "status": {"id": 1, "name": "Abierta"}, "updated_on": "2026-09-03T10:00:00Z",
               "assigned_to": {"id": 9, "name": "Luis"}}]
        client._get = MagicMock(side_effect=[{"issues": p1}, {"issues": p2}])

        result = client.get_issues(project_id=[1, 2], assigned_to_id=[7, 9], current_user_id=1)

        assert sorted(iss.id for iss in result) == [2, 3]


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

    def test_get_all_projects_assigns_full_name_and_sorts_by_it(self, client):
        """get_all_projects() debe asignar full_name con la jerarquía y ordenar por full_name.lower()."""
        projects = [
            RedmineProject(id=1, name="Zeta", identifier="z", parent_id=None),
            RedmineProject(id=2, name="Alpha", identifier="a", parent_id=1),
            RedmineProject(id=3, name="Beta", identifier="b", parent_id=None),
        ]

        with patch.object(client, "get_projects", side_effect=[projects, []]):
            result = client.get_all_projects()

        # full_name compuesto por la jerarquía
        by_id = {p.id: p for p in result}
        assert by_id[1].full_name == "Zeta"
        assert by_id[2].full_name == "Zeta > Alpha"
        assert by_id[3].full_name == "Beta"

        # Orden por full_name.lower(): "beta" < "zeta" < "zeta > alpha"
        assert [p.id for p in result] == [3, 1, 2]

    def test_get_all_projects_full_name_equals_name_without_parents(self, client):
        """Sin padres, full_name debe coincidir con name (compatibilidad con el orden previo)."""
        projects = [
            RedmineProject(id=1, name="Zebra", identifier="z", parent_id=None),
            RedmineProject(id=2, name="Alpha", identifier="a", parent_id=None),
        ]

        with patch.object(client, "get_projects", side_effect=[projects, []]):
            result = client.get_all_projects()

        assert all(p.full_name == p.name for p in result)
        assert [p.name for p in result] == ["Alpha", "Zebra"]

    def test_get_all_projects_respects_max_pages(self, client):
        """No debe exceder 20 páginas (límite de seguridad)."""
        page = [RedmineProject(id=i, name=f"P{i}", identifier=f"p{i}", parent_id=None) for i in range(100)]

        # Siempre devuelve 100 proyectos (nunca lista vacía)
        with patch.object(client, "get_projects", return_value=page) as mock_get:
            result = client.get_all_projects()
            assert mock_get.call_count == 20  # Máximo 20 páginas
            assert len(result) == 2000  # 20 * 100

    def test_get_all_projects_hierarchy_across_pages(self, client):
        """W6: la jerarquía se compone aunque padre e hijo lleguen en páginas distintas."""
        page1 = [RedmineProject(id=1, name="Padre", identifier="p", parent_id=None)]
        page2 = [RedmineProject(id=2, name="Hijo", identifier="h", parent_id=1)]

        with patch.object(client, "get_projects", side_effect=[page1, page2, []]) as mock_get:
            result = client.get_all_projects()

        assert mock_get.call_count == 3
        by_id = {p.id: p for p in result}
        assert by_id[1].full_name == "Padre"
        assert by_id[2].full_name == "Padre > Hijo"
        # Orden por full_name.lower(): "padre" < "padre > hijo"
        assert [p.id for p in result] == [1, 2]


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


# ================================================================
# Tests para journals, participantes y filtro por fecha de creación
# ================================================================


def _issue_json_with_journals():
    """Issue JSON de ejemplo con author, assigned_to y journals."""
    return {
        "id": 101,
        "subject": "Tarea con journals",
        "author": {"id": 1, "name": "Ana"},
        "assigned_to": {"id": 2, "name": "Luis"},
        "journals": [
            {
                "id": 11,
                "user": {"id": 3, "name": "Carlos"},
                "notes": "He avanzado con esto",
                "created_on": "2026-09-01T10:00:00Z",
            },
            {
                "id": 12,
                "user": {"id": 4, "name": "Diana"},
                "notes": "",
                "created_on": "2026-09-02T11:00:00Z",
            },
        ],
    }


class TestParseJournals:
    """Tests para el parseo de journals en _issue_from_json (tarea 1.1)."""

    def test_parse_journals_with_user_id_and_notes(self, client):
        """_issue_from_json debe parsear journals con user_id, user_name, notes y created_on."""
        issue = client._issue_from_json(_issue_json_with_journals())
        assert len(issue.journals) == 2
        first = issue.journals[0]
        assert isinstance(first, RedmineJournal)
        assert first.id == 11
        assert first.user_id == 3
        assert first.user_name == "Carlos"
        assert first.notes == "He avanzado con esto"
        assert first.created_on == "2026-09-01T10:00:00Z"

    def test_parse_journals_keeps_journals_without_notes(self, client):
        """Los journals sin notas (notes='') deben conservarse en la lista."""
        issue = client._issue_from_json(_issue_json_with_journals())
        second = issue.journals[1]
        assert second.id == 12
        assert second.user_id == 4
        assert second.user_name == "Diana"
        assert second.notes == ""
        assert second.created_on == "2026-09-02T11:00:00Z"

    def test_parse_journals_defaults_when_missing(self, client):
        """Un journal sin user ni notes debe usar valores por defecto."""
        raw = {
            "id": 1,
            "subject": "S",
            "author": {"id": 1, "name": "Ana"},
            "journals": [{"id": 21}],
        }
        issue = client._issue_from_json(raw)
        assert len(issue.journals) == 1
        j = issue.journals[0]
        assert j.user_id == 0
        assert j.user_name == ""
        assert j.notes == ""
        assert j.created_on == ""

    def test_parse_no_journals_returns_empty_list(self, client):
        """Sin clave journals, la lista debe quedar vacía."""
        raw = {"id": 1, "subject": "S", "author": {"id": 1, "name": "Ana"}}
        issue = client._issue_from_json(raw)
        assert issue.journals == []

    def test_parse_journals_conserva_details(self, client):
        """_parse_journals conserva los details (propiedad, valor anterior, valor nuevo)."""
        raw = {
            "id": 1,
            "subject": "S",
            "author": {"id": 1, "name": "Ana"},
            "journals": [
                {
                    "id": 21,
                    "user": {"id": 3, "name": "Carlos"},
                    "notes": "",
                    "details": [
                        {"property": "assigned_to_id", "old_value": "2", "new_value": "3"},
                    ],
                },
            ],
        }
        issue = client._issue_from_json(raw)
        j = issue.journals[0]
        assert j.details == [
            {"property": "assigned_to_id", "old_value": "2", "new_value": "3"},
        ]

    def test_parse_journals_details_vacio_sin_clave(self, client):
        """Un journal sin la clave details debe tener la lista vacía."""
        raw = {
            "id": 1,
            "subject": "S",
            "author": {"id": 1, "name": "Ana"},
            "journals": [{"id": 21, "user": {"id": 3, "name": "Carlos"}, "notes": ""}],
        }
        issue = client._issue_from_json(raw)
        assert issue.journals[0].details == []


class TestParticipantIds:
    """Tests para RedmineIssue.participant_ids (tarea 1.2)."""

    def test_participant_ids_union_without_duplicates(self):
        """participant_ids = unión sin duplicados de autor, asignado y autores de journals."""
        issue = RedmineIssue(
            id=1,
            subject="S",
            author_id=1,
            assigned_to_id=2,
            journals=[
                RedmineJournal(id=11, user_id=3, user_name="Carlos", notes="n", created_on=""),
                RedmineJournal(id=12, user_id=1, user_name="Ana", notes="", created_on=""),
                RedmineJournal(id=13, user_id=2, user_name="Luis", notes="", created_on=""),
            ],
        )
        assert issue.participant_ids == [1, 2, 3]

    def test_participant_ids_excludes_zeros(self):
        """Los ids 0 (sin autor/asignado) deben excluirse."""
        issue = RedmineIssue(
            id=1,
            subject="S",
            author_id=0,
            assigned_to_id=0,
            journals=[RedmineJournal(id=11, user_id=0, user_name="", notes="", created_on="")],
        )
        assert issue.participant_ids == []

    def test_participant_ids_empty_by_default(self):
        """Sin participantes, la lista debe estar vacía."""
        issue = RedmineIssue(id=1, subject="S")
        assert issue.participant_ids == []

    def test_participant_ids_incluye_asignados_historicos(self):
        """participant_ids incluye los asignados históricos de los details."""
        issue = RedmineIssue(
            id=1,
            subject="S",
            author_id=1,
            assigned_to_id=5,
            journals=[
                RedmineJournal(
                    id=11, user_id=4, user_name="Diana", notes="", created_on="",
                    details=[{"property": "assigned_to_id", "old_value": "2", "new_value": "3"}],
                ),
            ],
        )
        assert issue.participant_ids == [1, 5, 4, 2, 3]

    def test_participant_ids_historicos_sin_duplicados(self):
        """Un asignado histórico que además es autor no se duplica."""
        issue = RedmineIssue(
            id=1,
            subject="S",
            author_id=2,
            assigned_to_id=5,
            journals=[
                RedmineJournal(
                    id=11, user_id=2, user_name="Ana", notes="", created_on="",
                    details=[{"property": "assigned_to_id", "old_value": "2", "new_value": "3"}],
                ),
            ],
        )
        assert issue.participant_ids == [2, 5, 3]

    def test_participant_ids_historicos_ignora_no_numericos(self):
        """Los valores no numéricos o vacíos de los details se ignoran."""
        issue = RedmineIssue(
            id=1,
            subject="S",
            author_id=1,
            assigned_to_id=5,
            journals=[
                RedmineJournal(
                    id=11, user_id=4, user_name="Diana", notes="", created_on="",
                    details=[
                        {"property": "assigned_to_id", "old_value": "", "new_value": "abc"},
                        {"property": "assigned_to_id", "old_value": None, "new_value": "3"},
                    ],
                ),
            ],
        )
        assert issue.participant_ids == [1, 5, 4, 3]


class TestRolesForUser:
    """Tests para RedmineIssue.roles_for_user (tarea 2.4)."""

    def _issue(self, author_id=1, assigned_to_id=2, journals=None):
        return RedmineIssue(
            id=1,
            subject="S",
            author_id=author_id,
            assigned_to_id=assigned_to_id,
            journals=journals or [],
        )

    def test_creator_role(self):
        """El autor del issue tiene el rol 'creador'."""
        issue = self._issue(author_id=1)
        assert issue.roles_for_user(1) == {"creador"}

    def test_updater_role_from_journal_without_notes(self):
        """Autor de un journal sin notas es 'actualizador' (cambio de atributos)."""
        issue = self._issue(journals=[
            RedmineJournal(id=11, user_id=3, user_name="Carlos", notes="", created_on=""),
        ])
        assert issue.roles_for_user(3) == {"actualizador"}

    def test_participant_role_from_journal_with_notes(self):
        """Autor de un journal con notas es 'participante' (y 'actualizador')."""
        issue = self._issue(journals=[
            RedmineJournal(id=11, user_id=3, user_name="Carlos", notes="Comentario", created_on=""),
        ])
        assert issue.roles_for_user(3) == {"actualizador", "participante"}

    def test_participant_role_from_assignment(self):
        """El asignado actual es 'participante' aunque no tenga journals."""
        issue = self._issue(assigned_to_id=2)
        assert issue.roles_for_user(2) == {"participante"}

    def test_creator_with_multiple_roles(self):
        """Un usuario puede acumular varios roles (creador + actualizador + participante)."""
        issue = self._issue(author_id=1, assigned_to_id=1, journals=[
            RedmineJournal(id=11, user_id=1, user_name="Ana", notes="Comentario", created_on=""),
        ])
        assert issue.roles_for_user(1) == {"creador", "actualizador", "participante"}

    def test_unrelated_user_has_no_roles(self):
        """Un usuario sin relación con el issue no tiene roles."""
        issue = self._issue()
        assert issue.roles_for_user(99) == set()

    def test_participant_role_from_historical_assignment_old_value(self):
        """El valor anterior de un cambio de assigned_to_id otorga 'participante'."""
        issue = self._issue(assigned_to_id=5, journals=[
            RedmineJournal(
                id=11, user_id=4, user_name="Diana", notes="", created_on="",
                details=[{"property": "assigned_to_id", "old_value": "2", "new_value": "3"}],
            ),
        ])
        assert issue.roles_for_user(2) == {"participante"}

    def test_participant_role_from_historical_assignment_new_value(self):
        """El valor nuevo de un cambio de assigned_to_id otorga 'participante'."""
        issue = self._issue(assigned_to_id=5, journals=[
            RedmineJournal(
                id=11, user_id=4, user_name="Diana", notes="", created_on="",
                details=[{"property": "assigned_to_id", "old_value": "2", "new_value": "3"}],
            ),
        ])
        assert issue.roles_for_user(3) == {"participante"}

    def test_participante_por_notas_se_mantiene_con_details(self):
        """Con details presentes, el autor de notas sigue siendo 'participante'."""
        issue = self._issue(assigned_to_id=5, journals=[
            RedmineJournal(
                id=11, user_id=7, user_name="Eva", notes="Comentario", created_on="",
                details=[{"property": "assigned_to_id", "old_value": "2", "new_value": "3"}],
            ),
        ])
        assert issue.roles_for_user(7) == {"actualizador", "participante"}

    def test_participante_por_asignacion_actual_se_mantiene_con_details(self):
        """El asignado actual sigue siendo 'participante' aunque haya details."""
        issue = self._issue(assigned_to_id=5, journals=[
            RedmineJournal(
                id=11, user_id=7, user_name="Eva", notes="", created_on="",
                details=[{"property": "assigned_to_id", "old_value": "2", "new_value": "3"}],
            ),
        ])
        assert issue.roles_for_user(5) == {"participante"}

    def test_participant_role_from_legacy_assigned_to_property(self):
        """La propiedad legada 'assigned_to' también otorga 'participante'."""
        issue = self._issue(assigned_to_id=5, journals=[
            RedmineJournal(
                id=11, user_id=4, user_name="Diana", notes="", created_on="",
                details=[{"property": "assigned_to", "old_value": "2", "new_value": "3"}],
            ),
        ])
        assert issue.roles_for_user(2) == {"participante"}

    def test_participant_role_historico_con_valores_int(self):
        """Los details con old_value/new_value como int también otorgan 'participante'."""
        issue = self._issue(assigned_to_id=5, journals=[
            RedmineJournal(
                id=11, user_id=4, user_name="Diana", notes="", created_on="",
                details=[{"property": "assigned_to_id", "old_value": 2, "new_value": 3}],
            ),
        ])
        assert issue.roles_for_user(2) == {"participante"}
        assert issue.roles_for_user(3) == {"participante"}

    def test_participante_historico_que_ademas_comento(self):
        """Un asignado histórico que además comentó cumple 'participante' y casa en el filtro (tarea 15.5)."""
        issue = self._issue(assigned_to_id=5, journals=[
            RedmineJournal(
                id=11, user_id=2, user_name="Ana", notes="Comentario", created_on="",
                details=[{"property": "assigned_to_id", "old_value": "2", "new_value": "3"}],
            ),
        ])
        assert "participante" in issue.roles_for_user(2)
        assert issue.matches_user_filter({2}, {"participante"})


class TestMatchesUserFilter:
    """Tests para RedmineIssue.matches_user_filter (tarea 2.4)."""

    def _issue(self, author_id=1, assigned_to_id=2, journals=None):
        return RedmineIssue(
            id=1,
            subject="S",
            author_id=author_id,
            assigned_to_id=assigned_to_id,
            journals=journals or [],
        )

    def test_matches_creator(self):
        issue = self._issue(author_id=1)
        assert issue.matches_user_filter({1}, {"creador"})

    def test_does_not_match_wrong_role(self):
        issue = self._issue(author_id=1)
        assert not issue.matches_user_filter({1}, {"participante"})

    def test_matches_updater(self):
        issue = self._issue(journals=[
            RedmineJournal(id=11, user_id=3, user_name="Carlos", notes="", created_on=""),
        ])
        assert issue.matches_user_filter({3}, {"actualizador"})

    def test_matches_participant_by_comment(self):
        issue = self._issue(journals=[
            RedmineJournal(id=11, user_id=3, user_name="Carlos", notes="Comentario", created_on=""),
        ])
        assert issue.matches_user_filter({3}, {"participante"})

    def test_matches_participant_by_assignment(self):
        issue = self._issue(assigned_to_id=2)
        assert issue.matches_user_filter({2}, {"participante"})

    def test_matches_any_of_several_users(self):
        """Basta con que un usuario cumpla alguno de los roles seleccionados."""
        issue = self._issue(author_id=1, assigned_to_id=2)
        assert issue.matches_user_filter({5, 2}, {"creador", "participante"})

    def test_empty_user_ids_does_not_restrict(self):
        """Con user_ids vacío, la dimensión usuarios no restringe."""
        issue = self._issue(author_id=1)
        assert issue.matches_user_filter(set(), {"creador"})
        assert issue.matches_user_filter(set(), {"actualizador"})

    def test_matches_participante_historico_sin_notas(self):
        """Un asignado histórico sin journals con notas casa con el rol 'participante'."""
        issue = self._issue(assigned_to_id=5, journals=[
            RedmineJournal(
                id=11, user_id=4, user_name="Diana", notes="", created_on="",
                details=[{"property": "assigned_to_id", "old_value": "2", "new_value": "3"}],
            ),
        ])
        assert issue.matches_user_filter({2}, {"participante"})


class TestGetIssuesCreatedOn:
    """Tests para el filtro created_on en get_issues (tarea 1.3)."""

    @pytest.fixture
    def client(self):
        c = RedmineClient("https://redmine.example.com", "token")
        c._get = MagicMock(return_value={"issues": []})
        return c

    def test_created_on_range(self, client):
        """Con from y to debe enviar created_on=><from|to."""
        client.get_issues(created_on_from="2026-01-01", created_on_to="2026-03-31")
        _, kwargs = client._get.call_args
        assert kwargs["params"]["created_on"] == "><2026-01-01|2026-03-31"

    def test_created_on_from_only(self, client):
        """Solo con from debe enviar created_on>=from."""
        client.get_issues(created_on_from="2026-01-01")
        _, kwargs = client._get.call_args
        assert kwargs["params"]["created_on"] == ">=2026-01-01"

    def test_created_on_to_only(self, client):
        """Solo con to debe enviar created_on<=to."""
        client.get_issues(created_on_to="2026-03-31")
        _, kwargs = client._get.call_args
        assert kwargs["params"]["created_on"] == "<=2026-03-31"

    def test_created_on_equal_dates(self, client):
        """Con from == to debe enviar created_on=fecha."""
        client.get_issues(created_on_from="2026-01-01", created_on_to="2026-01-01")
        _, kwargs = client._get.call_args
        assert kwargs["params"]["created_on"] == "=2026-01-01"

    def test_created_on_absent_by_default(self, client):
        """Sin fechas no debe enviar el parámetro created_on."""
        client.get_issues()
        _, kwargs = client._get.call_args
        assert "created_on" not in kwargs["params"]


class TestGetIssuesIncludeJournals:
    """Tests para include_journals en get_issues (tarea 1.4)."""

    @pytest.fixture
    def client(self):
        c = RedmineClient("https://redmine.example.com", "token")
        c._get = MagicMock(return_value={"issues": []})
        return c

    def test_include_journals_adds_journals_to_include(self, client):
        """include_journals=True debe añadir 'journals' al parámetro include."""
        client.get_issues(include_journals=True)
        _, kwargs = client._get.call_args
        assert kwargs["params"]["include"] == "attachments,journals"

    def test_include_attachments_by_default(self, client):
        """Por defecto include debe seguir siendo 'attachments'."""
        client.get_issues()
        _, kwargs = client._get.call_args
        assert kwargs["params"]["include"] == "attachments"

    def test_include_journals_parses_journals_in_response(self, client):
        """Con include_journals=True, los journals de la respuesta se parsean en el issue."""
        client._get.return_value = {"issues": [_issue_json_with_journals()]}
        issues = client.get_issues(include_journals=True)
        assert len(issues) == 1
        assert len(issues[0].journals) == 2
        assert issues[0].journals[0].user_id == 3


class TestGetIssuesStatusFilter:
    """Tests para status_filter en get_issues (tarea 11.5)."""

    @pytest.fixture
    def client(self):
        c = RedmineClient("https://redmine.example.com", "token")
        c._get = MagicMock(return_value={"issues": []})
        return c

    def test_status_filter_lista_une_con_coma(self, client):
        """Con status_filter=[1, 2] envía status_id=1,2."""
        client.get_issues(status_filter=[1, 2])
        _, kwargs = client._get.call_args
        assert kwargs["params"]["status_id"] == "1,2"

    def test_status_filter_open_no_regresion(self, client):
        """Con status_filter='open' envía status_id=open (comportamiento actual)."""
        client.get_issues(status_filter="open")
        _, kwargs = client._get.call_args
        assert kwargs["params"]["status_id"] == "open"

    def test_status_filter_int_escalar(self, client):
        """Con status_filter=1 envía status_id=1."""
        client.get_issues(status_filter=1)
        _, kwargs = client._get.call_args
        assert kwargs["params"]["status_id"] == 1

    def test_status_filter_none_no_envia_parametro(self, client):
        """Con status_filter=None no se envía status_id."""
        client.get_issues(status_filter=None)
        _, kwargs = client._get.call_args
        assert "status_id" not in kwargs["params"]
