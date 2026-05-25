"""Constantes de la aplicación."""

from app import __app_name__, __version__, __org__

# ============================================================
# Identidad de la app
# ============================================================
APP_NAME = __app_name__
APP_VERSION = __version__
ORG_NAME = __org__
APP_DISPLAY_NAME = "PyIssuesTracker"

# ============================================================
# GitHub (auto-update)
# ============================================================
GITHUB_REPO_OWNER = "hector"
GITHUB_REPO_NAME = "pyIssuesTracker"
GITHUB_API_RELEASES = (
    f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases"
)

# ============================================================
# Redmine API defaults
# ============================================================
DEFAULT_REDMINE_URL = ""
DEFAULT_API_KEY = ""
REDMINE_REQUEST_TIMEOUT = 15  # segundos
REDMINE_PAGE_LIMIT = 100  # issues por página

# Estados estándar de Redmine (por nombre)
STATUS_OPEN = "Abierta"
STATUS_CLOSED = "Cerrada"
STATUS_RESOLVED = "Resuelta"
STATUS_REJECTED = "Rechazada"

# ============================================================
# Config keys (QSettings)
# ============================================================
KEY_REDMINE_URL = "redmine/url"
KEY_REDMINE_API_KEY = "redmine/api_key"
KEY_REDMINE_SESSION_COOKIE = "redmine/session_cookie"
KEY_REDMINE_EXTRA_HEADERS = "redmine/extra_headers"
KEY_PROXY_ENABLED = "proxy/enabled"
KEY_PROXY_TYPE = "proxy/type"        # http, https, socks5
KEY_PROXY_HOST = "proxy/host"
KEY_PROXY_PORT = "proxy/port"
KEY_PROXY_USER = "proxy/user"
KEY_PROXY_PASSWORD = "proxy/password"
KEY_THEME = "appearance/theme"
KEY_FILTER_PROJECT = "filter/project_id"
KEY_FILTER_PROJECT_NAME = "filter/project_name"
KEY_FILTER_FIXED = "filter/fixed"      # si el filtro de proyecto es persistente
KEY_FILTER_STATUS = "filter/status"
KEY_FILTER_PRIORITY = "filter/priority"
KEY_FILTER_TRACKER = "filter/tracker"
KEY_FILTER_ASSIGNED_TO = "filter/assigned_to"
KEY_WINDOW_GEOMETRY = "window/geometry"
KEY_WINDOW_STATE = "window/state"
KEY_LAST_UPDATE_CHECK = "update/last_check"

# ============================================================
# Temas disponibles
# ============================================================
THEMES = {
    "default": "Predeterminado (Claro)",
    "dark": "Oscuro",
    "fusion_light": "Fusion Claro",
    "fusion_dark": "Fusion Oscuro",
}
