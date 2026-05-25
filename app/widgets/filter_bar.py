from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QCheckBox, QLabel,
    QCompleter,
)


class FilterBar(QWidget):
    proyecto_cambiado = pyqtSignal(int, str)
    estado_cambiado = pyqtSignal(str)
    prioridad_cambiada = pyqtSignal(int)
    tracker_cambiado = pyqtSignal(int)
    asignado_cambiado = pyqtSignal(int)
    fijar_cambiado = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects: list[tuple[int, str]] = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Proyecto:"))

        self._project_combo = QComboBox()
        self._project_combo.setEditable(True)
        self._project_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._project_combo.setMinimumWidth(220)
        self._project_combo.setMaxVisibleItems(20)
        self._project_combo.currentIndexChanged.connect(self._on_project_selected)
        self._project_combo.lineEdit().returnPressed.connect(self._on_enter_pressed)
        layout.addWidget(self._project_combo)

        self._completer = QCompleter([], self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._project_combo.setCompleter(self._completer)

        self._fixed_checkbox = QCheckBox("Fijar filtro")
        self._fixed_checkbox.setToolTip("Mantener este filtro de proyecto al reiniciar la aplicación")
        self._fixed_checkbox.toggled.connect(self.fijar_cambiado.emit)
        layout.addWidget(self._fixed_checkbox)

        layout.addSpacing(16)
        layout.addWidget(QLabel("Estado:"))

        self._status_combo = QComboBox()
        self._status_combo.addItem("Abiertas", "open")
        self._status_combo.addItem("Todas", "*")
        self._status_combo.addItem("Cerradas", "closed")
        self._status_combo.currentIndexChanged.connect(self._on_status_changed)
        layout.addWidget(self._status_combo)

        layout.addSpacing(16)
        layout.addWidget(QLabel("Prioridad:"))

        self._priority_combo = QComboBox()
        self._priority_combo.setMinimumWidth(120)
        self._priority_combo.addItem("(Todas)", 0)
        self._priority_combo.currentIndexChanged.connect(self._on_priority_changed)
        layout.addWidget(self._priority_combo)

        layout.addSpacing(16)
        layout.addWidget(QLabel("Categoría:"))

        self._tracker_combo = QComboBox()
        self._tracker_combo.setMinimumWidth(120)
        self._tracker_combo.addItem("(Todas)", 0)
        self._tracker_combo.currentIndexChanged.connect(self._on_tracker_changed)
        layout.addWidget(self._tracker_combo)

        layout.addSpacing(16)
        layout.addWidget(QLabel("Asignado a:"))

        self._assigned_combo = QComboBox()
        self._assigned_combo.setMinimumWidth(150)
        self._assigned_combo.addItem("(Todos)", 0)
        self._assigned_combo.addItem("Sin asignar", -1)
        self._assigned_combo.addItem("Asignado a mí", -2)
        self._assigned_combo.currentIndexChanged.connect(self._on_assigned_changed)
        layout.addWidget(self._assigned_combo)

        layout.addStretch()

    def populate_projects(self, projects: list[tuple[int, str]]):
        self._projects = projects
        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        self._project_combo.addItem("(Todos los proyectos)", 0)
        names = []
        for pid, name in projects:
            prefix = ""
            self._project_combo.addItem(f"{prefix}{name}", pid)
            names.append(name)
        self._completer.model().setStringList(names)
        self._project_combo.blockSignals(False)

    def select_project(self, project_id: int, project_name: str):
        for i in range(self._project_combo.count()):
            if self._project_combo.itemData(i) == project_id:
                self._project_combo.blockSignals(True)
                self._project_combo.setCurrentIndex(i)
                self._project_combo.blockSignals(False)
                return
        if project_name:
            self._project_combo.blockSignals(True)
            self._project_combo.setCurrentText(project_name)
            self._project_combo.blockSignals(False)

    def populate_priorities(self, priorities: list[tuple[int, str]]):
        self._priority_combo.blockSignals(True)
        current_data = self._priority_combo.currentData()
        self._priority_combo.clear()
        self._priority_combo.addItem("(Todas)", 0)
        for pid, name in priorities:
            self._priority_combo.addItem(name, pid)
        for i in range(self._priority_combo.count()):
            if self._priority_combo.itemData(i) == current_data:
                self._priority_combo.setCurrentIndex(i)
                break
        self._priority_combo.blockSignals(False)

    def populate_trackers(self, trackers: list[tuple[int, str]]):
        self._tracker_combo.blockSignals(True)
        current_data = self._tracker_combo.currentData()
        self._tracker_combo.clear()
        self._tracker_combo.addItem("(Todas)", 0)
        for tid, name in trackers:
            self._tracker_combo.addItem(name, tid)
        for i in range(self._tracker_combo.count()):
            if self._tracker_combo.itemData(i) == current_data:
                self._tracker_combo.setCurrentIndex(i)
                break
        self._tracker_combo.blockSignals(False)

    def populate_assignees(self, assignees: list[tuple[int, str]]):
        self._assigned_combo.blockSignals(True)
        current_data = self._assigned_combo.currentData()
        self._assigned_combo.clear()
        self._assigned_combo.addItem("(Todos)", 0)
        self._assigned_combo.addItem("Sin asignar", -1)
        self._assigned_combo.addItem("Asignado a mí", -2)
        for uid, name in assignees:
            self._assigned_combo.addItem(name, uid)
        for i in range(self._assigned_combo.count()):
            if self._assigned_combo.itemData(i) == current_data:
                self._assigned_combo.setCurrentIndex(i)
                break
        self._assigned_combo.blockSignals(False)

    def set_status(self, status: str):
        for i in range(self._status_combo.count()):
            if self._status_combo.itemData(i) == status:
                self._status_combo.setCurrentIndex(i)
                return

    def set_priority(self, priority_id: int):
        for i in range(self._priority_combo.count()):
            if self._priority_combo.itemData(i) == priority_id:
                self._priority_combo.setCurrentIndex(i)
                return

    def set_tracker(self, tracker_id: int):
        for i in range(self._tracker_combo.count()):
            if self._tracker_combo.itemData(i) == tracker_id:
                self._tracker_combo.setCurrentIndex(i)
                return

    def set_assigned_to(self, assigned_to_id: int):
        for i in range(self._assigned_combo.count()):
            if self._assigned_combo.itemData(i) == assigned_to_id:
                self._assigned_combo.setCurrentIndex(i)
                return

    def set_fixed(self, fixed: bool):
        self._fixed_checkbox.setChecked(fixed)

    @property
    def selected_project_id(self) -> int:
        data = self._project_combo.currentData()
        return data if data is not None else 0

    @property
    def selected_project_name(self) -> str:
        return self._project_combo.currentText()

    @property
    def selected_status(self) -> str:
        return self._status_combo.currentData() or "open"

    @property
    def selected_priority(self) -> int:
        return self._priority_combo.currentData() or 0

    @property
    def selected_tracker(self) -> int:
        return self._tracker_combo.currentData() or 0

    @property
    def selected_assigned_to(self) -> int:
        return self._assigned_combo.currentData() or 0

    @property
    def is_fixed(self) -> bool:
        return self._fixed_checkbox.isChecked()

    def _on_project_selected(self, index: int):
        if index < 0:
            return
        pid = self._project_combo.itemData(index) or 0
        name = self._project_combo.itemText(index)
        self.proyecto_cambiado.emit(pid, name)

    def _on_enter_pressed(self):
        text = self._project_combo.currentText().strip().lower()
        for i in range(self._project_combo.count()):
            if self._project_combo.itemText(i).lower() == text:
                self._project_combo.setCurrentIndex(i)
                return
        for i, (pid, name) in enumerate(self._projects):
            if text in name.lower():
                self._project_combo.setCurrentIndex(i + 1)
                return

    def _on_status_changed(self, index: int):
        status = self._status_combo.currentData() or "open"
        self.estado_cambiado.emit(status)

    def _on_priority_changed(self, index: int):
        priority = self._priority_combo.currentData() or 0
        self.prioridad_cambiada.emit(priority)

    def _on_tracker_changed(self, index: int):
        tracker = self._tracker_combo.currentData() or 0
        self.tracker_cambiado.emit(tracker)

    def _on_assigned_changed(self, index: int):
        assigned = self._assigned_combo.currentData() or 0
        self.asignado_cambiado.emit(assigned)
