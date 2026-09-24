"""Diálogo de configuración del informe ODS (tareas 4.2 y 4.3).

Permite acotar el informe por usuarios implicados (con rol), por rango
de fechas de creación y por proyectos, antes de generar el fichero.
"""
from datetime import date

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QHBoxLayout, QCheckBox,
    QDateEdit, QDialogButtonBox, QMessageBox,
)

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
                 preselected_project_ids=None, parent=None):
        super().__init__(parent)
        self._projects = projects or []
        self._users = users or []
        self._preselected_project_ids = preselected_project_ids or []
        self.setWindowTitle("Generar informe")
        self.setMinimumWidth(420)
        self._setup_ui()

    # ================================================================
    # UI
    # ================================================================

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(self._build_users_group())
        layout.addWidget(self._build_dates_group())
        layout.addWidget(self._build_projects_group())

        buttons = QDialogButtonBox()
        buttons.addButton("Generar", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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

    # ================================================================
    # Validación
    # ================================================================

    def accept(self):
        """Valida los filtros antes de aceptar el diálogo."""
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