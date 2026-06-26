from datetime import date

from PyQt6.QtCore import pyqtSignal, Qt, QUrl, QSize, QPoint, QDate, QEvent
from PyQt6.QtGui import QDesktopServices, QIcon, QColor
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QPushButton, QToolButton, QToolTip, QStyle, QApplication,
    QProgressBar, QMenu, QDateEdit,
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


class TaskTable(QTableWidget):
    tarea_doble_click = pyqtSignal(int)
    tarea_abrir_url = pyqtSignal(int, str)
    cambio_rapido = pyqtSignal(int, str, int)  # issue_id, tipo, valor
    due_date_cambiada = pyqtSignal(int, str)  # issue_id, due_date

    COL_ID = 0
    COL_TRACKER = 1
    COL_TITLE = 2
    COL_START_DATE = 3
    COL_DUE_DATE = 4
    COL_STATUS = 5
    COL_ASSIGNED_TO = 6
    COL_PROGRESS = 7
    COL_URL = 8
    COL_CREATED = 9
    COL_UPDATED = 10

    HEADERS = ["ID", "Tracker", "Título", "Fecha inicio", "Fecha fin", "Estado", "Asignado a", "Progreso %", "", "Creado", "Modificado"]

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
        header.setSectionResizeMode(self.COL_TITLE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_START_DATE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_DUE_DATE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_ASSIGNED_TO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_PROGRESS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_URL, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(self.COL_URL, 40)
        header.setSectionResizeMode(self.COL_CREATED, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_UPDATED, QHeaderView.ResizeMode.ResizeToContents)

        self.cellDoubleClicked.connect(self._on_double_click)
        self._issues: list[dict] = []
        self._statuses: list[tuple[int, str]] = []
        self._current_user_id: int = 0
        self._frequent_people_ids: list[int] = []
        self._editing_row: int | None = None
        self._frequent_people_names: dict[int, str] = {}
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_context_data(self, statuses: list[tuple[int, str]], current_user_id: int,
                         frequent_people_ids: list[int], member_names: dict[int, str]):
        self._statuses = statuses
        self._current_user_id = current_user_id
        self._frequent_people_ids = frequent_people_ids
        self._frequent_people_names = member_names

    def _on_double_click(self, row: int, col: int):
        if row >= len(self._issues):
            return
        if col == self.COL_DUE_DATE:
            due_str = self._issues[row].get("due_date", "")
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
            self._editing_row = row
            self.setCellWidget(row, self.COL_DUE_DATE, date_edit)
            date_edit.setFocus()
            date_edit.show()
        else:
            self.tarea_doble_click.emit(self._issues[row]["id"])

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
        if self._editing_row is None:
            return
        row = self._editing_row
        date_edit = self.cellWidget(row, self.COL_DUE_DATE)
        if not isinstance(date_edit, QDateEdit):
            self._editing_row = None
            return
        self._editing_row = None
        self._on_due_date_edited(row, date_edit)

    def _cancel_due_date_edit(self):
        """Cancela la edición inline restaurando la fecha original."""
        if self._editing_row is None:
            return
        row = self._editing_row
        self._editing_row = None
        self.removeCellWidget(row, self.COL_DUE_DATE)
        old_due = self._issues[row].get("due_date", "")
        due_item = QTableWidgetItem(iso_to_display(old_due))
        due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        priority = self._issues[row].get("priority_name", "")
        bg_color = self._priority_bg(priority)
        if bg_color:
            due_item.setBackground(bg_color)
            due_item.setForeground(Qt.GlobalColor.white)
        self.setItem(row, self.COL_DUE_DATE, due_item)

    def _on_due_date_edited(self, row: int, date_edit: QDateEdit):
        if row >= len(self._issues):
            return
        issue_id = self._issues[row]["id"]
        new_due_iso = date_edit.date().toString("yyyy-MM-dd") if date_edit.date().isValid() else ""
        self.removeCellWidget(row, self.COL_DUE_DATE)
        self._issues[row]["due_date"] = new_due_iso
        due_item = QTableWidgetItem(iso_to_display(new_due_iso))
        due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, self.COL_DUE_DATE, due_item)
        self.due_date_cambiada.emit(issue_id, new_due_iso)

    def refresh_due_date_cell(self, issue_id: int, due_date: str):
        """Actualiza la celda de fecha fin para un issue (usado tras menú contextual)."""
        for row, issue in enumerate(self._issues):
            if issue["id"] == issue_id:
                self._issues[row]["due_date"] = due_date
                due_item = QTableWidgetItem(iso_to_display(due_date))
                due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Mantener colores de prioridad si existen
                priority = issue.get("priority_name", "")
                bg_color = self._priority_bg(priority)
                if bg_color:
                    due_item.setBackground(bg_color)
                    due_item.setForeground(Qt.GlobalColor.white)
                self.removeCellWidget(row, self.COL_DUE_DATE)
                self.setItem(row, self.COL_DUE_DATE, due_item)
                break

    def _show_context_menu(self, pos: QPoint):
        row = self.rowAt(pos.y())
        col = self.columnAt(pos.x())
        if row < 0 or row >= len(self._issues):
            return
        issue = self._issues[row]
        issue_id = issue["id"]
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

    def _priority_bg(self, priority_name: str) -> QColor | None:
        pname = (priority_name or "").lower().strip()
        if pname in ("inmediata", "immediate"):
            return self._BG_INMEDIATA
        if pname in ("urgente", "urgent"):
            return self._BG_URGENTE
        return None

    def _create_progress_bar(self, progress: int, bg_color: QColor | None = None) -> QProgressBar:
        """Crea una QProgressBar estilizada según el progreso y el color de fondo de prioridad."""
        bar = QProgressBar()
        bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        bar.customContextMenuRequested.connect(
            lambda pos: self.customContextMenuRequested.emit(
                bar.mapTo(self.viewport(), pos)
            )
        )
        bar.setRange(0, 100)
        bar.setValue(progress)
        bar.setTextVisible(True)
        bar.setFormat(f"{progress}%")
        bar.setFixedHeight(20)

        if bg_color:
            # Fondo rojo para prioridades altas
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {bg_color.name()};
                    border: 1px solid #555;
                    border-radius: 2px;
                    text-align: center;
                    color: white;
                }}
                QProgressBar::chunk {{
                    background-color: #ff9800;
                    border-radius: 1px;
                }}
            """)
        elif progress == 100:
            bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 2px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #2e7d32;
                    border-radius: 1px;
                }
            """)
        elif progress > 0:
            bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 2px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #f57c00;
                    border-radius: 1px;
                }
            """)
        else:
            bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 2px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #bdbdbd;
                    border-radius: 1px;
                }
            """)
        return bar

    def set_issues(self, issues: list[dict]):
        self._issues = issues
        self.setRowCount(len(issues))
        # Limpiar widgets de celdas previos (barras de progreso, botones y date edits)
        for row in range(self.rowCount()):
            self.removeCellWidget(row, self.COL_PROGRESS)
            self.removeCellWidget(row, self.COL_URL)
            self.removeCellWidget(row, self.COL_DUE_DATE)
        for row, issue in enumerate(issues):
            bg_color = self._priority_bg(issue.get("priority_name", ""))

            id_item = QTableWidgetItem()
            id_item.setData(Qt.ItemDataRole.DisplayRole, int(issue["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setData(Qt.ItemDataRole.UserRole, issue.get("project_id", 0))
            if bg_color:
                id_item.setBackground(bg_color)
                id_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_ID, id_item)

            tracker_item = QTableWidgetItem(issue.get("tracker_name", ""))
            tracker_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bg_color:
                tracker_item.setBackground(bg_color)
                tracker_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_TRACKER, tracker_item)

            title_item = QTableWidgetItem(issue.get("subject", ""))
            title_item.setToolTip(
                f"<b>{issue.get('tracker_name', '')} #{issue['id']}</b>: {issue.get('subject', '')}<br><br>"
                f"<b>Descripción:</b><br>{issue.get('description', 'Sin descripción')}<br><br>"
                f"<b>Proyecto:</b> {issue.get('project_name', '')}<br>"
                f"<b>Autor:</b> {issue.get('author_name', '')}<br>"
                f"<b>Asignado a:</b> {issue.get('assigned_to_name', 'Sin asignar')}<br>"
                f"<b>Prioridad:</b> {issue.get('priority_name', '')}"
            )
            if bg_color:
                title_item.setBackground(bg_color)
                title_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_TITLE, title_item)

            start_iso = issue.get("start_date", "")
            start_item = DateSortItem(start_iso, iso_to_display(start_iso))
            start_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bg_color:
                start_item.setBackground(bg_color)
                start_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_START_DATE, start_item)

            due_iso = issue.get("due_date", "")
            due_item = DateSortItem(due_iso, iso_to_display(due_iso))
            due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bg_color:
                due_item.setBackground(bg_color)
                due_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_DUE_DATE, due_item)

            status_item = QTableWidgetItem(issue.get("status_name", ""))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bg_color:
                status_item.setBackground(bg_color)
                status_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_STATUS, status_item)

            assigned_item = QTableWidgetItem(issue.get("assigned_to_name", ""))
            assigned_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bg_color:
                assigned_item.setBackground(bg_color)
                assigned_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_ASSIGNED_TO, assigned_item)

            progress = issue.get("done_ratio", 0)
            # Item dummy para ordenación numérica
            sort_item = QTableWidgetItem()
            sort_item.setData(Qt.ItemDataRole.DisplayRole, int(progress))
            self.setItem(row, self.COL_PROGRESS, sort_item)
            progress_bar = self._create_progress_bar(progress, bg_color)
            self.setCellWidget(row, self.COL_PROGRESS, progress_bar)

            btn = QToolButton()
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            btn.setIcon(icon)
            btn.setIconSize(QSize(16, 16))
            btn.setToolTip("Abrir en Redmine")
            btn.setAutoRaise(True)
            issue_id = issue["id"]
            issue_url = issue.get("url", "")
            btn.clicked.connect(lambda checked, iid=issue_id, url=issue_url: self.tarea_abrir_url.emit(iid, url))
            self.setCellWidget(row, self.COL_URL, btn)

            created_iso = issue.get("created_on", "")
            created_item = DateSortItem(
                created_iso, iso_datetime_to_display(created_iso)
            )
            created_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bg_color:
                created_item.setBackground(bg_color)
                created_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_CREATED, created_item)

            updated_iso = issue.get("updated_on", "")
            updated_item = DateSortItem(
                updated_iso, iso_datetime_to_display(updated_iso)
            )
            updated_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bg_color:
                updated_item.setBackground(bg_color)
                updated_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_UPDATED, updated_item)

    def get_selected_issue_id(self) -> int | None:
        rows = set()
        for idx in self.selectedIndexes():
            rows.add(idx.row())
        if len(rows) == 1:
            row = rows.pop()
            if row < len(self._issues):
                return self._issues[row]["id"]
        return None

    def get_selected_row_data(self) -> dict | None:
        rows = set()
        for idx in self.selectedIndexes():
            rows.add(idx.row())
        if len(rows) == 1:
            row = rows.pop()
            if row < len(self._issues):
                return self._issues[row]
        return None

    def clear_issues(self):
        self._issues = []
        self.setRowCount(0)
