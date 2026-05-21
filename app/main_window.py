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
from app.tray_icon import TrayManager
from app.utils.constants import APP_DISPLAY_NAME


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._settings = SettingsManager()
        self._redmine: RedmineClient | None = None
        self._tray: TrayManager | None = None
        self._projects: list[tuple[int, str]] = []
        self._statuses: list[tuple[int, str]] = []
        self._current_user_id: int = 0

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
        self._filter_bar.fijar_cambiado.connect(self._on_filter_fixed_changed)
        layout.addWidget(self._filter_bar)

        self._task_table = TaskTable()
        self._task_table.setObjectName("task_table")
        self._task_table.tarea_doble_click.connect(self._editar_tarea)
        self._task_table.tarea_abrir_url.connect(self._abrir_url_redmine)
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
            self._cargar_issues()
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
            self._filter_bar.populate_projects(self._projects)

            if self._settings.filter_fixed and self._settings.filter_project_id:
                self._filter_bar.select_project(
                    self._settings.filter_project_id,
                    self._settings.filter_project_name,
                )
            self._filter_bar.set_fixed(self._settings.filter_fixed)
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

    def _cargar_issues(self):
        if not self._redmine:
            return
        project_id = self._filter_bar.selected_project_id or None
        status_filter = self._filter_bar.selected_status
        try:
            issues = self._redmine.get_issues(project_id=project_id, status_filter=status_filter)
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
            self._task_table.set_issues(issues_dict)
            self._status_indicator.set_connected(True)
        except RedmineError as e:
            self._status_indicator.set_connected(False, str(e))

    # ================================================================
    # Acciones de tareas
    # ================================================================

    def _nueva_tarea(self):
        if not self._redmine:
            QMessageBox.warning(self, "Sin conexión", "Conéctate primero a Redmine.")
            return
        dlg = TaskDialog(self, projects=self._projects)
        if dlg.exec() == TaskDialog.DialogCode.Accepted:
            try:
                self._redmine.create_issue(
                    project_id=dlg.project_id,
                    subject=dlg.subject,
                    description=dlg.description,
                    tracker_id=dlg.tracker_id,
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
            data = self._redmine.get_issue(issue_id)
            issue = data.get("issue", {})
            task_data = {
                "id": issue.get("id"),
                "subject": issue.get("subject", ""),
                "description": issue.get("description", ""),
                "project_id": issue.get("project", {}).get("id", 0),
                "tracker_id": issue.get("tracker", {}).get("id", 1),
            }
            dlg = TaskDialog(self, projects=self._projects, task_data=task_data)
            if dlg.exec() == TaskDialog.DialogCode.Accepted:
                self._redmine.update_issue(
                    issue_id,
                    subject=dlg.subject,
                    description=dlg.description,
                    project_id=dlg.project_id,
                    tracker_id=dlg.tracker_id,
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
                self._redmine.assign_issue(issue_id, dlg.selected_user_id)
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

        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Marcar la tarea #{issue_id} como completada?\n\n"
            "Se pondrá el progreso al 100%, estado 'Resuelta' y fecha de fin a hoy.",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            resolved_status = next((sid for sid, sname in self._statuses if sname.lower() in ("resuelta", "resolved")), None)
            self._redmine.complete_issue(issue_id, done_ratio=100, status_id=resolved_status)
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
        self._cargar_issues()

    def _on_filter_status_changed(self, status: str):
        self._settings.filter_status = status
        self._cargar_issues()

    def _on_filter_fixed_changed(self, fixed: bool):
        self._settings.filter_fixed = fixed
        if fixed:
            self._settings.filter_project_id = self._filter_bar.selected_project_id
            self._settings.filter_project_name = self._filter_bar.selected_project_name

    # ================================================================
    # Configuración
    # ================================================================

    def _abrir_configuracion(self):
        dlg = SettingsDialog(self._settings, self)
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
