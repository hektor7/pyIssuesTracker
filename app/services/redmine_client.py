from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

from app.utils.constants import REDMINE_REQUEST_TIMEOUT, REDMINE_PAGE_LIMIT
from app.utils.projects import build_project_full_names


@dataclass
class RedmineProject:
    id: int
    name: str
    identifier: str
    parent_id: int | None = None
    children: list["RedmineProject"] = field(default_factory=list)
    full_name: str = ""


@dataclass
class RedmineIssue:
    id: int
    subject: str
    description: str = ""
    start_date: str = ""
    due_date: str = ""
    status_name: str = ""
    status_id: int = 0
    done_ratio: int = 0
    project_id: int = 0
    project_name: str = ""
    assigned_to_id: int = 0
    assigned_to_name: str = ""
    author_id: int = 0
    author_name: str = ""
    created_on: str = ""
    updated_on: str = ""
    tracker_id: int = 0
    tracker_name: str = ""
    priority_id: int = 0
    priority_name: str = ""
    category_id: int = 0
    category_name: str = ""
    attachments: list["RedmineAttachment"] = field(default_factory=list)
    custom_fields: dict[int, Any] = field(default_factory=dict)
    journals: list["RedmineJournal"] = field(default_factory=list)

    @property
    def participant_ids(self) -> list[int]:
        """Ids de los usuarios implicados en la tarea, sin duplicados.

        Unión (en orden de inserción) de author_id, assigned_to_id, los
        autores de los journals y los asignados históricos (old_value/new_value
        de los details de asignación), excluyendo los ids 0 (sin usuario) y
        los valores no numéricos.
        """
        ids: list[int] = []
        seen: set[int] = set()
        for uid in (self.author_id, self.assigned_to_id):
            if uid and uid not in seen:
                seen.add(uid)
                ids.append(uid)
        for j in self.journals:
            if j.user_id and j.user_id not in seen:
                seen.add(j.user_id)
                ids.append(j.user_id)
        # Asignados históricos: old_value/new_value de details de asignación
        for j in self.journals:
            for d in j.details:
                if d.get("property") not in ("assigned_to_id", "assigned_to"):
                    continue
                for raw in (d.get("old_value"), d.get("new_value")):
                    if raw is None:
                        continue
                    try:
                        uid = int(raw)
                    except (TypeError, ValueError):
                        continue
                    if uid and uid not in seen:
                        seen.add(uid)
                        ids.append(uid)
        return ids

    def roles_for_user(self, user_id: int) -> set[str]:
        """Roles de implicación de un usuario en la tarea.

        Devuelve un subconjunto de {"creador", "actualizador", "participante"}:
        - "creador": el usuario es el autor del issue.
        - "actualizador": el usuario es autor de cualquier journal.
        - "participante": el usuario es autor de algún journal con notas,
          es el asignado actual, o tuvo la tarea asignada en algún cambio de
          `assigned_to_id`/`assigned_to` registrado en los `details` de los
          journals (asignación histórica).
        """
        roles: set[str] = set()
        if user_id and user_id == self.author_id:
            roles.add("creador")
        journal_author_ids = {j.user_id for j in self.journals if j.user_id}
        if user_id in journal_author_ids:
            roles.add("actualizador")
            if any(j.user_id == user_id and j.notes for j in self.journals):
                roles.add("participante")
        if user_id and user_id == self.assigned_to_id:
            roles.add("participante")
        # Asignación histórica: el usuario fue old_value o new_value de un
        # cambio de asignado en los details de algún journal. La comparación
        # se hace con str(...) en ambos lados (D12) para soportar valores
        # como cadena o como entero, evitando comparar None.
        if user_id:
            uid_str = str(user_id)
            for j in self.journals:
                for d in j.details:
                    if d.get("property") in ("assigned_to_id", "assigned_to"):
                        old = d.get("old_value")
                        new = d.get("new_value")
                        if (old is not None and str(old) == uid_str) or \
                           (new is not None and str(new) == uid_str):
                            roles.add("participante")
        return roles

    def matches_user_filter(self, user_ids: set[int], roles: set[str]) -> bool:
        """Indica si la tarea cumple el filtro por usuarios implicados.

        True si algún uid de user_ids cumple alguno de los roles seleccionados.
        Si user_ids está vacío, la dimensión usuarios no restringe (True).
        """
        if not user_ids:
            return True
        return any(self.roles_for_user(uid) & roles for uid in user_ids)


@dataclass
class RedmineCustomField:
    """Definición de un campo personalizado de un proyecto Redmine."""
    id: int
    name: str
    field_format: str = ""
    is_required: bool = False
    multiple: bool = False
    possible_values: list[str] = field(default_factory=list)
    default_value: str = ""
    visible: bool = True
    editable: bool = True


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
    user_id: int = 0
    user_name: str = ""
    notes: str = ""
    created_on: str = ""
    details: list[dict] = field(default_factory=list)


@dataclass
class RedmineChecklistItem:
    id: int
    issue_id: int
    subject: str
    is_done: bool = False
    position: int = 0


@dataclass
class RedmineAttachment:
    id: int
    filename: str
    filesize: int = 0
    content_type: str = ""
    content_url: str = ""
    description: str = ""
    author_name: str = ""
    created_on: str = ""


class RedmineError(Exception):
    pass


class RedmineAuthError(RedmineError):
    pass


class RedmineConnectionError(RedmineError):
    pass


class RedmineSSOError(RedmineError):
    pass


class RedmineValidationError(RedmineError):
    """Error de validación devuelto por la API de Redmine (HTTP 422).

    Attributes:
        errors: Lista de mensajes de error de validación devueltos por la API.
    """

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class RedmineClient:
    def __init__(self, base_url: str, api_key: str, proxy_url: str | None = None,
                 session_cookie: str = "", extra_headers: dict[str, str] | None = None):
        url = base_url.strip()
        if url and not url.startswith(("http://", "https://")):
            url = "https://" + url
        self._base_url = url.rstrip("/")
        self._api_key = api_key
        self._proxy_url = proxy_url
        self._session_cookie = session_cookie
        self._extra_headers = extra_headers or {}
        self._client: httpx.Client | None = None
        self._cached_user_id: int | None = None

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

    def _extract_validation_errors(self, resp) -> list[str]:
        """Extrae mensajes de error de validación del JSON de respuesta (HTTP 422)."""
        body = self._safe_json(resp)
        if not body or not isinstance(body, dict):
            return [f"Error HTTP {resp.status_code}"]
        errors = body.get("errors", [])
        if not errors:
            return [f"Error HTTP {resp.status_code}"]
        if isinstance(errors, list):
            return [str(e) for e in errors]
        return [str(errors)]

    def _safe_json(self, resp) -> dict | None:
        """Intenta parsear JSON de una respuesta, devolviendo None si falla."""
        try:
            return resp.json()
        except Exception:
            return None

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
            if resp.status_code >= 400:
                body = self._safe_json(resp)
                detail = ""
                if body and isinstance(body, dict):
                    errors = body.get("errors", [])
                    if errors:
                        detail = ": " + "; ".join(str(e) for e in errors)
                raise RedmineError(f"Error HTTP {resp.status_code} en {path}{detail}")
            return resp.json()
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")

    def _post(self, path: str, data: dict) -> dict:
        resp = None
        try:
            resp = self.client.post(path, json=data)
            self._check_redirect(resp, path)
            if resp.status_code == 401:
                raise RedmineAuthError("API key no válida (HTTP 401)")
            if resp.status_code == 422:
                errors = self._extract_validation_errors(resp)
                raise RedmineValidationError(
                    f"Error de validación al crear/actualizar en {path}",
                    errors,
                )
            if resp.status_code >= 400:
                body = self._safe_json(resp)
                detail = ""
                if body and isinstance(body, dict):
                    errors = body.get("errors", [])
                    if errors:
                        detail = ": " + "; ".join(str(e) for e in errors)
                raise RedmineError(f"Error HTTP {resp.status_code} en {path}{detail}")
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")
        try:
            return resp.json() if resp is not None else {}
        except Exception:
            return {}

    def _put(self, path: str, data: dict) -> dict:
        resp = None
        try:
            resp = self.client.put(path, json=data)
            self._check_redirect(resp, path)
            if resp.status_code == 401:
                raise RedmineAuthError("API key no válida (HTTP 401)")
            if resp.status_code == 422:
                errors = self._extract_validation_errors(resp)
                raise RedmineValidationError(
                    f"Error de validación al actualizar en {path}",
                    errors,
                )
            if resp.status_code >= 400:
                body = self._safe_json(resp)
                detail = ""
                if body and isinstance(body, dict):
                    errors = body.get("errors", [])
                    if errors:
                        detail = ": " + "; ".join(str(e) for e in errors)
                raise RedmineError(f"Error HTTP {resp.status_code} en {path}{detail}")
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")
        try:
            return resp.json() if resp is not None else {}
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

    def get_projects(self, offset: int = 0, limit: int = 100) -> list[RedmineProject]:
        """Obtiene una página de proyectos desde la API de Redmine.

        Args:
            offset: Desplazamiento para paginación.
            limit: Número máximo de proyectos a obtener (máximo 100 por página).
        """
        raw = self._get("/projects.json", params={"limit": limit, "offset": offset})
        projects_list = raw.get("projects", [])
        projects: list[RedmineProject] = []
        for p in projects_list:
            projects.append(RedmineProject(
                id=p["id"],
                name=p["name"],
                identifier=p["identifier"],
                parent_id=p.get("parent", {}).get("id") if p.get("parent") else None,
            ))
        return projects

    def get_all_projects(self, page_limit: int = 100) -> list[RedmineProject]:
        """Obtiene todos los proyectos usando paginación.

        Itera sobre las páginas de la API hasta recibir una lista vacía,
        con un máximo de 20 páginas (2000 proyectos) como límite de seguridad.

        Args:
            page_limit: Número de proyectos por página.
        """
        all_projects: list[RedmineProject] = []
        max_pages = 20
        for page in range(max_pages):
            offset = page * page_limit
            projects = self.get_projects(offset=offset, limit=page_limit)
            if not projects:
                break
            all_projects.extend(projects)
        # Componer el nombre completo (jerarquía) y ordenar por él
        full_names = build_project_full_names(all_projects)
        for p in all_projects:
            p.full_name = full_names[p.id]
        all_projects.sort(key=lambda x: x.full_name.lower())
        return all_projects

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
        project_id: int | list[int] | None = None,
        status_filter: str | int | list[int] | None = "open",
        category_id: int | None = None,
        priority_id: int | None = None,
        assigned_to_id: int | str | list | None = None,
        due_date_from: str | None = None,
        due_date_to: str | None = None,
        created_on_from: str | None = None,
        created_on_to: str | None = None,
        include_journals: bool = False,
        current_user_id: int = 0,
        limit: int = REDMINE_PAGE_LIMIT,
        offset: int = 0,
    ) -> list[RedmineIssue]:
        include = "attachments"
        if include_journals:
            include += ",journals"
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "sort": "updated_on:desc",
            "include": include,
        }
        # Normalizar project_id: lista vacía o None → sin filtro; lista de 1 → escalar a int
        multiple_projects: list[int] | None = None
        if isinstance(project_id, list):
            if len(project_id) == 1:
                project_id = project_id[0]
            elif len(project_id) > 1:
                multiple_projects = [pid for pid in project_id if pid]
                project_id = None
        if project_id:
            params["project_id"] = project_id
        # status_filter: escalar (str/int) como hoy; lista → varios ids separados por coma
        if isinstance(status_filter, list):
            if status_filter:
                params["status_id"] = ",".join(map(str, status_filter))
        elif status_filter:
            params["status_id"] = status_filter
        if category_id:
            params["category_id"] = category_id
        if priority_id:
            params["priority_id"] = priority_id

        # Filtro de asignado: soporta int, str, lista, o None.
        # Si hay múltiples valores, se filtra client-side para garantizar OR correcto.
        client_side_ids: set | None = None
        if isinstance(assigned_to_id, list):
            if len(assigned_to_id) == 0:
                assigned_to_id = None
            elif len(assigned_to_id) == 1:
                assigned_to_id = assigned_to_id[0]  # valor único → API
            else:
                # Múltiples valores: no filtrar en API, hacer todo client-side
                client_side_ids = set(assigned_to_id)
                assigned_to_id = None

        if isinstance(assigned_to_id, str):
            params["assigned_to_id"] = assigned_to_id
        elif isinstance(assigned_to_id, int):
            params["assigned_to_id"] = assigned_to_id

        if due_date_from and due_date_to:
            if due_date_from == due_date_to:
                params["due_date"] = f"={due_date_from}"
            else:
                params["due_date"] = f"><{due_date_from}|{due_date_to}"
        elif due_date_from:
            params["due_date"] = f">={due_date_from}"
        elif due_date_to:
            params["due_date"] = f"<={due_date_to}"

        # Filtro por fecha de creación (misma sintaxis que due_date)
        if created_on_from and created_on_to:
            if created_on_from == created_on_to:
                params["created_on"] = f"={created_on_from}"
            else:
                params["created_on"] = f"><{created_on_from}|{created_on_to}"
        elif created_on_from:
            params["created_on"] = f">={created_on_from}"
        elif created_on_to:
            params["created_on"] = f"<={created_on_to}"

        # Multi-proyecto: una petición por proyecto, fusionando sin duplicados
        issues: list[RedmineIssue] = []
        if multiple_projects:
            seen_ids: set[int] = set()
            for pid in multiple_projects:
                project_params = dict(params)
                project_params["project_id"] = pid
                raw = self._get("/issues.json", params=project_params)
                for i in raw.get("issues", []):
                    if i["id"] in seen_ids:
                        continue
                    seen_ids.add(i["id"])
                    issues.append(self._issue_from_json(i))
            issues.sort(key=lambda x: x.updated_on or "", reverse=True)
        else:
            raw = self._get("/issues.json", params=params)
            issues = [self._issue_from_json(i) for i in raw.get("issues", [])]

        # Filtro client-side para múltiples asignados (OR lógico entre todos)
        if client_side_ids is not None:
            has_none = "!*" in client_side_ids
            has_me = "me" in client_side_ids
            num_ids = {a for a in client_side_ids if isinstance(a, int)}

            filtered: list[RedmineIssue] = []
            for iss in issues:
                aid = iss.assigned_to_id
                if aid in num_ids:
                    filtered.append(iss)
                elif has_none and aid == 0:
                    filtered.append(iss)
                elif has_me and aid == current_user_id:
                    filtered.append(iss)
            issues = filtered

        return issues

    @classmethod
    def _issue_from_json(cls, i: dict) -> RedmineIssue:
        """Convierte un dict de issue de la API Redmine en un RedmineIssue."""
        return RedmineIssue(
            id=i["id"],
            subject=i.get("subject", ""),
            description=i.get("description", ""),
            start_date=i.get("start_date", ""),
            due_date=i.get("due_date", ""),
            status_name=i.get("status", {}).get("name", ""),
            status_id=i.get("status", {}).get("id", 0),
            done_ratio=i.get("done_ratio", 0),
            project_id=i.get("project", {}).get("id", 0),
            project_name=i.get("project", {}).get("name", ""),
            assigned_to_id=i.get("assigned_to", {}).get("id", 0) if i.get("assigned_to") else 0,
            assigned_to_name=i.get("assigned_to", {}).get("name", "") if i.get("assigned_to") else "",
            author_id=i.get("author", {}).get("id", 0) if i.get("author") else 0,
            author_name=i.get("author", {}).get("name", ""),
            created_on=i.get("created_on", ""),
            updated_on=i.get("updated_on", ""),
            tracker_id=i.get("tracker", {}).get("id", 0),
            tracker_name=i.get("tracker", {}).get("name", ""),
            priority_id=i.get("priority", {}).get("id", 0),
            priority_name=i.get("priority", {}).get("name", ""),
            category_id=i.get("category", {}).get("id", 0),
            category_name=i.get("category", {}).get("name", ""),
            attachments=cls._parse_attachments(i.get("attachments", [])),
            custom_fields=cls._parse_custom_fields(i.get("custom_fields", [])),
            journals=cls._parse_journals(i.get("journals", [])),
        )

    @staticmethod
    def _parse_journals(journals_raw: list) -> list[RedmineJournal]:
        """Convierte el array journals de la API en una lista de RedmineJournal.

        Conserva TODOS los journals, incluidos los que no tienen notas
        (cambios de atributos), para poder clasificar el rol "actualizador".
        Cada journal conserva sus `details` (cambios de atributo) normalizados
        a dicts con `property`, `old_value` y `new_value` (valores tal cual,
        pueden ser cadenas o None).
        """
        journals = []
        for j in journals_raw:
            details = []
            for d in j.get("details", []) or []:
                details.append({
                    "property": d.get("property"),
                    "old_value": d.get("old_value"),
                    "new_value": d.get("new_value"),
                })
            journals.append(RedmineJournal(
                id=j.get("id", 0),
                user_id=(j.get("user") or {}).get("id", 0),
                user_name=(j.get("user") or {}).get("name", ""),
                notes=j.get("notes", ""),
                created_on=j.get("created_on", ""),
                details=details,
            ))
        return journals

    @staticmethod
    def _parse_custom_fields(custom_fields_raw: list) -> dict[int, Any]:
        """Convierte el array custom_fields de la API en un dict id -> valor."""
        result: dict[int, Any] = {}
        for cf in custom_fields_raw or []:
            cf_id = cf.get("id")
            if cf_id is not None:
                result[int(cf_id)] = cf.get("value")
        return result

    @staticmethod
    def _parse_attachments(attachments_raw: list) -> list[RedmineAttachment]:
        attachments = []
        for a in attachments_raw:
            attachments.append(RedmineAttachment(
                id=a.get("id", 0),
                filename=a.get("filename", ""),
                filesize=a.get("filesize", 0),
                content_type=a.get("content_type", ""),
                content_url=a.get("content_url", ""),
                description=a.get("description", ""),
                author_name=a.get("author", {}).get("name", ""),
                created_on=a.get("created_on", ""),
            ))
        return attachments

    # ---- Issue actions ----

    def get_issue(self, issue_id: int, include_journals: bool = False) -> dict:
        return self._get(f"/issues/{issue_id}.json", params={"include": "journals"} if include_journals else None)

    def get_issue_with_journals(self, issue_id: int) -> dict:
        """Obtiene issue + journals y attachments parseados."""
        raw = self._get(f"/issues/{issue_id}.json", params={"include": "journals,attachments"})
        issue_data = raw.get("issue", {})
        journals_raw = issue_data.get("journals", [])
        journals = []
        for j in journals_raw:
            if j.get("notes"):  # Solo journals con notas (ignorar cambios de atributos)
                journals.append(RedmineJournal(
                    id=j["id"],
                    user_name=(j.get("user") or {}).get("name", "Desconocido"),
                    notes=j.get("notes", ""),
                    created_on=j.get("created_on", ""),
                ))
        # Añadir category si existe
        cat = issue_data.get("category")
        if cat:
            issue_data["category_id"] = cat.get("id", 0)
            issue_data["category_name"] = cat.get("name", "")
        issue_data["_journals"] = journals
        # Parsear attachments
        issue_data["_attachments"] = self._parse_attachments(issue_data.get("attachments", []))
        # Valores actuales de campos personalizados (dict id -> valor)
        issue_data["_custom_fields"] = self._parse_custom_fields(issue_data.get("custom_fields", []))
        return issue_data

    def create_issue(self, project_id: int, subject: str, description: str = "",
                     tracker_id: int = 1, priority_id: int = 2,
                     assigned_to_id: int | None = None,
                     category_id: int = 0, start_date: str = "",
                     due_date: str = "",
                     done_ratio: int = 0,
                     uploads: list[dict] | None = None,
                     custom_fields: dict[int, Any] | None = None) -> dict:
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
        if due_date:
            payload["due_date"] = due_date
        if done_ratio:
            payload["done_ratio"] = done_ratio
        if uploads:
            payload["uploads"] = uploads
        if custom_fields:
            payload["custom_fields"] = self._serialize_custom_fields(custom_fields)
        return self._post("/issues.json", {"issue": payload})

    @staticmethod
    def _serialize_custom_fields(custom_fields: dict[int, Any]) -> list[dict]:
        """Serializa un dict id -> valor al formato de la API: [{"id": N, "value": X}].

        Las entradas con valor None se omiten (no se envían).
        """
        return [
            {"id": cf_id, "value": value}
            for cf_id, value in custom_fields.items()
            if value is not None
        ]

    def update_issue(self, issue_id: int, **fields) -> dict:
        uploads = fields.pop("uploads", None)
        custom_fields = fields.pop("custom_fields", None)
        payload: dict[str, Any] = {"issue": fields}
        if uploads:
            payload["issue"]["uploads"] = uploads
        if custom_fields:
            payload["issue"]["custom_fields"] = self._serialize_custom_fields(custom_fields)
        return self._put(f"/issues/{issue_id}.json", payload)

    def assign_issue(self, issue_id: int, user_id: int, notes: str = "") -> dict:
        fields: dict[str, Any] = {"assigned_to_id": user_id}
        if notes:
            fields["notes"] = notes
        return self.update_issue(issue_id, **fields)

    def complete_issue(self, issue_id: int, done_ratio: int = 100,
                       status_id: int | None = None, notes: str = "",
                       due_date: str = "") -> dict:
        fields: dict[str, Any] = {"done_ratio": done_ratio}
        if status_id:
            fields["status_id"] = status_id
        if notes:
            fields["notes"] = notes
        if due_date:
            fields["due_date"] = due_date
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

    def get_project_custom_fields(self, project_id: int) -> list[RedmineCustomField]:
        """Obtiene los campos personalizados definidos en un proyecto.

        Realiza GET /projects/{id}.json?include=issue_custom_fields y mapea
        cada entrada de `issue_custom_fields` a un RedmineCustomField.
        """
        raw = self._get(f"/projects/{project_id}.json", params={"include": "issue_custom_fields"})
        project = raw.get("project", {})
        fields: list[RedmineCustomField] = []
        for cf in project.get("issue_custom_fields", []) or []:
            fields.append(RedmineCustomField(
                id=cf["id"],
                name=cf.get("name", ""),
                field_format=cf.get("field_format", ""),
                is_required=bool(cf.get("is_required", False)),
                multiple=bool(cf.get("multiple", False)),
                possible_values=cf.get("possible_values", []) or [],
                default_value=cf.get("default_value", ""),
                visible=cf.get("visible", True),
                editable=cf.get("editable", True),
            ))
        return fields

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
        """Obtiene el ID del usuario actual, cacheando el resultado."""
        if self._cached_user_id is not None:
            return self._cached_user_id
        data = self._get("/users/current.json")
        self._cached_user_id = data["user"]["id"]
        return self._cached_user_id

    def upload_file(self, file_path: str) -> dict:
        """Sube un archivo a Redmine mediante POST /uploads.json.

        Args:
            file_path: Ruta local del archivo a subir.

        Returns:
            dict con la respuesta de Redmine, ej: {"upload": {"token": "..."}}

        Raises:
            RedmineError: Si el archivo no existe, la subida falla o el servidor
                          no soporta uploads.
        """
        import mimetypes
        import os

        if not os.path.isfile(file_path):
            raise RedmineError(f"Archivo no encontrado: {file_path}")

        with open(file_path, "rb") as f:
            file_content = f.read()

        filename = os.path.basename(file_path)
        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or "application/octet-stream"

        headers = {
            "X-Redmine-API-Key": self._api_key,
            "Content-Type": "application/octet-stream",
        }
        if self._session_cookie:
            headers["Cookie"] = self._session_cookie
        headers.update(self._extra_headers)

        try:
            with httpx.Client(
                base_url=self._base_url,
                headers=headers,
                timeout=REDMINE_REQUEST_TIMEOUT * 4,
                follow_redirects=False,
                proxy=self._proxy_url if self._proxy_url else None,
            ) as upload_client:
                resp = upload_client.post("/uploads.json", content=file_content)
                if resp.status_code == 401:
                    raise RedmineAuthError("API key no válida (HTTP 401)")
                if resp.status_code == 404:
                    raise RedmineError(
                        "La subida de archivos no está disponible en este servidor Redmine "
                        "(HTTP 404). El plugin de uploads podría no estar habilitado."
                    )
                if resp.status_code == 405:
                    raise RedmineError(
                        "La subida de archivos no está permitida en este servidor Redmine "
                        "(HTTP 405). Verifica la configuración del servidor."
                    )
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError(
                "Timeout al subir el archivo (puede ser demasiado grande)."
            )

    def delete_attachment(self, attachment_id: int) -> bool:
        """Elimina un adjunto via DELETE /attachments/{id}.json.

        Returns:
            True si la eliminacion fue exitosa, False en caso de error.
        """
        try:
            self._delete(f"/attachments/{attachment_id}.json")
            return True
        except RedmineError:
            return False

    def download_attachment(self, content_url: str, dest_path: str):
        """Descarga un adjunto desde content_url a dest_path usando streaming."""
        client = self._build_client()
        try:
            with client.stream("GET", content_url) as response:
                response.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
        except httpx.HTTPError as e:
            raise RedmineError(f"Error al descargar adjunto: {e}") from e
        finally:
            client.close()

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None
