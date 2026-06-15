from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextBrowser,
    QPlainTextEdit, QPushButton, QScrollArea,
    QFrame, QSizePolicy, QHBoxLayout,
)
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QCompleter


class CommentsWidget(QWidget):
    """Widget para mostrar comentarios existentes y añadir nuevos."""

    nota_agregada = pyqtSignal(str)  # Emite el texto de la nueva nota

    def __init__(self, parent=None):
        super().__init__(parent)
        self._completer = None
        self._text_changed_handler = None
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

    @staticmethod
    def _journal_get(j, key: str, default: str = ""):
        """Obtiene un valor de un journal, ya sea objeto RedmineJournal o diccionario."""
        if hasattr(j, key):
            value = getattr(j, key, default)
            return value if value is not None else default
        elif hasattr(j, "get"):
            value = j.get(key, default)
            return value if value is not None else default
        return default

    def set_comments(self, journals: list):
        """Carga los comentarios existentes.
        
        Args:
            journals: Lista de diccionarios u objetos RedmineJournal con user_name, notes, created_on.
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
                user = self._journal_get(j, 'user_name', 'Desconocido')
                date = self._journal_get(j, 'created_on', '')
                header = QLabel(f"<b>{user}</b> — {date}")
                header.setStyleSheet("background: transparent;")
                f_layout.addWidget(header)

                # Texto del comentario (read-only)
                text_browser = QTextBrowser()
                text_browser.setPlainText(self._journal_get(j, 'notes', ''))
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

    def set_members(self, members: list[tuple[int, str]]):
        """Configura el autocompletado @usuario con los miembros del proyecto."""
        names = [name for _, name in members]

        # Desconectar handler anterior si existe
        if self._text_changed_handler is not None:
            try:
                self._note_edit.textChanged.disconnect(self._text_changed_handler)
            except (TypeError, RuntimeError):
                pass
            self._text_changed_handler = None

        # Destruir completer anterior
        if self._completer is not None:
            self._completer.deleteLater()
            self._completer = None

        if not names:
            return

        self._completer = QCompleter(names, self._note_edit)
        self._completer.setWidget(self._note_edit)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._completer.setMaxVisibleItems(5)

        def insert_mention(completed_text: str):
            """Reemplaza @texto_parcial por @Nombre Completo en el editor."""
            try:
                cursor = self._note_edit.textCursor()
                text = self._note_edit.toPlainText()
                pos = cursor.position()
                at_pos = text.rfind('@', 0, pos)
                if at_pos >= 0:
                    cursor.setPosition(at_pos)
                    cursor.setPosition(pos, cursor.MoveMode.KeepAnchor)
                    cursor.insertText(f"@{completed_text} ")
            except RuntimeError:
                pass

        self._completer.activated.connect(insert_mention)

        def on_text_changed():
            if self._completer is None:
                return
            try:
                cursor = self._note_edit.textCursor()
                text = self._note_edit.toPlainText()
                pos = cursor.position()
                at_pos = text.rfind('@', 0, pos)
                if at_pos >= 0:
                    after_at = text[at_pos:pos]
                    if ' ' not in after_at and '\n' not in after_at:
                        prefix = after_at[1:] if len(after_at) > 1 else ""
                        self._completer.setCompletionPrefix(prefix)
                        if self._completer.completionCount() > 0:
                            self._completer.complete()
                        return
                popup = self._completer.popup() if self._completer else None
                if popup:
                    popup.hide()
            except RuntimeError:
                pass  # Widget destruido

        self._text_changed_handler = on_text_changed
        self._note_edit.textChanged.connect(on_text_changed)

    def clear(self):
        """Limpia todos los comentarios y el campo de nueva nota."""
        self._note_edit.clear()
        self.set_comments([])


def setup_mention_completer(text_edit: QPlainTextEdit, names: list[str]):
    """Configura un QCompleter para autocompletar @usuario en un QPlainTextEdit.

    El completer se activa cuando el usuario escribe '@' seguido de texto sin espacios.
    """
    completer = QCompleter(names, text_edit)
    completer.setWidget(text_edit)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    completer.setMaxVisibleItems(5)

    def insert_mention(completed_text: str):
        """Reemplaza @texto_parcial por @Nombre Completo en el editor."""
        try:
            cursor = text_edit.textCursor()
            text = text_edit.toPlainText()
            pos = cursor.position()
            at_pos = text.rfind('@', 0, pos)
            if at_pos >= 0:
                cursor.setPosition(at_pos)
                cursor.setPosition(pos, cursor.MoveMode.KeepAnchor)
                cursor.insertText(f"@{completed_text} ")
        except RuntimeError:
            pass

    completer.activated.connect(insert_mention)

    def on_text_changed():
        try:
            cursor = text_edit.textCursor()
            text = text_edit.toPlainText()
            pos = cursor.position()
            # Buscar la última '@' antes del cursor
            at_pos = text.rfind('@', 0, pos)
            if at_pos >= 0:
                after_at = text[at_pos:pos]
                # Solo activar si no hay espacio después de @ (es una mención en curso)
                if ' ' not in after_at and '\n' not in after_at:
                    # Eliminar el @ del prefijo para que coincida con los nombres
                    prefix = after_at[1:] if len(after_at) > 1 else ""
                    completer.setCompletionPrefix(prefix)
                    if completer.completionCount() > 0:
                        completer.complete()
                    return
            popup = completer.popup()
            if popup:
                popup.hide()
        except RuntimeError:
            pass  # Widget destruido

    text_edit.textChanged.connect(on_text_changed)
    return completer
