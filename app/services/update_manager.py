import sys
from datetime import datetime
from typing import Callable

import httpx
from packaging.version import Version

from app import __version__
from app.utils.constants import GITHUB_API_RELEASES, REDMINE_REQUEST_TIMEOUT


class UpdateInfo:
    def __init__(self, version: str, url: str, notes: str = "", available: bool = False):
        self.version = version
        self.url = url
        self.notes = notes
        self.available = available


class UpdateManager:
    def __init__(self, proxy_url: str | None = None):
        self._proxy_url = proxy_url
        self._current_version = Version(__version__)

    def check_for_updates(self) -> UpdateInfo:
        with httpx.Client(
            timeout=REDMINE_REQUEST_TIMEOUT,
            proxy=self._proxy_url if self._proxy_url else None,
        ) as client:
            try:
                resp = client.get(
                    GITHUB_API_RELEASES,
                    params={"per_page": 5},
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                resp.raise_for_status()
                releases = resp.json()
            except Exception:
                return UpdateInfo(version="", url="", available=False)

        latest_stable: dict | None = None
        for rel in releases:
            if rel.get("prerelease", False) or rel.get("draft", False):
                continue
            latest_stable = rel
            break

        if not latest_stable:
            return UpdateInfo(version="", url="", available=False)

        tag = latest_stable.get("tag_name", "").lstrip("v")
        if not tag:
            return UpdateInfo(version="", url="", available=False)

        try:
            remote_version = Version(tag)
        except Exception:
            return UpdateInfo(version="", url="", available=False)

        # Seleccionar asset según la plataforma
        assets = latest_stable.get("assets", [])
        if not assets:
            return UpdateInfo(version="", url="", available=False)

        if sys.platform == "win32":
            matching = [a for a in assets if a.get("name", "").endswith(".exe")]
        else:
            matching = [a for a in assets if not a.get("name", "").endswith(".exe")]

        if not matching:
            return UpdateInfo(version="", url="", available=False)

        download_url = matching[0].get("browser_download_url", "")
        if not download_url:
            return UpdateInfo(version="", url="", available=False)

        available = remote_version > self._current_version
        notes = latest_stable.get("body", "") or ""
        # Si el release no tiene notas, generar texto mínimo
        if not notes.strip():
            release_name = latest_stable.get("name", "") or tag
            release_url = latest_stable.get("html_url", "")
            notes = f"{release_name}\n\n🔗 {release_url}" if release_url else release_name

        return UpdateInfo(
            version=tag,
            url=download_url,
            notes=notes[:500] if notes else "",
            available=available,
        )

    def download_release(
        self,
        url: str,
        dest_path: str,
        progress_callback: Callable[[int], None] | None = None,
    ) -> bool:
        with httpx.Client(
            timeout=300,
            follow_redirects=True,
            proxy=self._proxy_url if self._proxy_url else None,
        ) as client:
            try:
                with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    total = resp.headers.get("content-length")
                    total = int(total) if total else None
                    downloaded = 0
                    with open(dest_path, "wb") as f:
                        for chunk in resp.iter_bytes(chunk_size=65536):
                            f.write(chunk)
                            if progress_callback is not None:
                                downloaded += len(chunk)
                                if total:
                                    percent = int(downloaded * 100 / total)
                                    progress_callback(percent)
                                else:
                                    progress_callback(-1)
                return True
            except Exception:
                return False
