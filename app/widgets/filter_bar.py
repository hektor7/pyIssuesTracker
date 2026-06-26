from datetime import date, timedelta

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QCheckBox, QLabel,
    QCompleter, QLineEdit, QDateEdit,
)

from app.widgets.multi_select_combo import MultiSelectCombo


class FilterBar(QWidget):
    proyecto_cambiado = pyqtSignal(int, str)
    estado_cambiado = pyqtSignal(str)
    prioridad_cambiada = pyqtSignal(int)
    categoria_cambiada = pyqtSignal(int)
    asignado_cambiado = pyqtSignal(list)
    fijar_cambiado = pyqtSignal(bool)
    busqueda_cambiada = pyqtSignal(str)
    fecha_cambiada = pyqtSignal(str, str)  # due_date_from, due_date_to

    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects: list[tuple[int, str]] = []
        self._project_lookup: dict[int, str] = {}
        self._current_date_from: str | None = None
        self._current_date_to: str | None = None
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 2, 4, 2)
        main_layout.setSpacing(4)

        # --- Fila 1: filtros existentes ---
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        row1.addWidget(QLabel("Proyecto:"))

        self._project_combo = QComboBox()
        self._project_combo.setEditable(True)
        self._project_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._project_combo.setMinimumWidth(220)
        self._project_combo.setMaxVisibleItems(20)
        self._project_combo.currentIndexChanged.connect(self._on_project_selected)
        self._project_combo.lineEdit().returnPressed.connect(self._on_enter_pressed)
        row1.addWidget(self._project_combo)

        self._completer = QCompleter([], self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._project_combo.setCompleter(self._completer)

        self._fixed_checkbox = QCheckBox("Fijar filtro")
        self._fixed_checkbox.setToolTip("Mantener este filtro de proyecto al reiniciar la aplicación")
        self._fixed_checkbox.toggled.connect(self.fijar_cambiado.emit)
        row1.addWidget(self._fixed_checkbox)

        row1.addSpacing(16)
        row1.addWidget(QLabel("Estado:"))

        self._status_combo = QComboBox()
        self._status_combo.addItem("Abiertas", "open")
        self._status_combo.addItem("Todas", "*")
        self._status_combo.addItem("Cerradas", "closed")
        self._status_combo.currentIndexChanged.connect(self._on_status_changed)
        row1.addWidget(self._status_combo)

        row1.addSpacing(16)
        row1.addWidget(QLabel("Prioridad:"))

        self._priority_combo = QComboBox()
        self._priority_combo.setEditable(True)
        self._priority_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._priority_combo.setMinimumWidth(120)
        self._priority_combo.addItem("(Todas)", 0)
        self._priority_combo.currentIndexChanged.connect(self._on_priority_changed)
        row1.addWidget(self._priority_combo)

        self._priority_completer = QCompleter([], self)
        self._priority_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._priority_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._priority_combo.setCompleter(self._priority_completer)

        row1.addSpacing(16)
        row1.addWidget(QLabel("Categoría:"))

        self._category_combo = QComboBox()
        self._category_combo.setEditable(True)
        self._category_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._category_combo.setMinimumWidth(120)
        self._category_combo.addItem("(Todas)", 0)
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        row1.addWidget(self._category_combo)

        self._category_completer = QCompleter([], self)
        self._category_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._category_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._category_combo.setCompleter(self._category_completer)

        row1.addSpacing(16)
        row1.addWidget(QLabel("Asignado a:"))

        self._assigned_combo = MultiSelectCombo()
        self._assigned_combo.set_fixed_options([
            (MultiSelectCombo.ALL, "Todos"),
            (MultiSelectCombo.NONE, "Sin asignar"),
            (MultiSelectCombo.ME, "Asignado a mí"),
        ])
        self._assigned_combo.seleccion_cambiada.connect(self._on_assigned_changed)
        row1.addWidget(self._assigned_combo)

        row1.addSpacing(16)
        row1.addWidget(QLabel("Fecha fin:"))

        self._date_preset_combo = QComboBox()
        self._date_preset_combo.addItems([
            "Sin filtro", "Hoy", "Ayer", "Esta semana",
            "Semana pasada", "Este mes", "Mes pasado",
            "Rango personalizado",
        ])
        self._date_preset_combo.currentIndexChanged.connect(self._on_date_preset_changed)
        row1.addWidget(self._date_preset_combo)

        self._date_from_edit = QDateEdit()
        self._date_from_edit.setCalendarPopup(True)
        self._date_from_edit.setDisplayFormat("dd/MM/yyyy")
        self._date_from_edit.setDate(date.today())
        self._date_from_edit.setVisible(False)
        row1.addWidget(self._date_from_edit)

        self._date_to_edit = QDateEdit()
        self._date_to_edit.setCalendarPopup(True)
        self._date_to_edit.setDisplayFormat("dd/MM/yyyy")
        self._date_to_edit.setDate(date.today())
        self._date_to_edit.setVisible(False)
        row1.addWidget(self._date_to_edit)
        self._date_from_edit.dateChanged.connect(self._on_date_from_changed)
        self._date_to_edit.dateChanged.connect(self._on_date_to_changed)

        row1.addStretch()
        main_layout.addLayout(row1)

        # --- Fila 2: búsqueda por texto ---
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(QLabel("Buscar:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Buscar por título...")
        self._search_edit.setMinimumWidth(300)
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._on_search_text_changed)
        row2.addWidget(self._search_edit)
        row2.addStretch()
        main_layout.addLayout(row2)

    def populate_projects(self, projects: list[tuple[int, str]], hierarchy: dict[int, int | None] | None = None):
        self._projects = projects
        self._project_lookup = {pid: name for pid, name in projects}
        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        self._project_combo.addItem("(Todos los proyectos)", 0)
        names = []
        for pid, name in projects:
            indent = ""
            if hierarchy:
                depth = 0
                parent = hierarchy.get(pid)
                while parent:
                    depth += 1
                    parent = hierarchy.get(parent)
                indent = "  " * depth
            display = f"{indent}{name}"
            self._project_combo.addItem(display, pid)
            self._project_combo.setItemData(self._project_combo.count() - 1, name, Qt.ItemDataRole.ToolTipRole)
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
        names = [self._priority_combo.itemText(i) for i in range(self._priority_combo.count())]
        self._priority_completer.model().setStringList(names)
        self._priority_combo.blockSignals(False)

    def populate_categories(self, categories: list[tuple[int, str]]):
        self._category_combo.blockSignals(True)
        current_data = self._category_combo.currentData()
        self._category_combo.clear()
        self._category_combo.addItem("(Todas)", 0)
        for cid, name in categories:
            self._category_combo.addItem(name, cid)
        for i in range(self._category_combo.count()):
            if self._category_combo.itemData(i) == current_data:
                self._category_combo.setCurrentIndex(i)
                break
        names = [self._category_combo.itemText(i) for i in range(self._category_combo.count())]
        self._category_completer.model().setStringList(names)
        self._category_combo.blockSignals(False)

    def populate_assignees(self, assignees: list[tuple[int, str]]):
        self._assigned_combo.set_items(assignees)

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

    def set_category(self, category_id: int):
        for i in range(self._category_combo.count()):
            if self._category_combo.itemData(i) == category_id:
                self._category_combo.setCurrentIndex(i)
                return

    def set_assigned_to(self, assigned_to_ids: list):
        self._assigned_combo.set_selected_ids(assigned_to_ids)

    def set_fixed(self, fixed: bool):
        self._fixed_checkbox.setChecked(fixed)

    @property
    def selected_project_id(self) -> int:
        data = self._project_combo.currentData()
        return data if data is not None else 0

    @property
    def selected_project_name(self) -> str:
        return self._project_lookup.get(self.selected_project_id, "")

    @property
    def selected_status(self) -> str:
        return self._status_combo.currentData() or "open"

    @property
    def selected_priority(self) -> int:
        return self._priority_combo.currentData() or 0

    @property
    def selected_category(self) -> int:
        return self._category_combo.currentData() or 0

    @property
    def selected_assigned_to(self) -> list:
        return self._assigned_combo.selected_ids()

    @property
    def selected_date_preset(self) -> int:
        """Índice del preset de fecha seleccionado (0=Sin filtro, ..., 7=Rango)."""
        return self._date_preset_combo.currentIndex()

    @property
    def selected_date_from(self) -> str | None:
        """Fecha 'desde' actual del filtro de fecha, o None si no hay filtro."""
        if self._current_date_from:
            return self._current_date_from
        return None

    @property
    def selected_date_to(self) -> str | None:
        """Fecha 'hasta' actual del filtro de fecha, o None si no hay filtro."""
        if self._current_date_to:
            return self._current_date_to
        return None

    @property
    def is_fixed(self) -> bool:
        return self._fixed_checkbox.isChecked()

    def set_date_preset(self, index: int, date_from: str | None = None,
                        date_to: str | None = None):
        """Restaura el filtro de fecha desde valores persistidos.

        Args:
            index: Índice del preset en el combo (0=Sin filtro, ..., 7=Rango personalizado)
            date_from: Fecha desde en ISO (YYYY-MM-DD) para rango personalizado
            date_to: Fecha hasta en ISO (YYYY-MM-DD) para rango personalizado
        """
        if 0 <= index < self._date_preset_combo.count():
            self._date_preset_combo.setCurrentIndex(index)
        if index == 7 and date_from and date_to:
            from PyQt6.QtCore import QDate
            df = QDate.fromString(date_from, "yyyy-MM-dd")
            dt = QDate.fromString(date_to, "yyyy-MM-dd")
            if df.isValid():
                self._date_from_edit.setDate(df)
            if dt.isValid():
                self._date_to_edit.setDate(dt)
            self._update_date_filter(date_from, date_to)

    def _on_project_selected(self, index: int):
        if index < 0:
            return
        pid = self._project_combo.itemData(index) or 0
        name = self._project_lookup.get(pid, "")
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

    def _on_category_changed(self, index: int):
        category = self._category_combo.currentData() or 0
        self.categoria_cambiada.emit(category)

    def _on_assigned_changed(self, assigned: list):
        self.asignado_cambiado.emit(assigned)

    def _on_date_preset_changed(self, index: int):
        today = date.today()
        if index == 0:  # Sin filtro
            self._date_from_edit.setVisible(False)
            self._date_to_edit.setVisible(False)
            self._update_date_filter(None, None)
        elif index == 1:  # Hoy
            self._date_from_edit.setVisible(False)
            self._date_to_edit.setVisible(False)
            self._update_date_filter(today.isoformat(), today.isoformat())
        elif index == 2:  # Ayer
            self._date_from_edit.setVisible(False)
            self._date_to_edit.setVisible(False)
            yesterday = today - timedelta(days=1)
            self._update_date_filter(yesterday.isoformat(), yesterday.isoformat())
        elif index == 3:  # Esta semana
            self._date_from_edit.setVisible(False)
            self._date_to_edit.setVisible(False)
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
            self._update_date_filter(monday.isoformat(), sunday.isoformat())
        elif index == 4:  # Semana pasada
            self._date_from_edit.setVisible(False)
            self._date_to_edit.setVisible(False)
            monday = today - timedelta(days=today.weekday() + 7)
            sunday = monday + timedelta(days=6)
            self._update_date_filter(monday.isoformat(), sunday.isoformat())
        elif index == 5:  # Este mes
            self._date_from_edit.setVisible(False)
            self._date_to_edit.setVisible(False)
            first = today.replace(day=1)
            if today.month == 12:
                last = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            self._update_date_filter(first.isoformat(), last.isoformat())
        elif index == 6:  # Mes pasado
            self._date_from_edit.setVisible(False)
            self._date_to_edit.setVisible(False)
            if today.month == 1:
                first = today.replace(year=today.year - 1, month=12, day=1)
                last = today.replace(day=1) - timedelta(days=1)
            else:
                first = today.replace(month=today.month - 1, day=1)
                last = today.replace(day=1) - timedelta(days=1)
            self._update_date_filter(first.isoformat(), last.isoformat())
        elif index == 7:  # Rango personalizado
            self._date_from_edit.setVisible(True)
            self._date_to_edit.setVisible(True)
            # No aplicar filtro hasta que el usuario seleccione fechas explícitamente
            self._current_date_from = None
            self._current_date_to = None
            self.fecha_cambiada.emit("", "")

    def _update_date_filter(self, date_from: str | None, date_to: str | None):
        """Almacena los valores de fecha y emite la señal."""
        self._current_date_from = date_from
        self._current_date_to = date_to
        self.fecha_cambiada.emit(date_from or "", date_to or "")

    def _on_date_from_changed(self):
        if self._date_preset_combo.currentIndex() == 7:
            self._update_date_filter(
                self._date_from_edit.date().toString("yyyy-MM-dd"),
                self._date_to_edit.date().toString("yyyy-MM-dd"),
            )

    def _on_date_to_changed(self):
        if self._date_preset_combo.currentIndex() == 7:
            self._update_date_filter(
                self._date_from_edit.date().toString("yyyy-MM-dd"),
                self._date_to_edit.date().toString("yyyy-MM-dd"),
            )

    def _on_search_text_changed(self, text: str):
        self.busqueda_cambiada.emit(text)

    def set_search_text(self, text: str):
        self._search_edit.setText(text)
