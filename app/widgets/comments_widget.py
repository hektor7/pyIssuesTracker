from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextBrowser,
    QPlainTextEdit, QPushButton, QScrollArea,
    QFrame, QSizePolicy, QHBoxLayout,
)
from PyQt6.QtGui import QFont


class CommentsWidget(QWidget):
    """Widget para mostrar comentarios existentes y añadir nuevos."""

    nota_agregada = pyqtSignal(str)  # Emite el texto de la nueva nota

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Título
        title = QLabel("Comentarios")
        title.setFont(QFont(title.font().family(), -1, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # Scroll area para comentarios existentes
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setMaximumHeight(180)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._comments_container = QWidget()
        self._comments_layout = QVBoxLayout(self._comments_container)
        self._comments_layout.setContentsMargins(0, 0, 0, 0)
        self._comments_layout.setSpacing(4)
        self._scroll_area.setWidget(self._comments_container)
        main_layout.addWidget(self._scroll_area)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(sep)

        # Campo para nuevo comentario
        new_label = QLabel("Nuevo comentario:")
        new_label.setFont(QFont(new_label.font().family(), -1, QFont.Weight.Bold))
        main_layout.addWidget(new_label)

        self._note_edit = QPlainTextEdit()
        self._note_edit.setPlaceholderText("Escribe un comentario...")
        self._note_edit.setMaximumHeight(80)
        self._note_edit.setTabChangesFocus(True)
        main_layout.addWidget(self._note_edit)

        # Botón añadir
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._add_btn = QPushButton("Añadir comentario")
        self._add_btn.clicked.connect(self._on_add_note)
        btn_layout.addWidget(self._add_btn)
        main_layout.addLayout(btn_layout)

    def set_comments(self, journals: list):
        """Carga los comentarios existentes.
        
        Args:
            journals: Lista de diccionarios con keys: 'user_name', 'notes', 'created_on'
        """
        # Limpiar comentarios anteriores
        while self._comments_layout.count():
            item = self._comments_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not journals:
            no_comments = QLabel("(Sin comentarios)")
            no_comments.setStyleSheet("color: palette(mid); font-style: italic;")
            self._comments_layout.addWidget(no_comments)
        else:
            for j in journals:
                # Marco para cada comentario
                frame = QFrame()
                frame.setFrameShape(QFrame.Shape.StyledPanel)
                frame.setStyleSheet("QFrame { background: palette(alternate-base); border-radius: 4px; padding: 4px; }")
                f_layout = QVBoxLayout(frame)
                f_layout.setContentsMargins(6, 4, 6, 4)
                f_layout.setSpacing(2)

                # Cabecera: autor y fecha
                header = QLabel(f"<b>{j.get('user_name', 'Desconocido')}</b> — {j.get('created_on', '')}")
                header.setStyleSheet("background: transparent;")
                f_layout.addWidget(header)

                # Texto del comentario (read-only)
                text_browser = QTextBrowser()
                text_browser.setPlainText(j.get('notes', ''))
                text_browser.setMaximumHeight(80)
                text_browser.setStyleSheet("QTextBrowser { background: transparent; border: none; }")
                f_layout.addWidget(text_browser)

                self._comments_layout.addWidget(frame)

        self._comments_layout.addStretch()

    def _on_add_note(self):
        text = self._note_edit.toPlainText().strip()
        if text:
            self.nota_agregada.emit(text)
            self._note_edit.clear()

    def clear(self):
        """Limpia todos los comentarios y el campo de nueva nota."""
        self._note_edit.clear()
        self.set_comments([])
