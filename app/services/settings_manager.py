import json

from PyQt6.QtCore import QSettings

from app.utils.constants import (
    ORG_NAME,
    APP_NAME,
    KEY_REDMINE_URL,
    KEY_REDMINE_API_KEY,
    KEY_REDMINE_SESSION_COOKIE,
    KEY_REDMINE_EXTRA_HEADERS,
    KEY_FILTER_PRIORITY,
    KEY_FILTER_TRACKER,
    KEY_FILTER_ASSIGNED_TO,
    KEY_PROXY_ENABLED,
    KEY_PROXY_TYPE,
    KEY_PROXY_HOST,
    KEY_PROXY_PORT,
    KEY_PROXY_USER,
    KEY_PROXY_PASSWORD,
    KEY_THEME,
    KEY_FILTER_PROJECT,
    KEY_FILTER_PROJECT_NAME,
    KEY_FILTER_FIXED,
    KEY_FILTER_STATUS,
    KEY_WINDOW_GEOMETRY,
    KEY_WINDOW_STATE,
    KEY_LAST_UPDATE_CHECK,
    DEFAULT_REDMINE_URL,
    DEFAULT_API_KEY,
)


class SettingsManager:
    def __init__(self):
        self._settings = QSettings(ORG_NAME, APP_NAME)

    # ---- Redmine ----

    @property
    def redmine_url(self) -> str:
        return self._settings.value(KEY_REDMINE_URL, DEFAULT_REDMINE_URL)

    @redmine_url.setter
    def redmine_url(self, value: str):
        self._settings.setValue(KEY_REDMINE_URL, value)

    @property
    def redmine_api_key(self) -> str:
        return self._settings.value(KEY_REDMINE_API_KEY, DEFAULT_API_KEY)

    @redmine_api_key.setter
    def redmine_api_key(self, value: str):
        self._settings.setValue(KEY_REDMINE_API_KEY, value)

    @property
    def redmine_configured(self) -> bool:
        return bool(self.redmine_url.strip()) and bool(self.redmine_api_key.strip())

    @staticmethod
    def _parse_cookie_json(raw: str) -> str | None:
        """Convierte el JSON de Firefox DevTools a formato Cookie header."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        # Busca el primer dict anidado (las cookies) sin importar la clave raíz
        for val in data.values():
            if isinstance(val, dict):
                pairs = [f"{k}={v}" for k, v in val.items()]
                return "; ".join(pairs)
        return None

    @property
    def session_cookie(self) -> str:
        raw = self._settings.value(KEY_REDMINE_SESSION_COOKIE, "")
        parsed = self._parse_cookie_json(raw)
        if parsed is not None:
            return parsed
        # Las cabeceras HTTP no admiten saltos de línea; normalizamos a una sola línea
        return " ".join(raw.splitlines()).strip()

    @session_cookie.setter
    def session_cookie(self, value: str):
        self._settings.setValue(KEY_REDMINE_SESSION_COOKIE, value.strip())

    @property
    def extra_headers(self) -> str:
        return self._settings.value(KEY_REDMINE_EXTRA_HEADERS, "")

    @extra_headers.setter
    def extra_headers(self, value: str):
        self._settings.setValue(KEY_REDMINE_EXTRA_HEADERS, value.strip())

    def parse_extra_headers(self) -> dict[str, str]:
        headers = {}
        for line in self.extra_headers.splitlines():
            line = line.strip()
            if ":" in line:
                key, _, val = line.partition(":")
                headers[key.strip()] = val.strip()
        return headers

    # ---- Proxy ----

    @property
    def proxy_enabled(self) -> bool:
        return bool(self._settings.value(KEY_PROXY_ENABLED, False))

    @proxy_enabled.setter
    def proxy_enabled(self, value: bool):
        self._settings.setValue(KEY_PROXY_ENABLED, value)

    @property
    def proxy_type(self) -> str:
        return self._settings.value(KEY_PROXY_TYPE, "http")

    @proxy_type.setter
    def proxy_type(self, value: str):
        self._settings.setValue(KEY_PROXY_TYPE, value)

    @property
    def proxy_host(self) -> str:
        return self._settings.value(KEY_PROXY_HOST, "")

    @proxy_host.setter
    def proxy_host(self, value: str):
        self._settings.setValue(KEY_PROXY_HOST, value)

    @property
    def proxy_port(self) -> int:
        return int(self._settings.value(KEY_PROXY_PORT, 0))

    @proxy_port.setter
    def proxy_port(self, value: int):
        self._settings.setValue(KEY_PROXY_PORT, value)

    @property
    def proxy_user(self) -> str:
        return self._settings.value(KEY_PROXY_USER, "")

    @proxy_user.setter
    def proxy_user(self, value: str):
        self._settings.setValue(KEY_PROXY_USER, value)

    @property
    def proxy_password(self) -> str:
        return self._settings.value(KEY_PROXY_PASSWORD, "")

    @proxy_password.setter
    def proxy_password(self, value: str):
        self._settings.setValue(KEY_PROXY_PASSWORD, value)

    def build_proxy_url(self) -> str | None:
        if not self.proxy_enabled or not self.proxy_host.strip():
            return None
        user_pass = ""
        if self.proxy_user:
            user_pass = f"{self.proxy_user}:{self.proxy_password}@"
        port = f":{self.proxy_port}" if self.proxy_port else ""
        return f"{self.proxy_type}://{user_pass}{self.proxy_host}{port}"

    # ---- Apariencia ----

    @property
    def theme(self) -> str:
        return self._settings.value(KEY_THEME, "default")

    @theme.setter
    def theme(self, value: str):
        self._settings.setValue(KEY_THEME, value)

    # ---- Filtros ----

    @property
    def filter_project_id(self) -> int:
        return int(self._settings.value(KEY_FILTER_PROJECT, 0))

    @filter_project_id.setter
    def filter_project_id(self, value: int):
        self._settings.setValue(KEY_FILTER_PROJECT, value)

    @property
    def filter_project_name(self) -> str:
        return self._settings.value(KEY_FILTER_PROJECT_NAME, "")

    @filter_project_name.setter
    def filter_project_name(self, value: str):
        self._settings.setValue(KEY_FILTER_PROJECT_NAME, value)

    @property
    def filter_fixed(self) -> bool:
        return bool(self._settings.value(KEY_FILTER_FIXED, False))

    @filter_fixed.setter
    def filter_fixed(self, value: bool):
        self._settings.setValue(KEY_FILTER_FIXED, value)

    @property
    def filter_status(self) -> str:
        return self._settings.value(KEY_FILTER_STATUS, "open")

    @filter_status.setter
    def filter_status(self, value: str):
        self._settings.setValue(KEY_FILTER_STATUS, value)

    @property
    def filter_priority(self) -> int:
        val = self._settings.value(KEY_FILTER_PRIORITY, 0)
        return int(val) if val else 0

    @filter_priority.setter
    def filter_priority(self, value: int):
        self._settings.setValue(KEY_FILTER_PRIORITY, value)

    @property
    def filter_tracker(self) -> int:
        val = self._settings.value(KEY_FILTER_TRACKER, 0)
        return int(val) if val else 0

    @filter_tracker.setter
    def filter_tracker(self, value: int):
        self._settings.setValue(KEY_FILTER_TRACKER, value)

    @property
    def filter_assigned_to(self) -> int:
        val = self._settings.value(KEY_FILTER_ASSIGNED_TO, 0)
        return int(val) if val else 0

    @filter_assigned_to.setter
    def filter_assigned_to(self, value: int):
        self._settings.setValue(KEY_FILTER_ASSIGNED_TO, value)

    # ---- Ventana ----

    @property
    def window_geometry(self):
        return self._settings.value(KEY_WINDOW_GEOMETRY)

    @window_geometry.setter
    def window_geometry(self, value):
        self._settings.setValue(KEY_WINDOW_GEOMETRY, value)

    @property
    def window_state(self):
        return self._settings.value(KEY_WINDOW_STATE)

    @window_state.setter
    def window_state(self, value):
        self._settings.setValue(KEY_WINDOW_STATE, value)

    # ---- Update ----

    @property
    def last_update_check(self) -> str:
        return self._settings.value(KEY_LAST_UPDATE_CHECK, "")

    @last_update_check.setter
    def last_update_check(self, value: str):
        self._settings.setValue(KEY_LAST_UPDATE_CHECK, value)
