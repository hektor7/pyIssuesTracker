from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPlainTextEdit,
    QDialogButtonBox, QComboBox, QFormLayout,
)


class RejectDialog(QDialog):
    def __init__(self, issue_id: int, statuses: list[tuple[int, str]], parent=None):
        super().__init__(parent)
        self._issue_id = issue_id
        self._statuses = statuses
        self.setWindowTitle(f"Rechazar tarea #{issue_id}")
        self.setMinimumWidth(400)
        self.setMinimumHeight(250)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Motivo del rechazo para la tarea <b>#{self._issue_id}</b>:"))

        form = QFormLayout()
        self._status_combo = QComboBox()
        for sid, sname in self._statuses:
            self._status_combo.addItem(sname, sid)
        form.addRow("Nuevo estado:", self._status_combo)
        layout.addLayout(form)

        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setPlaceholderText("Explica el motivo del rechazo (se añadirá como comentario)...")
        self._notes_edit.setMinimumHeight(100)
        layout.addWidget(self._notes_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def reject_status_id(self) -> int:
        return self._status_combo.currentData() or 0

    @property
    def reject_notes(self) -> str:
        return self._notes_edit.toPlainText().strip()
