from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox,
    QDialogButtonBox, QCheckBox, QFormLayout,
)


class AssignDialog(QDialog):
    def __init__(self, issue_id: int, members: list[tuple[int, str]],
                 current_user_id: int, parent=None):
        super().__init__(parent)
        self._issue_id = issue_id
        self._members = members
        self._current_user_id = current_user_id
        self.setWindowTitle(f"Asignar tarea #{issue_id}")
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Selecciona el usuario para asignar la tarea <b>#{self._issue_id}</b>:"))

        form = QFormLayout()
        self._assign_self_cb = QCheckBox("Asignarme a mí")
        self._assign_self_cb.setChecked(True)
        self._assign_self_cb.toggled.connect(self._toggle_user_combo)
        form.addRow(self._assign_self_cb)

        self._user_combo = QComboBox()
        self._user_combo.setEnabled(False)
        for uid, uname in self._members:
            label = f"{uname}"
            if uid == self._current_user_id:
                label += " (yo)"
            self._user_combo.addItem(label, uid)
        form.addRow("Usuario:", self._user_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _toggle_user_combo(self, checked: bool):
        self._user_combo.setEnabled(not checked)

    @property
    def selected_user_id(self) -> int:
        if self._assign_self_cb.isChecked():
            return self._current_user_id
        return self._user_combo.currentData() or self._current_user_id
