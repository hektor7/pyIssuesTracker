from PyQt6.QtCore import pyqtSignal, Qt, QUrl, QSize
from PyQt6.QtGui import QDesktopServices, QIcon, QColor
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QPushButton, QToolButton, QToolTip, QStyle, QApplication,
    QProgressBar,
)


class TaskTable(QTableWidget):
    tarea_doble_click = pyqtSignal(int)
    tarea_abrir_url = pyqtSignal(int, str)

    COL_ID = 0
    COL_TITLE = 1
    COL_START_DATE = 2
    COL_STATUS = 3
    COL_ASSIGNED_TO = 4
    COL_PROGRESS = 5
    COL_URL = 6

    HEADERS = ["ID", "Título", "Fecha inicio", "Estado", "Asignado a", "Progreso %", ""]

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
        self.verticalHeader().setDefaultSectionSize(28)

        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(self.COL_ID, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_TITLE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_START_DATE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_ASSIGNED_TO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_PROGRESS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_URL, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(self.COL_URL, 40)

        self.cellDoubleClicked.connect(self._on_double_click)
        self._issues: list[dict] = []

    def _on_double_click(self, row: int, col: int):
        if row < len(self._issues):
            self.tarea_doble_click.emit(self._issues[row]["id"])

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
                    background-color: #c62828;
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
        # Limpiar widgets de celdas previos (barras de progreso y botones)
        for row in range(self.rowCount()):
            self.removeCellWidget(row, self.COL_PROGRESS)
            self.removeCellWidget(row, self.COL_URL)
        for row, issue in enumerate(issues):
            bg_color = self._priority_bg(issue.get("priority_name", ""))

            id_item = QTableWidgetItem(str(issue["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setData(Qt.ItemDataRole.UserRole, issue.get("project_id", 0))
            if bg_color:
                id_item.setBackground(bg_color)
                id_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_ID, id_item)

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

            start_item = QTableWidgetItem(issue.get("start_date", ""))
            start_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bg_color:
                start_item.setBackground(bg_color)
                start_item.setForeground(Qt.GlobalColor.white)
            self.setItem(row, self.COL_START_DATE, start_item)

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
            progress_bar = self._create_progress_bar(progress, bg_color)
            self.setCellWidget(row, self.COL_PROGRESS, progress_bar)

            btn = QToolButton()
            icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            btn.setIcon(icon)
            btn.setIconSize(QSize(16, 16))
            btn.setToolTip("Abrir en Redmine")
            btn.setAutoRaise(True)
            issue_id = issue["id"]
            issue_url = issue.get("url", "")
            btn.clicked.connect(lambda checked, iid=issue_id, url=issue_url: self.tarea_abrir_url.emit(iid, url))
            self.setCellWidget(row, self.COL_URL, btn)

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
