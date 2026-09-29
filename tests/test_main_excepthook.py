"""Tests del sys.excepthook global (S1 / tarea 8.6).

Verifica que _install_excepthook() registra a nivel CRITICAL las excepciones
no capturadas y conserva el comportamiento previo (llama al hook original).
"""

import logging
import sys

import pytest


@pytest.fixture
def main_module():
    import main as main_module
    return main_module


class TestExcepthookGlobal:
    def test_registra_critical_y_delega_al_hook_previo(self, main_module, caplog):
        llamado = []
        sys.excepthook = lambda t, v, tb: llamado.append((t, v, tb))
        main_module._install_excepthook()

        try:
            raise RuntimeError("boom no capturado")
        except RuntimeError:
            tipo, valor, tb = sys.exc_info()

        with caplog.at_level(logging.CRITICAL):
            sys.excepthook(tipo, valor, tb)

        # El hook previo se conserva y se invoca (comportamiento por defecto)
        assert len(llamado) == 1
        assert llamado[0][0] is RuntimeError
        # La excepción no capturada se registra a nivel CRITICAL
        assert any(
            r.levelno == logging.CRITICAL and "boom no capturado" in r.getMessage()
            for r in caplog.records
        )

    def test_no_rompe_si_el_logging_falla(self, main_module, monkeypatch):
        """Un fallo interno del logging no impide delegar al hook previo."""
        llamado = []
        sys.excepthook = lambda t, v, tb: llamado.append((t, v, tb))
        main_module._install_excepthook()

        def _explota(*args, **kwargs):
            raise RuntimeError("logging roto")

        monkeypatch.setattr(
            "app.services.logging_config.setup_logging", _explota
        )

        try:
            raise ValueError("boom")
        except ValueError:
            tipo, valor, tb = sys.exc_info()

        sys.excepthook(tipo, valor, tb)

        assert len(llamado) == 1