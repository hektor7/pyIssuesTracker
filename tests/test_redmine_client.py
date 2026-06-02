from unittest.mock import MagicMock, patch

import pytest

from app.services.redmine_client import RedmineClient


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
