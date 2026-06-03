from unittest.mock import MagicMock, patch, mock_open

import pytest

from app.services.redmine_client import RedmineClient, RedmineAttachment, RedmineIssue


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
