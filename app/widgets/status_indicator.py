from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QBrush
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy


class StatusIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._connected = False
        self._label = QLabel("Desconectado")
        self._label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)
        layout.addStretch()
        layout.addWidget(self._label)
        self.setLayout(layout)
        self.setFixedHeight(28)

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_state = True
        self._blinking = False

    def set_connected(self, connected: bool, message: str = ""):
        self._connected = connected
        self._blinking = False
        self._blink_timer.stop()
        if connected:
            self._label.setText(message or "Conectado")
        else:
            self._label.setText(message or "Desconectado")
        self.update()

    def set_connecting(self):
        self._blinking = True
        self._blink_state = True
        self._label.setText("Conectando...")
        self._blink_timer.start(600)

    def _toggle_blink(self):
        self._blink_state = not self._blink_state
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._blinking and self._blink_state:
            color = QColor(255, 165, 0)  # naranja parpadeante
        elif self._connected:
            color = QColor(0, 200, 0)    # verde
        else:
            color = QColor(220, 40, 40)  # rojo

        cx, cy = 14, self.height() // 2
        r = 5
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        painter.end()
