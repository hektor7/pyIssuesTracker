"""Widget de combo multiselección con checkboxes.

Reemplaza QComboBox cuando se necesita seleccionar múltiples opciones.
Muestra un QPushButton que al hacer clic despliega un popup con checkboxes.
"""

from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFrame, QApplication, QLineEdit,
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
        self._selected_ids: set[int] = {self.ALL}
        self._fixed_options: list[tuple[int, str]] = []  # opciones especiales al inicio
        self._filter_text: str = ""  # filtro de búsqueda vigente

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

        # Campo de búsqueda por texto (tarea 2.1)
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Buscar...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._apply_filter)
        popup_layout.addWidget(self._search_edit)

        self._list = QListWidget()
        self._list.setMaximumHeight(250)
        self._list.itemChanged.connect(self._on_item_changed)
        popup_layout.addWidget(self._list)

        # Cierre por clic fuera: Qt oculta el popup; el event filter limpia la
        # búsqueda y resetea _popup_open para que el siguiente clic vuelva a abrir.
        self._popup.installEventFilter(self)

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
        self._selected_ids = set(ids) if ids else {self.ALL}
        self._sync_list_checkmarks()
        self._update_button_text()
        self.seleccion_cambiada.emit(sorted(self._selected_ids))

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
            item.setToolTip(fname)  # tarea 2.4
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
            item.setToolTip(name)  # tarea 2.4
            self._list.addItem(item)

        self._list.blockSignals(False)

        # Reaplicar el filtro de búsqueda vigente (tarea 2.3)
        self._apply_filter(self._filter_text)

    def _apply_filter(self, texto: str):
        """Filtra los ítems visibles por subcadena (case-insensitive).

        Las opciones fijas nunca se ocultan. No altera la selección ni los
        checkmarks: solo cambia la visibilidad de los ítems (tarea 2.2).
        """
        self._filter_text = texto
        needle = texto.strip().lower()
        fixed_ids = {fid for fid, _ in self._fixed_options}
        for i in range(self._list.count()):
            item = self._list.item(i)
            iid = item.data(Qt.ItemDataRole.UserRole)
            if iid in fixed_ids:
                item.setHidden(False)
            elif needle and needle not in item.text().lower():
                item.setHidden(True)
            else:
                item.setHidden(False)

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
            self._button.setToolTip("")  # tarea 2.5
            return

        selected = sorted(self._selected_ids)
        if len(selected) == 1:
            sid = selected[0]
            name = self._name_for_id(sid)
            if name is not None:
                self._button.setText(name)
                self._button.setToolTip(name)  # tarea 2.5
            else:
                # Fallback: id desconocido → texto con el id y tooltip vacío (14.4)
                self._button.setText(str(sid))
                self._button.setToolTip("")
        else:
            self._button.setText(f"{len(selected)} seleccionados")
            self._button.setToolTip("")  # tarea 2.5

    def _name_for_id(self, sid: int) -> str | None:
        """Nombre del ítem con el id dado, o None si no se conoce.

        Busca primero en la lista visible y, como respaldo, en las fuentes de
        datos (_items y _fixed_options) por si el id no está renderizado.
        """
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == sid:
                return item.text()
        for iid, name in self._items:
            if iid == sid:
                return name
        for fid, fname in self._fixed_options:
            if fid == sid:
                return fname
        return None

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
        # El campo de búsqueda se vacía al abrir y al cerrar (tarea 2.6)
        self._search_edit.clear()

    def hideEvent(self, event):
        """Cierra el popup si el widget padre se oculta."""
        if self._popup_open:
            self._popup.hide()
            self._popup_open = False
        self._search_edit.clear()  # tarea 2.6
        super().hideEvent(event)

    def eventFilter(self, obj, event):
        """Limpia la búsqueda y resetea _popup_open cuando el popup se oculta.

        Cubre el cierre por clic fuera (Qt oculta el popup con un evento Hide),
        de modo que el siguiente clic en el botón vuelve a abrir el popup y el
        campo de búsqueda queda vacío (tarea 14.1).
        """
        if obj is self._popup and event.type() == QEvent.Type.Hide:
            self._search_edit.clear()
            self._popup_open = False
        return super().eventFilter(obj, event)
