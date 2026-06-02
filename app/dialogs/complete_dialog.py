from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QPlainTextEdit,
)


class CompleteDialog(QDialog):
    def __init__(self, issue_id: int, parent=None):
        super().__init__(parent)
        self._issue_id = issue_id
        self.setWindowTitle(f"Completar tarea #{issue_id}")
        self.setMinimumWidth(400)
        self.setMinimumHeight(250)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(
            f"<b>¿Marcar la tarea #{self._issue_id} como completada?</b><br><br>"
            "Se pondrá el progreso al 100%, estado 'Resuelta' y fecha de fin a hoy."
        ))

        layout.addWidget(QLabel("Comentario (opcional):"))
        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setPlaceholderText("Añadir un comentario (opcional)...")
        self._notes_edit.setMaximumHeight(100)
        layout.addWidget(self._notes_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def notes(self) -> str:
        return self._notes_edit.toPlainText().strip()
