"""Widget de selección múltiple de valores de texto con checkboxes.

Muestra un QPushButton con un resumen de la selección que despliega un popup
con una lista de opciones marcables. La única fuente de verdad es el
`checkState` de cada item: la lista no usa selección de filas.
"""

from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QFrame, QLineEdit, QAbstractItemView,
)

TEXTO_SIN_OPCIONES = "Sin opciones disponibles"


class MultiValueCombo(QWidget):
    """Multiselector plegable de valores de texto.

    Expone `set_items()`, `selected_values()`, `set_selected_values()` y la
    señal `seleccion_cambiada(list)` con los valores marcados.
    """

    seleccion_cambiada = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: list[str] = []
        self._filter_text = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._button = QPushButton("")
        self._button.setMinimumWidth(150)
        self._button.clicked.connect(self._toggle_popup)
        layout.addWidget(self._button)

        # Popup con el widget como parent para que se destruya con el combo.
        self._popup = QFrame(
            self, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self._popup.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)
        popup_layout = QVBoxLayout(self._popup)
        popup_layout.setContentsMargins(2, 2, 2, 2)
        popup_layout.setSpacing(0)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Buscar...")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._apply_filter)
        popup_layout.addWidget(self._search_edit)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._list.setWordWrap(False)
        self._list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self._list.setMaximumHeight(250)
        self._list.itemChanged.connect(self._on_item_changed)
        popup_layout.addWidget(self._list)

        # Limpia la búsqueda cuando Qt oculta el popup (clic fuera).
        self._popup.installEventFilter(self)
        self._popup_open = False

    def set_items(self, values: list[str]):
        """Reconstruye las opciones conservando las que sigan marcadas."""
        self._values = [str(v) for v in values or []]
        selected = set(self.selected_values())
        self._list.blockSignals(True)
        self._list.clear()
        for text in self._values:
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if text in selected
                else Qt.CheckState.Unchecked
            )
            item.setToolTip(text)
            self._list.addItem(item)
        self._list.blockSignals(False)

        # Sin opciones el control queda deshabilitado con un texto de ayuda.
        self.setEnabled(bool(self._values))
        self._apply_filter(self._filter_text)
        self._update_button_text()

    def selected_values(self) -> list[str]:
        """Devuelve los valores marcados en el orden de las opciones."""
        return [
            self._list.item(i).text()
            for i in range(self._list.count())
            if self._list.item(i).checkState() == Qt.CheckState.Checked
        ]

    def set_selected_values(self, values: list[str]):
        """Sustituye la selección completa por los valores indicados."""
        wanted = {str(v) for v in values or []}
        self._list.blockSignals(True)
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setCheckState(
                Qt.CheckState.Checked if item.text() in wanted
                else Qt.CheckState.Unchecked
            )
        self._list.blockSignals(False)
        self._update_button_text()
        self.seleccion_cambiada.emit(self.selected_values())

    def _on_item_changed(self, _item: QListWidgetItem):
        """Actualiza el resumen y emite la señal al marcar/desmarcar."""
        self._update_button_text()
        self.seleccion_cambiada.emit(self.selected_values())

    def _texto_resumen(self) -> str:
        """Texto completo del resumen según el número de valores marcados."""
        selected = self.selected_values()
        if not selected:
            return ""
        if len(selected) == 1:
            return selected[0]
        return f"{len(selected)} seleccionados"

    def _update_button_text(self):
        """Muestra el resumen, elidido si no cabe, con tooltip completo."""
        if not self._values:
            self._button.setText(TEXTO_SIN_OPCIONES)
            self._button.setToolTip("")
            return

        selected = self.selected_values()
        texto = self._texto_resumen()
        ancho = self._button.width() - 20
        if texto and ancho > 0:
            texto = self._button.fontMetrics().elidedText(
                texto, Qt.TextElideMode.ElideRight, ancho
            )
        if self._button.text() != texto:
            self._button.setText(texto)
        self._button.setToolTip(", ".join(selected))

    def _apply_filter(self, texto: str):
        """Filtra por subcadena sin distinguir mayúsculas ni alterar la selección."""
        self._filter_text = texto
        needle = texto.strip().lower()
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setHidden(bool(needle) and needle not in item.text().lower())

    def _toggle_popup(self):
        """Abre o cierra el popup bajo el botón; la búsqueda se vacía siempre."""
        if self._popup_open:
            self._popup.hide()
            self._popup_open = False
        else:
            pos = self._button.mapToGlobal(QPoint(0, self._button.height()))
            self._popup.setMinimumWidth(self._button.width())
            self._popup.move(pos)
            self._popup.show()
            self._popup_open = True
        self._search_edit.clear()

    def hideEvent(self, event):
        """Cierra el popup y vacía la búsqueda al ocultar el widget."""
        if self._popup.isVisible():
            self._popup.hide()
        self._popup_open = False
        self._search_edit.clear()
        super().hideEvent(event)

    def resizeEvent(self, event):
        """Recalcula la elisión del resumen cuando cambia el ancho."""
        super().resizeEvent(event)
        if hasattr(self, "_button"):
            self._update_button_text()

    def eventFilter(self, obj, event):
        """Limpia la búsqueda cuando el popup se oculta por cualquier vía."""
        if obj is self._popup and event.type() == QEvent.Type.Hide:
            self._search_edit.clear()
            self._popup_open = False
        return super().eventFilter(obj, event)
