"""Diálogo de configuración del informe ODS (tareas 4.2 y 4.3).

Permite acotar el informe por usuarios implicados (con rol), por rango
de fechas de creación y por proyectos, antes de generar el fichero.
"""
from datetime import date

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QHBoxLayout, QCheckBox,
    QDateEdit, QDialogButtonBox, QMessageBox, QGridLayout,
)

from app.services.report_generator import REPORT_FIELDS
from app.widgets.multi_select_combo import MultiSelectCombo

# Roles de implicación disponibles en el informe
ROLES_IMPLICACION = [
    ("creador", "Creador"),
    ("actualizador", "Actualizador"),
    ("participante", "Participante"),
]


class ReportDialog(QDialog):
    """Diálogo de filtros para generar un informe ODS de tareas."""

    def __init__(self, projects=None, users=None,
                 preselected_project_ids=None, parent=None, custom_fields=None,
                 custom_fields_provider=None):
        super().__init__(parent)
        self._projects = projects or []
        self._users = users or []
        self._preselected_project_ids = preselected_project_ids or []
        self._custom_fields = custom_fields or []
        self._custom_fields_provider = custom_fields_provider
        self._custom_fields_checked: set[str] = set()
        self.setWindowTitle("Generar informe")
        self.setMinimumWidth(420)
        self._setup_ui()
        # Conectar después de _setup_ui() para no disparar durante la construcción
        # (set_selected_ids con preselección emite seleccion_cambiada).
        self._projects_combo.seleccion_cambiada.connect(self._on_projects_changed)

    # ================================================================
    # UI
    # ================================================================

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(self._build_fields_group())
        layout.addWidget(self._build_users_group())
        layout.addWidget(self._build_dates_group())
        layout.addWidget(self._build_projects_group())

        buttons = QDialogButtonBox()
        buttons.addButton("Generar", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_fields_group(self) -> QGroupBox:
        """Grupo 'Campos del informe': un QCheckBox por campo del catálogo.

        Todas las casillas aparecen marcadas por defecto (comportamiento
        actual: el informe incluye todos los campos). Incluye un subgrupo
        'Campos personalizados' (recalculable) con una casilla por campo,
        desmarcadas por defecto; se oculta si no hay campos.
        """
        group = QGroupBox("Campos del informe")
        vbox = QVBoxLayout(group)
        vbox.setSpacing(6)

        grid = QGridLayout()
        grid.setSpacing(6)
        self._field_checkboxes: dict[str, QCheckBox] = {}
        for index, (key, label) in enumerate(REPORT_FIELDS):
            cb = QCheckBox(label)
            cb.setChecked(True)
            self._field_checkboxes[key] = cb
            grid.addWidget(cb, index // 2, index % 2)
        vbox.addLayout(grid)

        self._custom_field_checkboxes: dict[str, QCheckBox] = {}
        self._custom_fields_group = QGroupBox("Campos personalizados")
        self._custom_fields_grid = QGridLayout(self._custom_fields_group)
        self._custom_fields_grid.setSpacing(6)
        vbox.addWidget(self._custom_fields_group)
        self._populate_custom_fields(self._custom_fields)

        return group

    def _populate_custom_fields(self, fields: list[tuple[int, str]]):
        """Reconstruye las casillas del subgrupo 'Campos personalizados'.

        Vacía el grid y las casillas previas. Si fields está vacío, oculta el
        subgrupo. Si no, lo muestra y crea una casilla por campo, preservando
        el marcado previo (self._custom_fields_checked) de las claves que sigan
        existiendo; las nuevas quedan desmarcadas.
        """
        # Guardar el marcado previo antes de vaciar
        self._custom_fields_checked = {
            key for key, cb in self._custom_field_checkboxes.items() if cb.isChecked()
        }
        for cb in self._custom_field_checkboxes.values():
            self._custom_fields_grid.removeWidget(cb)
            cb.deleteLater()
        self._custom_field_checkboxes = {}

        if not fields:
            self._custom_fields_group.setVisible(False)
            return

        self._custom_fields_group.setVisible(True)
        for index, (cf_id, cf_name) in enumerate(fields):
            key = f"cf_{cf_id}"
            cb = QCheckBox(cf_name)
            cb.setChecked(key in self._custom_fields_checked)
            self._custom_field_checkboxes[key] = cb
            self._custom_fields_grid.addWidget(cb, index // 2, index % 2)

    def _build_users_group(self) -> QGroupBox:
        """Grupo 'Usuarios implicados': multiselect + checkboxes de rol."""
        group = QGroupBox("Usuarios implicados")
        vbox = QVBoxLayout(group)
        vbox.setSpacing(6)

        self._users_combo = MultiSelectCombo()
        self._users_combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        self._users_combo.set_items(self._users)
        vbox.addWidget(self._users_combo)

        roles_row = QHBoxLayout()
        roles_row.setSpacing(12)
        self._roles_checkboxes: dict[str, QCheckBox] = {}
        for role_key, role_label in ROLES_IMPLICACION:
            cb = QCheckBox(role_label)
            cb.setChecked(True)
            self._roles_checkboxes[role_key] = cb
            roles_row.addWidget(cb)
        roles_row.addStretch()
        vbox.addLayout(roles_row)

        return group

    def _build_dates_group(self) -> QGroupBox:
        """Grupo 'Fechas de creación': dos QDateEdit con checkbox habilitador."""
        group = QGroupBox("Fechas de creación")
        vbox = QVBoxLayout(group)
        vbox.setSpacing(6)

        self._from_check = QCheckBox("Desde:")
        self._from_check.setChecked(False)
        self._from_date = QDateEdit()
        self._from_date.setCalendarPopup(True)
        self._from_date.setDisplayFormat("dd/MM/yyyy")
        self._from_date.setDate(date.today())
        self._from_date.setEnabled(False)
        self._from_check.toggled.connect(self._from_date.setEnabled)
        vbox.addLayout(self._date_row(self._from_check, self._from_date))

        self._to_check = QCheckBox("Hasta:")
        self._to_check.setChecked(False)
        self._to_date = QDateEdit()
        self._to_date.setCalendarPopup(True)
        self._to_date.setDisplayFormat("dd/MM/yyyy")
        self._to_date.setDate(date.today())
        self._to_date.setEnabled(False)
        self._to_check.toggled.connect(self._to_date.setEnabled)
        vbox.addLayout(self._date_row(self._to_check, self._to_date))

        return group

    @staticmethod
    def _date_row(check: QCheckBox, date_edit: QDateEdit) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(check)
        row.addWidget(date_edit)
        row.addStretch()
        return row

    def _build_projects_group(self) -> QGroupBox:
        """Grupo 'Proyectos': multiselect con preselección opcional."""
        group = QGroupBox("Proyectos")
        vbox = QVBoxLayout(group)
        vbox.setSpacing(6)

        self._projects_combo = MultiSelectCombo()
        self._projects_combo.set_fixed_options([(MultiSelectCombo.ALL, "Todos")])
        self._projects_combo.set_items(self._projects)
        if self._preselected_project_ids:
            self._projects_combo.set_selected_ids(self._preselected_project_ids)
        vbox.addWidget(self._projects_combo)

        return group

    # ================================================================
    # Propiedades de filtros
    # ================================================================

    @property
    def selected_user_ids(self) -> list[int]:
        """IDs de usuarios seleccionados ([] si solo está 'Todos')."""
        ids = self._users_combo.selected_ids()
        if MultiSelectCombo.ALL in ids:
            return []
        return ids

    @property
    def selected_roles(self) -> list[str]:
        """Subconjunto de ['creador', 'actualizador', 'participante'] marcado."""
        return [key for key, cb in self._roles_checkboxes.items() if cb.isChecked()]

    @property
    def created_from(self) -> str | None:
        """Fecha 'desde' en ISO (YYYY-MM-DD) o None si el checkbox está desactivado."""
        if not self._from_check.isChecked():
            return None
        return self._from_date.date().toString("yyyy-MM-dd")

    @property
    def created_to(self) -> str | None:
        """Fecha 'hasta' en ISO (YYYY-MM-DD) o None si el checkbox está desactivado."""
        if not self._to_check.isChecked():
            return None
        return self._to_date.date().toString("yyyy-MM-dd")

    @property
    def selected_project_ids(self) -> list[int]:
        """IDs de proyectos seleccionados ([] si solo está 'Todos')."""
        ids = self._projects_combo.selected_ids()
        if MultiSelectCombo.ALL in ids:
            return []
        return ids

    def _on_projects_changed(self):
        """Recalcula los campos personalizados al cambiar la selección de proyectos.

        Si hay custom_fields_provider, consulta los campos para los proyectos
        seleccionados ([] = todos) y reconstruye el subgrupo. Si el provider
        falla, el subgrupo queda vacío sin romper el diálogo.
        """
        if not self._custom_fields_provider:
            return
        try:
            fields = self._custom_fields_provider(self.selected_project_ids)
        except Exception:
            fields = []
        self._custom_fields = fields
        self._populate_custom_fields(fields)

    @property
    def selected_fields(self) -> list[str]:
        """Claves de los campos marcados.

        Primero las estándar en el orden canónico de REPORT_FIELDS y después
        las claves cf_<id> de los campos personalizados marcados, en el orden
        recibido en custom_fields.
        """
        standard = [
            key for key, _ in REPORT_FIELDS
            if self._field_checkboxes[key].isChecked()
        ]
        custom = [
            key for key in self._custom_field_checkboxes
            if self._custom_field_checkboxes[key].isChecked()
        ]
        return standard + custom

    # ================================================================
    # Validación
    # ================================================================

    def accept(self):
        """Valida los filtros antes de aceptar el diálogo."""
        if not self.selected_fields:
            QMessageBox.warning(
                self, "Campos requeridos",
                "Selecciona al menos un campo para el informe.",
            )
            return
        if not self.selected_roles:
            QMessageBox.warning(
                self, "Roles requeridos",
                "Selecciona al menos un rol de implicación.",
            )
            return
        frm = self.created_from
        to = self.created_to
        if frm and to and frm > to:
            QMessageBox.warning(
                self, "Rango inválido",
                "La fecha 'desde' no puede ser posterior a la fecha 'hasta'.",
            )
            return
        super().accept()