from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPlainTextEdit, QComboBox, QDialogButtonBox,
    QLabel, QSpinBox, QMessageBox, QGroupBox,
    QDateEdit, QSlider, QHBoxLayout, QScrollArea,
    QWidget, QCompleter, QSizePolicy,
)

from app.services.redmine_client import RedmineClient
from app.widgets.comments_widget import CommentsWidget
from app.widgets.checklist_widget import ChecklistWidget


class TaskDialog(QDialog):
    def __init__(self, parent=None, projects: list[tuple[int, str]] | None = None,
                 trackers: list[tuple[int, str]] | None = None,
                 priorities: list[tuple[int, str]] | None = None,
                 initial_categories: list[tuple[int, str]] | None = None,
                 redmine_client: RedmineClient | None = None,
                 task_data: dict | None = None):
        super().__init__(parent)
        self._projects = projects or []
        self._trackers = trackers or []
        self._priorities = priorities or []
        self._initial_categories = initial_categories or []
        self._redmine = redmine_client
        self._task_data = task_data or {}
        self._is_edit = bool(task_data)

        self.setWindowTitle("Editar tarea" if self._is_edit else "Nueva tarea")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._setup_ui()
        self._populate_fields()

        # Cargar checklists y comentarios solo en modo edición
        if self._is_edit and self._redmine:
            self._load_checklists()
            self._load_comments()

    # ================================================================
    # UI Setup
    # ================================================================

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        # --- Scroll area principal ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)

        # --- ID (solo edición) ---
        if self._is_edit:
            id_layout = QHBoxLayout()
            id_layout.addWidget(QLabel("ID:"))
            self._id_label = QLabel(str(self._task_data.get("id", "")))
            self._id_label.setStyleSheet("font-weight: bold;")
            id_layout.addWidget(self._id_label)
            id_layout.addStretch()
            scroll_layout.addLayout(id_layout)

        # --- Grupo: Datos básicos ---
        basic_group = QGroupBox("Datos básicos")
        basic_form = QFormLayout(basic_group)
        basic_form.setSpacing(6)

        # Proyecto (buscable)
        self._project_combo = self._make_searchable_combo()
        for pid, pname in self._projects:
            self._project_combo.addItem(pname, pid)
        self._project_combo.currentIndexChanged.connect(self._on_project_changed)
        basic_form.addRow("Proyecto:", self._project_combo)

        # Tracker (buscable)
        self._tracker_combo = self._make_searchable_combo()
        for tid, tname in self._trackers:
            self._tracker_combo.addItem(tname, tid)
        basic_form.addRow("Tracker:", self._tracker_combo)

        # Asunto
        self._subject_edit = QLineEdit()
        self._subject_edit.setPlaceholderText("Título de la tarea")
        basic_form.addRow("Asunto:", self._subject_edit)

        # Descripción
        self._description_edit = QPlainTextEdit()
        self._description_edit.setPlaceholderText("Descripción detallada...")
        self._description_edit.setMinimumHeight(100)
        basic_form.addRow("Descripción:", self._description_edit)

        scroll_layout.addWidget(basic_group)

        # --- Grupo: Detalles ---
        details_group = QGroupBox("Detalles")
        details_form = QFormLayout(details_group)
        details_form.setSpacing(6)

        # Estado (solo edición)
        if self._is_edit:
            self._status_combo = QComboBox()
            # Los estados se cargarán en _populate_fields desde task_data
            details_form.addRow("Estado:", self._status_combo)

        # Prioridad (buscable)
        self._prior_combo = self._make_searchable_combo()
        default_priority_index = 0
        for i, (pid, pname) in enumerate(self._priorities):
            self._prior_combo.addItem(pname, pid)
            if pid == 2:  # Normal por defecto en Redmine
                default_priority_index = i
        if self._prior_combo.count() > default_priority_index:
            self._prior_combo.setCurrentIndex(default_priority_index)
        details_form.addRow("Prioridad:", self._prior_combo)

        # Categoría (buscable, carga dinámica)
        self._cat_combo = self._make_searchable_combo()
        self._populate_categories(self._initial_categories)
        details_form.addRow("Categoría:", self._cat_combo)

        # Fecha de inicio
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setDate(date.today())
        details_form.addRow("Fecha inicio:", self._date_edit)

        # Progreso
        progress_widget = QWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(4)

        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 100)
        self._progress_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._progress_slider.setTickInterval(10)
        progress_layout.addWidget(self._progress_slider)

        self._progress_spin = QSpinBox()
        self._progress_spin.setRange(0, 100)
        self._progress_spin.setSuffix(" %")
        self._progress_spin.setSingleStep(5)
        self._progress_spin.setFixedWidth(80)
        progress_layout.addWidget(self._progress_spin)

        # Sincronización bidireccional
        self._progress_slider.valueChanged.connect(self._on_slider_changed)
        self._progress_spin.valueChanged.connect(self._on_spin_changed)

        details_form.addRow("Progreso:", progress_widget)

        scroll_layout.addWidget(details_group)

        # --- Grupo: Checklist ---
        self._checklist_group = QGroupBox("Checklist")
        checklist_layout = QVBoxLayout(self._checklist_group)
        self._checklist_widget = ChecklistWidget()
        self._checklist_widget.item_toggled.connect(self._on_checklist_item_toggled)
        self._checklist_widget.item_agregado.connect(self._on_checklist_item_added)
        self._checklist_widget.item_eliminado.connect(self._on_checklist_item_deleted)
        checklist_layout.addWidget(self._checklist_widget)
        self._checklist_group.setVisible(False)  # Oculto hasta cargar
        scroll_layout.addWidget(self._checklist_group)

        # --- Grupo: Comentarios ---
        self._comments_group = QGroupBox("Comentarios")
        comments_layout = QVBoxLayout(self._comments_group)
        self._comments_widget = CommentsWidget()
        self._comments_widget.nota_agregada.connect(self._on_add_comment)
        comments_layout.addWidget(self._comments_widget)
        self._comments_group.setVisible(False)  # Oculto en nueva tarea
        scroll_layout.addWidget(self._comments_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # --- Botones ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _make_searchable_combo(self) -> QComboBox:
        """Crea un QComboBox editable con QCompleter para búsqueda por teclado (MatchContains)."""
        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        completer = QCompleter(combo)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        combo.setCompleter(completer)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return combo

    # ================================================================
    # Population
    # ================================================================

    def _populate_fields(self):
        if not self._is_edit:
            return

        # Proyecto
        pid = self._task_data.get("project_id", 0)
        self._set_combo_data(self._project_combo, pid)

        # Tracker
        tid = self._task_data.get("tracker_id", 1)
        self._set_combo_data(self._tracker_combo, tid)

        # Asunto
        self._subject_edit.setText(self._task_data.get("subject", ""))

        # Descripción
        self._description_edit.setPlainText(self._task_data.get("description", ""))

        # Prioridad
        prior_id = self._task_data.get("priority_id", 2)
        self._set_combo_data(self._prior_combo, prior_id)

        # Categoría - se cargará dinámicamente al cambiar proyecto
        # pero establecemos el valor inicial para que _populate_categories lo seleccione
        self._pending_category_id = self._task_data.get("category_id", 0)

        # Fecha inicio
        start_str = self._task_data.get("start_date", "")
        if start_str:
            try:
                d = date.fromisoformat(start_str)
                self._date_edit.setDate(d)
            except (ValueError, TypeError):
                pass

        # Progreso
        done = self._task_data.get("done_ratio", 0)
        self._progress_slider.blockSignals(True)
        self._progress_spin.blockSignals(True)
        self._progress_slider.setValue(done)
        self._progress_spin.setValue(done)
        self._progress_slider.blockSignals(False)
        self._progress_spin.blockSignals(False)

        # Cargar categorías del proyecto
        if self._redmine and pid:
            self._load_categories_for_project(pid)

    def _set_combo_data(self, combo: QComboBox, data_value):
        """Selecciona el item del combo cuyo userData coincida con data_value."""
        for i in range(combo.count()):
            if combo.itemData(i) == data_value:
                combo.setCurrentIndex(i)
                return

    # ================================================================
    # Carga dinámica de categorías
    # ================================================================

    def _on_project_changed(self):
        project_id = self._project_combo.currentData() or 0
        if project_id and self._redmine:
            self._load_categories_for_project(project_id)

    def _load_categories_for_project(self, project_id: int):
        try:
            cats = self._redmine.get_project_issue_categories(project_id)
            categories = [(c.id, c.name) for c in cats]
            self._populate_categories(categories)
        except Exception:
            pass

    def _populate_categories(self, categories: list[tuple[int, str]]):
        """Puebla el combo de categorías con búsqueda."""
        self._cat_combo.blockSignals(True)
        self._cat_combo.clear()
        self._cat_combo.addItem("(Sin categoría)", 0)
        names = ["(Sin categoría)"]
        for cid, cname in categories:
            self._cat_combo.addItem(cname, cid)
            names.append(cname)
        # Actualizar el completer
        completer = self._cat_combo.completer()
        if completer:
            completer.model().setStringList(names)
        self._cat_combo.blockSignals(False)

        # Si hay categoría pendiente, seleccionarla
        if hasattr(self, '_pending_category_id') and self._pending_category_id:
            self._set_combo_data(self._cat_combo, self._pending_category_id)
            self._pending_category_id = 0

    # ================================================================
    # Checklists
    # ================================================================

    def _load_checklists(self):
        issue_id = self._task_data.get("id", 0)
        if not issue_id or not self._redmine:
            return
        try:
            items = self._redmine.get_checklists(issue_id)
            items_data = [
                {"id": i.id, "subject": i.subject, "is_done": i.is_done, "position": i.position}
                for i in items
            ]
            self._checklist_widget.set_items(items_data)
            self._checklist_group.setVisible(True)
        except Exception:
            # Plugin no instalado o error: ocultar sección
            self._checklist_group.setVisible(False)

    def _on_checklist_item_toggled(self, item_id: int, checked: bool):
        if self._redmine:
            try:
                self._redmine.update_checklist_item(item_id, is_done=1 if checked else 0)
            except Exception:
                pass  # Silencioso, el usuario ya ve el toggle

    def _on_checklist_item_added(self, subject: str):
        issue_id = self._task_data.get("id", 0)
        if self._redmine and issue_id:
            try:
                result = self._redmine.create_checklist_item(issue_id, subject)
                # Intentar obtener el id del nuevo item de la respuesta
                new_id = result.get("checklist", {}).get("id", 0)
                if new_id:
                    self._checklist_widget.add_item_widget(new_id, subject, False)
                else:
                    # Recargar todos los items
                    self._load_checklists()
            except Exception:
                pass

    def _on_checklist_item_deleted(self, item_id: int):
        if self._redmine:
            try:
                self._redmine.delete_checklist_item(item_id)
                self._checklist_widget.remove_item_widget(item_id)
            except Exception:
                pass

    # ================================================================
    # Comentarios
    # ================================================================

    def _load_comments(self):
        """Carga los comentarios desde task_data (ya deben venir pre-cargados desde main_window)."""
        journals = self._task_data.get("journals", [])
        self._comments_widget.set_comments(journals)
        self._comments_group.setVisible(True)

    def _on_add_comment(self, text: str):
        issue_id = self._task_data.get("id", 0)
        if self._redmine and issue_id:
            try:
                self._redmine.add_issue_note(issue_id, text)
                # No recargamos; el comentario se guardó en el servidor
            except Exception:
                QMessageBox.warning(self, "Error", "No se pudo añadir el comentario.")

    # ================================================================
    # Progreso - sincronización slider/spin
    # ================================================================

    def _on_slider_changed(self, value: int):
        self._progress_spin.blockSignals(True)
        self._progress_spin.setValue(value)
        self._progress_spin.blockSignals(False)

    def _on_spin_changed(self, value: int):
        self._progress_slider.blockSignals(True)
        self._progress_slider.setValue(value)
        self._progress_slider.blockSignals(False)

    # ================================================================
    # Validación
    # ================================================================

    def _validate_and_accept(self):
        if not self._subject_edit.text().strip():
            QMessageBox.warning(self, "Validación", "El asunto es obligatorio.")
            self._subject_edit.setFocus()
            return
        self.accept()

    # ================================================================
    # Properties
    # ================================================================

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

    @property
    def priority_id(self) -> int:
        return self._prior_combo.currentData() or 2

    @property
    def category_id(self) -> int:
        return self._cat_combo.currentData() or 0

    @property
    def start_date(self) -> str:
        return self._date_edit.date().toString("yyyy-MM-dd")

    @property
    def done_ratio(self) -> int:
        return self._progress_spin.value()

    @property
    def status_id(self) -> int:
        if hasattr(self, '_status_combo'):
            return self._status_combo.currentData() or 0
        return 0
