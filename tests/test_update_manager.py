"""Tests unitarios para UpdateManager y UpdateInfo."""

import sys
from unittest.mock import MagicMock, PropertyMock, patch

import httpx
import pytest
from packaging.version import Version

from app import __version__
from app.services.update_manager import UpdateInfo, UpdateManager


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def sample_release_win32():
    """Release simulado con assets para Windows (.exe) y Linux."""
    return {
        "tag_name": "v0.4.0",
        "prerelease": False,
        "draft": False,
        "body": "Notas de la versión 0.4.0\n\nCorrecciones y mejoras.",
        "assets": [
            {
                "name": "PyIssuesTracker.exe",
                "browser_download_url": "https://github.com/hector/pyIssuesTracker/releases/download/v0.4.0/PyIssuesTracker.exe",
                "content_type": "application/x-msdownload",
            },
            {
                "name": "PyIssuesTracker",
                "browser_download_url": "https://github.com/hector/pyIssuesTracker/releases/download/v0.4.0/PyIssuesTracker",
                "content_type": "application/octet-stream",
            },
        ],
    }


@pytest.fixture
def sample_release_linux():
    """Release simulado con assets para Windows (.exe) y Linux."""
    return {
        "tag_name": "v0.4.0",
        "prerelease": False,
        "draft": False,
        "body": "Notas de la versión 0.4.0\n\nCorrecciones y mejoras.",
        "assets": [
            {
                "name": "PyIssuesTracker.exe",
                "browser_download_url": "https://github.com/hector/pyIssuesTracker/releases/download/v0.4.0/PyIssuesTracker.exe",
                "content_type": "application/x-msdownload",
            },
            {
                "name": "PyIssuesTracker",
                "browser_download_url": "https://github.com/hector/pyIssuesTracker/releases/download/v0.4.0/PyIssuesTracker",
                "content_type": "application/octet-stream",
            },
        ],
    }


# ============================================================
# Tests: 5.1 — check_for_updates devuelve asset .exe en Windows
# ============================================================

class TestCheckForUpdatesPlatform:
    """Tests de selección de asset según plataforma (tasks 5.1, 5.2)."""

    def test_windows_returns_exe_asset(self, sample_release_win32):
        """En Windows devuelve el asset .exe."""
        mock_response = MagicMock()
        mock_response.json.return_value = [sample_release_win32]
        mock_response.raise_for_status = MagicMock()

        with (
            patch("app.services.update_manager.sys.platform", "win32"),
            patch.object(httpx.Client, "request", return_value=mock_response),
        ):
            um = UpdateManager()
            info = um.check_for_updates()

        assert info.available is True
        assert info.url == sample_release_win32["assets"][0]["browser_download_url"]
        assert info.version == "0.4.0"

    def test_linux_returns_non_exe_asset(self, sample_release_linux):
        """En Linux devuelve el asset sin extensión .exe."""
        mock_response = MagicMock()
        mock_response.json.return_value = [sample_release_linux]
        mock_response.raise_for_status = MagicMock()

        with (
            patch("app.services.update_manager.sys.platform", "linux"),
            patch.object(httpx.Client, "request", return_value=mock_response),
        ):
            um = UpdateManager()
            info = um.check_for_updates()

        assert info.available is True
        assert info.url == sample_release_linux["assets"][1]["browser_download_url"]
        assert info.version == "0.4.0"

    def test_no_compatible_asset_returns_not_available(self):
        """Si no hay asset compatible con la plataforma, devuelve available=False."""
        assets_sin_exe = [
            {
                "name": "PyIssuesTracker",
                "browser_download_url": "https://example.com/PyIssuesTracker",
            },
        ]
        release = {
            "tag_name": "v0.4.0",
            "prerelease": False,
            "draft": False,
            "body": "",
            "assets": assets_sin_exe,
        }
        mock_response = MagicMock()
        mock_response.json.return_value = [release]
        mock_response.raise_for_status = MagicMock()

        with (
            patch("app.services.update_manager.sys.platform", "win32"),
            patch.object(httpx.Client, "request", return_value=mock_response),
        ):
            um = UpdateManager()
            info = um.check_for_updates()

        assert info.available is False
        assert info.url == ""

    def test_no_assets_at_all_returns_not_available(self):
        """Si el release no tiene assets, devuelve available=False."""
        release = {
            "tag_name": "v0.4.0",
            "prerelease": False,
            "draft": False,
            "body": "",
            "assets": [],
        }
        mock_response = MagicMock()
        mock_response.json.return_value = [release]
        mock_response.raise_for_status = MagicMock()

        with (
            patch.object(httpx.Client, "request", return_value=mock_response),
        ):
            um = UpdateManager()
            info = um.check_for_updates()

        assert info.available is False


# ============================================================
# Tests: 5.3 — Ignorar prereleases y drafts
# ============================================================

class TestCheckForUpdatesIgnoresNonStable:
    """check_for_updates ignora prereleases y drafts (task 5.3)."""

    def test_ignores_prerelease(self):
        """Ignora releases marcados como prerelease."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "tag_name": "v0.5.0-beta",
                "prerelease": True,
                "draft": False,
                "body": "",
                "assets": [{"name": "PyIssuesTracker.exe", "browser_download_url": "http://exe"}],
            },
            {
                "tag_name": "v0.4.0",
                "prerelease": False,
                "draft": False,
                "body": "",
                "assets": [{"name": "PyIssuesTracker.exe", "browser_download_url": "http://exe"}],
            },
        ]
        mock_response.raise_for_status = MagicMock()

        with (
            patch("app.services.update_manager.sys.platform", "win32"),
            patch.object(httpx.Client, "request", return_value=mock_response),
        ):
            um = UpdateManager()
            info = um.check_for_updates()

        assert info.available is True
        assert info.version == "0.4.0"

    def test_ignores_draft(self):
        """Ignora releases marcados como draft."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "tag_name": "v0.5.0-draft",
                "prerelease": False,
                "draft": True,
                "body": "",
                "assets": [{"name": "PyIssuesTracker.exe", "browser_download_url": "http://exe"}],
            },
            {
                "tag_name": "v0.4.0",
                "prerelease": False,
                "draft": False,
                "body": "",
                "assets": [{"name": "PyIssuesTracker.exe", "browser_download_url": "http://exe"}],
            },
        ]
        mock_response.raise_for_status = MagicMock()

        with (
            patch("app.services.update_manager.sys.platform", "win32"),
            patch.object(httpx.Client, "request", return_value=mock_response),
        ):
            um = UpdateManager()
            info = um.check_for_updates()

        assert info.available is True
        assert info.version == "0.4.0"

    def test_all_prereleases_returns_not_available(self):
        """Si solo hay prereleases, devuelve available=False."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "tag_name": "v0.5.0-beta",
                "prerelease": True,
                "draft": False,
                "body": "",
                "assets": [{"name": "PyIssuesTracker.exe", "browser_download_url": "http://exe"}],
            },
        ]
        mock_response.raise_for_status = MagicMock()

        with (
            patch("app.services.update_manager.sys.platform", "win32"),
            patch.object(httpx.Client, "request", return_value=mock_response),
        ):
            um = UpdateManager()
            info = um.check_for_updates()

        assert info.available is False

    def test_network_error_returns_not_available(self):
        """Error de red devuelve available=False sin propagar excepción."""
        with patch.object(httpx.Client, "request", side_effect=httpx.ConnectError("sin red")):
            um = UpdateManager()
            info = um.check_for_updates()

        assert info.available is False


# ============================================================
# Tests: 5.4 — progress_callback en download_release
# ============================================================

class TestDownloadReleaseProgress:
    """download_release llama al progress_callback con porcentajes (task 5.4)."""

    def test_progress_callback_called_with_percentages(self, tmp_path):
        """Verifica que el callback recibe porcentajes correctos durante descarga."""
        chunks = [b"x" * 65536, b"y" * 65536, b"z" * 16384]  # 3 chunks = 147456 bytes
        total_size = 65536 + 65536 + 16384  # 147456

        class MockResponse:
            def __init__(self):
                self.headers = {"content-length": str(total_size)}
                self._chunks = iter(chunks)

            def raise_for_status(self):
                pass

            def iter_bytes(self, chunk_size=65536):
                return iter(chunks)

        mock_stream = MagicMock()
        mock_stream.__enter__.return_value = MockResponse()

        progress_values = []

        def progress_callback(percent: int):
            progress_values.append(percent)

        with patch.object(httpx.Client, "stream", return_value=mock_stream):
            um = UpdateManager()
            dest = tmp_path / "test_download.bin"
            result = um.download_release(
                "https://example.com/file",
                str(dest),
                progress_callback=progress_callback,
            )

        assert result is True
        assert len(progress_values) == 3  # 3 chunks

        chunk1_pct = int(65536 * 100 / total_size)
        chunk2_pct = int(131072 * 100 / total_size)
        chunk3_pct = int(147456 * 100 / total_size)

        assert progress_values == [chunk1_pct, chunk2_pct, chunk3_pct]

    def test_progress_callback_indeterminate_without_content_length(self, tmp_path):
        """Sin content-length, progress_callback recibe -1."""
        chunks = [b"x" * 65536, b"y" * 65536]

        class MockResponse:
            def __init__(self):
                self.headers = {}  # Sin content-length
                self._chunks = iter(chunks)

            def raise_for_status(self):
                pass

            def iter_bytes(self, chunk_size=65536):
                return iter(chunks)

        mock_stream = MagicMock()
        mock_stream.__enter__.return_value = MockResponse()

        progress_values = []

        def progress_callback(percent: int):
            progress_values.append(percent)

        with patch.object(httpx.Client, "stream", return_value=mock_stream):
            um = UpdateManager()
            dest = tmp_path / "test_no_size.bin"
            result = um.download_release(
                "https://example.com/file",
                str(dest),
                progress_callback=progress_callback,
            )

        assert result is True
        assert progress_values == [-1, -1]

    def test_progress_callback_none_still_works(self, tmp_path):
        """Si progress_callback es None, la descarga funciona sin errores."""
        chunks = [b"test data"]

        class MockResponse:
            def __init__(self):
                self.headers = {"content-length": "9"}

            def raise_for_status(self):
                pass

            def iter_bytes(self, chunk_size=65536):
                return iter(chunks)

        mock_stream = MagicMock()
        mock_stream.__enter__.return_value = MockResponse()

        with patch.object(httpx.Client, "stream", return_value=mock_stream):
            um = UpdateManager()
            dest = tmp_path / "test_no_callback.bin"
            result = um.download_release("https://example.com/file", str(dest))

        assert result is True
