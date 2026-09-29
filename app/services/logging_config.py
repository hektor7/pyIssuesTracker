"""Configuración central del logging de PyIssuesTracker.

Proporciona:
- `setup_logging()`: configura el logger raíz con un `RotatingFileHandler`
  en la carpeta de configuración del usuario y un `QtLogHandler` para la
  ventana de depuración. Idempotente: llamadas repetidas no duplican handlers.
- `FiltroSecretos`: redacta la API key de Redmine y credenciales en los
  mensajes antes de escribirlos.
- `QtLogHandler`: handler de logging que emite una señal Qt (sin conflicto de
  metaclase) para que la ventana de depuración muestre los mensajes en vivo.
"""

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

# Estado de módulo para la idempotencia de setup_logging()
_file_handler: RotatingFileHandler | None = None
_qt_handler: "QtLogHandler | None" = None

_FORMATO = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def get_log_path() -> Path:
    """Ruta del fichero de log en la carpeta de configuración del usuario.

    En Linux: $XDG_CONFIG_HOME/PyIssuesTracker/pyissuestracker.log
    (por defecto ~/.config/PyIssuesTracker/pyissuestracker.log).
    """
    base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    path = base / "PyIssuesTracker" / "pyissuestracker.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


class FiltroSecretos(logging.Filter):
    """Redacta secretos (API key de Redmine, cabecera X-Redmine-API-Key, api_key=).

    `filter()` devuelve siempre True (nunca descarta el record), pero muta
    `record.msg` y `record.args` para que el valor del secreto nunca llegue
    al fichero de log.
    """

    _secret_value: str = ""

    @classmethod
    def set_secret_value(cls, value: str):
        cls._secret_value = value or ""

    def filter(self, record: logging.LogRecord) -> bool:
        secret = self._secret_value
        if not secret:
            # Fallback: leer la API key configurada si está disponible (fail-open)
            try:
                from app.services.settings_manager import SettingsManager
                secret = SettingsManager().redmine_api_key or ""
            except Exception:
                secret = ""
        if isinstance(record.msg, str):
            record.msg = self._redact(record.msg, secret)
        if record.args:
            record.args = self._redact_args(record.args, secret)
        return True

    @staticmethod
    def _redact(text: str, secret: str) -> str:
        text = re.sub(r"(X-Redmine-API-Key:\s*)[^\s]+", r"\1[REDACTADO]", text)
        text = re.sub(r"(api_key=)[^\s&]+", r"\1[REDACTADO]", text)
        if secret:
            text = text.replace(secret, "[REDACTADO]")
        return text

    @classmethod
    def _redact_args(cls, args, secret: str):
        if isinstance(args, dict):
            return {
                k: cls._redact(v, secret) if isinstance(v, str) else v
                for k, v in args.items()
            }
        if isinstance(args, tuple):
            return tuple(
                cls._redact(a, secret) if isinstance(a, str) else a
                for a in args
            )
        return args


class _LogBridge(QObject):
    """Puente QObject que transporta la señal del handler de logging."""

    mensaje_emitido = pyqtSignal(str)


class QtLogHandler(logging.Handler):
    """Handler de logging que emite una señal Qt con el mensaje formateado.

    QObject y logging.Handler no pueden heredarse juntos (conflicto de
    metaclase), por eso la señal vive en un puente `_LogBridge` interno.
    """

    def __init__(self, level: int = logging.NOTSET):
        super().__init__(level)
        self._bridge = _LogBridge()
        self.mensaje_emitido = self._bridge.mensaje_emitido

    def emit(self, record: logging.LogRecord):
        try:
            self._bridge.mensaje_emitido.emit(self.format(record))
        except Exception:
            self.handleError(record)


def get_qt_handler() -> QtLogHandler | None:
    """Devuelve el QtLogHandler configurado (o None si no se ha configurado)."""
    return _qt_handler


def setup_logging(
    log_dir: str | None = None,
    level: int = logging.INFO,
    max_bytes: int = 1_000_000,
    backup_count: int = 3,
    enable_qt_handler: bool = True,
) -> logging.Logger:
    """Configura el logger raíz con fichero rotativo + filtro de secretos.

    Idempotente: si ya existe un RotatingFileHandler para la misma ruta, no se
    duplica; si la ruta cambia, se reemplaza el handler anterior.

    Args:
        log_dir: Directorio del fichero de log. Si es None, se usa la carpeta
            de configuración del usuario (get_log_path()).
        level: Nivel mínimo del logger raíz.
        max_bytes: Tamaño máximo del fichero antes de rotar.
        backup_count: Número de backups conservados.
        enable_qt_handler: Si True, añade el QtLogHandler para la ventana de
            depuración (solo la primera vez).

    Returns:
        El logger raíz configurado.
    """
    global _file_handler, _qt_handler

    logger = logging.getLogger()
    logger.setLevel(level)
    # Nota: el FiltroSecretos se añade a los HANDLERS (no al logger raíz):
    # desde Python 3.12, Logger.filter() ya no consulta los filtros de los
    # ancestros, por lo que un filtro en el raíz no se aplicaría a los
    # records de los loggers hijos. Los filtros de handler sí se aplican
    # siempre en Handler.handle().

    if log_dir is None:
        path = get_log_path()
    else:
        path = Path(log_dir) / "pyissuestracker.log"
    path.parent.mkdir(parents=True, exist_ok=True)

    # Bajo pytest y sin log_dir explícito NO se añade el RotatingFileHandler:
    # evita escribir en el log real del usuario (~/.config/PyIssuesTracker/...)
    # durante la ejecución de los tests. Si hubiera un handler previo (p. ej.
    # de un test con log_dir=tmp_path) se retira para no dejar handlers
    # huérfanos. El QtLogHandler se mantiene según enable_qt_handler. Con
    # log_dir explícito (p. ej. tmp_path) el fichero sí se crea.
    bajo_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST"))
    if log_dir is None and bajo_pytest:
        if _file_handler is not None:
            logger.removeHandler(_file_handler)
            _file_handler.close()
            _file_handler = None
    else:
        if _file_handler is not None:
            if str(_file_handler.baseFilename) == str(path):
                _file_handler.setLevel(level)
            else:
                logger.removeHandler(_file_handler)
                _file_handler.close()
                _file_handler = None

        if _file_handler is None:
            _file_handler = RotatingFileHandler(
                path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            _file_handler.setFormatter(logging.Formatter(_FORMATO))
            _file_handler.addFilter(FiltroSecretos())
            logger.addHandler(_file_handler)

    if enable_qt_handler and _qt_handler is None:
        _qt_handler = QtLogHandler()
        _qt_handler.setFormatter(logging.Formatter(_FORMATO))
        _qt_handler.addFilter(FiltroSecretos())
        logger.addHandler(_qt_handler)

    return logger