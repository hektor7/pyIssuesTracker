import httpx
import mimetypes
import os
import subprocess
import tempfile
import webbrowser
from datetime import date, datetime

from urllib.parse import urljoin

from PyQt6.QtCore import QTimer, QUrl, Qt
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QStatusBar,
    QMessageBox, QMenuBar, QMenu, QApplication,
    QDialog, QLabel, QDialogButtonBox, QFileDialog,
)

from app import __version__
from app.services.settings_manager import SettingsManager
from app.services.redmine_client import (
    RedmineClient, RedmineError, RedmineAuthError, RedmineConnectionError,
    RedmineSSOError, RedmineValidationError,
)
from app.services.update_manager import UpdateManager
from app.widgets.status_indicator import StatusIndicator
from app.widgets.toolbar import IssueToolbar
from app.widgets.filter_bar import FilterBar
from app.widgets.task_table import TaskTable
from app.dialogs.settings_dialog import SettingsDialog
from app.dialogs.task_dialog import TaskDialog
from app.dialogs.reject_dialog import RejectDialog
from app.dialogs.assign_dialog import AssignDialog
from app.dialogs.complete_dialog import CompleteDialog
from app.dialogs.report_dialog import ReportDialog
from app.services.report_generator import ReportGenerator, REPORT_COLUMNS
from app.tray_icon import TrayManager
from app.utils.constants import APP_DISPLAY_NAME
from app.widgets.searchable_combo import make_searchable_combo, update_completer_model


class ProjectSelectDialog(QDialog):
    """Diálogo de selección de proyecto destino con combo buscable (tarea 5.4)."""

    def __init__(self, projects: list[tuple[int, str]], parent=None):
        super().__init__(parent)
        self._projects = projects or []
        self.setWindowTitle("Copiar a otro proyecto")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Selecciona el proyecto destino:"))

        self._combo = make_searchable_combo()
        for pid, pname in self._projects:
            self._combo.addItem(pname, pid)
        update_completer_model(self._combo)
        layout.addWidget(self._combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def selected_project_id(self) -> int:
        return self._combo.currentData() or 0


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._settings = SettingsManager()
        self._redmine: RedmineClient | None = None
        self._tray: TrayManager | None = None
        self._projects: list[tuple[int, str]] = []
        self._project_full_names: dict[int, str] = {}
        self._project_hierarchy: dict[int, int | None] = {}
        self._statuses: list[tuple[int, str]] = []
        self._priorities: list[tuple[int, str]] = []
        self._trackers: list[tuple[int, str]] = []
        self._current_user_id: int = 0
        self._search_text: str = ""

        self._known_issue_ids: dict[int, set[int]] = {}
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._check_new_issues)

        self.setWindowTitle(f"{APP_DISPLAY_NAME} v{__version__}")
        self.setMinimumSize(900, 550)
        self._setup_ui()
        self._setup_menu()
        self._setup_tray()
        self._restore_window_state()

        QTimer.singleShot(300, self._auto_connect)

    # ================================================================
    # UI Setup
    # ================================================================

    def _setup_ui(self):
        self.setObjectName("main_window")

        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._toolbar = IssueToolbar(self)
        self.addToolBar(self._toolbar)
        self._connect_toolbar_signals()

        self._filter_bar = FilterBar()
        self._filter_bar.setObjectName("filter_bar")
        self._filter_bar.proyecto_cambiado.connect(self._on_filter_project_changed)
        self._filter_bar.estado_cambiado.connect(self._on_filter_status_changed)
        self._filter_bar.prioridad_cambiada.connect(self._on_filter_priority_changed)
        self._filter_bar.categoria_cambiada.connect(self._on_filter_category_changed)
        self._filter_bar.asignado_cambiado.connect(self._on_filter_assigned_changed)
        self._filter_bar.fijar_cambiado.connect(self._on_filter_fixed_changed)
        self._filter_bar.busqueda_cambiada.connect(self._on_busqueda_cambiada)
        self._filter_bar.fecha_cambiada.connect(self._on_filter_date_changed)
        layout.addWidget(self._filter_bar)

        self._task_table = TaskTable()
        self._task_table.setObjectName("task_table")
        self._task_table.tarea_doble_click.connect(self._editar_tarea)
        self._task_table.tarea_abrir_url.connect(self._abrir_url_redmine)
        self._task_table.tarea_mover_proyecto.connect(self._copiar_tarea_otro_proyecto)
        self._task_table.cambio_rapido.connect(self._on_cambio_rapido)
        self._task_table.due_date_cambiada.connect(self._on_due_date_changed)
        self._task_table.columnas_cambiadas.connect(self._on_columnas_cambiadas)
        layout.addWidget(self._task_table)

        # Restaurar visibilidad de columnas persistida
        if self._settings.visible_columns is not None:
            self._task_table.apply_visible_column_keys(self._settings.visible_columns)

        self._status_indicator = StatusIndicator()
        self._status_indicator.setObjectName("status_indicator")
        self.setStatusBar(QStatusBar(self))

        from PyQt6.QtWidgets import QLabel
        self._proxy_label = QLabel()
        self._proxy_label.setStyleSheet("padding: 0 6px; color: #2196F3; font-weight: bold;")
        self.statusBar().addWidget(self._proxy_label)
        self.statusBar().addPermanentWidget(self._status_indicator)

        if self._settings.proxy_enabled and self._settings.proxy_host:
            self._proxy_label.setText(" PROXY ")
            self._proxy_label.setToolTip(
                f"Proxy: {self._settings.proxy_type}://{self._settings.proxy_host}:{self._settings.proxy_port}"
            )
        else:
            self._proxy_label.clear()

    def _setup_menu(self):
        mb = self.menuBar()
        mb.setObjectName("main_menu_bar")

        archivo_menu = mb.addMenu("&Archivo")
        archivo_menu.setObjectName("menu_archivo")

        action_config = QAction("&Configuracion...", self)
        action_config.setShortcut("Ctrl+,")
        action_config.triggered.connect(self._abrir_configuracion)
        archivo_menu.addAction(action_config)

        action_conectar = QAction("&Conectar", self)
        action_conectar.setShortcut("Ctrl+R")
        action_conectar.triggered.connect(self._conectar_redmine)
        archivo_menu.addAction(action_conectar)

        archivo_menu.addSeparator()

        action_update = QAction("&Buscar actualizaciones...", self)
        action_update.triggered.connect(self._buscar_actualizaciones)
        archivo_menu.addAction(action_update)

        archivo_menu.addSeparator()

        action_salir = QAction("&Salir", self)
        action_salir.setShortcut("Ctrl+Q")
        action_salir.triggered.connect(self._salir)
        archivo_menu.addAction(action_salir)

        self._apply_menu_style()

    def _connect_toolbar_signals(self):
        self._toolbar.nuevo_clicked.connect(self._nueva_tarea)
        self._toolbar.editar_clicked.connect(self._editar_tarea_seleccionada)
        self._toolbar.asignar_clicked.connect(self._asignar_tarea)
        self._toolbar.completar_clicked.connect(self._completar_tarea)
        self._toolbar.rechazar_clicked.connect(self._rechazar_tarea)
        self._toolbar.refrescar_clicked.connect(self._cargar_issues)
        self._toolbar.informe_clicked.connect(self._generar_informe)
        self._toolbar.configuracion_clicked.connect(self._abrir_configuracion)

    def _apply_menu_style(self):
        self.menuBar().setStyleSheet("""
            QMenuBar { background: palette(window); padding: 2px; }
            QMenuBar::item:selected { background: palette(highlight); }
            QMenu { background: palette(window); border: 1px solid palette(mid); }
            QMenu::item:selected { background: palette(highlight); color: palette(highlighted-text); }
        """)

    # ================================================================
    # Tray
    # ================================================================

    def _setup_tray(self):
        self._tray = TrayManager(self)
        self._tray.mostrar_ventana.connect(self._mostrar_ventana)
        self._tray.salir.connect(self._salir)
        self._tray.conectar.connect(self._conectar_redmine)

    # ================================================================
    # Conexión Redmine
    # ================================================================

    def _auto_connect(self):
        # Verificar actualizaciones tras un breve retraso para no bloquear el arranque
        QTimer.singleShot(2000, self._check_updates_auto)

        if self._settings.redmine_configured:
            self._conectar_redmine()

    def _check_updates_auto(self):
        """Verifica actualizaciones automáticamente si han pasado más de 24h desde la última."""
        from datetime import datetime, timedelta

        last_check_str = self._settings.last_update_check
        should_check = True
        if last_check_str:
            try:
                last_check = datetime.fromisoformat(last_check_str)
                if datetime.now() - last_check < timedelta(hours=24):
                    should_check = False
            except (ValueError, TypeError):
                pass

        if not should_check:
            return

        proxy_url = self._settings.build_proxy_url()
        um = UpdateManager(proxy_url=proxy_url)
        info = um.check_for_updates()
        self._settings.last_update_check = datetime.now().isoformat()

        if info.available:
            from app.dialogs.update_dialog import UpdateDialog
            dlg = UpdateDialog(info, um, self)
            dlg.exec()

    def _buscar_actualizaciones(self):
        """Busca actualizaciones manualmente (menú Archivo > Buscar actualizaciones...)."""
        proxy_url = self._settings.build_proxy_url()
        um = UpdateManager(proxy_url=proxy_url)
        info = um.check_for_updates()
        if info.available:
            from app.dialogs.update_dialog import UpdateDialog
            dlg = UpdateDialog(info, um, self)
            dlg.exec()
        else:
            QMessageBox.information(
                self, "Actualización",
                "No hay actualizaciones disponibles.\n"
                "Ya tienes la versión más reciente.",
            )

    def _conectar_redmine(self):
        if not self._settings.redmine_configured:
            self._abrir_configuracion()
            return

        self._status_indicator.set_connecting()
        proxy_url = self._settings.build_proxy_url()
        self._redmine = RedmineClient(
            self._settings.redmine_url,
            self._settings.redmine_api_key,
            proxy_url,
            session_cookie=self._settings.session_cookie,
            extra_headers=self._settings.parse_extra_headers(),
        )

        try:
            self._redmine.test_connection()
            self._current_user_id = self._redmine.get_current_user_id()
            self._status_indicator.set_connected(True, "Conectado")
            self._tray.set_icon_connected(True)
            self._tray.notify(APP_DISPLAY_NAME, "Conectado a Redmine correctamente")
            self._cargar_proyectos()
            self._cargar_estados()
            self._cargar_priorities()
            self._cargar_trackers()
            self._cargar_issues()
            self._update_poll_timer()
        except RedmineAuthError as e:
            self._status_indicator.set_connected(False, "Error de autenticación")
            self._tray.set_icon_connected(False)
            QMessageBox.critical(self, "Error de autenticación",
                                 f"API key no válida o permisos insuficientes.\n\n{str(e)}")
        except RedmineSSOError as e:
            self._status_indicator.set_connected(False, "SSO detectado")
            self._tray.set_icon_connected(False)
            QMessageBox.warning(self, "Portal de autenticación (SSO)",
                                f"{str(e)}")
        except RedmineConnectionError as e:
            self._status_indicator.set_connected(False, "Sin conexión")
            self._tray.set_icon_connected(False)
            QMessageBox.warning(self, "Error de conexión",
                                f"No se pudo conectar al servidor Redmine.\n\n{str(e)}")
        except httpx.UnsupportedProtocol as e:
            self._status_indicator.set_connected(False, "URL inválida")
            self._tray.set_icon_connected(False)
            QMessageBox.warning(self, "URL inválida",
                                f"La URL del servidor Redmine no es válida. Asegúrate de que empiece con https://.\n\n{str(e)}")
        except RedmineError as e:
            self._status_indicator.set_connected(False, "Error")
            self._tray.set_icon_connected(False)
            QMessageBox.warning(self, "Error", str(e))

    # ================================================================
    # Carga de datos
    # ================================================================

    def _cargar_proyectos(self):
        if not self._redmine:
            return
        try:
            projects = self._redmine.get_all_projects()
            # Una sola pasada: nombre completo, jerarquía y lista visible
            self._project_full_names = {}
            self._project_hierarchy = {}
            self._projects = []
            for p in projects:
                full_name = p.full_name or p.name
                self._project_full_names[p.id] = full_name
                self._project_hierarchy[p.id] = p.parent_id
                self._projects.append((p.id, full_name))
            self._filter_bar.populate_projects(self._projects, self._project_hierarchy)

            if self._settings.filter_fixed and self._settings.filter_projects:
                self._filter_bar.select_projects(self._settings.filter_projects)
                self._cargar_categorias_proyecto(self._settings.filter_projects)
                self._cargar_miembros_proyecto(self._settings.filter_projects)
            self._filter_bar.set_fixed(self._settings.filter_fixed)
            self._filter_bar.set_status(self._settings.filter_status)
            self._filter_bar.set_priority(self._settings.filter_priority)
            self._filter_bar.set_category(self._settings.filter_category)
            self._filter_bar.set_assigned_to(self._settings.filter_assigned_to)
            # Restaurar filtro de fecha
            self._filter_bar.set_date_preset(
                self._settings.filter_date_preset,
                self._settings.filter_date_from or None,
                self._settings.filter_date_to or None,
            )
        except RedmineError:
            pass

    def _cargar_estados(self):
        if not self._redmine:
            return
        try:
            statuses = self._redmine.get_issue_statuses()
            self._statuses = [(s.id, s.name) for s in statuses]
        except RedmineError:
            self._statuses = []
        self._update_task_table_context()

    def _cargar_priorities(self):
        if not self._redmine:
            return
        try:
            priorities = self._redmine.get_issue_priorities()
            self._priorities = [(p.id, p.name) for p in priorities]
            self._filter_bar.populate_priorities(self._priorities)
        except RedmineError:
            self._priorities = []
        self._task_table.set_priorities(self._priorities)

    def _cargar_trackers(self):
        if not self._redmine:
            return
        try:
            trackers = self._redmine.get_trackers()
            self._trackers = [(t.id, t.name) for t in trackers]
        except RedmineError:
            self._trackers = []

    def _cargar_categorias_proyecto(self, project_ids):
        if isinstance(project_ids, int):
            project_ids = [project_ids] if project_ids else []
        if not self._redmine:
            self._filter_bar.populate_categories([])
            return
        categories: list[tuple[int, str]] = []
        for pid in project_ids:
            try:
                cats = self._redmine.get_project_issue_categories(pid)
                categories.extend([(c.id, c.name) for c in cats])
            except RedmineError:
                continue
        # Dedupe por id de categoría
        seen = set()
        unique: list[tuple[int, str]] = []
        for cid, cname in categories:
            if cid not in seen:
                seen.add(cid)
                unique.append((cid, cname))
        self._filter_bar.populate_categories(unique)

    def _cargar_miembros_proyecto(self, project_ids):
        if isinstance(project_ids, int):
            project_ids = [project_ids] if project_ids else []
        if not self._redmine:
            self._filter_bar.populate_assignees([])
            return
        members: list[tuple[int, str]] = []
        for pid in project_ids:
            try:
                mbs = self._redmine.get_project_memberships(pid)
                members.extend([(m.user_id, m.user_name) for m in mbs if m.user_id])
            except RedmineError:
                continue
        # Dedupe por id de usuario
        seen = set()
        unique: list[tuple[int, str]] = []
        for mid, mname in members:
            if mid not in seen:
                seen.add(mid)
                unique.append((mid, mname))
        self._filter_bar.populate_assignees(unique)

    def _cargar_issues(self, *, track_known: bool = True):
        if not self._redmine:
            return
        project_ids = self._filter_bar.selected_project_ids
        status_filter = self._filter_bar.selected_status
        priority_id = self._filter_bar.selected_priority or None
        category_id = self._filter_bar.selected_category or None
        due_date_from = self._filter_bar.selected_date_from
        due_date_to = self._filter_bar.selected_date_to

        assigned_raw = self._filter_bar.selected_assigned_to  # list[int]
        assigned_to_ids: list | None = None
        if assigned_raw and 0 not in assigned_raw:  # "Todos" no está seleccionado
            assigned_to_ids = []
            for aid in assigned_raw:
                if aid == -1:
                    assigned_to_ids.append("!*")
                elif aid == -2:
                    assigned_to_ids.append("me")
                else:
                    assigned_to_ids.append(aid)
            if not assigned_to_ids:
                assigned_to_ids = None

        try:
            issues = self._redmine.get_issues(
                project_id=project_ids or None,
                status_filter=status_filter,
                category_id=category_id,
                priority_id=priority_id,
                assigned_to_id=assigned_to_ids,
                due_date_from=due_date_from,
                due_date_to=due_date_to,
                current_user_id=self._current_user_id,
            )
            issues_dict = [
                {
                    "id": iss.id,
                    "subject": iss.subject,
                    "description": iss.description,
                    "start_date": iss.start_date,
                    "due_date": iss.due_date,
                    "status_name": iss.status_name,
                    "status_id": iss.status_id,
                    "done_ratio": iss.done_ratio,
                    "project_id": iss.project_id,
                    "project_name": self._project_full_names.get(iss.project_id, iss.project_name),
                    "assigned_to_id": iss.assigned_to_id,
                    "assigned_to_name": iss.assigned_to_name,
                    "author_name": iss.author_name,
                    "tracker_name": iss.tracker_name,
                    "priority_name": iss.priority_name,
                    "priority_id": iss.priority_id,
                    "category_name": iss.category_name,
                    "created_on": iss.created_on,
                    "updated_on": iss.updated_on,
                    "url": urljoin(self._settings.redmine_url.rstrip("/") + "/", f"issues/{iss.id}"),
                }
                for iss in issues
            ]
            # Filtro cliente-side por texto en título
            if self._search_text:
                search_lower = self._search_text.lower()
                issues_dict = [i for i in issues_dict if search_lower in i.get("subject", "").lower()]
            self._task_table.set_issues(issues_dict)
            self._update_task_table_context()
            self._status_indicator.set_connected(True)
            if track_known:
                if project_ids:
                    for pid in project_ids:
                        self._known_issue_ids[pid] = {
                            iss["id"] for iss in issues_dict if iss.get("project_id") == pid
                        }
                else:
                    self._known_issue_ids[None] = {iss["id"] for iss in issues_dict}
        except RedmineError as e:
            self._status_indicator.set_connected(False, str(e))

    # ================================================================
    # Informe ODS
    # ================================================================

    def _report_users(self) -> list[tuple[int, str]]:
        """Usuarios implicables en el informe (miembros de los proyectos en filtro).

        Si el FilterBar tiene proyectos seleccionados, usa esos; si no, usa
        todos los proyectos cargados. Deduplica por user_id > 0.
        """
        if not self._redmine:
            return []
        project_ids = self._filter_bar.selected_project_ids
        if not project_ids:
            project_ids = [pid for pid, _ in self._projects]
        members: list[tuple[int, str]] = []
        for pid in project_ids:
            try:
                mbs = self._redmine.get_project_memberships(pid)
                members.extend([(m.user_id, m.user_name) for m in mbs if m.user_id])
            except RedmineError:
                continue
        seen: set[int] = set()
        unique: list[tuple[int, str]] = []
        for mid, mname in members:
            if mid not in seen:
                seen.add(mid)
                unique.append((mid, mname))
        return unique

    def _generar_informe(self):
        """Genera un informe ODS con los filtros elegidos en el ReportDialog."""
        if not self._redmine:
            QMessageBox.warning(self, "Sin conexión", "Conéctate primero a Redmine.")
            return

        users = self._report_users()
        preselected = [pid for pid in self._filter_bar.selected_project_ids if pid > 0]

        dlg = ReportDialog(self._projects, users, preselected, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        project_ids = dlg.selected_project_ids or None
        try:
            issues = self._redmine.get_issues(
                project_id=project_ids,
                status_filter="*",
                created_on_from=dlg.created_from,
                created_on_to=dlg.created_to,
                include_journals=True,
                current_user_id=self._current_user_id,
            )
        except RedmineError as e:
            QMessageBox.critical(self, "Error",
                                 f"No se pudieron obtener las tareas:\n{str(e)}")
            return

        # Filtro client-side por usuarios implicados y rol
        user_ids = set(dlg.selected_user_ids)
        roles = set(dlg.selected_roles)
        filtered = [iss for iss in issues if iss.matches_user_filter(user_ids, roles)]

        if not filtered:
            QMessageBox.information(
                self, "Sin resultados",
                "Ninguna tarea cumple los filtros seleccionados.",
            )
            return

        default_name = f"informe_{datetime.now():%Y%m%d_%H%M}.ods"
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe", default_name, "Hoja de cálculo ODF (*.ods)"
        )
        if not path:
            return
        if not path.lower().endswith(".ods"):
            path += ".ods"

        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                generator = ReportGenerator(REPORT_COLUMNS, sheet_name="Informe")
                for row in self._compose_report_rows(filtered):
                    generator.add_row(row)
                generator.write(path)
            finally:
                QApplication.restoreOverrideCursor()
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"No se pudo generar el informe:\n{str(e)}")
            return

        QMessageBox.information(self, "Informe generado",
                                f"Informe guardado en:\n{path}")

    def _compose_report_rows(self, issues) -> list[list]:
        """Construye las filas del informe alineadas con REPORT_COLUMNS."""
        rows: list[list] = []
        for iss in issues:
            rows.append([
                iss.id,
                self._project_full_names.get(iss.project_id, iss.project_name),
                iss.tracker_name,
                iss.subject,
                iss.status_name,
                iss.priority_name,
                iss.assigned_to_name,
                iss.author_name,
                self._parse_iso_date(iss.created_on),
                self._parse_iso_date(iss.start_date),
                self._parse_iso_date(iss.due_date),
                iss.done_ratio,
                iss.category_name,
                self._parse_iso_date(iss.updated_on),
                self._implicated_users(iss),
            ])
        return rows

    @staticmethod
    def _parse_iso_date(value: str):
        """Convierte una cadena ISO (fecha o datetime) a datetime.date.

        Acepta tanto "2026-01-01" como "2026-01-01T10:00:00Z". Si el valor
        está vacío o no es una fecha válida, devuelve "".
        """
        if not value:
            return ""
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return ""

    @staticmethod
    def _implicated_users(issue) -> str:
        """Nombres de los usuarios implicados en una tarea, unidos por ', '.

        Construye un mapa {user_id: user_name} desde el autor, el asignado y
        los autores de los journals, y une los nombres de participant_ids en
        orden, sin duplicados. Si no hay ninguno, devuelve "".
        """
        names: dict[int, str] = {}
        if issue.author_id:
            names[issue.author_id] = issue.author_name
        if issue.assigned_to_id:
            names[issue.assigned_to_id] = issue.assigned_to_name
        for j in issue.journals:
            if j.user_id and j.user_id not in names:
                names[j.user_id] = j.user_name
        return ", ".join(names[uid] for uid in issue.participant_ids if uid in names)

    # ================================================================
    # Acciones de tareas
    # ================================================================

    def _nueva_tarea(self):
        if not self._redmine:
            QMessageBox.warning(self, "Sin conexión", "Conéctate primero a Redmine.")
            return

        # Cargar categorías y miembros si hay un proyecto seleccionado en el filtro
        initial_categories = []
        members: list[tuple[int, str]] = []
        default_project_id = self._filter_bar.selected_project_id
        if default_project_id:
            try:
                cats = self._redmine.get_project_issue_categories(default_project_id)
                initial_categories = [(c.id, c.name) for c in cats]
            except RedmineError:
                pass
            try:
                mbs = self._redmine.get_project_memberships(default_project_id)
                members = [(m.user_id, m.user_name) for m in mbs if m.user_id]
            except RedmineError:
                pass

        dlg = TaskDialog(
            self,
            projects=self._projects,
            trackers=self._trackers,
            priorities=self._priorities,
            statuses=self._statuses,
            initial_categories=initial_categories,
            redmine_client=self._redmine,
            default_project_id=default_project_id,
            members=members,
            current_user_id=self._current_user_id,
        )
        if dlg.exec() == TaskDialog.DialogCode.Accepted:
            try:
                result = self._redmine.create_issue(
                    project_id=dlg.project_id,
                    subject=dlg.subject,
                    description=dlg.description,
                    tracker_id=dlg.tracker_id,
                    priority_id=dlg.priority_id,
                    category_id=dlg.category_id,
                    assigned_to_id=dlg.assigned_to_id or None,
                    start_date=dlg.start_date,
                    due_date=dlg.due_date if dlg.due_enabled else "",
                    done_ratio=dlg.done_ratio,
                    uploads=dlg.upload_tokens or None,
                    custom_fields=dlg.custom_fields or None,
                )
                # Crear items del checklist pendientes
                new_issue_id = result.get("issue", {}).get("id", 0)
                if new_issue_id and dlg.pending_checklist_items:
                    failed_items: list[str] = []
                    for subject in dlg.pending_checklist_items:
                        try:
                            self._redmine.create_checklist_item(new_issue_id, subject)
                        except Exception:
                            failed_items.append(subject)
                    if failed_items:
                        QMessageBox.warning(
                            self, "Checklist parcial",
                            f"La tarea se creó correctamente, pero algunos items del checklist "
                            f"no pudieron crearse:\n" +
                            "\n".join(f"  • {item}" for item in failed_items)
                        )
                self._cargar_issues()
            except RedmineValidationError as e:
                errors_text = "\n".join(f"  • {err}" for err in e.errors) if e.errors else str(e)
                QMessageBox.critical(self, "Error de validación",
                                     f"Redmine rechazó la tarea:\n{errors_text}")
            except RedmineConnectionError as e:
                QMessageBox.critical(self, "Error de conexión", str(e))
            except RedmineError as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la tarea:\n{str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Error inesperado",
                                     f"Ocurrió un error inesperado al crear la tarea:\n{str(e)}")

    def _editar_tarea_seleccionada(self):
        issue_id = self._task_table.get_selected_issue_id()
        if not issue_id:
            QMessageBox.information(self, "Sin selección", "Selecciona una tarea para editar.")
            return
        self._editar_tarea(issue_id)

    def _editar_tarea(self, issue_id: int):
        if not self._redmine:
            return
        try:
            data = self._redmine.get_issue_with_journals(issue_id)
            # data ya contiene _journals y los campos planos
            task_data = {
                "id": data.get("id"),
                "subject": data.get("subject", ""),
                "description": data.get("description", ""),
                "project_id": data.get("project", {}).get("id", 0),
                "tracker_id": data.get("tracker", {}).get("id", 1),
                "priority_id": data.get("priority", {}).get("id", 2),
                "category_id": data.get("category_id", 0),
                "assigned_to_id": data.get("assigned_to", {}).get("id", 0) if data.get("assigned_to") else 0,
                "start_date": data.get("start_date", ""),
                "due_date": data.get("due_date", ""),
                "done_ratio": data.get("done_ratio", 0),
                "status_id": data.get("status", {}).get("id", 0),
                "journals": data.get("_journals", []),
                "attachments": data.get("_attachments", []),
                "custom_fields": data.get("_custom_fields", {}),
            }

            # Cargar categorías y miembros iniciales para el proyecto de la tarea
            project_id = task_data["project_id"]
            initial_categories = []
            members: list[tuple[int, str]] = []
            if project_id:
                try:
                    cats = self._redmine.get_project_issue_categories(project_id)
                    initial_categories = [(c.id, c.name) for c in cats]
                except RedmineError:
                    pass
                try:
                    mbs = self._redmine.get_project_memberships(project_id)
                    members = [(m.user_id, m.user_name) for m in mbs if m.user_id]
                except RedmineError:
                    pass

            dlg = TaskDialog(
                self,
                projects=self._projects,
                trackers=self._trackers,
                priorities=self._priorities,
                statuses=self._statuses,
                initial_categories=initial_categories,
                redmine_client=self._redmine,
                task_data=task_data,
                members=members,
                current_user_id=self._current_user_id,
            )
            if dlg.exec() == TaskDialog.DialogCode.Accepted:
                self._redmine.update_issue(
                    issue_id,
                    subject=dlg.subject,
                    description=dlg.description,
                    project_id=dlg.project_id,
                    tracker_id=dlg.tracker_id,
                    priority_id=dlg.priority_id,
                    category_id=dlg.category_id,
                    assigned_to_id=dlg.assigned_to_id or None,
                    start_date=dlg.start_date,
                    due_date=dlg.due_date if dlg.due_enabled else "",
                    done_ratio=dlg.done_ratio,
                    status_id=dlg.status_id if dlg.status_id else None,
                    uploads=dlg.upload_tokens or None,
                    custom_fields=dlg.custom_fields or None,
                )
                if dlg.pending_comment:
                    self._redmine.add_issue_note(issue_id, dlg.pending_comment)
                self._cargar_issues()
        except RedmineValidationError as e:
            errors_text = "\n".join(f"  • {err}" for err in e.errors) if e.errors else str(e)
            QMessageBox.critical(self, "Error de validación",
                                 f"Redmine rechazó la actualización:\n{errors_text}")
        except RedmineConnectionError as e:
            QMessageBox.critical(self, "Error de conexión", str(e))
        except RedmineError as e:
            QMessageBox.critical(self, "Error", f"No se pudo editar la tarea:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error inesperado",
                                 f"Ocurrió un error inesperado al editar la tarea:\n{str(e)}")

    @staticmethod
    def _compose_copied_description(issue_id: int, description: str) -> str:
        """Compone la descripción de la copia citando el origen en blockquote (D2).

        Devuelve la frase literal "Tarea creada partiendo de la tarea #<id>", una
        línea en blanco y cada línea de la descripción origen prefijada con "> ".
        Si la descripción origen está vacía, solo se incluye la frase.
        """
        header = f"Tarea creada partiendo de la tarea #{issue_id}"
        if not description or not description.strip():
            return header
        quoted = "\n".join(f"> {line}" for line in description.splitlines())
        return f"{header}\n\n{quoted}"

    def _copiar_tarea_otro_proyecto(self, issue_id: int):
        """Copia una tarea a otro proyecto (tareas 5.3, 5.4, 7.2 y 7.3).

        Pide el proyecto destino, obtiene la tarea origen con journals/adjuntos,
        carga categorías, miembros y campos personalizados del destino y abre el
        TaskDialog en modo copia. La creación real (create_issue) y la copia de
        adjuntos (descarga + resubida) pertenecen a otra fase (7.4/7.5).
        """
        if not self._redmine:
            return

        dlg = ProjectSelectDialog(self._projects, self)
        if dlg.exec() != ProjectSelectDialog.DialogCode.Accepted:
            return
        dest_project_id = dlg.selected_project_id
        if not dest_project_id:
            return

        try:
            data = self._redmine.get_issue_with_journals(issue_id)
        except RedmineError as e:
            QMessageBox.critical(self, "Error",
                                 f"No se pudo obtener la tarea origen:\n{str(e)}")
            return

        subject = data.get("subject", "")
        description = data.get("description", "")
        attachments = data.get("_attachments", [])

        # Cargar categorías y miembros del proyecto destino (patrón de _nueva_tarea)
        initial_categories: list[tuple[int, str]] = []
        members: list[tuple[int, str]] = []
        try:
            cats = self._redmine.get_project_issue_categories(dest_project_id)
            initial_categories = [(c.id, c.name) for c in cats]
        except RedmineError:
            pass
        try:
            mbs = self._redmine.get_project_memberships(dest_project_id)
            members = [(m.user_id, m.user_name) for m in mbs if m.user_id]
        except RedmineError:
            pass
        # Los campos personalizados del destino los carga TaskDialog al seleccionar
        # el proyecto (default_project_id dispara _on_project_changed).

        copy_dlg = TaskDialog(
            self,
            projects=self._projects,
            trackers=self._trackers,
            priorities=self._priorities,
            statuses=self._statuses,
            initial_categories=initial_categories,
            redmine_client=self._redmine,
            default_project_id=dest_project_id,
            members=members,
            current_user_id=self._current_user_id,
            copy_from_issue_id=issue_id,
            copy_attachments=attachments,
            copy_subject=subject,
            copy_description=self._compose_copied_description(issue_id, description),
        )
        if copy_dlg.exec() != TaskDialog.DialogCode.Accepted:
            return

        # 7.4: copiar los adjuntos propuestos (descarga temporal + resubida).
        # La tarea origen solo se lee: nunca se modifica (7.6).
        # Los archivos nuevos añadidos en el diálogo (upload_tokens) se combinan
        # con los tokens de los adjuntos propuestos copiados.
        uploads: list[dict] = list(copy_dlg.upload_tokens or [])
        proposed = copy_dlg.proposed_attachments
        if proposed:
            try:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    for att in proposed:
                        filename = TaskDialog._attachment_get(att, "filename", "sin_nombre")
                        content_url = TaskDialog._attachment_get(att, "content_url", "")
                        if not content_url:
                            raise RedmineError(
                                f"No se encontró la URL de descarga del adjunto '{filename}'."
                            )
                        # W3: prefijar con el id del adjunto para que dos adjuntos
                        # con el mismo filename no se sobrescriban en tmp.
                        att_id = TaskDialog._attachment_get(att, "id", 0)
                        dest_path = os.path.join(tmp_dir, f"{att_id}_{os.path.basename(filename)}")
                        self._redmine.download_attachment(content_url, dest_path)
                        result = self._redmine.upload_file(dest_path)
                        token = result.get("upload", {}).get("token", "")
                        if not token:
                            raise RedmineError(
                                f"No se pudo obtener el token de subida para '{filename}'."
                            )
                        content_type, _ = mimetypes.guess_type(filename)
                        uploads.append({
                            "token": token,
                            "filename": filename,
                            "content_type": content_type or "application/octet-stream",
                        })
            except Exception as e:
                QMessageBox.critical(
                    self, "Error al copiar adjuntos",
                    f"No se pudieron copiar los adjuntos:\n{str(e)}"
                )
                return  # No crear la tarea con datos incompletos

        # 7.5: crear la tarea en el proyecto destino (el origen no se toca, 7.6)
        try:
            result = self._redmine.create_issue(
                project_id=copy_dlg.project_id,
                subject=copy_dlg.subject,
                description=copy_dlg.description_raw,
                tracker_id=copy_dlg.tracker_id,
                priority_id=copy_dlg.priority_id,
                category_id=copy_dlg.category_id,
                assigned_to_id=copy_dlg.assigned_to_id or None,
                start_date=copy_dlg.start_date,
                due_date=copy_dlg.due_date if copy_dlg.due_enabled else "",
                done_ratio=copy_dlg.done_ratio,
                custom_fields=copy_dlg.custom_fields or None,
                uploads=uploads or None,
            )
            # Crear items del checklist pendientes (mismo manejo que _nueva_tarea)
            new_issue_id = result.get("issue", {}).get("id", 0)
            if new_issue_id and copy_dlg.pending_checklist_items:
                failed_items: list[str] = []
                for subject in copy_dlg.pending_checklist_items:
                    try:
                        self._redmine.create_checklist_item(new_issue_id, subject)
                    except Exception:
                        failed_items.append(subject)
                if failed_items:
                    QMessageBox.warning(
                        self, "Checklist parcial",
                        f"La tarea se creó correctamente, pero algunos items del checklist "
                        f"no pudieron crearse:\n" +
                        "\n".join(f"  • {item}" for item in failed_items)
                    )
            self._cargar_issues()
        except RedmineValidationError as e:
            errors_text = "\n".join(f"  • {err}" for err in e.errors) if e.errors else str(e)
            QMessageBox.critical(self, "Error de validación",
                                 f"Redmine rechazó la tarea:\n{errors_text}")
        except RedmineConnectionError as e:
            QMessageBox.critical(self, "Error de conexión", str(e))
        except RedmineError as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear la tarea:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error inesperado",
                                 f"Ocurrió un error inesperado al crear la tarea:\n{str(e)}")

    def _asignar_tarea(self):
        issue_id = self._task_table.get_selected_issue_id()
        if not issue_id:
            QMessageBox.information(self, "Sin selección", "Selecciona una tarea para asignar.")
            return
        if not self._redmine:
            return
        row_data = self._task_table.get_selected_row_data()
        project_id = row_data.get("project_id", 0) if row_data else 0
        members: list[tuple[int, str]] = []
        try:
            if project_id:
                mbs = self._redmine.get_project_memberships(project_id)
                members = [(m.user_id, m.user_name) for m in mbs]
        except RedmineError:
            pass

        dlg = AssignDialog(issue_id, members, self._current_user_id, self)
        if dlg.exec() == AssignDialog.DialogCode.Accepted:
            try:
                self._redmine.assign_issue(issue_id, dlg.selected_user_id, notes=dlg.notes)
                self._registrar_asignacion(dlg.selected_user_id)
                self._cargar_issues()
            except RedmineError as e:
                QMessageBox.critical(self, "Error", f"No se pudo asignar:\n{str(e)}")

    def _completar_tarea(self):
        issue_id = self._task_table.get_selected_issue_id()
        if not issue_id:
            QMessageBox.information(self, "Sin selección", "Selecciona una tarea para completar.")
            return
        if not self._redmine:
            return

        dlg = CompleteDialog(issue_id, self)
        if dlg.exec() != CompleteDialog.DialogCode.Accepted:
            return

        try:
            resolved_status = next((sid for sid, sname in self._statuses if sname.lower() in ("resuelta", "resolved")), None)
            if resolved_status is None:
                QMessageBox.warning(self, "No se puede completar",
                                    "No se encontró un estado 'Resuelta' o 'Resolved' entre los estados "
                                    "disponibles. La tarea no se puede completar.\n\n"
                                    "Contacte con el administrador de Redmine.")
                return

            due_date_str = date.today().isoformat()
            try:
                self._redmine.complete_issue(
                    issue_id,
                    done_ratio=100,
                    status_id=resolved_status,
                    notes=dlg.notes,
                    due_date=due_date_str,
                )
            except RedmineValidationError:
                # Si Redmine rechaza el due_date, reintentar sin él
                self._redmine.complete_issue(
                    issue_id,
                    done_ratio=100,
                    status_id=resolved_status,
                    notes=dlg.notes,
                )
            self._cargar_issues()
            self._tray.notify(APP_DISPLAY_NAME, f"Tarea #{issue_id} completada")
        except RedmineValidationError as e:
            errors_text = "\n".join(f"  • {err}" for err in e.errors) if e.errors else str(e)
            QMessageBox.warning(self, "Error al completar",
                                f"Redmine rechazó la operación. Causas posibles:\n"
                                f"  • El estado 'Resuelta' no es válido para el tracker de esta tarea\n"
                                f"  • La tarea no permite transición directa a completada\n"
                                f"  • La fecha de fin no es válida\n\n"
                                f"Detalle del servidor:\n{errors_text}")
        except RedmineError as e:
            QMessageBox.critical(self, "Error", f"No se pudo completar:\n{str(e)}")

    def _rechazar_tarea(self):
        issue_id = self._task_table.get_selected_issue_id()
        if not issue_id:
            QMessageBox.information(self, "Sin selección", "Selecciona una tarea para rechazar.")
            return
        if not self._redmine:
            return

        dlg = RejectDialog(issue_id, self._statuses, self)
        if dlg.exec() == RejectDialog.DialogCode.Accepted:
            try:
                self._redmine.reject_issue(issue_id, dlg.reject_status_id, dlg.reject_notes)
                self._cargar_issues()
                self._tray.notify(APP_DISPLAY_NAME, f"Tarea #{issue_id} rechazada")
            except RedmineError as e:
                QMessageBox.critical(self, "Error", f"No se pudo rechazar:\n{str(e)}")

    def _abrir_url_redmine(self, issue_id: int, url: str):
        if not url:
            if self._settings.redmine_url:
                base = self._settings.redmine_url.rstrip("/")
                url = f"{base}/issues/{issue_id}"
            else:
                return

        # Método 1: probar navegadores directamente (evita xdg-open si falla Firefox)
        for browser in ("google-chrome", "chromium-browser", "chromium", "firefox"):
            try:
                subprocess.Popen(
                    [browser, url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return
            except FileNotFoundError:
                continue

        # Método 2: QDesktopServices (usa xdg-open)
        if QDesktopServices.openUrl(QUrl(url)):
            return

        # Método 3: webbrowser (último intento programático)
        if webbrowser.open(url):
            return

        # Fallback final: copiar al portapapeles y mostrar la URL
        clipboard = QApplication.clipboard()
        clipboard.setText(url)
        QMessageBox.information(
            self, "Abrir en Redmine",
            f"No se pudo abrir el navegador.\n\n"
            f"La URL se ha copiado al portapapeles:\n{url}"
        )

    def _on_due_date_changed(self, issue_id: int, due_date: str):
        if not self._redmine:
            return
        try:
            self._redmine.update_issue(issue_id, due_date=due_date if due_date else "")
            self._task_table.refresh_due_date_cell(issue_id, due_date)
        except RedmineError as e:
            QMessageBox.warning(self, "Error", f"No se pudo actualizar la fecha de fin:\n{str(e)}")

    def _on_columnas_cambiadas(self):
        """Persiste la visibilidad de columnas y recarga los datos."""
        self._settings.visible_columns = self._task_table.visible_column_keys()
        self._cargar_issues()

    # ================================================================
    # Filtros
    # ================================================================

    def _on_filter_project_changed(self, project_ids: list):
        if self._settings.filter_fixed:
            self._settings.filter_projects = project_ids
        self._cargar_categorias_proyecto(project_ids)
        self._cargar_miembros_proyecto(project_ids)
        self._cargar_issues()
        self._update_poll_timer()

    def _on_filter_status_changed(self, status: str):
        self._settings.filter_status = status
        self._cargar_issues()

    def _on_filter_priority_changed(self, priority_id: int):
        self._settings.filter_priority = priority_id
        self._cargar_issues()

    def _on_filter_category_changed(self, category_id: int):
        self._settings.filter_category = category_id
        self._cargar_issues()

    def _on_filter_assigned_changed(self, assigned_to_ids: list):
        self._settings.filter_assigned_to = assigned_to_ids
        self._cargar_issues()

    def _on_filter_fixed_changed(self, fixed: bool):
        self._settings.filter_fixed = fixed
        if fixed:
            self._settings.filter_projects = self._filter_bar.selected_project_ids

    def _on_busqueda_cambiada(self, text: str):
        self._search_text = text.strip()
        self._cargar_issues()

    def _on_filter_date_changed(self, due_date_from: str, due_date_to: str):
        self._settings.filter_date_preset = self._filter_bar.selected_date_preset
        self._settings.filter_date_from = self._filter_bar.selected_date_from or ""
        self._settings.filter_date_to = self._filter_bar.selected_date_to or ""
        self._cargar_issues()

    def _update_poll_timer(self):
        subscribed = self._settings.notifications_projects
        has_projects = bool(self._filter_bar.selected_project_ids) or bool(subscribed)
        if has_projects and self._redmine:
            interval_ms = self._settings.poll_interval_minutes * 60000
            self._poll_timer.start(interval_ms)
        else:
            self._poll_timer.stop()

    def _check_new_issues(self):
        if not self._redmine:
            return

        subscribed = self._settings.notifications_projects
        if subscribed:
            project_ids = subscribed
        else:
            project_ids = self._filter_bar.selected_project_ids
            if not project_ids:
                return

        assigned_only = self._settings.notifications_assigned_only
        assigned_to = "me" if assigned_only else None
        all_new_issues: list = []

        for pid in project_ids:
            try:
                issues = self._redmine.get_issues(
                    project_id=pid,
                    status_filter="open",
                    assigned_to_id=assigned_to,
                )
                known = self._known_issue_ids.get(pid, set())
                current_ids = {iss.id for iss in issues}
                new_ids = current_ids - known
                if new_ids:
                    all_new_issues.extend(iss for iss in issues if iss.id in new_ids)
                self._known_issue_ids[pid] = current_ids
            except RedmineError:
                continue

        if all_new_issues and self._settings.notifications_enabled:
            self._notify_new_issues(all_new_issues)
        if self._filter_bar.selected_project_ids:
            self._cargar_issues(track_known=False)

    def _notify_new_issues(self, new_issues: list):
        count = len(new_issues)
        if count == 1:
            title = "Nueva tarea"
            message = f"#{new_issues[0].id}: {new_issues[0].subject}"
        else:
            title = f"{count} nuevas tareas"
            subjects = ", ".join(f"#{iss.id}" for iss in new_issues[:3])
            if count > 3:
                subjects += f" y {count - 3} más"
            message = subjects
        self._tray.notify(APP_DISPLAY_NAME, message, duration_ms=8000)
        self._mostrar_ventana()

    def _update_task_table_context(self):
        member_names: dict[int, str] = {}
        # Intentar obtener nombres de miembros del proyecto actual
        row_data = self._task_table.get_selected_row_data()
        project_id = row_data.get("project_id", 0) if row_data else self._filter_bar.selected_project_id
        if project_id and self._redmine:
            try:
                mbs = self._redmine.get_project_memberships(project_id)
                for m in mbs:
                    member_names[m.user_id] = m.user_name
            except RedmineError:
                pass
        self._task_table.set_context_data(
            self._statuses,
            self._current_user_id,
            self._settings.frequent_people,
            member_names,
        )

    def _registrar_asignacion(self, user_id: int):
        if user_id and user_id != self._current_user_id:
            self._settings.add_frequent_person(user_id)
            self._update_task_table_context()

    def _on_cambio_rapido(self, issue_id: int, tipo: str, valor: int):
        if not self._redmine:
            return

        if tipo == "progreso":
            reply = QMessageBox.question(
                self, "Confirmar cambio",
                f"¿Cambiar progreso de tarea #{issue_id} al {valor}%?"
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            try:
                self._redmine.update_issue(issue_id, done_ratio=valor)
                self._cargar_issues()
            except RedmineValidationError as e:
                errors_text = "\n".join(f"  • {err}" for err in e.errors) if e.errors else str(e)
                QMessageBox.warning(self, "Cambio no permitido",
                                    f"Redmine rechazó el cambio de progreso.\n\n"
                                    f"Detalle:\n{errors_text}")
            except RedmineError as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el progreso:\n{str(e)}")

        elif tipo == "asignado":
            nombre = "mí" if valor == self._current_user_id else f"usuario #{valor}"
            reply = QMessageBox.question(
                self, "Confirmar asignación",
                f"¿Asignar tarea #{issue_id} a {nombre}?"
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            try:
                self._redmine.assign_issue(issue_id, valor)
                self._registrar_asignacion(valor)
                self._cargar_issues()
            except RedmineError as e:
                QMessageBox.critical(self, "Error", f"No se pudo asignar:\n{str(e)}")

        elif tipo == "estado":
            # Buscar nombre del estado
            estado_nombre = next((sname for sid, sname in self._statuses if sid == valor), f"ID {valor}")
            reply = QMessageBox.question(
                self, "Confirmar cambio de estado",
                f"¿Cambiar estado de tarea #{issue_id} a \"{estado_nombre}\"?"
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            try:
                self._redmine.update_issue(issue_id, status_id=valor)
                self._cargar_issues()
            except RedmineValidationError as e:
                errors_text = "\n".join(f"  • {err}" for err in e.errors) if e.errors else str(e)
                QMessageBox.warning(self, "Cambio no permitido",
                                    f"Redmine rechazó el cambio de estado. Esto suele ocurrir porque "
                                    f"el estado seleccionado no está permitido en el workflow de esta tarea.\n\n"
                                    f"Detalle:\n{errors_text}")
            except RedmineError as e:
                QMessageBox.critical(self, "Error", f"No se pudo cambiar el estado:\n{str(e)}")

    # ================================================================
    # Configuración
    # ================================================================

    def _abrir_configuracion(self):
        dlg = SettingsDialog(self._settings, self, projects=self._projects)
        dlg.exec()

    # ================================================================
    # Ventana
    # ================================================================

    def _mostrar_ventana(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _salir(self):
        if self._redmine:
            self._redmine.close()
        self._save_window_state()
        if self._tray:
            self._tray.hide()
        QApplication.quit()

    def _restore_window_state(self):
        geom = self._settings.window_geometry
        if geom:
            self.restoreGeometry(geom)
        state = self._settings.window_state
        if state:
            self.restoreState(state)

    def _save_window_state(self):
        self._settings.window_geometry = self.saveGeometry()
        self._settings.window_state = self.saveState()

    def closeEvent(self, event):
        self._save_window_state()
        event.accept()
