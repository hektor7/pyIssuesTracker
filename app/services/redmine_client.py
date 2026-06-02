from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

from app.utils.constants import REDMINE_REQUEST_TIMEOUT, REDMINE_PAGE_LIMIT


@dataclass
class RedmineProject:
    id: int
    name: str
    identifier: str
    parent_id: int | None = None
    children: list["RedmineProject"] = field(default_factory=list)


@dataclass
class RedmineIssue:
    id: int
    subject: str
    description: str = ""
    start_date: str = ""
    status_name: str = ""
    status_id: int = 0
    done_ratio: int = 0
    project_id: int = 0
    project_name: str = ""
    assigned_to_id: int = 0
    assigned_to_name: str = ""
    author_name: str = ""
    created_on: str = ""
    updated_on: str = ""
    tracker_id: int = 0
    tracker_name: str = ""
    priority_id: int = 0
    priority_name: str = ""
    category_id: int = 0
    category_name: str = ""


@dataclass
class RedmineStatus:
    id: int
    name: str
    is_closed: bool = False


@dataclass
class RedminePriority:
    id: int
    name: str
    is_default: bool = False


@dataclass
class RedmineIssueCategory:
    id: int
    name: str
    project_id: int = 0


@dataclass
class RedmineMembership:
    id: int
    user_id: int
    user_name: str


@dataclass
class RedmineTracker:
    id: int
    name: str
    default_status_id: int = 0


@dataclass
class RedmineJournal:
    id: int
    user_name: str
    notes: str
    created_on: str


@dataclass
class RedmineChecklistItem:
    id: int
    issue_id: int
    subject: str
    is_done: bool = False
    position: int = 0


class RedmineError(Exception):
    pass


class RedmineAuthError(RedmineError):
    pass


class RedmineConnectionError(RedmineError):
    pass


class RedmineSSOError(RedmineError):
    pass


class RedmineClient:
    def __init__(self, base_url: str, api_key: str, proxy_url: str | None = None,
                 session_cookie: str = "", extra_headers: dict[str, str] | None = None):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._proxy_url = proxy_url
        self._session_cookie = session_cookie
        self._extra_headers = extra_headers or {}
        self._client: httpx.Client | None = None

    def _build_client(self) -> httpx.Client:
        headers = {
            "X-Redmine-API-Key": self._api_key,
            "Content-Type": "application/json",
        }
        if self._session_cookie:
            headers["Cookie"] = self._session_cookie
        headers.update(self._extra_headers)

        return httpx.Client(
            base_url=self._base_url,
            headers=headers,
            timeout=REDMINE_REQUEST_TIMEOUT,
            follow_redirects=False,
            proxy=self._proxy_url if self._proxy_url else None,
        )

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            resp = self.client.get(path, params=params or {})
            self._check_redirect(resp, path)
            if resp.status_code == 401:
                raise RedmineAuthError("API key no válida (HTTP 401)")
            if resp.status_code == 403:
                raise RedmineAuthError("Acceso denegado (HTTP 403)")
            if resp.status_code == 404:
                raise RedmineError(f"Recurso no encontrado: {path}")
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")

    def _post(self, path: str, data: dict) -> dict:
        try:
            resp = self.client.post(path, json=data)
            self._check_redirect(resp, path)
            if resp.status_code == 401:
                raise RedmineAuthError("API key no válida (HTTP 401)")
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")

    def _put(self, path: str, data: dict) -> dict:
        try:
            resp = self.client.put(path, json=data)
            self._check_redirect(resp, path)
            if resp.status_code == 401:
                raise RedmineAuthError("API key no válida (HTTP 401)")
            resp.raise_for_status()
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")
        try:
            return resp.json()
        except Exception:
            return {}

    def _delete(self, path: str) -> dict:
        try:
            resp = self.client.delete(path)
            self._check_redirect(resp, path)
            if resp.status_code == 401:
                raise RedmineAuthError("API key no válida (HTTP 401)")
            if resp.status_code == 404:
                raise RedmineError(f"Recurso no encontrado: {path}")
            resp.raise_for_status()
            return {}
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")

    def _check_redirect(self, resp, path: str):
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "")
            if "login" in location.lower() or "sso" in location.lower() or "auth" in location.lower():
                raise RedmineSSOError(
                    "El servidor Redmine esta protegido por un portal de autenticacion (SSO).\n\n"
                    "La API key no es suficiente. El administrador debe configurar\n"
                    "Redmine para permitir acceso API sin pasar por el SSO."
                )
            raise RedmineSSOError(
                f"Redireccion inesperada [{resp.status_code}] en '{path}'."
            )

    def test_connection(self) -> bool:
        self._get("/users/current.json")
        return True

    # ---- Proyectos ----

    def get_projects(self) -> list[RedmineProject]:
        raw = self._get("/projects.json", params={"limit": 200})
        projects_list = raw.get("projects", [])
        projects: list[RedmineProject] = []
        for p in projects_list:
            projects.append(RedmineProject(
                id=p["id"],
                name=p["name"],
                identifier=p["identifier"],
                parent_id=p.get("parent", {}).get("id") if p.get("parent") else None,
            ))
        projects.sort(key=lambda x: x.name.lower())
        return projects

    # ---- Trackers ----

    def get_trackers(self) -> list[RedmineTracker]:
        """GET /trackers.json"""
        raw = self._get("/trackers.json")
        trackers = []
        for t in raw.get("trackers", []):
            trackers.append(RedmineTracker(
                id=t["id"],
                name=t["name"],
                default_status_id=t.get("default_status", {}).get("id", 0),
            ))
        return trackers

    # ---- Issues ----

    def get_issues(
        self,
        project_id: int | None = None,
        status_filter: str = "open",
        category_id: int | None = None,
        priority_id: int | None = None,
        assigned_to_id: int | str | None = None,
        limit: int = REDMINE_PAGE_LIMIT,
        offset: int = 0,
    ) -> list[RedmineIssue]:
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "sort": "updated_on:desc",
            "include": "attachments",
        }
        if project_id:
            params["project_id"] = project_id
        if status_filter:
            params["status_id"] = status_filter
        if category_id:
            params["category_id"] = category_id
        if priority_id:
            params["priority_id"] = priority_id
        if assigned_to_id == "!*":
            params["assigned_to_id"] = "!*"
        elif assigned_to_id == "me":
            params["assigned_to_id"] = "me"
        elif assigned_to_id:
            params["assigned_to_id"] = assigned_to_id

        raw = self._get("/issues.json", params=params)
        issues_raw = raw.get("issues", [])
        issues: list[RedmineIssue] = []
        for i in issues_raw:
            iss = RedmineIssue(
                id=i["id"],
                subject=i.get("subject", ""),
                description=i.get("description", ""),
                start_date=i.get("start_date", ""),
                status_name=i.get("status", {}).get("name", ""),
                status_id=i.get("status", {}).get("id", 0),
                done_ratio=i.get("done_ratio", 0),
                project_id=i.get("project", {}).get("id", 0),
                project_name=i.get("project", {}).get("name", ""),
                assigned_to_id=i.get("assigned_to", {}).get("id", 0) if i.get("assigned_to") else 0,
                assigned_to_name=i.get("assigned_to", {}).get("name", "") if i.get("assigned_to") else "",
                author_name=i.get("author", {}).get("name", ""),
                created_on=i.get("created_on", ""),
                updated_on=i.get("updated_on", ""),
                tracker_id=i.get("tracker", {}).get("id", 0),
                tracker_name=i.get("tracker", {}).get("name", ""),
                priority_id=i.get("priority", {}).get("id", 0),
                priority_name=i.get("priority", {}).get("name", ""),
                category_id=i.get("category", {}).get("id", 0),
                category_name=i.get("category", {}).get("name", ""),
            )
            issues.append(iss)
        return issues

    # ---- Issue actions ----

    def get_issue(self, issue_id: int, include_journals: bool = False) -> dict:
        return self._get(f"/issues/{issue_id}.json", params={"include": "journals"} if include_journals else None)

    def get_issue_with_journals(self, issue_id: int) -> dict:
        """Obtiene issue + journals parseados."""
        raw = self.get_issue(issue_id, include_journals=True)
        issue_data = raw.get("issue", {})
        journals_raw = issue_data.get("journals", [])
        journals = []
        for j in journals_raw:
            if j.get("notes"):  # Solo journals con notas (ignorar cambios de atributos)
                journals.append(RedmineJournal(
                    id=j["id"],
                    user_name=j.get("user", {}).get("name", "Desconocido"),
                    notes=j.get("notes", ""),
                    created_on=j.get("created_on", ""),
                ))
        # Añadir category si existe
        cat = issue_data.get("category")
        if cat:
            issue_data["category_id"] = cat.get("id", 0)
            issue_data["category_name"] = cat.get("name", "")
        issue_data["_journals"] = journals
        return issue_data

    def create_issue(self, project_id: int, subject: str, description: str = "",
                     tracker_id: int = 1, priority_id: int = 2,
                     assigned_to_id: int | None = None,
                     category_id: int = 0, start_date: str = "",
                     done_ratio: int = 0) -> dict:
        payload: dict[str, Any] = {
            "project_id": project_id,
            "subject": subject,
            "description": description,
            "tracker_id": tracker_id,
            "priority_id": priority_id,
        }
        if assigned_to_id:
            payload["assigned_to_id"] = assigned_to_id
        if category_id:
            payload["category_id"] = category_id
        if start_date:
            payload["start_date"] = start_date
        if done_ratio:
            payload["done_ratio"] = done_ratio
        return self._post("/issues.json", {"issue": payload})

    def update_issue(self, issue_id: int, **fields) -> dict:
        return self._put(f"/issues/{issue_id}.json", {"issue": fields})

    def assign_issue(self, issue_id: int, user_id: int, notes: str = "") -> dict:
        fields: dict[str, Any] = {"assigned_to_id": user_id}
        if notes:
            fields["notes"] = notes
        return self.update_issue(issue_id, **fields)

    def complete_issue(self, issue_id: int, done_ratio: int = 100,
                       status_id: int | None = None, notes: str = "") -> dict:
        fields: dict[str, Any] = {"done_ratio": done_ratio}
        if status_id:
            fields["status_id"] = status_id
        if notes:
            fields["notes"] = notes
        return self.update_issue(issue_id, **fields)

    def reject_issue(self, issue_id: int, status_id: int, notes: str = "") -> dict:
        fields: dict[str, Any] = {"status_id": status_id}
        if notes:
            fields["notes"] = notes
        return self._put(f"/issues/{issue_id}.json", {"issue": fields})

    def add_issue_note(self, issue_id: int, notes: str) -> dict:
        """Añade una nota (comentario) a una issue existente."""
        return self._put(f"/issues/{issue_id}.json", {"issue": {"notes": notes}})

    # ---- Checklists (plugin RedmineUP) ----

    def get_checklists(self, issue_id: int) -> list[RedmineChecklistItem]:
        """GET /issues/{issue_id}/checklists.json"""
        raw = self._get(f"/issues/{issue_id}/checklists.json")
        items = []
        for c in raw.get("checklists", []):
            items.append(RedmineChecklistItem(
                id=c["id"],
                issue_id=c.get("issue_id", issue_id),
                subject=c["subject"],
                is_done=bool(c.get("is_done", False)),
                position=c.get("position", 0),
            ))
        return items

    def create_checklist_item(self, issue_id: int, subject: str,
                              is_done: bool = False) -> dict:
        """POST /issues/{issue_id}/checklists.json"""
        return self._post(
            f"/issues/{issue_id}/checklists.json",
            {"checklist": {"subject": subject, "is_done": 1 if is_done else 0}}
        )

    def update_checklist_item(self, item_id: int, **fields) -> dict:
        """PUT /checklists/{item_id}.json"""
        return self._put(f"/checklists/{item_id}.json", {"checklist": fields})

    def delete_checklist_item(self, item_id: int) -> dict:
        """DELETE /checklists/{item_id}.json"""
        return self._delete(f"/checklists/{item_id}.json")

    # ---- Estados ----

    def get_issue_statuses(self) -> list[RedmineStatus]:
        raw = self._get("/issue_statuses.json")
        statuses = []
        for s in raw.get("issue_statuses", []):
            statuses.append(RedmineStatus(
                id=s["id"],
                name=s["name"],
                is_closed=s.get("is_closed", False),
            ))
        return statuses

    def get_issue_priorities(self) -> list[RedminePriority]:
        raw = self._get("/enumerations/issue_priorities.json")
        priorities = []
        for p in raw.get("issue_priorities", []):
            priorities.append(RedminePriority(
                id=p["id"],
                name=p["name"],
                is_default=p.get("is_default", False),
            ))
        return priorities

    def get_project_issue_categories(self, project_id: int) -> list[RedmineIssueCategory]:
        raw = self._get(f"/projects/{project_id}/issue_categories.json")
        categories = []
        for c in raw.get("issue_categories", []):
            categories.append(RedmineIssueCategory(
                id=c["id"],
                name=c["name"],
                project_id=project_id,
            ))
        return categories

    # ---- Miembros del proyecto ----

    def get_project_memberships(self, project_id: int) -> list[RedmineMembership]:
        raw = self._get(f"/projects/{project_id}/memberships.json", params={"limit": 200})
        memberships = []
        for m in raw.get("memberships", []):
            user = m.get("user", {})
            memberships.append(RedmineMembership(
                id=m["id"],
                user_id=user.get("id", 0),
                user_name=user.get("name", ""),
            ))
        return memberships

    def get_current_user_id(self) -> int:
        data = self._get("/users/current.json")
        return data["user"]["id"]

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None
