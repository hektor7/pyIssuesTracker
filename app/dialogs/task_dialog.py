from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPlainTextEdit, QComboBox, QDialogButtonBox,
    QLabel, QSpinBox, QMessageBox,
)


class TaskDialog(QDialog):
    def __init__(self, parent=None, projects: list[tuple[int, str]] | None = None,
                 trackers: list[tuple[int, str]] | None = None,
                 task_data: dict | None = None):
        super().__init__(parent)
        self._projects = projects or []
        self._trackers = trackers or []
        self._task_data = task_data or {}
        self._is_edit = bool(task_data)

        self.setWindowTitle("Editar tarea" if self._is_edit else "Nueva tarea")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(8)

        if self._is_edit:
            self._id_label = QLabel(str(self._task_data.get("id", "")))
            form.addRow("ID:", self._id_label)

        self._project_combo = QComboBox()
        for pid, pname in self._projects:
            self._project_combo.addItem(pname, pid)
        form.addRow("Proyecto:", self._project_combo)

        self._tracker_combo = QComboBox()
        for tid, tname in self._trackers:
            self._tracker_combo.addItem(tname, tid)
        form.addRow("Tracker:", self._tracker_combo)

        self._subject_edit = QLineEdit()
        self._subject_edit.setPlaceholderText("Título de la tarea")
        form.addRow("Asunto:", self._subject_edit)

        self._description_edit = QPlainTextEdit()
        self._description_edit.setPlaceholderText("Descripción detallada...")
        self._description_edit.setMinimumHeight(120)
        form.addRow("Descripción:", self._description_edit)

        layout.addLayout(form)
        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _populate_fields(self):
        if self._is_edit:
            pid = self._task_data.get("project_id", 0)
            for i in range(self._project_combo.count()):
                if self._project_combo.itemData(i) == pid:
                    self._project_combo.setCurrentIndex(i)
                    break
            tid = self._task_data.get("tracker_id", 1)
            for i in range(self._tracker_combo.count()):
                if self._tracker_combo.itemData(i) == tid:
                    self._tracker_combo.setCurrentIndex(i)
                    break
            self._subject_edit.setText(self._task_data.get("subject", ""))
            self._description_edit.setPlainText(self._task_data.get("description", ""))

    def _validate_and_accept(self):
        if not self._subject_edit.text().strip():
            QMessageBox.warning(self, "Validación", "El asunto es obligatorio.")
            self._subject_edit.setFocus()
            return
        self.accept()

    @property
    def project_id(self) -> int:
        return self._project_combo.currentData() or 0

    @property
    def tracker_id(self) -> int:
        return self._tracker_combo.currentData() or 1

    @property
    def subject(self) -> str:
        return self._subject_edit.text().strip()

    @property
    def description(self) -> str:
        return self._description_edit.toPlainText().strip()
