from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox,
    QLineEdit, QPushButton, QScrollArea,
    QFrame, QHBoxLayout, QMenu,
)
from PyQt6.QtGui import QFont, QAction


class ChecklistWidget(QWidget):
    """Widget para visualizar y gestionar checklists (plugin RedmineUP)."""

    item_toggled = pyqtSignal(int, bool)    # item_id, nuevo estado is_done
    item_agregado = pyqtSignal(str)         # texto del nuevo item
    item_eliminado = pyqtSignal(int)        # item_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes: dict[int, QCheckBox] = {}
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Título
        title = QLabel("Checklist")
        title.setFont(QFont(title.font().family(), -1, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # Scroll area para items
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setMaximumHeight(150)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._items_container = QWidget()
        self._items_layout = QVBoxLayout(self._items_container)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(2)
        self._scroll_area.setWidget(self._items_container)
        main_layout.addWidget(self._scroll_area)

        # Campo para nuevo item
        add_layout = QHBoxLayout()
        add_layout.setSpacing(4)
        self._new_item_edit = QLineEdit()
        self._new_item_edit.setPlaceholderText("Nuevo item de checklist...")
        self._new_item_edit.returnPressed.connect(self._on_add_item)
        add_layout.addWidget(self._new_item_edit)
        self._add_btn = QPushButton("+")
        self._add_btn.setToolTip("Añadir item")
        self._add_btn.setFixedWidth(30)
        self._add_btn.clicked.connect(self._on_add_item)
        add_layout.addWidget(self._add_btn)
        main_layout.addLayout(add_layout)

    def set_items(self, items: list):
        """Carga los items de la checklist.
        
        Args:
            items: Lista de diccionarios con keys: 'id', 'subject', 'is_done', 'position'
        """
        # Limpiar items anteriores
        self._checkboxes.clear()
        while self._items_layout.count():
            item = self._items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not items:
            no_items = QLabel("(Sin items)")
            no_items.setStyleSheet("color: palette(mid); font-style: italic;")
            self._items_layout.addWidget(no_items)
        else:
            # Ordenar por position
            sorted_items = sorted(items, key=lambda x: x.get('position', 0))
            for item_data in sorted_items:
                cb = QCheckBox(item_data['subject'])
                cb.setChecked(item_data.get('is_done', False))
                cb.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                cb.customContextMenuRequested.connect(
                    lambda pos, iid=item_data['id']: self._show_context_menu(pos, iid)
                )
                item_id = item_data['id']
                cb.toggled.connect(lambda checked, iid=item_id: self.item_toggled.emit(iid, checked))
                self._checkboxes[item_id] = cb
                self._items_layout.addWidget(cb)

        self._items_layout.addStretch()

    def _on_add_item(self):
        text = self._new_item_edit.text().strip()
        if text:
            self.item_agregado.emit(text)
            self._new_item_edit.clear()

    def _show_context_menu(self, pos, item_id: int):
        menu = QMenu(self)
        delete_action = QAction("Eliminar item", self)
        delete_action.triggered.connect(lambda: self.item_eliminado.emit(item_id))
        menu.addAction(delete_action)
        # Mostrar menú en la posición global
        widget = self._checkboxes.get(item_id)
        if widget:
            menu.exec(widget.mapToGlobal(pos))

    def add_item_widget(self, item_id: int, subject: str, is_done: bool = False):
        """Añade un widget de checkbox para un nuevo item (ya creado en servidor)."""
        cb = QCheckBox(subject)
        cb.setChecked(is_done)
        cb.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        cb.customContextMenuRequested.connect(
            lambda pos, iid=item_id: self._show_context_menu(pos, iid)
        )
        cb.toggled.connect(lambda checked, iid=item_id: self.item_toggled.emit(iid, checked))
        self._checkboxes[item_id] = cb
        # Insertar antes del stretch
        self._items_layout.insertWidget(self._items_layout.count() - 1, cb)

    def remove_item_widget(self, item_id: int):
        """Elimina el widget de un item."""
        if item_id in self._checkboxes:
            cb = self._checkboxes.pop(item_id)
            self._items_layout.removeWidget(cb)
            cb.deleteLater()

    def set_item_checked(self, item_id: int, checked: bool):
        """Establece el estado checked de un item sin emitir señal."""
        if item_id in self._checkboxes:
            self._checkboxes[item_id].blockSignals(True)
            self._checkboxes[item_id].setChecked(checked)
            self._checkboxes[item_id].blockSignals(False)

    def clear(self):
        """Limpia todos los items y el campo de texto."""
        self._new_item_edit.clear()
        self.set_items([])
