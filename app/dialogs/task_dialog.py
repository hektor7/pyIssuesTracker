from datetime import date
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPlainTextEdit, QComboBox, QDialogButtonBox,
    QLabel, QSpinBox, QMessageBox, QGroupBox,
    QDateEdit, QSlider, QHBoxLayout, QScrollArea,
    QWidget, QSizePolicy,
    QPushButton, QFileDialog, QFrame, QCheckBox,
    QDoubleSpinBox, QListWidget, QAbstractItemView,
)

from app.services.redmine_client import RedmineClient
from app.widgets.comments_widget import CommentsWidget
from app.widgets.checklist_widget import ChecklistWidget
from app.widgets.searchable_combo import make_searchable_combo, update_completer_model


class TaskDialog(QDialog):
    def __init__(self, parent=None, projects: list[tuple[int, str]] | None = None,
                 trackers: list[tuple[int, str]] | None = None,
                 priorities: list[tuple[int, str]] | None = None,
                 statuses: list[tuple[int, str]] | None = None,
                 initial_categories: list[tuple[int, str]] | None = None,
                 redmine_client: RedmineClient | None = None,
                 task_data: dict | None = None,
                 default_project_id: int = 0,
                 members: list[tuple[int, str]] | None = None,
                 current_user_id: int = 0,
                 copy_from_issue_id: int = 0,
                 copy_attachments: list | None = None,
                 copy_subject: str = "",
                 copy_description: str = ""):
        super().__init__(parent)
        self._projects = projects or []
        self._trackers = trackers or []
        self._priorities = priorities or []
        self._statuses = statuses or []
        self._initial_categories = initial_categories or []
        self._redmine = redmine_client
        self._task_data = task_data or {}
        self._is_edit = bool(task_data)
        self._default_project_id = default_project_id or 0
        self._members = members or []
        self._current_user_id = current_user_id
        # Modo copia: alta (no edición) con datos y adjuntos propuestos del origen.
        self._copy_mode = bool(copy_from_issue_id)
        self._copy_from_issue_id = copy_from_issue_id
        self._copy_attachments: list = list(copy_attachments) if copy_attachments else []
        self._copy_subject = copy_subject
        self._copy_description = copy_description
        self._pending_files: list[str] = []
        self._upload_tokens: list[dict] = []
        self._pending_checklist_items: list[str] = []  # items en modo creación
        self._temp_checklist_counter: int = -1  # IDs temporales negativos
        # Campos personalizados: valores previos del issue (para poder limpiarlos)
        # y widgets construidos dinámicamente por proyecto.
        self._initial_custom_fields: dict[int, Any] = {}
        self._custom_field_widgets: dict[int, dict] = {}
        if task_data:
            raw_cf = task_data.get("custom_fields") or task_data.get("_custom_fields") or {}
            self._initial_custom_fields = {
                int(k): v for k, v in raw_cf.items()
            } if isinstance(raw_cf, dict) else {}

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
            self._load_attachments()
        elif self._copy_mode:
            # En modo copia se muestran los adjuntos origen como propuesta.
            self._load_attachments()

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
        self._update_completer_model(self._project_combo)
        self._project_combo.currentIndexChanged.connect(self._on_project_changed)
        basic_form.addRow("Proyecto:", self._project_combo)

        # Tracker (buscable)
        self._tracker_combo = self._make_searchable_combo()
        for tid, tname in self._trackers:
            self._tracker_combo.addItem(tname, tid)
        self._update_completer_model(self._tracker_combo)
        self._tracker_combo.setEnabled(True)  # Asegurar editable en ambos modos
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
        # Configurar autocompletado @usuario en descripción
        if self._members:
            from app.widgets.comments_widget import setup_mention_completer
            names = [name for _, name in self._members]
            self._description_completer = setup_mention_completer(self._description_edit, names)

        scroll_layout.addWidget(basic_group)

        # --- Grupo: Detalles ---
        details_group = QGroupBox("Detalles")
        details_form = QFormLayout(details_group)
        details_form.setSpacing(6)

        # Estado (solo edición)
        if self._is_edit:
            self._status_combo = QComboBox()
            for sid, sname in self._statuses:
                self._status_combo.addItem(sname, sid)
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
        self._update_completer_model(self._prior_combo)
        details_form.addRow("Prioridad:", self._prior_combo)

        # Asignado a (buscable, visible en creación y edición)
        self._assigned_combo = self._make_searchable_combo()
        self._populate_members(self._members)
        details_form.addRow("Asignado a:", self._assigned_combo)

        # Categoría (buscable, carga dinámica)
        self._cat_combo = self._make_searchable_combo()
        self._populate_categories(self._initial_categories)
        details_form.addRow("Categoría:", self._cat_combo)

        # Fecha de inicio
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDisplayFormat("dd/MM/yyyy")
        self._date_edit.setDate(date.today())
        details_form.addRow("Fecha inicio:", self._date_edit)

        # Fecha de fin
        due_widget = QWidget()
        due_layout = QHBoxLayout(due_widget)
        due_layout.setContentsMargins(0, 0, 0, 0)
        due_layout.setSpacing(4)
        self._due_check = QCheckBox("Fecha fin:")
        self._due_check.toggled.connect(self._on_due_check_toggled)
        due_layout.addWidget(self._due_check)
        self._due_edit = QDateEdit()
        self._due_edit.setCalendarPopup(True)
        self._due_edit.setDisplayFormat("dd/MM/yyyy")
        self._due_edit.setDate(date.today())
        self._due_edit.setEnabled(False)
        due_layout.addWidget(self._due_edit)
        details_form.addRow("", due_widget)

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
        # En modo edición se oculta hasta que _load_checklists confirme que hay items;
        # en modo creación se muestra siempre.
        if self._is_edit:
            self._checklist_group.setVisible(False)
        scroll_layout.addWidget(self._checklist_group)

        # --- Grupo: Campos personalizados ---
        # Se inserta entre Checklist y Comentarios; oculto hasta cargar campos.
        self._custom_fields_group = QGroupBox("Campos personalizados")
        self._custom_fields_form = QFormLayout(self._custom_fields_group)
        self._custom_fields_form.setSpacing(6)
        self._custom_fields_group.setVisible(False)
        scroll_layout.addWidget(self._custom_fields_group)

        # --- Grupo: Comentarios ---
        self._comments_group = QGroupBox("Comentarios")
        comments_layout = QVBoxLayout(self._comments_group)
        self._comments_widget = CommentsWidget()
        if self._members:
            self._comments_widget.set_members(self._members)
        comments_layout.addWidget(self._comments_widget)
        self._comments_group.setVisible(False)  # Oculto en nueva tarea
        scroll_layout.addWidget(self._comments_group)

        # --- Grupo: Documentos adjuntos ---
        self._attachments_group = QGroupBox("Documentos adjuntos")
        self._attachments_layout = QVBoxLayout(self._attachments_group)
        self._attachments_layout.setSpacing(4)
        self._attachments_group.setVisible(False)  # Oculto hasta cargar
        scroll_layout.addWidget(self._attachments_group)

        # --- Grupo: Adjuntar archivos ---
        self._upload_group = QGroupBox("Adjuntar archivos")
        upload_layout = QVBoxLayout(self._upload_group)
        upload_layout.setSpacing(4)

        add_file_btn = QPushButton("Añadir archivo...")
        add_file_btn.clicked.connect(self._on_add_file)
        upload_layout.addWidget(add_file_btn)

        self._files_list_layout = QVBoxLayout()
        upload_layout.addLayout(self._files_list_layout)
        self._upload_group.setVisible(True)
        scroll_layout.addWidget(self._upload_group)

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
        """Crea un combo buscable delegando en el helper compartido."""
        return make_searchable_combo()

    @staticmethod
    def _update_completer_model(combo: QComboBox):
        """Sincroniza el modelo del QCompleter delegando en el helper compartido."""
        update_completer_model(combo)

    # ================================================================
    # Population
    # ================================================================

    def _populate_fields(self):
        if not self._is_edit:
            if self._default_project_id:
                self._set_combo_data(self._project_combo, self._default_project_id)
                self._on_project_changed()
            if self._copy_mode:
                self._subject_edit.setText(self._copy_subject)
                self._description_edit.setPlainText(self._copy_description)
            if self._members:
                self._populate_members(self._members)
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

        # Estado
        if hasattr(self, '_status_combo'):
            sid = self._task_data.get("status_id", 0)
            self._set_combo_data(self._status_combo, sid)

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

        # Fecha fin
        due_str = self._task_data.get("due_date", "")
        if due_str:
            try:
                d = date.fromisoformat(due_str)
                self._due_edit.setDate(d)
                self._due_check.setChecked(True)
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

        # Asignado a
        assigned_id = self._task_data.get("assigned_to_id", 0)
        if assigned_id:
            self._set_combo_data(self._assigned_combo, assigned_id)

        # Cargar categorías y campos personalizados del proyecto
        if self._redmine and pid:
            self._load_categories_for_project(pid)
            self._load_custom_fields_for_project(pid)

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
            self._load_members_for_project(project_id)
            self._load_custom_fields_for_project(project_id)

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
        self._update_completer_model(self._cat_combo)
        self._cat_combo.blockSignals(False)

        # Si hay categoría pendiente, seleccionarla
        if hasattr(self, '_pending_category_id') and self._pending_category_id:
            self._set_combo_data(self._cat_combo, self._pending_category_id)
            self._pending_category_id = 0

    # ================================================================
    # Miembros (Asignado a)
    # ================================================================

    def _populate_members(self, members: list[tuple[int, str]]):
        self._assigned_combo.blockSignals(True)
        self._assigned_combo.clear()
        self._assigned_combo.addItem("(Sin asignar)", 0)
        names = ["(Sin asignar)"]

        # Ordenar miembros: usuario actual primero, resto alfabéticamente
        current_user = None
        other_members: list[tuple[int, str]] = []
        for mid, mname in members:
            if mid == self._current_user_id and self._current_user_id:
                current_user = (mid, mname)
            else:
                other_members.append((mid, mname))
        # Ordenar el resto alfabéticamente
        other_members.sort(key=lambda x: x[1].lower())

        # Añadir usuario actual primero si es miembro
        if current_user:
            self._assigned_combo.addItem(current_user[1], current_user[0])
            names.append(current_user[1])

        for mid, mname in other_members:
            self._assigned_combo.addItem(mname, mid)
            names.append(mname)
        self._update_completer_model(self._assigned_combo)
        self._assigned_combo.blockSignals(False)

    def _load_members_for_project(self, project_id: int):
        try:
            mbs = self._redmine.get_project_memberships(project_id)
            members = [(m.user_id, m.user_name) for m in mbs if m.user_id]
            self._populate_members(members)
        except Exception:
            self._populate_members([])

    # ================================================================
    # Campos personalizados
    # ================================================================

    def _load_custom_fields_for_project(self, project_id: int):
        """Carga los campos personalizados del proyecto y construye sus widgets.

        Oculta el grupo si el proyecto no tiene campos o si la carga falla.
        """
        self._clear_custom_fields()
        if not project_id or not self._redmine:
            self._custom_fields_group.setVisible(False)
            return
        try:
            fields = self._redmine.get_project_custom_fields(project_id)
        except Exception:
            # Si falla la carga, ocultar la sección sin romper el diálogo
            self._custom_fields_group.setVisible(False)
            return
        if not fields:
            self._custom_fields_group.setVisible(False)
            return
        for field_def in fields:
            self._add_custom_field_widget(field_def)
        self._apply_custom_field_values()
        self._custom_fields_group.setVisible(True)

    def _clear_custom_fields(self):
        """Elimina los widgets de campos personalizados construidos."""
        while self._custom_fields_form.rowCount():
            self._custom_fields_form.removeRow(0)
        self._custom_field_widgets.clear()

    def _add_custom_field_widget(self, field_def):
        """Construye el widget de un campo según su field_format y lo añade al form."""
        label = field_def.name + (" *" if field_def.is_required else "")
        widget, kind, extra = self._build_custom_field_widget(field_def)
        if extra is not None:
            container = QWidget()
            h_layout = QHBoxLayout(container)
            h_layout.setContentsMargins(0, 0, 0, 0)
            h_layout.setSpacing(4)
            h_layout.addWidget(widget)
            h_layout.addWidget(extra)
            h_layout.addStretch()
            self._custom_fields_form.addRow(label + ":", container)
        else:
            self._custom_fields_form.addRow(label + ":", widget)
        self._custom_field_widgets[field_def.id] = {
            "field": field_def,
            "kind": kind,
            "widget": widget,
            "extra": extra,
        }

    def _build_custom_field_widget(self, field_def):
        """Crea el control de edición según field_format.

        Returns:
            (widget, kind, extra): kind identifica el tipo para serializar;
            extra es un widget adicional (p. ej. checkbox de fecha) o None.
        """
        fmt = field_def.field_format
        # Campo de valor múltiple: multiselección sobre possible_values
        if field_def.multiple:
            list_widget = QListWidget()
            list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
            for value in field_def.possible_values or []:
                list_widget.addItem(str(value))
            list_widget.setMaximumHeight(100)
            return list_widget, "multiple", None

        if fmt == "string":
            return QLineEdit(), "string", None
        if fmt == "text":
            edit = QPlainTextEdit()
            edit.setMaximumHeight(80)
            return edit, "text", None
        if fmt == "int":
            spin = QSpinBox()
            spin.setRange(-2147483648, 2147483647)
            spin.setSpecialValueText("")  # 0 se muestra como vacío
            return spin, "int", None
        if fmt == "float":
            dspin = QDoubleSpinBox()
            dspin.setRange(-1e12, 1e12)
            dspin.setDecimals(4)
            dspin.setSpecialValueText("")  # 0.0 se muestra como vacío
            return dspin, "float", None
        if fmt == "date":
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("yyyy-MM-dd")
            date_edit.setDate(date.today())
            check = QCheckBox("Sin valor")
            check.setChecked(True)
            date_edit.setEnabled(False)
            check.toggled.connect(lambda checked: date_edit.setEnabled(not checked))
            return date_edit, "date", check
        if fmt == "bool":
            return QCheckBox(), "bool", None
        if fmt == "list":
            combo = QComboBox()
            combo.addItem("", "")  # opción vacía para poder limpiar
            for value in field_def.possible_values or []:
                combo.addItem(str(value), str(value))
            return combo, "list", None
        # Formato no contemplado: fallback a texto libre
        return QLineEdit(), "string", None

    def _apply_custom_field_values(self):
        """Aplica el valor previo del issue o el default_value a cada widget."""
        for cf_id, entry in self._custom_field_widgets.items():
            previous = self._initial_custom_fields.get(cf_id)
            # Un campo "tenía valor previo" aunque sea 0/0.0: distinguirlo de "sin valor".
            had_value = previous is not None and previous != "" and previous != []
            entry["had_value"] = had_value
            if had_value:
                self._set_custom_field_value(entry, previous)
            elif entry["field"].default_value not in (None, ""):
                self._set_custom_field_value(entry, entry["field"].default_value)

    def _set_custom_field_value(self, entry: dict, value):
        """Asigna un valor (del issue o default) al widget de un campo."""
        kind = entry["kind"]
        widget = entry["widget"]
        if kind == "bool":
            widget.setChecked(str(value).lower() in ("1", "true", "yes"))
        elif kind == "date":
            check = entry["extra"]
            try:
                d = date.fromisoformat(str(value)[:10])
                widget.setDate(d)
                check.setChecked(False)
            except (ValueError, TypeError):
                check.setChecked(True)
        elif kind == "int":
            try:
                widget.setValue(int(value))
            except (ValueError, TypeError):
                widget.setValue(0)
        elif kind == "float":
            try:
                widget.setValue(float(value))
            except (ValueError, TypeError):
                widget.setValue(0.0)
        elif kind == "list":
            idx = widget.findData(str(value))
            if idx >= 0:
                widget.setCurrentIndex(idx)
        elif kind == "multiple":
            selected = value if isinstance(value, list) else [value]
            selected_strs = {str(v) for v in selected}
            for i in range(widget.count()):
                if widget.item(i).text() in selected_strs:
                    widget.item(i).setSelected(True)
        else:  # string / text
            if kind == "text":
                widget.setPlainText(str(value))
            else:
                widget.setText(str(value))

    def _read_custom_field_value(self, entry: dict, had_value: bool = False):
        """Serializa el valor actual del widget según su tipo.

        had_value indica que el campo ya tenía valor previo en el issue: en ese
        caso un 0/0.0 numérico se serializa como "0"/"0.0" en lugar de "".
        """
        kind = entry["kind"]
        widget = entry["widget"]
        if kind == "bool":
            if widget.isChecked():
                return "1"
            # Sin marcar: "0" solo si tenía valor previo o es obligatorio;
            # en caso contrario se omite (D7: vacíos sin valor previo no se envían).
            if had_value or entry["field"].is_required:
                return "0"
            return ""
        if kind == "date":
            check = entry["extra"]
            if check.isChecked():
                return ""
            return widget.date().toString("yyyy-MM-dd")
        if kind == "int":
            return "" if widget.value() == 0 and not had_value else str(widget.value())
        if kind == "float":
            return "" if widget.value() == 0.0 and not had_value else str(widget.value())
        if kind == "list":
            return widget.currentData() or ""
        if kind == "multiple":
            return [widget.item(i).text() for i in range(widget.count())
                    if widget.item(i).isSelected()]
        if kind == "text":
            return widget.toPlainText().strip()
        return widget.text().strip()

    @property
    def custom_fields(self) -> dict[int, Any]:
        """Devuelve los valores de los campos personalizados listos para la API.

        Incluye con "" (o []) los campos que el issue ya tenía y el usuario ha
        vaciado, para permitir limpiarlos; omite los vacíos sin valor previo.
        """
        result: dict[int, Any] = {}
        for cf_id, entry in self._custom_field_widgets.items():
            had_value = entry.get("had_value", False)
            value = self._read_custom_field_value(entry, had_value)
            if value == "" or value == []:
                if had_value:
                    result[cf_id] = [] if entry["kind"] == "multiple" else ""
                continue
            result[cf_id] = value
        return result

    # ================================================================
    # Subida de archivos
    # ================================================================

    def _on_add_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos para adjuntar")
        for f in files:
            if f not in self._pending_files:
                self._pending_files.append(f)
                self._add_file_row(f)

    def _add_file_row(self, file_path: str):
        import os
        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet(
            "QFrame { background: palette(alternate-base); border-radius: 4px; padding: 4px; }"
        )
        f_layout = QHBoxLayout(frame)
        f_layout.setContentsMargins(6, 4, 6, 4)
        f_layout.setSpacing(8)

        info = QLabel(f"<b>{filename}</b>  <span style='color: gray;'>({self._format_filesize(size)})</span>")
        info.setStyleSheet("background: transparent;")
        f_layout.addWidget(info, 1)

        frame.setProperty("file_path", file_path)
        remove_btn = QPushButton("Eliminar")
        remove_btn.setFixedWidth(80)
        remove_btn.clicked.connect(lambda checked, p=file_path: self._on_remove_file(p))
        f_layout.addWidget(remove_btn)

        self._files_list_layout.addWidget(frame)

    def _on_remove_file(self, file_path: str):
        if file_path in self._pending_files:
            self._pending_files.remove(file_path)
        for i in range(self._files_list_layout.count()):
            widget = self._files_list_layout.itemAt(i).widget()
            if widget and widget.property("file_path") == file_path:
                widget.deleteLater()
                break

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
        # En modo creación, los items aún no existen en Redmine; revertir toggle
        if not self._is_edit:
            self._checklist_widget.set_item_checked(item_id, not checked)
            return
        if self._redmine:
            try:
                self._redmine.update_checklist_item(item_id, is_done=1 if checked else 0)
            except Exception:
                pass  # Silencioso, el usuario ya ve el toggle

    def _on_checklist_item_added(self, subject: str):
        if not self._is_edit:
            # Modo creación: almacenar pendiente y añadir widget con ID temporal
            self._pending_checklist_items.append(subject)
            self._checklist_widget.add_item_widget(
                self._temp_checklist_counter, subject, False
            )
            self._temp_checklist_counter -= 1
            return

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
        if not self._is_edit:
            # Modo creación: eliminar de la lista pendiente y del widget
            if item_id < 0:
                idx = -(item_id + 1)
                if 0 <= idx < len(self._pending_checklist_items):
                    self._pending_checklist_items.pop(idx)
            self._checklist_widget.remove_item_widget(item_id)
            return

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

    # ================================================================
    # Adjuntos
    # ================================================================

    def _load_attachments(self):
        """Carga los adjuntos desde task_data (o la propuesta en modo copia)."""
        if self._copy_mode:
            attachments = self._copy_attachments
        else:
            attachments = self._task_data.get("attachments", [])
        # Limpiar adjuntos anteriores
        while self._attachments_layout.count():
            item = self._attachments_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not attachments:
            no_att = QLabel("(Sin adjuntos)")
            no_att.setStyleSheet("color: palette(mid); font-style: italic;")
            self._attachments_layout.addWidget(no_att)
        else:
            for att in attachments:
                frame = QFrame()
                frame.setFrameShape(QFrame.Shape.StyledPanel)
                frame.setStyleSheet("QFrame { background: palette(alternate-base); border-radius: 4px; padding: 4px; }")
                f_layout = QHBoxLayout(frame)
                f_layout.setContentsMargins(6, 4, 6, 4)
                f_layout.setSpacing(8)

                # Info del adjunto
                filename = self._attachment_get(att, "filename", "sin_nombre")
                filesize = self._attachment_get(att, "filesize", 0)
                created_on = self._attachment_get(att, "created_on", "")

                size_str = self._format_filesize(filesize)
                info = QLabel(f"<b>{filename}</b><br><span style='color: gray;'>{size_str} — {created_on}</span>")
                info.setStyleSheet("background: transparent;")
                f_layout.addWidget(info, 1)

                # Boton descargar
                download_btn = QPushButton("Descargar")
                download_btn.setFixedWidth(90)
                download_btn.clicked.connect(lambda checked, a=att: self._on_download_attachment(a))
                f_layout.addWidget(download_btn)

                # Boton eliminar (en modo copia: quitar de la propuesta, sin borrar)
                attachment_id = self._attachment_get(att, "id", 0)
                frame.setProperty("attachment_id", attachment_id)
                delete_btn = QPushButton("−")
                delete_btn.setFixedWidth(30)
                if self._copy_mode:
                    delete_btn.setToolTip("Quitar de la propuesta")
                    delete_btn.clicked.connect(
                        lambda checked, aid=attachment_id:
                        self._on_remove_proposed_attachment(aid)
                    )
                else:
                    delete_btn.setToolTip("Eliminar adjunto")
                    delete_btn.clicked.connect(
                        lambda checked, aid=attachment_id, fn=filename:
                        self._on_delete_attachment(aid, fn)
                    )
                f_layout.addWidget(delete_btn)

                self._attachments_layout.addWidget(frame)

        self._attachments_group.setVisible(True)

    def _on_download_attachment(self, attachment):
        """Abre dialogo Guardar como y descarga el adjunto."""
        filename = self._attachment_get(attachment, "filename", "archivo")
        content_url = self._attachment_get(attachment, "content_url", "")

        if not content_url:
            QMessageBox.warning(self, "Error", "No se encontró la URL de descarga del adjunto.")
            return

        dest_path, _ = QFileDialog.getSaveFileName(self, "Guardar adjunto", filename)
        if not dest_path:
            return  # Usuario canceló

        try:
            self._redmine.download_attachment(content_url, dest_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo descargar el adjunto:\n{str(e)}")

    def _on_delete_attachment(self, attachment_id: int, filename: str):
        """Elimina un adjunto previa confirmacion del usuario."""
        if not self._redmine:
            return

        reply = QMessageBox.question(
            self,
            "Eliminar adjunto",
            f"¿Eliminar permanentemente {filename}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._redmine.delete_attachment(attachment_id):
            # Eliminar el widget de la lista visual (buscando por propiedad)
            for i in range(self._attachments_layout.count()):
                widget = self._attachments_layout.itemAt(i).widget()
                if widget and widget.property("attachment_id") == attachment_id:
                    widget.deleteLater()
                    break
        else:
            QMessageBox.warning(
                self, "Error",
                f"No se pudo eliminar el adjunto '{filename}'.\n"
                f"Es posible que el servidor Redmine no soporte esta operación."
            )

    def _on_remove_proposed_attachment(self, attachment_id: int):
        """Quita un adjunto de la propuesta de copia SIN tocar el servidor.

        Nunca llama a delete_attachment: solo elimina el widget y la entrada de
        la lista de propuesta.
        """
        # S3: un id 0 (improbable) no debe eliminar toda la propuesta por filtrado.
        if attachment_id == 0:
            return
        self._copy_attachments = [
            att for att in self._copy_attachments
            if self._attachment_get(att, "id", 0) != attachment_id
        ]
        for i in range(self._attachments_layout.count()):
            widget = self._attachments_layout.itemAt(i).widget()
            if widget and widget.property("attachment_id") == attachment_id:
                widget.deleteLater()
                break

    @staticmethod
    def _attachment_get(att, key: str, default=""):
        """Obtiene un valor de un adjunto, ya sea dict u objeto."""
        if hasattr(att, key):
            return getattr(att, key, default)
        elif hasattr(att, "get"):
            return att.get(key, default)
        return default

    @staticmethod
    def _format_filesize(size_bytes: int) -> str:
        """Formatea bytes a KB o MB legible."""
        if size_bytes >= 1048576:
            return f"{size_bytes / 1048576:.1f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes > 0:
            return f"{size_bytes} B"
        return ""

    # ================================================================
    # Fecha fin - toggle checkbox
    # ================================================================

    def _on_due_check_toggled(self, checked: bool):
        self._due_edit.setEnabled(checked)
        if not checked:
            self._due_edit.setDate(date.today())

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

        self._upload_tokens = []
        if self._pending_files and self._redmine:
            for file_path in self._pending_files:
                try:
                    result = self._redmine.upload_file(file_path)
                    token = result.get("upload", {}).get("token", "")
                    if token:
                        import os
                        import mimetypes
                        filename = os.path.basename(file_path)
                        content_type, _ = mimetypes.guess_type(filename)
                        self._upload_tokens.append({
                            "token": token,
                            "filename": filename,
                            "content_type": content_type or "application/octet-stream",
                        })
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error al subir archivo",
                        f"No se pudo subir el archivo:\n{str(e)}"
                    )
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
    def description_raw(self) -> str:
        """Texto crudo de la descripción, sin strip (flujo de copia)."""
        return self._description_edit.toPlainText()

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
    def due_date(self) -> str:
        return self._due_edit.date().toString("yyyy-MM-dd")

    @property
    def due_enabled(self) -> bool:
        return self._due_check.isChecked()

    @property
    def done_ratio(self) -> int:
        return self._progress_spin.value()

    @property
    def status_id(self) -> int:
        if hasattr(self, '_status_combo'):
            return self._status_combo.currentData() or 0
        return 0

    @property
    def assigned_to_id(self) -> int:
        return self._assigned_combo.currentData() or 0

    @property
    def upload_tokens(self) -> list[dict]:
        return self._upload_tokens

    @property
    def pending_checklist_items(self) -> list[str]:
        """Devuelve los items de checklist pendientes de crear (solo modo nueva tarea)."""
        return list(self._pending_checklist_items)

    @property
    def proposed_attachments(self) -> list:
        """Adjuntos que quedan en la propuesta de copia (modo copia)."""
        return list(self._copy_attachments)

    @property
    def pending_comment(self) -> str:
        """Devuelve el comentario pendiente escrito en el diálogo (vacío si no hay)."""
        return self._comments_widget.pending_comment()
