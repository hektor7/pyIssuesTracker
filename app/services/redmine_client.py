from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Any

import copy
import httpx

from app.utils.constants import REDMINE_REQUEST_TIMEOUT, REDMINE_PAGE_LIMIT
from app.utils.projects import build_project_full_names
from app.services.custom_field_definitions import parse_issue_form_custom_fields

import logging

logger = logging.getLogger(__name__)


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
    definition_source: str = ""
    degraded_reason: str = ""


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
    """Error base de la API de Redmine.

    Attributes:
        status_code: Código HTTP que originó el error, si está disponible.
    """

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class RedmineAuthError(RedmineError):
    pass


class RedmineConnectionError(RedmineError):
    pass


class RedmineSSOError(RedmineError):
    """Redirección del servidor que impide completar la petición.

    Attributes:
        location: Valor del header `Location`, si está disponible.
    """

    def __init__(self, message: str, location: str = ""):
        super().__init__(message)
        self.location = location


class RedmineValidationError(RedmineError):
    """Error de validación devuelto por la API de Redmine (HTTP 422).

    Attributes:
        errors: Lista de mensajes de error de validación devueltos por la API.
    """

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class RedmineClient:
    _CUSTOM_FIELDS_PAGE_LIMIT = 100
    _CUSTOM_FIELDS_MAX_PAGES = 20

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
        # Caché de definiciones de campos personalizados (D6). Vive en la
        # instancia: un cliente nuevo no comparte nada con el anterior.
        self._project_custom_fields: dict[int, list[RedmineCustomField]] = {}
        self._custom_field_definitions: dict[int, RedmineCustomField] | None = None
        self._custom_field_definitions_error: str | None = None
        self._project_form_definitions: dict[int, dict[int, RedmineCustomField]] = {}
        self._project_form_errors: dict[int, str] = {}
        self._issue_form_auth_failure: str | None = None

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
        except Exception as e:
            logger.debug("No se pudo parsear el JSON de la respuesta (%s): %s",
                         getattr(resp, "status_code", "?"), e)
            return None

    def _raise_for_status(
        self,
        resp,
        path: str,
        validation_message: str | None = None,
    ) -> None:
        """Lanza la excepción adecuada según el código HTTP de la respuesta.

        Replica el mapeo histórico de `_get` (401/403 → RedmineAuthError,
        404 → RedmineError, resto ≥400 → RedmineError con detalle de
        `errors`) y adjunta `status_code` a la excepción.

        Args:
            resp: Respuesta HTTP.
            path: Ruta solicitada, usada en los mensajes.
            validation_message: Si se indica, un HTTP 422 se convierte en
                `RedmineValidationError` con ese mensaje y los errores
                parseados (comportamiento de `_post`/`_put`).
        """
        if resp.status_code == 401:
            raise RedmineAuthError("API key no válida (HTTP 401)", status_code=401)
        if resp.status_code == 403:
            raise RedmineAuthError("Acceso denegado (HTTP 403)", status_code=403)
        if resp.status_code == 404:
            raise RedmineError(f"Recurso no encontrado: {path}", status_code=404)
        if resp.status_code == 422 and validation_message is not None:
            errors = self._extract_validation_errors(resp)
            raise RedmineValidationError(validation_message, errors)
        if resp.status_code >= 400:
            body = self._safe_json(resp)
            detail = ""
            if body and isinstance(body, dict):
                errors = body.get("errors", [])
                if errors:
                    detail = ": " + "; ".join(str(e) for e in errors)
            raise RedmineError(
                f"Error HTTP {resp.status_code} en {path}{detail}",
                status_code=resp.status_code,
            )

    def _parse_json(self, resp, path: str) -> dict:
        """Parsea el JSON de una respuesta y convierte un cuerpo inválido.

        Un 200 con HTML (SSO, proxy) no debe escapar como `ValueError`: se
        convierte en `RedmineError` para que la cascada de campos personalizados
        pueda degradar al formulario HTML y el informe ODS no se rompa.
        """
        try:
            return resp.json()
        except ValueError as exc:
            raise RedmineError(
                f"Respuesta no válida de Redmine en '{path}': el cuerpo no es JSON",
                status_code=getattr(resp, "status_code", None),
            ) from exc

    def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            resp = self.client.get(path, params=params or {})
            self._check_redirect(resp, path)
            self._raise_for_status(resp, path)
            return self._parse_json(resp, path)
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")
        except httpx.HTTPError as e:
            raise RedmineConnectionError(
                f"Error de transporte con el servidor Redmine: {e}"
            )

    def _get_text(self, path: str, params: dict | None = None) -> str:
        """Obtiene el cuerpo de una respuesta no JSON (por ejemplo, HTML).

        Comparte el tratamiento de redirecciones y errores HTTP de `_get`,
        pero devuelve `resp.text` en lugar de parsear JSON.
        """
        try:
            resp = self.client.get(path, params=params or {})
            self._check_redirect(resp, path)
            self._raise_for_status(resp, path)
            return resp.text
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")
        except httpx.HTTPError as e:
            raise RedmineConnectionError(
                f"Error de transporte con el servidor Redmine: {e}"
            )

    def _post(self, path: str, data: dict) -> dict:
        resp = None
        try:
            resp = self.client.post(path, json=data)
            self._check_redirect(resp, path)
            self._raise_for_status(
                resp,
                path,
                validation_message=(
                    f"Error de validación al crear/actualizar en {path}"
                ),
            )
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")
        try:
            return resp.json() if resp is not None else {}
        except Exception as e:
            logger.warning("No se pudo parsear el JSON de la respuesta POST (%s): %s",
                           getattr(resp, "status_code", "?"), e)
            return {}

    def _put(self, path: str, data: dict) -> dict:
        resp = None
        try:
            resp = self.client.put(path, json=data)
            self._check_redirect(resp, path)
            self._raise_for_status(
                resp,
                path,
                validation_message=(
                    f"Error de validación al actualizar en {path}"
                ),
            )
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")
        try:
            return resp.json() if resp is not None else {}
        except Exception as e:
            logger.warning("No se pudo parsear el JSON de la respuesta PUT (%s): %s",
                           getattr(resp, "status_code", "?"), e)
            return {}

    def _delete(self, path: str) -> dict:
        try:
            resp = self.client.delete(path)
            self._check_redirect(resp, path)
            self._raise_for_status(resp, path)
            return {}
        except httpx.ConnectError as e:
            raise RedmineConnectionError(f"No se pudo conectar al servidor Redmine: {e}")
        except httpx.TimeoutException:
            raise RedmineConnectionError("Timeout al conectar al servidor Redmine")

    def _check_redirect(self, resp, path: str):
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "") or ""
            if "login" in location.lower() or "sso" in location.lower() or "auth" in location.lower():
                raise RedmineSSOError(
                    "El servidor Redmine esta protegido por un portal de autenticacion (SSO).\n\n"
                    "La API key no es suficiente. El administrador debe configurar\n"
                    "Redmine para permitir acceso API sin pasar por el SSO.",
                    location=location,
                )
            raise RedmineSSOError(
                f"Redireccion inesperada [{resp.status_code}] en '{path}'.",
                location=location,
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

    def get_project_trackers(self, project_id: int) -> list[tuple[int, str]]:
        """Obtiene los trackers (tipos) definidos en un proyecto concreto.

        Realiza GET /projects/{id}.json?include=trackers y devuelve
        [(id, nombre), ...]. Un proyecto sin trackers devuelve lista vacía.
        Los errores de red/API se propagan (el fail-open lo aplica el caller).
        """
        raw = self._get(f"/projects/{project_id}.json", params={"include": "trackers"})
        project = raw.get("project", {})
        return [
            (t["id"], t["name"])
            for t in project.get("trackers", []) or []
        ]

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
        failed_projects: list | None = None,
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

        # Multi-proyecto: una petición por proyecto, fusionando sin duplicados.
        # Cada proyecto se consulta de forma AISLADA: un fallo (404/403/timeout)
        # en uno de ellos no aborta el merge; el pid fallido se acumula en
        # failed_projects (si se pasó) y se registra en el log.
        issues: list[RedmineIssue] = []
        if multiple_projects:
            seen_ids: set[int] = set()
            for pid in multiple_projects:
                project_params = dict(params)
                project_params["project_id"] = pid
                try:
                    raw = self._get("/issues.json", params=project_params)
                except RedmineError as e:
                    logger.error(
                        "Error al cargar issues del proyecto %s: %s", pid, e
                    )
                    if failed_projects is not None:
                        failed_projects.append(pid)
                    continue
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
        # Redmine rechaza category_id=0 ("Category is not included in the list").
        # Un valor falsy (0 o None) se normaliza a "" (semántica nativa de Redmine
        # para "sin categoría"); un id positivo se envía tal cual.
        if "category_id" in fields and not fields["category_id"]:
            fields["category_id"] = ""
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

    def _describe_error(self, exc: RedmineError) -> str:
        """Motivo legible y sin secretos de un fallo de la API de Redmine."""
        status = getattr(exc, "status_code", None)
        if isinstance(exc, RedmineConnectionError):
            return "no se pudo conectar con Redmine"
        if isinstance(exc, RedmineSSOError):
            return "redirección de autenticación (SSO)"
        if status == 401:
            return "la API key no es válida (HTTP 401)"
        if status == 403:
            return "la API key no tiene permisos de administrador (HTTP 403)"
        if status == 404:
            return "las definiciones no están disponibles (HTTP 404)"
        if status is not None:
            return f"error HTTP {status} al consultar las definiciones"
        return str(exc)

    def _fetch_project_custom_field_stubs(self, project_id: int) -> list[tuple[int, str]]:
        """Obtiene solo id, nombre y orden de la pertenencia al proyecto (D2).

        El `include=issue_custom_fields` de Redmine real no devuelve la
        definición completa: cualquier clave extra se ignora deliberadamente.
        """
        raw = self._get(
            f"/projects/{project_id}.json",
            params={"include": "issue_custom_fields"},
        )
        if not isinstance(raw, dict):
            raise RedmineError(
                "Respuesta inválida al consultar los campos del proyecto"
            )
        project = raw.get("project", {}) or {}
        if not isinstance(project, dict):
            raise RedmineError(
                "Respuesta inválida al consultar los campos del proyecto"
            )
        stubs: list[tuple[int, str]] = []
        for cf in project.get("issue_custom_fields", []) or []:
            if not isinstance(cf, dict) or "id" not in cf:
                continue
            try:
                cf_id = int(cf["id"])
            except (TypeError, ValueError):
                raise RedmineError(
                    "Identificador de campo personalizado inválido en el proyecto"
                )
            stubs.append((cf_id, cf.get("name", "")))
        return stubs

    @staticmethod
    def _normalize_possible_values(raw_values: list | None) -> list[str]:
        """Normaliza `possible_values` en objetos {value,label} o cadenas."""
        if not isinstance(raw_values, list):
            return []
        normalizados: list[str] = []
        for item in raw_values or []:
            if isinstance(item, dict):
                valor = item.get("value")
                if valor is None:
                    valor = item.get("label", "")
            else:
                valor = item
            normalizados.append("" if valor is None else str(valor))
        return normalizados

    def _admin_custom_field_from_json(self, cf: dict) -> RedmineCustomField:
        """Construye la definición completa desde `/custom_fields.json`."""
        return RedmineCustomField(
            id=int(cf["id"]),
            name=cf.get("name", ""),
            field_format=cf.get("field_format", "") or "",
            is_required=bool(cf.get("is_required", False)),
            multiple=bool(cf.get("multiple", False)),
            possible_values=self._normalize_possible_values(
                cf.get("possible_values")
            ),
            default_value=cf.get("default_value", "") or "",
            visible=cf.get("visible", True),
            editable=cf.get("editable", True),
            definition_source="admin",
        )

    def _fetch_custom_field_definitions(self) -> dict[int, RedmineCustomField]:
        """Consulta `/custom_fields.json` y mapea las definiciones por id.

        Paginación defensiva (D1): si la respuesta no trae `total_count`
        numérico se hace una sola petición sin `limit`/`offset`. Si lo trae y
        supera lo acumulado, se piden páginas hasta alcanzarlo o hasta recibir
        una página vacía, con un tope de 20 peticiones. Un endpoint que ignore
        `limit`/`offset` no provoca un bucle infinito: el tope lo corta.
        """
        definitions: dict[int, RedmineCustomField] = {}
        total_count: int | None = None
        offset = 0

        for _ in range(self._CUSTOM_FIELDS_MAX_PAGES):
            if offset == 0:
                raw = self._get("/custom_fields.json")
            else:
                raw = self._get(
                    "/custom_fields.json",
                    params={
                        "limit": self._CUSTOM_FIELDS_PAGE_LIMIT,
                        "offset": offset,
                    },
                )
            if not isinstance(raw, dict):
                raise RedmineError("Respuesta inválida de /custom_fields.json")
            pagina = raw.get("custom_fields", []) or []
            if not isinstance(pagina, list):
                raise RedmineError("Respuesta inválida de /custom_fields.json")

            for cf in pagina:
                if not isinstance(cf, dict) or "id" not in cf:
                    continue
                if cf.get("customized_type") != "issue":
                    continue
                try:
                    cf_id = int(cf["id"])
                except (TypeError, ValueError):
                    continue
                definitions[cf_id] = self._admin_custom_field_from_json(cf)

            if total_count is None:
                raw_total = raw.get("total_count")
                if isinstance(raw_total, (int, float)) and not isinstance(
                    raw_total, bool
                ):
                    total_count = int(raw_total)
                else:
                    break

            offset += len(pagina)
            if not pagina or offset >= total_count:
                break

        return definitions

    def _load_admin_definitions(
        self,
    ) -> tuple[dict[int, RedmineCustomField], str | None]:
        """Devuelve las definiciones de administrador y memoriza el fallo."""
        if self._custom_field_definitions is not None:
            return self._custom_field_definitions, None
        if self._custom_field_definitions_error is not None:
            return {}, self._custom_field_definitions_error
        try:
            definitions = self._fetch_custom_field_definitions()
        except RedmineError as exc:
            self._custom_field_definitions_error = self._describe_error(exc)
            return {}, self._custom_field_definitions_error
        self._custom_field_definitions = definitions
        return definitions, None

    @staticmethod
    def _looks_like_login_page(html: str) -> bool:
        """Heurística mínima para identificar una página de login de Redmine."""
        lowered = html.lower()
        return (
            "login-form" in lowered
            or 'name="username"' in lowered
            or "name='username'" in lowered
        )

    @staticmethod
    def _is_authentication_redirect(exc: RedmineSSOError) -> bool:
        """Indica si una redirección apunta a un flujo de autenticación.

        Solo estas redirecciones justifican la caché negativa global del
        formulario HTML. Una redirección benigna (trailing slash, canónica,
        idioma) debe degradar únicamente el proyecto afectado.
        """
        location = (getattr(exc, "location", "") or "").lower()
        if location:
            return any(
                token in location
                for token in ("login", "sso", "saml", "oauth", "/auth")
            )
        message = str(exc).lower()
        return any(
            token in message
            for token in ("login", "sso", "autenticacion", "authentication")
        )

    def _describe_html_error(self, exc: RedmineError) -> str:
        """Motivo legible de un fallo al pedir el formulario HTML."""
        status = getattr(exc, "status_code", None)
        if isinstance(exc, RedmineSSOError):
            if self._is_authentication_redirect(exc):
                return "la Cookie de sesión no es válida o ha caducado"
            return (
                "el servidor redirigió el formulario a otra ubicación "
                "(redirección no autenticativa)"
            )
        if isinstance(exc, RedmineAuthError):
            return "la Cookie de sesión no es válida o ha caducado"
        if isinstance(exc, RedmineConnectionError):
            return "no se pudo conectar con Redmine para obtener el formulario"
        if status == 404:
            return "el formulario de nueva incidencia no existe (HTTP 404)"
        if status is not None:
            return (
                f"error HTTP {status} al obtener el formulario de nueva incidencia"
            )
        return str(exc)

    def _get_project_issue_form_definitions(
        self, project_id: int
    ) -> dict[int, RedmineCustomField]:
        """Obtiene y cachea las definiciones parciales del formulario HTML.

        Solo resuelve `field_format`, `multiple` y `possible_values`; el resto
        de la definición conserva sus valores por defecto (D1/D5).
        """
        if project_id in self._project_form_definitions:
            return self._project_form_definitions[project_id]
        if self._issue_form_auth_failure is not None:
            self._project_form_definitions[project_id] = {}
            self._project_form_errors[project_id] = self._issue_form_auth_failure
            return {}

        try:
            html = self._get_text(f"/projects/{project_id}/issues/new")
        except RedmineError as exc:
            motivo = self._describe_html_error(exc)
            self._project_form_definitions[project_id] = {}
            self._project_form_errors[project_id] = motivo
            if isinstance(exc, RedmineAuthError):
                self._issue_form_auth_failure = motivo
            elif isinstance(exc, RedmineSSOError) and self._is_authentication_redirect(exc):
                self._issue_form_auth_failure = motivo
            return {}

        parsed = parse_issue_form_custom_fields(html)
        if not parsed and self._looks_like_login_page(html):
            motivo = "la Cookie de sesión no es válida (página de login)"
            self._issue_form_auth_failure = motivo
            self._project_form_definitions[project_id] = {}
            self._project_form_errors[project_id] = motivo
            return {}

        definitions = {
            cf_id: RedmineCustomField(
                id=cf_id,
                name="",
                field_format=parsed_field.field_format,
                multiple=parsed_field.multiple,
                possible_values=list(parsed_field.possible_values),
                definition_source="html",
            )
            for cf_id, parsed_field in parsed.items()
        }
        self._project_form_definitions[project_id] = definitions
        if not definitions:
            self._project_form_errors[project_id] = (
                "el formulario no contiene controles de campos personalizados"
            )
        return definitions

    def _degradation_reason(self, project_id: int, admin_error: str | None) -> str:
        """Construye un motivo legible para un campo sin definición."""
        motivos: list[str] = []
        if admin_error:
            motivos.append(
                f"definiciones de administrador no disponibles: {admin_error}"
            )
        else:
            motivos.append(
                "la definición de administrador no contiene este campo"
            )
        if not self._session_cookie:
            motivos.append("no hay Cookie de sesión configurada")
        else:
            html_error = self._project_form_errors.get(project_id)
            if html_error:
                motivos.append(html_error)
            else:
                motivos.append(
                    "el campo no aparece en el formulario de nueva incidencia "
                    "(puede ser de solo lectura o de otro tracker)"
                )
        return "; ".join(motivos)

    def _degraded_custom_field(
        self, project_id: int, cf_id: int, name: str, reason: str
    ) -> RedmineCustomField:
        """Devuelve el campo en modo texto libre y registra el diagnóstico."""
        logger.warning(
            "Campo personalizado sin definición: proyecto=%s campo=%s "
            "nombre=%r motivo=%s",
            project_id,
            cf_id,
            name,
            reason,
        )
        return RedmineCustomField(
            id=cf_id,
            name=name,
            field_format="",
            is_required=False,
            multiple=False,
            possible_values=[],
            default_value="",
            visible=True,
            editable=True,
            definition_source="none",
            degraded_reason=reason,
        )

    def clear_custom_field_cache(self) -> None:
        """Vacía las cachés de definiciones y el fallo global del HTML.

        Se expone para tests y para un futuro refresco manual. La caché vive
        en la instancia, por lo que un cliente nuevo tampoco reutiliza nada.
        """
        self._project_custom_fields.clear()
        self._custom_field_definitions = None
        self._custom_field_definitions_error = None
        self._project_form_definitions.clear()
        self._project_form_errors.clear()
        self._issue_form_auth_failure = None

    def get_project_custom_fields(self, project_id: int) -> list[RedmineCustomField]:
        """Obtiene los campos personalizados definidos en un proyecto.

        La pertenencia al proyecto aporta solo id, nombre y orden. La
        definición se resuelve primero con `/custom_fields.json`; si no está
        disponible, se completa con el formulario HTML (nivel 3).
        """
        if project_id in self._project_custom_fields:
            return copy.deepcopy(self._project_custom_fields[project_id])

        stubs = self._fetch_project_custom_field_stubs(project_id)
        if not stubs:
            self._project_custom_fields[project_id] = []
            return []

        definitions, admin_error = self._load_admin_definitions()
        resolved: dict[int, RedmineCustomField] = {
            cf_id: definitions[cf_id]
            for cf_id, _name in stubs
            if cf_id in definitions
        }
        missing = [cf_id for cf_id, _name in stubs if cf_id not in resolved]

        if missing and self._session_cookie:
            html_definitions = self._get_project_issue_form_definitions(project_id)
            for cf_id in missing:
                if cf_id in html_definitions:
                    resolved[cf_id] = html_definitions[cf_id]

        fields: list[RedmineCustomField] = []
        for cf_id, name in stubs:
            definition = resolved.get(cf_id)
            if definition is not None:
                fields.append(replace(definition, name=name))
            else:
                fields.append(
                    self._degraded_custom_field(
                        project_id,
                        cf_id,
                        name,
                        self._degradation_reason(project_id, admin_error),
                    )
                )
        self._project_custom_fields[project_id] = fields
        return copy.deepcopy(fields)

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
        except RedmineError as e:
            logger.warning("No se pudo eliminar el adjunto %s: %s", attachment_id, e)
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
