from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QStatusBar,
    QMessageBox, QMenuBar, QMenu, QApplication,
)

from app import __version__
from app.services.settings_manager import SettingsManager
from app.services.redmine_client import (
    RedmineClient, RedmineError, RedmineAuthError, RedmineConnectionError,
    RedmineSSOError,
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
from app.tray_icon import TrayManager
from app.utils.constants import APP_DISPLAY_NAME


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._settings = SettingsManager()
        self._redmine: RedmineClient | None = None
        self._tray: TrayManager | None = None
        self._projects: list[tuple[int, str]] = []
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
        layout.addWidget(self._filter_bar)

        self._task_table = TaskTable()
        self._task_table.setObjectName("task_table")
        self._task_table.tarea_doble_click.connect(self._editar_tarea)
        self._task_table.tarea_abrir_url.connect(self._abrir_url_redmine)
        self._task_table.cambio_rapido.connect(self._on_cambio_rapido)
        layout.addWidget(self._task_table)

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
        if self._settings.redmine_configured:
            self._conectar_redmine()

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
            projects = self._redmine.get_projects()
            self._projects = [(p.id, p.name) for p in projects]
            self._project_hierarchy = {p.id: p.parent_id for p in projects}
            self._filter_bar.populate_projects(self._projects, self._project_hierarchy)

            if self._settings.filter_fixed and self._settings.filter_project_id:
                self._filter_bar.select_project(
                    self._settings.filter_project_id,
                    self._settings.filter_project_name,
                )
                self._cargar_categorias_proyecto(self._settings.filter_project_id)
                self._cargar_miembros_proyecto(self._settings.filter_project_id)
            self._filter_bar.set_fixed(self._settings.filter_fixed)
            self._filter_bar.set_status(self._settings.filter_status)
            self._filter_bar.set_priority(self._settings.filter_priority)
            self._filter_bar.set_category(self._settings.filter_category)
            self._filter_bar.set_assigned_to(self._settings.filter_assigned_to)
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

    def _cargar_trackers(self):
        if not self._redmine:
            return
        try:
            trackers = self._redmine.get_trackers()
            self._trackers = [(t.id, t.name) for t in trackers]
        except RedmineError:
            self._trackers = []

    def _cargar_categorias_proyecto(self, project_id: int):
        if not self._redmine or not project_id:
            self._filter_bar.populate_categories([])
            return
        try:
            cats = self._redmine.get_project_issue_categories(project_id)
            categories = [(c.id, c.name) for c in cats]
            self._filter_bar.populate_categories(categories)
        except RedmineError:
            self._filter_bar.populate_categories([])

    def _cargar_miembros_proyecto(self, project_id: int):
        if not self._redmine or not project_id:
            self._filter_bar.populate_assignees([])
            return
        try:
            mbs = self._redmine.get_project_memberships(project_id)
            assignees = [(m.user_id, m.user_name) for m in mbs if m.user_id]
            self._filter_bar.populate_assignees(assignees)
        except RedmineError:
            self._filter_bar.populate_assignees([])

    def _cargar_issues(self, *, track_known: bool = True):
        if not self._redmine:
            return
        project_id = self._filter_bar.selected_project_id or None
        status_filter = self._filter_bar.selected_status
        priority_id = self._filter_bar.selected_priority or None
        category_id = self._filter_bar.selected_category or None

        assigned_raw = self._filter_bar.selected_assigned_to
        if assigned_raw == 0:
            assigned_to_id = None
        elif assigned_raw == -1:
            assigned_to_id = "!*"
        elif assigned_raw == -2:
            assigned_to_id = "me"
        else:
            assigned_to_id = assigned_raw

        try:
            issues = self._redmine.get_issues(
                project_id=project_id,
                status_filter=status_filter,
                category_id=category_id,
                priority_id=priority_id,
                assigned_to_id=assigned_to_id,
            )
            issues_dict = [
                {
                    "id": iss.id,
                    "subject": iss.subject,
                    "description": iss.description,
                    "start_date": iss.start_date,
                    "status_name": iss.status_name,
                    "status_id": iss.status_id,
                    "done_ratio": iss.done_ratio,
                    "project_id": iss.project_id,
                    "project_name": iss.project_name,
                    "assigned_to_id": iss.assigned_to_id,
                    "assigned_to_name": iss.assigned_to_name,
                    "author_name": iss.author_name,
                    "tracker_name": iss.tracker_name,
                    "priority_name": iss.priority_name,
                    "url": f"{self._settings.redmine_url}/issues/{iss.id}",
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
                self._known_issue_ids[project_id] = {iss["id"] for iss in issues_dict}
        except RedmineError as e:
            self._status_indicator.set_connected(False, str(e))

    # ================================================================
    # Acciones de tareas
    # ================================================================

    def _nueva_tarea(self):
        if not self._redmine:
            QMessageBox.warning(self, "Sin conexión", "Conéctate primero a Redmine.")
            return

        # Cargar categorías iniciales si hay un proyecto seleccionado en el filtro
        initial_categories = []
        default_project_id = self._filter_bar.selected_project_id
        if default_project_id:
            try:
                cats = self._redmine.get_project_issue_categories(default_project_id)
                initial_categories = [(c.id, c.name) for c in cats]
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
        )
        if dlg.exec() == TaskDialog.DialogCode.Accepted:
            try:
                self._redmine.create_issue(
                    project_id=dlg.project_id,
                    subject=dlg.subject,
                    description=dlg.description,
                    tracker_id=dlg.tracker_id,
                    priority_id=dlg.priority_id,
                    category_id=dlg.category_id,
                    start_date=dlg.start_date,
                    done_ratio=dlg.done_ratio,
                )
                self._cargar_issues()
            except RedmineError as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la tarea:\n{str(e)}")

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
                "start_date": data.get("start_date", ""),
                "done_ratio": data.get("done_ratio", 0),
                "status_id": data.get("status", {}).get("id", 0),
                "journals": data.get("_journals", []),
                "attachments": data.get("_attachments", []),
            }

            # Cargar categorías iniciales para el proyecto de la tarea
            project_id = task_data["project_id"]
            initial_categories = []
            if project_id:
                try:
                    cats = self._redmine.get_project_issue_categories(project_id)
                    initial_categories = [(c.id, c.name) for c in cats]
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
                    start_date=dlg.start_date,
                    done_ratio=dlg.done_ratio,
                    status_id=dlg.status_id if dlg.status_id else None,
                )
                self._cargar_issues()
        except RedmineError as e:
            QMessageBox.critical(self, "Error", f"No se pudo editar la tarea:\n{str(e)}")

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
            self._redmine.complete_issue(issue_id, done_ratio=100, status_id=resolved_status, notes=dlg.notes)
            self._cargar_issues()
            self._tray.notify(APP_DISPLAY_NAME, f"Tarea #{issue_id} completada")
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
        if url:
            QDesktopServices.openUrl(QUrl(url))
        elif self._settings.redmine_url:
            QDesktopServices.openUrl(QUrl(f"{self._settings.redmine_url}/issues/{issue_id}"))

    # ================================================================
    # Filtros
    # ================================================================

    def _on_filter_project_changed(self, project_id: int, project_name: str):
        if self._settings.filter_fixed:
            self._settings.filter_project_id = project_id
            self._settings.filter_project_name = project_name
        self._cargar_categorias_proyecto(project_id)
        self._cargar_miembros_proyecto(project_id)
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

    def _on_filter_assigned_changed(self, assigned_to_id: int):
        self._settings.filter_assigned_to = assigned_to_id
        self._cargar_issues()

    def _on_filter_fixed_changed(self, fixed: bool):
        self._settings.filter_fixed = fixed
        if fixed:
            self._settings.filter_project_id = self._filter_bar.selected_project_id
            self._settings.filter_project_name = self._filter_bar.selected_project_name

    def _on_busqueda_cambiada(self, text: str):
        self._search_text = text.strip()
        self._cargar_issues()

    def _update_poll_timer(self):
        subscribed = self._settings.notifications_projects
        has_projects = bool(self._filter_bar.selected_project_id) or bool(subscribed)
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
            pid = self._filter_bar.selected_project_id
            if not pid:
                return
            project_ids = [pid]

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
        if self._filter_bar.selected_project_id:
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
