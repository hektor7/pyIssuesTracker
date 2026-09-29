"""Tests del sistema de logging (cambio corregir-errores-tarea-y-filtro-con-diagnostico).

Cubren las tareas 1.1-1.4: ruta/formato del log, rotación, ocultación de
secretos y QtLogHandler.
"""

import logging
import os
import re
from pathlib import Path

import pytest

from app.services.logging_config import (
    FiltroSecretos,
    QtLogHandler,
    get_log_path,
    setup_logging,
)


@pytest.fixture(autouse=True)
def _limpiar_logging():
    """Guarda y restaura los handlers del logger raíz y el estado del módulo."""
    import app.services.logging_config as lc

    logger = logging.getLogger()
    prev_handlers = list(logger.handlers)
    prev_level = logger.level
    prev_file = lc._file_handler
    prev_qt = lc._qt_handler
    prev_secret = FiltroSecretos._secret_value
    yield
    # Restaurar estado
    for h in list(logger.handlers):
        if h not in prev_handlers:
            logger.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass
    logger.setLevel(prev_level)
    lc._file_handler = prev_file
    lc._qt_handler = prev_qt
    FiltroSecretos._secret_value = prev_secret


class TestRutaYFormato:
    """1.1: setup_logging() crea el fichero y las entradas incluyen timestamp/nivel/módulo."""

    def test_get_log_path_linux(self):
        """En Linux la ruta es $XDG_CONFIG_HOME/PyIssuesTracker/pyissuestracker.log."""
        expected = (
            Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
            / "PyIssuesTracker"
            / "pyissuestracker.log"
        )
        assert get_log_path() == expected

    def test_setup_logging_crea_fichero(self, tmp_path):
        """setup_logging(log_dir=...) crea el fichero de log en ese directorio."""
        setup_logging(log_dir=str(tmp_path))
        assert (tmp_path / "pyissuestracker.log").exists()

    def test_entradas_con_timestamp_nivel_y_modulo(self, tmp_path):
        """Las entradas incluyen marca de tiempo, nivel y módulo."""
        setup_logging(log_dir=str(tmp_path))
        logging.getLogger("mi.modulo.prueba").info("mensaje de prueba")
        contenido = (tmp_path / "pyissuestracker.log").read_text(encoding="utf-8")
        assert "mensaje de prueba" in contenido
        assert "INFO" in contenido
        assert "mi.modulo.prueba" in contenido
        assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", contenido)

    def test_setup_logging_idempotente(self, tmp_path):
        """Llamar dos veces no duplica handlers."""
        setup_logging(log_dir=str(tmp_path))
        setup_logging(log_dir=str(tmp_path))
        logger = logging.getLogger()
        file_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert len(file_handlers) == 1


class TestRotacion:
    """1.2: al superar el tamaño máximo, RotatingFileHandler rota y conserva backups."""

    def test_rota_y_conserva_backups(self, tmp_path):
        setup_logging(log_dir=str(tmp_path), max_bytes=500, backup_count=2)
        logger = logging.getLogger("rotacion")
        for i in range(200):
            logger.warning("mensaje de relleno número %d para forzar la rotación", i)
        # El fichero principal existe y al menos un backup se ha creado
        assert (tmp_path / "pyissuestracker.log").exists()
        backups = sorted(tmp_path.glob("pyissuestracker.log.*"))
        assert len(backups) >= 1


class TestOcultacionSecretos:
    """1.3: la API key y la cabecera X-Redmine-API-Key no aparecen en el fichero."""

    def test_redacta_cabecera_y_valor_de_api_key(self, tmp_path):
        FiltroSecretos.set_secret_value("sk-secreto-123")
        setup_logging(log_dir=str(tmp_path))
        logger = logging.getLogger("secretos")
        logger.error("Petición con X-Redmine-API-Key: sk-secreto-123 falló")
        logger.error("URL con api_key=sk-secreto-123 y más texto")
        logger.error("El valor suelto sk-secreto-123 no debe aparecer")
        contenido = (tmp_path / "pyissuestracker.log").read_text(encoding="utf-8")
        assert "sk-secreto-123" not in contenido
        assert "[REDACTADO]" in contenido

    def test_filtro_devuelve_true_siempre(self):
        """filter() devuelve True (nunca descarta el record)."""
        filtro = FiltroSecretos()
        record = logging.LogRecord("m", logging.INFO, __file__, 1, "hola", None, None)
        assert filtro.filter(record) is True


class TestQtLogHandler:
    """1.4: QtLogHandler emite una señal Qt al recibir un LogRecord."""

    def test_emite_senal_con_mensaje_formateado(self, qapp):
        handler = QtLogHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        recibidos = []
        handler.mensaje_emitido.connect(recibidos.append)
        record = logging.LogRecord(
            "mi.modulo", logging.WARNING, __file__, 1, "mensaje de prueba", None, None
        )
        handler.emit(record)
        assert recibidos == ["WARNING mi.modulo: mensaje de prueba"]

    def test_emite_senal_con_secreto_redactado(self, qapp):
        FiltroSecretos.set_secret_value("sk-otro-secreto")
        handler = QtLogHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.addFilter(FiltroSecretos())
        recibidos = []
        handler.mensaje_emitido.connect(recibidos.append)
        record = logging.LogRecord(
            "m", logging.ERROR, __file__, 1, "api_key=sk-otro-secreto", None, None
        )
        # handle() aplica los filtros del handler antes de emit()
        handler.handle(record)
        assert recibidos == ["api_key=[REDACTADO]"]


class TestSetupLoggingBajoPytest:
    """8.8: setup_logging() no escribe fichero bajo pytest sin log_dir explícito."""

    def test_sin_log_dir_bajo_pytest_no_anade_file_handler(self, monkeypatch):
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_logging_config.py::test_x")
        setup_logging(log_dir=None)
        logger = logging.getLogger()
        file_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.handlers.RotatingFileHandler)
        ]
        assert file_handlers == []

    def test_con_log_dir_si_crea_fichero(self, tmp_path):
        """Con log_dir explícito el fichero se crea igualmente bajo pytest."""
        setup_logging(log_dir=str(tmp_path))
        assert (tmp_path / "pyissuestracker.log").exists()