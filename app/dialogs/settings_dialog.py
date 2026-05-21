from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QDialogButtonBox, QLabel,
    QMessageBox, QTabWidget, QWidget, QPlainTextEdit,
)
from app.services.settings_manager import SettingsManager
from app.utils.constants import THEMES


class SettingsDialog(QDialog):
    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings = settings
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

        group = QGroupBox("Configuración del proxy")
        form = QFormLayout(group)
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

        layout.addWidget(group)
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

    def _toggle_proxy_fields(self, enabled: bool):
        pass

    def _load_settings(self):
        self._url_edit.setText(self._settings.redmine_url)
        self._apikey_edit.setText(self._settings.redmine_api_key)
        self._cookie_edit.setPlainText(self._settings.session_cookie)
        self._headers_edit.setPlainText(self._settings.extra_headers)
        self._proxy_enabled_cb.setChecked(self._settings.proxy_enabled)
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
        self.accept()
