"""Widget de combo multiselección con checkboxes.

Reemplaza QComboBox cuando se necesita seleccionar múltiples opciones.
Muestra un QPushButton que al hacer clic despliega un popup con checkboxes.
"""

from PyQt6.QtCore import pyqtSignal, Qt, QPoint
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFrame, QApplication,
)


class MultiSelectCombo(QWidget):
    """Combo desplegable con checkboxes para multiselección.

    Emite seleccion_cambiada(list) cuando cambia la selección.
    La lista contiene los IDs de los items seleccionados.
    """

    seleccion_cambiada = pyqtSignal(list)

    # Valores especiales para las opciones fijas
    ALL = 0        # "(Todos)"
    NONE = -1      # "Sin asignar"
    ME = -2        # "Asignado a mí"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[tuple[int, str]] = []  # (id, texto)
        self._selected_ids: set[int] = set()
        self._fixed_options: list[tuple[int, str]] = []  # opciones especiales al inicio

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._button = QPushButton("Todos")
        self._button.setMinimumWidth(150)
        self._button.clicked.connect(self._toggle_popup)
        layout.addWidget(self._button)

        # Popup con la lista de checkboxes
        self._popup = QFrame()
        self._popup.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self._popup.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        popup_layout = QVBoxLayout(self._popup)
        popup_layout.setContentsMargins(2, 2, 2, 2)
        popup_layout.setSpacing(0)

        self._list = QListWidget()
        self._list.setMaximumHeight(250)
        self._list.itemChanged.connect(self._on_item_changed)
        popup_layout.addWidget(self._list)

        self._popup_open = False

    def set_fixed_options(self, options: list[tuple[int, str]]):
        """Establece opciones fijas al inicio de la lista (ej. Todos, Sin asignar, Asignado a mí).

        Args:
            options: Lista de (id, texto). IDs negativos indican opciones especiales.
        """
        self._fixed_options = options
        self._rebuild_list()

    def set_items(self, items: list[tuple[int, str]]):
        """Reemplaza los items dinámicos (miembros del proyecto).

        Args:
            items: Lista de (id, nombre).
        """
        self._items = items
        self._rebuild_list()

    def set_selected_ids(self, ids: list[int]):
        """Establece la selección actual."""
        self._selected_ids = set(ids)
        self._sync_list_checkmarks()
        self._update_button_text()

    def selected_ids(self) -> list[int]:
        """Devuelve la lista de IDs seleccionados."""
        return sorted(self._selected_ids)

    def _rebuild_list(self):
        """Reconstruye la lista de checkboxes."""
        self._list.blockSignals(True)
        self._list.clear()

        # Opciones fijas (Todos, Sin asignar, Asignado a mí)
        for fid, fname in self._fixed_options:
            item = QListWidgetItem(fname)
            item.setData(Qt.ItemDataRole.UserRole, fid)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if fid in self._selected_ids
                else Qt.CheckState.Unchecked
            )
            self._list.addItem(item)

        # Items dinámicos
        for iid, name in self._items:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, iid)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if iid in self._selected_ids
                else Qt.CheckState.Unchecked
            )
            self._list.addItem(item)

        self._list.blockSignals(False)

    def _sync_list_checkmarks(self):
        """Sincroniza los checkmarks de la lista con _selected_ids."""
        self._list.blockSignals(True)
        for i in range(self._list.count()):
            item = self._list.item(i)
            iid = item.data(Qt.ItemDataRole.UserRole)
            item.setCheckState(
                Qt.CheckState.Checked if iid in self._selected_ids
                else Qt.CheckState.Unchecked
            )
        self._list.blockSignals(False)

    def _on_item_changed(self, item: QListWidgetItem):
        """Handler cuando se marca/desmarca un checkbox."""
        iid = item.data(Qt.ItemDataRole.UserRole)
        checked = item.checkState() == Qt.CheckState.Checked

        # Si se marca "Todos" (id=0), desmarcar el resto
        if iid == self.ALL and checked:
            self._selected_ids = {self.ALL}
            self._sync_list_checkmarks()
        elif iid == self.ALL and not checked:
            self._selected_ids.discard(self.ALL)
        else:
            if checked:
                # Si se marca un item específico, quitar "Todos"
                self._selected_ids.discard(self.ALL)
                self._selected_ids.add(iid)
            else:
                self._selected_ids.discard(iid)

        # Si no queda nada seleccionado, marcar "Todos"
        if not self._selected_ids:
            self._selected_ids = {self.ALL}
            self._sync_list_checkmarks()

        self._update_button_text()
        self.seleccion_cambiada.emit(sorted(self._selected_ids))

    def _update_button_text(self):
        """Actualiza el texto del botón según la selección."""
        if not self._selected_ids or self.ALL in self._selected_ids:
            self._button.setText("Todos")
            return

        selected = sorted(self._selected_ids)
        if len(selected) == 1:
            # Buscar el nombre
            sid = selected[0]
            for i in range(self._list.count()):
                item = self._list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == sid:
                    self._button.setText(item.text())
                    return
            self._button.setText(str(sid))
        else:
            self._button.setText(f"{len(selected)} seleccionados")

    def _toggle_popup(self):
        """Abre o cierra el popup."""
        if self._popup_open:
            self._popup.hide()
            self._popup_open = False
        else:
            # Posicionar debajo del botón
            pos = self._button.mapToGlobal(QPoint(0, self._button.height()))
            self._popup.setMinimumWidth(self._button.width())
            self._popup.move(pos)
            self._popup.show()
            self._popup_open = True

    def hideEvent(self, event):
        """Cierra el popup si el widget padre se oculta."""
        if self._popup_open:
            self._popup.hide()
            self._popup_open = False
        super().hideEvent(event)
