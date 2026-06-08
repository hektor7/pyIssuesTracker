from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QDialogButtonBox, QLabel,
    QMessageBox, QTabWidget, QWidget, QPlainTextEdit,
    QListWidget, QListWidgetItem, QRadioButton, QButtonGroup,
)
from app.services.settings_manager import SettingsManager
from app.utils.constants import THEMES

_TODOS_ITEM_TEXT = "[TODOS]"
_TODOS_ITEM_ID = -1


class SettingsDialog(QDialog):
    def __init__(self, settings: SettingsManager, parent=None, projects: list[tuple[int, str]] | None = None):
        super().__init__(parent)
        self._settings = settings
        self._projects = projects or []
        self.setWindowTitle("Configuración")
        self.setMinimumWidth(480)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        tabs.addTab(self._create_redmine_tab(), "Redmine")
        tabs.addTab(self._create_proxy_tab(), "Proxy")
        tabs.addTab(self._create_appearance_tab(), "Apariencia")
        tabs.addTab(self._create_notifications_tab(), "Notificaciones")

        layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_redmine_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setSpacing(10)

        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://")
        form.addRow("URL del servidor:", self._url_edit)

        self._apikey_edit = QLineEdit()
        self._apikey_edit.setPlaceholderText("Tu API key de Redmine")
        self._apikey_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API Key:", self._apikey_edit)

        self._cookie_edit = QPlainTextEdit()
        self._cookie_edit.setPlaceholderText(
            "cookie1=valor1; cookie2=valor2; _redmine_session=..."
        )
        self._cookie_edit.setMaximumHeight(55)
        form.addRow("Cookie:", self._cookie_edit)

        self._headers_edit = QPlainTextEdit()
        self._headers_edit.setPlaceholderText(
            "X-Custom-Header: valor\nAuthorization: Bearer token"
        )
        self._headers_edit.setMaximumHeight(55)
        form.addRow("Headers extra:", self._headers_edit)

        info = QLabel(
            "API key: Mi cuenta -> Mostrar API key.\n"
            "Cookie: F12 -> Network -> recarga -> peticion a Redmine ->\n"
            "        Request Headers -> copia el valor COMPLETO de 'Cookie'.\n"
            "Headers extra: anade otros headers que necesite el SSO (uno por linea,\n"
            "        formato 'Clave: Valor')."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; font-size: 10pt;")
        form.addRow(info)

        return widget

    def _create_proxy_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._proxy_enabled_cb = QCheckBox("Usar proxy para conexiones salientes")
        self._proxy_enabled_cb.toggled.connect(self._toggle_proxy_fields)
        layout.addWidget(self._proxy_enabled_cb)

        self._proxy_group = QGroupBox("Configuración del proxy")
        form = QFormLayout(self._proxy_group)
        form.setSpacing(8)

        self._proxy_type_combo = QComboBox()
        self._proxy_type_combo.addItems(["http", "https", "socks5"])
        form.addRow("Tipo:", self._proxy_type_combo)

        self._proxy_host_edit = QLineEdit()
        self._proxy_host_edit.setPlaceholderText("proxy.ejemplo.com")
        form.addRow("Host:", self._proxy_host_edit)

        self._proxy_port_spin = QSpinBox()
        self._proxy_port_spin.setRange(1, 65535)
        self._proxy_port_spin.setValue(8080)
        form.addRow("Puerto:", self._proxy_port_spin)

        self._proxy_user_edit = QLineEdit()
        self._proxy_user_edit.setPlaceholderText("(opcional)")
        form.addRow("Usuario:", self._proxy_user_edit)

        self._proxy_pass_edit = QLineEdit()
        self._proxy_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._proxy_pass_edit.setPlaceholderText("(opcional)")
        form.addRow("Contraseña:", self._proxy_pass_edit)

        layout.addWidget(self._proxy_group)
        layout.addStretch()
        return widget

    def _create_appearance_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        form.setSpacing(10)

        self._theme_combo = QComboBox()
        for key, label in THEMES.items():
            self._theme_combo.addItem(label, key)
        form.addRow("Tema:", self._theme_combo)

        note = QLabel("El cambio de tema se aplica tras reiniciar la aplicación.")
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 10pt;")
        form.addRow(note)

        return widget

    def _create_notifications_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # -- Habilitar notificaciones --
        self._notif_enabled_cb = QCheckBox("Activar notificaciones de nuevas tareas")
        self._notif_enabled_cb.toggled.connect(self._toggle_notif_fields)
        layout.addWidget(self._notif_enabled_cb)

        # -- Suscripcion por proyecto --
        proj_group = QGroupBox("Proyectos suscritos")
        proj_layout = QVBoxLayout(proj_group)
        proj_info = QLabel("Recibir notificaciones de los proyectos seleccionados.\nSi ninguno esta marcado, se notifican todos.")
        proj_info.setWordWrap(True)
        proj_info.setStyleSheet("color: gray; font-size: 10pt;")
        proj_layout.addWidget(proj_info)

        self._notif_projects_list = QListWidget()
        self._notif_projects_list.setMaximumHeight(150)

        # Item [TODOS]
        todos_item = QListWidgetItem(_TODOS_ITEM_TEXT)
        todos_item.setData(Qt.ItemDataRole.UserRole, _TODOS_ITEM_ID)
        todos_item.setFlags(todos_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        todos_item.setCheckState(Qt.CheckState.Checked)
        self._notif_projects_list.addItem(todos_item)

        # Items de proyectos
        for pid, pname in self._projects:
            item = QListWidgetItem(pname)
            item.setData(Qt.ItemDataRole.UserRole, pid)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self._notif_projects_list.addItem(item)

        self._notif_projects_list.itemChanged.connect(self._on_project_item_changed)
        proj_layout.addWidget(self._notif_projects_list)
        layout.addWidget(proj_group)

        # -- Filtro por asignacion --
        assign_group = QGroupBox("Filtro de tareas")
        assign_layout = QVBoxLayout(assign_group)

        self._notif_assigned_group = QButtonGroup(widget)
        self._notif_assigned_all_rb = QRadioButton("Todas las tareas del proyecto")
        self._notif_assigned_mine_rb = QRadioButton("Solo las tareas que tengo asignadas")
        self._notif_assigned_group.addButton(self._notif_assigned_all_rb, 0)
        self._notif_assigned_group.addButton(self._notif_assigned_mine_rb, 1)
        assign_layout.addWidget(self._notif_assigned_all_rb)
        assign_layout.addWidget(self._notif_assigned_mine_rb)
        layout.addWidget(assign_group)

        # -- Intervalo de polling --
        poll_group = QGroupBox("Frecuencia de comprobacion")
        poll_layout = QHBoxLayout(poll_group)

        poll_label = QLabel("Comprobar nuevas tareas cada:")
        self._notif_poll_spin = QSpinBox()
        self._notif_poll_spin.setRange(1, 60)
        self._notif_poll_spin.setSuffix(" min")
        self._notif_poll_spin.setValue(5)
        poll_layout.addWidget(poll_label)
        poll_layout.addWidget(self._notif_poll_spin)
        poll_layout.addStretch()
        layout.addWidget(poll_group)

        layout.addStretch()
        return widget

    def _on_project_item_changed(self, item: QListWidgetItem):
        """Logica [TODOS]: al marcar/desmarcar proyectos."""
        self._notif_projects_list.blockSignals(True)

        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid == _TODOS_ITEM_ID:
            if item.checkState() == Qt.CheckState.Checked:
                # Marcar TODOS desmarca los proyectos concretos
                for i in range(1, self._notif_projects_list.count()):
                    self._notif_projects_list.item(i).setCheckState(Qt.CheckState.Unchecked)
        else:
            if item.checkState() == Qt.CheckState.Checked:
                # Marcar un proyecto concreto desmarca [TODOS]
                self._notif_projects_list.item(0).setCheckState(Qt.CheckState.Unchecked)

        self._notif_projects_list.blockSignals(False)

    def _toggle_notif_fields(self, enabled: bool):
        """Habilita/deshabilita los campos de notificacion."""
        notif_tab = self._notif_enabled_cb.parent().parent()  # layout -> widget (tab)
        if isinstance(notif_tab, QWidget):
            for child in notif_tab.findChildren(QGroupBox):
                child.setEnabled(enabled)

    def _toggle_proxy_fields(self, enabled: bool):
        """Habilita/deshabilita los campos de configuracion del proxy."""
        self._proxy_group.setEnabled(enabled)

    def _load_settings(self):
        self._url_edit.setText(self._settings.redmine_url)
        self._apikey_edit.setText(self._settings.redmine_api_key)
        self._cookie_edit.setPlainText(self._settings.session_cookie)
        self._headers_edit.setPlainText(self._settings.extra_headers)
        self._proxy_enabled_cb.setChecked(self._settings.proxy_enabled)
        self._toggle_proxy_fields(self._settings.proxy_enabled)
        idx = self._proxy_type_combo.findText(self._settings.proxy_type)
        if idx >= 0:
            self._proxy_type_combo.setCurrentIndex(idx)
        self._proxy_host_edit.setText(self._settings.proxy_host)
        self._proxy_port_spin.setValue(self._settings.proxy_port or 8080)
        self._proxy_user_edit.setText(self._settings.proxy_user)
        self._proxy_pass_edit.setText(self._settings.proxy_password)
        theme = self._settings.theme
        idx_theme = self._theme_combo.findData(theme)
        if idx_theme >= 0:
            self._theme_combo.setCurrentIndex(idx_theme)

        # Notificaciones
        self._notif_enabled_cb.setChecked(self._settings.notifications_enabled)
        self._notif_poll_spin.setValue(self._settings.poll_interval_minutes)
        self._notif_assigned_mine_rb.setChecked(self._settings.notifications_assigned_only)
        self._notif_assigned_all_rb.setChecked(not self._settings.notifications_assigned_only)

        subscribed = self._settings.notifications_projects
        self._notif_projects_list.blockSignals(True)
        if not subscribed:
            # Sin preferencia especifica -> TODOS
            self._notif_projects_list.item(0).setCheckState(Qt.CheckState.Checked)
            for i in range(1, self._notif_projects_list.count()):
                self._notif_projects_list.item(i).setCheckState(Qt.CheckState.Unchecked)
        else:
            # Proyectos especificos seleccionados
            self._notif_projects_list.item(0).setCheckState(Qt.CheckState.Unchecked)
            for i in range(1, self._notif_projects_list.count()):
                item = self._notif_projects_list.item(i)
                pid = item.data(Qt.ItemDataRole.UserRole)
                item.setCheckState(Qt.CheckState.Checked if pid in subscribed else Qt.CheckState.Unchecked)
        self._notif_projects_list.blockSignals(False)
        self._toggle_notif_fields(self._settings.notifications_enabled)

    def _save_and_accept(self):
        self._settings.redmine_url = self._url_edit.text().strip()
        self._settings.redmine_api_key = self._apikey_edit.text().strip()
        self._settings.session_cookie = self._cookie_edit.toPlainText().strip()
        self._settings.extra_headers = self._headers_edit.toPlainText().strip()
        self._settings.proxy_enabled = self._proxy_enabled_cb.isChecked()
        self._settings.proxy_type = self._proxy_type_combo.currentText()
        self._settings.proxy_host = self._proxy_host_edit.text().strip()
        self._settings.proxy_port = self._proxy_port_spin.value()
        self._settings.proxy_user = self._proxy_user_edit.text().strip()
        self._settings.proxy_password = self._proxy_pass_edit.text().strip()
        self._settings.theme = self._theme_combo.currentData()

        # Notificaciones
        self._settings.notifications_enabled = self._notif_enabled_cb.isChecked()
        self._settings.poll_interval_minutes = self._notif_poll_spin.value()
        self._settings.notifications_assigned_only = self._notif_assigned_mine_rb.isChecked()

        todos_checked = self._notif_projects_list.item(0).checkState() == Qt.CheckState.Checked
        if todos_checked:
            self._settings.notifications_projects = []
        else:
            selected = []
            for i in range(1, self._notif_projects_list.count()):
                item = self._notif_projects_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    selected.append(item.data(Qt.ItemDataRole.UserRole))
            self._settings.notifications_projects = selected

        self.accept()
