from datetime import date

from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QDate, QEvent, QRect
from PyQt6.QtGui import QBrush, QColor, QPainter, QPalette, QPen
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyle, QApplication, QMenu, QDateEdit,
    QStyledItemDelegate, QStyleOptionViewItem,
)

from app.utils.dates import iso_to_display, iso_datetime_to_display


class DateSortItem(QTableWidgetItem):
    """QTableWidgetItem que ordena fechas cronológicamente usando ISO.

    Almacena la fecha ISO en UserRole para comparación y muestra
    el texto formateado (DD/MM/YY HH:MM) como display.
    """

    ISO_ROLE = Qt.ItemDataRole.UserRole + 100

    def __init__(self, iso_str: str, display_text: str):
        super().__init__(display_text)
        if iso_str:
            self.setData(self.ISO_ROLE, iso_str)

    def __lt__(self, other: QTableWidgetItem) -> bool:
        self_iso = self.data(self.ISO_ROLE)
        other_iso = other.data(self.ISO_ROLE)
        if self_iso is not None and other_iso is not None:
            return str(self_iso) < str(other_iso)
        # Fallback a comparación de texto si no hay ISO
        return super().__lt__(other)


class ProgressBarDelegate(QStyledItemDelegate):
    """Pinta la barra de progreso de la columna "Progreso %".

    El porcentaje es dato puro del modelo (entero en DisplayRole), de modo que
    la barra sigue siempre a su fila aunque la tabla se ordene o recargue.
    Respeta el fondo/foreground de prioridad establecidos en el item.
    """

    CHUNK_DONE = QColor("#2e7d32")      # 100 %
    CHUNK_PARTIAL = QColor("#f57c00")   # 1-99 %
    CHUNK_EMPTY = QColor("#bdbdbd")     # 0 %
    CHUNK_PRIORITY = QColor("#ff9800")  # fila de prioridad alta

    @staticmethod
    def _progress_value(index) -> int:
        value = index.data(Qt.ItemDataRole.DisplayRole)
        try:
            value = int(value)
        except (TypeError, ValueError):
            return 0
        return max(0, min(100, value))

    @staticmethod
    def _priority_background(index) -> QColor | None:
        data = index.data(Qt.ItemDataRole.BackgroundRole)
        if isinstance(data, QBrush):
            color = data.color()
        elif isinstance(data, QColor):
            color = data
        else:
            return None
        return color if color.isValid() else None

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        value = self._progress_value(index)
        priority_bg = self._priority_background(index)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        cell_rect = option.rect
        if priority_bg is not None:
            painter.fillRect(cell_rect, priority_bg)
        else:
            bg_brush = option.backgroundBrush
            if bg_brush.style() == Qt.BrushStyle.NoBrush:
                bg_brush = option.palette.brush(QPalette.ColorRole.Base)
            painter.fillRect(cell_rect, bg_brush)

        bar_rect = cell_rect.adjusted(4, 5, -4, -5)
        if bar_rect.width() > 0 and bar_rect.height() > 0:
            if priority_bg is not None or value > 0:
                track_color = QColor("#ffffff")
            else:
                # A 0 % se muestra la barra en gris
                track_color = self.CHUNK_EMPTY

            painter.setPen(QPen(QColor("#555555")))
            painter.setBrush(QBrush(track_color))
            painter.drawRoundedRect(bar_rect, 2, 2)

            if value > 0:
                if priority_bg is not None:
                    chunk_color = self.CHUNK_PRIORITY
                elif value == 100:
                    chunk_color = self.CHUNK_DONE
                else:
                    chunk_color = self.CHUNK_PARTIAL
                chunk_width = int(bar_rect.width() * value / 100)
                if chunk_width >= 2:
                    chunk_rect = QRect(
                        bar_rect.x() + 1,
                        bar_rect.y() + 1,
                        chunk_width - 2,
                        bar_rect.height() - 2,
                    )
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(chunk_color))
                    painter.drawRoundedRect(chunk_rect, 1, 1)

        text = f"{value}%"
        if priority_bg is not None:
            painter.setPen(QColor("white"))
        else:
            painter.setPen(option.palette.color(QPalette.ColorRole.Text))
        painter.drawText(cell_rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()


class TaskTable(QTableWidget):
    tarea_doble_click = pyqtSignal(int)
    tarea_abrir_url = pyqtSignal(int, str)
    tarea_mover_proyecto = pyqtSignal(int)  # issue_id a copiar/mover de proyecto
    cambio_rapido = pyqtSignal(int, str, int)  # issue_id, tipo, valor
    due_date_cambiada = pyqtSignal(int, str)  # issue_id, due_date
    columnas_cambiadas = pyqtSignal()  # visibilidad de columnas modificada

    COL_ID = 0
    COL_TRACKER = 1
    COL_PROJECT = 2
    COL_TITLE = 3
    COL_START_DATE = 4
    COL_DUE_DATE = 5
    COL_PRIORITY = 6
    COL_STATUS = 7
    COL_ASSIGNED_TO = 8
    COL_CATEGORY = 9
    COL_PROGRESS = 10
    COL_URL = 11
    COL_CREATED = 12
    COL_UPDATED = 13

    HEADERS = [
        "ID", "Tracker", "Proyecto", "Título", "Fecha inicio", "Fecha fin",
        "Prioridad", "Estado", "Asignado a", "Categoría", "Progreso %", "",
        "Creado", "Modificado",
    ]

    # Columnas ocultas por defecto
    HIDDEN_BY_DEFAULT = {COL_PROJECT, COL_PRIORITY, COL_CATEGORY}

    # Claves estables para persistir la visibilidad de columnas
    COLUMN_KEYS = {
        COL_ID: "id",
        COL_TRACKER: "tracker",
        COL_PROJECT: "project",
        COL_TITLE: "title",
        COL_START_DATE: "start_date",
        COL_DUE_DATE: "due_date",
        COL_PRIORITY: "priority",
        COL_STATUS: "status",
        COL_ASSIGNED_TO: "assigned_to",
        COL_CATEGORY: "category",
        COL_PROGRESS: "progress",
        COL_URL: "url",
        COL_CREATED: "created",
        COL_UPDATED: "updated",
    }

    # Rol propio donde se guarda el id de la issue de cada fila
    ISSUE_ID_ROLE = Qt.ItemDataRole.UserRole + 1000

    _BG_INMEDIATA = QColor(200, 0, 0)
    _BG_URGENTE = QColor(180, 20, 20)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        self.verticalHeader().setDefaultSectionSize(28)

        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(self.COL_ID, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_TRACKER, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_PROJECT, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_TITLE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_START_DATE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_DUE_DATE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_PRIORITY, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_ASSIGNED_TO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_CATEGORY, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_PROGRESS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_URL, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(self.COL_URL, 40)
        header.setSectionResizeMode(self.COL_CREATED, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_UPDATED, QHeaderView.ResizeMode.ResizeToContents)

        # Ocultar las columnas opcionales por defecto
        for col in self.HIDDEN_BY_DEFAULT:
            self.setColumnHidden(col, True)

        # Menú contextual sobre las cabeceras para mostrar/ocultar columnas
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_column_menu)

        # Barra de progreso pintada por delegate (sin cell widget)
        self._progress_delegate = ProgressBarDelegate(self)
        self.setItemDelegateForColumn(self.COL_PROGRESS, self._progress_delegate)

        self.cellDoubleClicked.connect(self._on_double_click)
        self.cellClicked.connect(self._on_cell_clicked)
        self._issues: list[dict] = []
        self._issues_by_id: dict[int, dict] = {}
        self._statuses: list[tuple[int, str]] = []
        self._current_user_id: int = 0
        self._frequent_people_ids: list[int] = []
        self._editing_issue_id: int | None = None
        self._frequent_people_names: dict[int, str] = {}
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_context_data(self, statuses: list[tuple[int, str]], current_user_id: int,
                         frequent_people_ids: list[int], member_names: dict[int, str]):
        self._statuses = statuses
        self._current_user_id = current_user_id
        self._frequent_people_ids = frequent_people_ids
        self._frequent_people_names = member_names

    # ------------------------------------------------------------------
    # Resolución fila -> issue por ID (invariante ante ordenación)
    # ------------------------------------------------------------------

    def _issue_id_at_row(self, row: int) -> int | None:
        """Devuelve el id de la issue mostrada en la fila, o None."""
        if row < 0 or row >= self.rowCount():
            return None
        item = self.item(row, self.COL_ID)
        if item is None:
            return None
        data = item.data(self.ISSUE_ID_ROLE)
        if data is None:
            return None
        try:
            return int(data)
        except (TypeError, ValueError):
            return None

    def _issue_at_row(self, row: int) -> dict | None:
        """Devuelve el dict de la issue mostrada en la fila, o None."""
        issue_id = self._issue_id_at_row(row)
        if issue_id is None:
            return None
        return self._issues_by_id.get(issue_id)

    def _row_for_issue_id(self, issue_id: int) -> int | None:
        """Localiza la fila actual de una issue por su id."""
        for row in range(self.rowCount()):
            if self._issue_id_at_row(row) == issue_id:
                return row
        return None

    # ------------------------------------------------------------------
    # Estilos
    # ------------------------------------------------------------------

    def _priority_bg(self, priority_name: str) -> QColor | None:
        pname = (priority_name or "").lower().strip()
        if pname in ("inmediata", "immediate"):
            return self._BG_INMEDIATA
        if pname in ("urgente", "urgent"):
            return self._BG_URGENTE
        return None

    def _apply_issue_style(self, item: QTableWidgetItem, issue: dict) -> QTableWidgetItem:
        """Guarda el id de la issue en el item y aplica el resaltado de prioridad."""
        item.setData(self.ISSUE_ID_ROLE, int(issue["id"]))
        bg_color = self._priority_bg(issue.get("priority_name", ""))
        if bg_color:
            item.setBackground(bg_color)
            item.setForeground(Qt.GlobalColor.white)
        return item

    # ------------------------------------------------------------------
    # Edición inline de fecha
    # ------------------------------------------------------------------

    def _on_double_click(self, row: int, col: int):
        issue = self._issue_at_row(row)
        if issue is None:
            return
        if col == self.COL_URL:
            # La URL se abre con un clic simple; el doble clic no abre la tarea
            return
        if col == self.COL_DUE_DATE:
            due_str = issue.get("due_date", "")
            d = date.today()
            if due_str:
                try:
                    d = date.fromisoformat(due_str)
                except (ValueError, TypeError):
                    pass
            date_edit = QDateEdit(QDate(d.year, d.month, d.day))
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("dd/MM/yyyy")
            date_edit.installEventFilter(self)
            self._editing_issue_id = int(issue["id"])
            self.setCellWidget(row, self.COL_DUE_DATE, date_edit)
            date_edit.setFocus()
            date_edit.show()
        else:
            self.tarea_doble_click.emit(int(issue["id"]))

    def _on_cell_clicked(self, row: int, col: int):
        """Abre la URL en Redmine al hacer clic en la columna URL."""
        if col != self.COL_URL:
            return
        issue = self._issue_at_row(row)
        if issue is None:
            return
        url = self._build_issue_url(issue.get("url", ""))
        if not url:
            return
        self.tarea_abrir_url.emit(int(issue["id"]), url)

    def eventFilter(self, obj, event):
        """Maneja Escape (cancelar), Enter (confirmar) y pérdida de foco del QDateEdit inline."""
        if isinstance(obj, QDateEdit):
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Escape:
                    self._cancel_due_date_edit()
                    return True
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self._commit_due_date_edit()
                    return True
            elif event.type() == QEvent.Type.FocusOut:
                # Si el foco NO va al calendar popup (hijo del QDateEdit), hacer commit
                new_focus = QApplication.focusWidget()
                if new_focus is None or not self._is_descendant_of(obj, new_focus):
                    # Pequeño delay para permitir que el popup tome el foco
                    QApplication.instance().processEvents()
                    new_focus = QApplication.focusWidget()
                    if new_focus is None or not self._is_descendant_of(obj, new_focus):
                        self._commit_due_date_edit()
        return super().eventFilter(obj, event)

    @staticmethod
    def _is_descendant_of(parent, child) -> bool:
        """Comprueba si child es descendiente de parent en la jerarquía de widgets."""
        w = child
        while w is not None:
            if w is parent:
                return True
            w = w.parent()
        return False

    def _commit_due_date_edit(self):
        """Confirma la edición inline de fecha y cierra el editor."""
        if self._editing_issue_id is None:
            return
        issue_id = self._editing_issue_id
        row = self._row_for_issue_id(issue_id)
        date_edit = self.cellWidget(row, self.COL_DUE_DATE) if row is not None else None
        if not isinstance(date_edit, QDateEdit):
            self._editing_issue_id = None
            return
        self._editing_issue_id = None
        self._on_due_date_edited(row, date_edit)

    def _cancel_due_date_edit(self):
        """Cancela la edición inline restaurando la fecha original."""
        if self._editing_issue_id is None:
            return
        issue_id = self._editing_issue_id
        self._editing_issue_id = None
        row = self._row_for_issue_id(issue_id)
        if row is None:
            return
        self.removeCellWidget(row, self.COL_DUE_DATE)
        issue = self._issue_at_row(row)
        if issue is None:
            return
        old_due = issue.get("due_date", "")
        due_item = DateSortItem(old_due, iso_to_display(old_due))
        due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(due_item, issue)
        self.setItem(row, self.COL_DUE_DATE, due_item)

    def _on_due_date_edited(self, row: int, date_edit: QDateEdit):
        issue = self._issue_at_row(row)
        if issue is None:
            return
        issue_id = int(issue["id"])
        new_due_iso = date_edit.date().toString("yyyy-MM-dd") if date_edit.date().isValid() else ""
        self.removeCellWidget(row, self.COL_DUE_DATE)
        issue["due_date"] = new_due_iso
        due_item = DateSortItem(new_due_iso, iso_to_display(new_due_iso))
        due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(due_item, issue)
        self.setItem(row, self.COL_DUE_DATE, due_item)
        self.due_date_cambiada.emit(issue_id, new_due_iso)

    def refresh_due_date_cell(self, issue_id: int, due_date: str):
        """Actualiza la celda de fecha fin para un issue (usado tras menú contextual)."""
        issue = self._issues_by_id.get(int(issue_id))
        if issue is None:
            return
        issue["due_date"] = due_date
        row = self._row_for_issue_id(int(issue_id))
        if row is None:
            return
        due_item = DateSortItem(due_date, iso_to_display(due_date))
        due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(due_item, issue)
        self.removeCellWidget(row, self.COL_DUE_DATE)
        self.setItem(row, self.COL_DUE_DATE, due_item)

    # ------------------------------------------------------------------
    # Menú de columnas
    # ------------------------------------------------------------------

    def _show_column_menu(self, pos: QPoint):
        """Muestra el menú contextual de cabeceras para mostrar/ocultar columnas."""
        menu = QMenu(self)
        for col in range(self.columnCount()):
            label = self._column_label(col)
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(not self.isColumnHidden(col))
            action.triggered.connect(lambda checked, c=col: self._toggle_column(c, checked))
        menu.exec(self.horizontalHeader().viewport().mapToGlobal(pos))

    def _column_label(self, col: int) -> str:
        if col == self.COL_URL:
            return "Abrir en Redmine"
        return self.HEADERS[col]

    def _toggle_column(self, col: int, visible: bool):
        self.setColumnHidden(col, not visible)
        self.columnas_cambiadas.emit()

    def visible_column_keys(self) -> list[str]:
        """Devuelve las claves de las columnas visibles en este momento."""
        return [
            self.COLUMN_KEYS[col]
            for col in range(self.columnCount())
            if not self.isColumnHidden(col)
        ]

    def apply_visible_column_keys(self, keys: list[str]):
        """Aplica la visibilidad de columnas desde una lista de claves persistidas."""
        keyset = set(keys or [])
        for col in range(self.columnCount()):
            self.setColumnHidden(col, self.COLUMN_KEYS.get(col) not in keyset)

    # ------------------------------------------------------------------
    # Menú contextual de fila
    # ------------------------------------------------------------------

    def _show_context_menu(self, pos: QPoint):
        row = self.rowAt(pos.y())
        col = self.columnAt(pos.x())
        issue = self._issue_at_row(row)
        if issue is None:
            return
        issue_id = int(issue["id"])
        issue_url = issue.get("url", "")

        if col == self.COL_PROGRESS:
            self._show_progress_menu(pos, issue_id, issue.get("done_ratio", 0), issue_url)
        elif col == self.COL_ASSIGNED_TO:
            self._show_assign_menu(pos, issue_id, issue_url)
        elif col == self.COL_STATUS:
            self._show_status_menu(pos, issue_id, issue.get("status_id", 0), issue_url)
        elif col == self.COL_DUE_DATE:
            self._show_due_date_menu(pos, issue_id, issue.get("due_date", ""), issue_url)
        else:
            # Generic context menu
            menu = QMenu(self)
            self._add_copy_url_action(menu, issue_url)
            menu.addSeparator()
            action_move = menu.addAction("Mover a otro proyecto...")
            action_move.triggered.connect(
                lambda checked, iid=issue_id: self.tarea_mover_proyecto.emit(iid)
            )
            action_open = menu.addAction("Abrir en Redmine")
            action_open.triggered.connect(lambda checked, iid=issue_id, url=issue_url:
                                           self.tarea_abrir_url.emit(iid, url))
            menu.exec(self.viewport().mapToGlobal(pos))
            return

    @staticmethod
    def _build_issue_url(issue_url: str | None) -> str:
        """Devuelve la URL limpia, o cadena vacía si no hay."""
        return (issue_url or "").strip()

    def _add_copy_url_action(self, menu: QMenu, issue_url: str):
        """Añade acción 'Copiar URL' al menú contextual."""
        url = self._build_issue_url(issue_url)
        action_copy = menu.addAction("Copiar URL")
        if not url:
            action_copy.setEnabled(False)
        else:
            action_copy.triggered.connect(lambda checked, u=url: QApplication.clipboard().setText(u))

    def _show_progress_menu(self, pos: QPoint, issue_id: int, current: int, issue_url: str):
        menu = QMenu(self)
        for pct in (0, 20, 40, 60, 80, 100):
            action = menu.addAction(f"{pct}%")
            action.setCheckable(True)
            if pct == current:
                action.setChecked(True)
            action.triggered.connect(lambda checked, v=pct: self.cambio_rapido.emit(issue_id, "progreso", v))
        menu.addSeparator()
        self._add_copy_url_action(menu, issue_url)
        action_open = menu.addAction("Abrir en Redmine")
        action_open.triggered.connect(lambda checked, iid=issue_id, url=issue_url: self.tarea_abrir_url.emit(iid, url))
        menu.exec(self.viewport().mapToGlobal(pos))

    def _show_due_date_menu(self, pos: QPoint, issue_id: int, due_date: str, issue_url: str):
        menu = QMenu(self)
        due_empty = not due_date or due_date.strip() == ""
        action_clear = menu.addAction("Limpiar fecha fin")
        action_clear.setEnabled(not due_empty)
        action_clear.triggered.connect(lambda checked: self.due_date_cambiada.emit(issue_id, ""))
        menu.addSeparator()
        self._add_copy_url_action(menu, issue_url)
        action_open = menu.addAction("Abrir en Redmine")
        action_open.triggered.connect(lambda checked, iid=issue_id, url=issue_url: self.tarea_abrir_url.emit(iid, url))
        menu.exec(self.viewport().mapToGlobal(pos))

    def _show_status_menu(self, pos: QPoint, issue_id: int, current_status_id: int, issue_url: str):
        menu = QMenu(self)
        for sid, sname in self._statuses:
            action = menu.addAction(sname)
            action.setCheckable(True)
            if sid == current_status_id:
                action.setChecked(True)
            action.triggered.connect(lambda checked, v=sid: self.cambio_rapido.emit(issue_id, "estado", v))
        menu.addSeparator()
        self._add_copy_url_action(menu, issue_url)
        action_open = menu.addAction("Abrir en Redmine")
        action_open.triggered.connect(lambda checked, iid=issue_id, url=issue_url: self.tarea_abrir_url.emit(iid, url))
        menu.exec(self.viewport().mapToGlobal(pos))

    def _show_assign_menu(self, pos: QPoint, issue_id: int, issue_url: str):
        menu = QMenu(self)

        accion_yo = menu.addAction("Asignarme a mí")
        accion_yo.triggered.connect(
            lambda: self.cambio_rapido.emit(issue_id, "asignado", self._current_user_id)
        )

        menu.addSeparator()

        if self._frequent_people_ids:
            for uid in self._frequent_people_ids:
                name = self._frequent_people_names.get(uid, f"Usuario #{uid}")
                action = menu.addAction(name)
                action.triggered.connect(lambda checked, v=uid: self.cambio_rapido.emit(issue_id, "asignado", v))
        else:
            accion_vacia = menu.addAction("No hay personas frecuentes")
            accion_vacia.setEnabled(False)

        menu.addSeparator()
        self._add_copy_url_action(menu, issue_url)
        action_open = menu.addAction("Abrir en Redmine")
        action_open.triggered.connect(lambda checked, iid=issue_id, url=issue_url: self.tarea_abrir_url.emit(iid, url))
        menu.exec(self.viewport().mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Repoblado
    # ------------------------------------------------------------------

    def _populate_row(self, row: int, issue: dict):
        """Rellena todas las celdas de una fila a partir de una issue."""
        id_item = QTableWidgetItem()
        id_item.setData(Qt.ItemDataRole.DisplayRole, int(issue["id"]))
        id_item.setData(Qt.ItemDataRole.UserRole, issue.get("project_id", 0))
        id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(id_item, issue)
        self.setItem(row, self.COL_ID, id_item)

        tracker_item = QTableWidgetItem(issue.get("tracker_name", ""))
        tracker_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(tracker_item, issue)
        self.setItem(row, self.COL_TRACKER, tracker_item)

        project_item = QTableWidgetItem(issue.get("project_name", ""))
        project_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(project_item, issue)
        self.setItem(row, self.COL_PROJECT, project_item)

        title_item = QTableWidgetItem(issue.get("subject", ""))
        title_item.setToolTip(
            f"<b>{issue.get('tracker_name', '')} #{issue['id']}</b>: {issue.get('subject', '')}<br><br>"
            f"<b>Descripción:</b><br>{issue.get('description', 'Sin descripción')}<br><br>"
            f"<b>Proyecto:</b> {issue.get('project_name', '')}<br>"
            f"<b>Autor:</b> {issue.get('author_name', '')}<br>"
            f"<b>Asignado a:</b> {issue.get('assigned_to_name', 'Sin asignar')}<br>"
            f"<b>Prioridad:</b> {issue.get('priority_name', '')}"
        )
        self._apply_issue_style(title_item, issue)
        self.setItem(row, self.COL_TITLE, title_item)

        start_iso = issue.get("start_date", "")
        start_item = DateSortItem(start_iso, iso_to_display(start_iso))
        start_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(start_item, issue)
        self.setItem(row, self.COL_START_DATE, start_item)

        due_iso = issue.get("due_date", "")
        due_item = DateSortItem(due_iso, iso_to_display(due_iso))
        due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(due_item, issue)
        self.setItem(row, self.COL_DUE_DATE, due_item)

        priority_item = QTableWidgetItem(issue.get("priority_name", ""))
        priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(priority_item, issue)
        self.setItem(row, self.COL_PRIORITY, priority_item)

        status_item = QTableWidgetItem(issue.get("status_name", ""))
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(status_item, issue)
        self.setItem(row, self.COL_STATUS, status_item)

        assigned_item = QTableWidgetItem(issue.get("assigned_to_name", ""))
        assigned_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(assigned_item, issue)
        self.setItem(row, self.COL_ASSIGNED_TO, assigned_item)

        category_item = QTableWidgetItem(issue.get("category_name", ""))
        category_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(category_item, issue)
        self.setItem(row, self.COL_CATEGORY, category_item)

        # Progreso: entero en DisplayRole; el ProgressBarDelegate pinta la barra
        progress = issue.get("done_ratio", 0) or 0
        progress_item = QTableWidgetItem()
        progress_item.setData(Qt.ItemDataRole.DisplayRole, int(progress))
        progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(progress_item, issue)
        self.setItem(row, self.COL_PROGRESS, progress_item)

        # URL: item con icono; se abre mediante cellClicked
        url_item = QTableWidgetItem()
        url_item.setIcon(
            QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        )
        url_item.setToolTip("Abrir en Redmine")
        url_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(url_item, issue)
        self.setItem(row, self.COL_URL, url_item)

        created_iso = issue.get("created_on", "")
        created_item = DateSortItem(created_iso, iso_datetime_to_display(created_iso))
        created_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(created_item, issue)
        self.setItem(row, self.COL_CREATED, created_item)

        updated_iso = issue.get("updated_on", "")
        updated_item = DateSortItem(updated_iso, iso_datetime_to_display(updated_iso))
        updated_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_issue_style(updated_item, issue)
        self.setItem(row, self.COL_UPDATED, updated_item)

    def set_issues(self, issues: list[dict]):
        """Repuebla la tabla de forma atómica, aislada de la ordenación activa."""
        header = self.horizontalHeader()
        section = header.sortIndicatorSection()
        order = header.sortIndicatorOrder()

        self._issues = list(issues)
        self._issues_by_id = {int(issue["id"]): issue for issue in issues}
        self._editing_issue_id = None

        # Desactivar la ordenación durante el poblado evita que Qt reordene
        # las filas a mitad de la carga y mezcle celdas de distintas tareas.
        self.setSortingEnabled(False)

        # Eliminar widgets de celda residuales (p. ej. QDateEdit de edición inline)
        for row in range(self.rowCount()):
            for col in (self.COL_PROGRESS, self.COL_URL, self.COL_DUE_DATE):
                if self.cellWidget(row, col) is not None:
                    self.removeCellWidget(row, col)

        self.clearContents()
        self.setRowCount(len(issues))

        for row, issue in enumerate(issues):
            self._populate_row(row, issue)

        # Reactivar la ordenación y reaplicar la que estaba activa
        self.setSortingEnabled(True)
        if section >= 0:
            self.sortItems(section, order)

    def get_selected_issue_id(self) -> int | None:
        rows = {idx.row() for idx in self.selectedIndexes()}
        if len(rows) == 1:
            return self._issue_id_at_row(rows.pop())
        return None

    def get_selected_row_data(self) -> dict | None:
        rows = {idx.row() for idx in self.selectedIndexes()}
        if len(rows) == 1:
            return self._issue_at_row(rows.pop())
        return None

    def clear_issues(self):
        self._issues = []
        self._issues_by_id = {}
        self._editing_issue_id = None
        self.setRowCount(0)
