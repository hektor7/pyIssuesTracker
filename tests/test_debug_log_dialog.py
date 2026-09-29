"""Tests de la ventana de depuración (W1 / tarea 8.4).

Cubren: construcción no modal, QPlainTextEdit de solo lectura con límite de
líneas, aparición del texto al recibir la señal del QtLogHandler, filtro por
nivel y el botón Limpiar.
"""

import logging

import pytest
from PyQt6.QtCore import Qt

from app.dialogs.debug_log_dialog import DebugLogDialog
from app.services.logging_config import QtLogHandler


@pytest.fixture
def dialog(qapp):
    return DebugLogDialog()


class TestConstruccion:
    """La ventana se construye, es no modal y el texto es de solo lectura."""

    def test_se_construye_y_es_no_modal(self, dialog):
        assert dialog is not None
        assert dialog.windowModality() == Qt.WindowModality.NonModal

    def test_text_es_solo_lectura_con_limite_de_lineas(self, dialog):
        assert dialog._text.isReadOnly() is True
        assert dialog._text.maximumBlockCount() > 0


class TestMensajesEnVivo:
    """Al recibir la señal mensaje_emitido (o _append_message) el texto aparece."""

    def test_append_message_muestra_texto(self, dialog):
        dialog._append_message("ERROR app: boom")
        assert "ERROR app: boom" in dialog._text.toPlainText()

    def test_recibe_senal_del_qt_log_handler(self, qapp):
        handler = QtLogHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        dialog = DebugLogDialog()
        handler.mensaje_emitido.connect(dialog._append_message)

        record = logging.LogRecord(
            "mi.modulo", logging.ERROR, __file__, 1, "boom", None, None
        )
        handler.emit(record)

        assert "ERROR mi.modulo: boom" in dialog._text.toPlainText()


class TestFiltroPorNivel:
    """El filtro por nivel oculta lo inferior y muestra lo igual o superior.

    Los mensajes usan el formato real del log: '%(asctime)s %(levelname)s ...'.
    """

    def test_oculta_mensajes_por_debajo_del_nivel(self, dialog):
        dialog._level_filter = logging.WARNING
        dialog._append_message("2026-09-29 10:00:00 INFO app: detalle")
        assert "INFO app: detalle" not in dialog._text.toPlainText()

    def test_muestra_mensajes_de_nivel_igual_o_superior(self, dialog):
        dialog._level_filter = logging.WARNING
        dialog._append_message("2026-09-29 10:00:00 WARNING app: aviso")
        dialog._append_message("2026-09-29 10:00:00 ERROR app: fallo")
        texto = dialog._text.toPlainText()
        assert "WARNING app: aviso" in texto
        assert "ERROR app: fallo" in texto


class TestLimpiar:
    """El botón Limpiar vacía el contenido."""

    def test_limpiar_vacia_el_contenido(self, dialog):
        dialog._append_message("ERROR app: boom")
        assert dialog._text.toPlainText() != ""
        dialog._limpiar()
        assert dialog._text.toPlainText() == ""