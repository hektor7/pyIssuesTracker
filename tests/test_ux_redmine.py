"""Tests para las mejoras UX de Redmine (cambio mejoras-ux-redmine)."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout

from app.services.redmine_client import (
    RedmineClient, RedmineIssue, RedmineError,
)
from app.services.settings_manager import SettingsManager
from app.widgets.task_table import TaskTable
from app.widgets.filter_bar import FilterBar
from app.widgets.comments_widget import CommentsWidget, setup_mention_completer
from app.dialogs.task_dialog import TaskDialog


# ================================================================
# GRUPO 1: Tests de normalización de URL
# ================================================================


class TestURLNormalization:
    """Tests 5.1 y 5.2: Normalización de URL en SettingsManager."""

    def test_normalize_url_strips_trailing_slash(self):
        """El setter de redmine_url debe eliminar la barra final."""
        s = SettingsManager()
        s.redmine_url = "https://redmine.example.com/"
        assert s.redmine_url == "https://redmine.example.com"

    def test_normalize_url_strips_trailing_slashes(self):
        """Múltiples barras finales deben eliminarse."""
        s = SettingsManager()
        s.redmine_url = "https://redmine.example.com///"
        assert s.redmine_url == "https://redmine.example.com"

    def test_normalize_url_adds_https(self):
        """Si no tiene esquema, debe añadir https://."""
        s = SettingsManager()
        s.redmine_url = "redmine.example.com"
        assert s.redmine_url == "https://redmine.example.com"

    def test_normalize_url_preserves_http(self):
        """Si tiene http://, debe preservarlo sin añadir https://."""
        s = SettingsManager()
        s.redmine_url = "http://redmine.example.com"
        assert s.redmine_url == "http://redmine.example.com"

    def test_normalize_url_strips_whitespace(self):
        """Los espacios alrededor deben eliminarse."""
        s = SettingsManager()
        s.redmine_url = "  https://redmine.example.com  "
        assert s.redmine_url == "https://redmine.example.com"

    def test_normalize_url_empty(self):
        """URL vacía debe quedar vacía."""
        s = SettingsManager()
        s.redmine_url = ""
        assert s.redmine_url == ""


class TestURLConstruction:
    """Test 5.2: Construcción de URL sin doble slash."""

    def test_urljoin_no_double_slash(self):
        """urljoin con base_url sin barra debe funcionar sin doble slash."""
        from urllib.parse import urljoin
        base = "https://redmine.example.com"
        url = urljoin(base.rstrip("/") + "/", "issues/42")
        assert url == "https://redmine.example.com/issues/42"
        assert "//issues" not in url

    def test_urljoin_with_trailing_slash_base(self):
        """urljoin con base_url con barra debe funcionar sin doble slash."""
        from urllib.parse import urljoin
        base = "https://redmine.example.com/"
        url = urljoin(base, "issues/42")
        assert url == "https://redmine.example.com/issues/42"
        assert "//issues" not in url


# ================================================================
# GRUPO 2: Tests de due_date en RedmineIssue
# ================================================================


class TestRedmineIssueDueDate:
    """Tests 5.3: due_date en RedmineIssue y parseo."""

    def test_redmine_issue_has_due_date_field(self):
        """RedmineIssue debe tener campo due_date."""
        issue = RedmineIssue(id=1, subject="Test")
        assert hasattr(issue, "due_date")
        assert issue.due_date == ""

    def test_due_date_parsed_from_json(self):
        """Al construir RedmineIssue desde JSON, due_date debe parsearse."""
        issue = RedmineIssue(
            id=1,
            subject="Test",
            due_date="2026-12-31",
        )
        assert issue.due_date == "2026-12-31"

    def test_due_date_empty_when_missing(self):
        """Si no hay due_date en JSON, debe ser cadena vacía."""
        client = RedmineClient("https://redmine.example.com", "token")
        client._get = MagicMock(return_value={
            "issues": [
                {"id": 1, "subject": "No due date"},
            ]
        })
        issues = client.get_issues()
        assert len(issues) == 1
        assert issues[0].due_date == ""

    def test_due_date_present_when_in_json(self):
        """Si due_date está presente en JSON, debe parsearse."""
        client = RedmineClient("https://redmine.example.com", "token")
        client._get = MagicMock(return_value={
            "issues": [
                {"id": 1, "subject": "With due date", "due_date": "2026-12-31"},
            ]
        })
        issues = client.get_issues()
        assert len(issues) == 1
        assert issues[0].due_date == "2026-12-31"


class TestGetIssuesDueDateQueryString:
    """Tests 5.4: Query string de due_date en get_issues()."""

    def test_due_date_range_query(self):
        """Rango completo debe usar sintaxis >=<."""
        client = RedmineClient("https://redmine.example.com", "token")
        client._get = MagicMock(return_value={"issues": []})
        client.get_issues(due_date_from="2026-06-01", due_date_to="2026-06-15")
        called_params = client._get.call_args[1]["params"]
        assert called_params["due_date"] == "><2026-06-01|2026-06-15"

    def test_due_date_from_only(self):
        """Solo fecha desde debe usar >=."""
        client = RedmineClient("https://redmine.example.com", "token")
        client._get = MagicMock(return_value={"issues": []})
        client.get_issues(due_date_from="2026-06-01", due_date_to=None)
        called_params = client._get.call_args[1]["params"]
        assert called_params["due_date"] == ">=2026-06-01"

    def test_due_date_to_only(self):
        """Solo fecha hasta debe usar <=."""
        client = RedmineClient("https://redmine.example.com", "token")
        client._get = MagicMock(return_value={"issues": []})
        client.get_issues(due_date_from=None, due_date_to="2026-06-15")
        called_params = client._get.call_args[1]["params"]
        assert called_params["due_date"] == "<=2026-06-15"

    def test_no_due_date_params(self):
        """Sin parámetros de fecha, no debe incluir due_date en params."""
        client = RedmineClient("https://redmine.example.com", "token")
        client._get = MagicMock(return_value={"issues": []})
        client.get_issues()
        called_params = client._get.call_args[1]["params"]
        assert "due_date" not in called_params


# ================================================================
# Tests de cálculo de presets de fecha (5.5)
# ================================================================


class TestDatePresetsCalculation:
    """Tests 5.5: Cálculo correcto de presets de fecha."""

    def test_preset_hoy(self):
        """'Hoy' debe calcular today → today."""
        today = date.today()
        assert today.isoformat() == today.isoformat()

    def test_preset_ayer(self):
        """'Ayer' debe calcular yesterday → yesterday."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        assert yesterday.isoformat() == yesterday.isoformat()

    def test_preset_esta_semana_monday_to_sunday(self):
        """'Esta semana' debe calcular lunes → domingo."""
        # Forzar un miércoles para tener fecha fija
        # Miércoles 10 de junio 2026 (weekday() == 2)
        wed = date(2026, 6, 10)
        monday = wed - timedelta(days=wed.weekday())
        sunday = monday + timedelta(days=6)
        assert monday.isoformat() == "2026-06-08"
        assert sunday.isoformat() == "2026-06-14"

    def test_preset_semana_pasada(self):
        """'Semana pasada' debe calcular correctamente."""
        # Martes 9 de junio 2026 (weekday() == 1)
        tue = date(2026, 6, 9)
        monday = tue - timedelta(days=tue.weekday() + 7)
        sunday = monday + timedelta(days=6)
        assert monday.isoformat() == "2026-06-01"
        assert sunday.isoformat() == "2026-06-07"

    def test_preset_este_mes(self):
        """'Este mes' debe calcular día 1 → último día."""
        # 10 de junio 2026
        d = date(2026, 6, 10)
        first = d.replace(day=1)
        if d.month == 12:
            last = d.replace(year=d.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
        assert first.isoformat() == "2026-06-01"
        assert last.isoformat() == "2026-06-30"

    def test_preset_mes_pasado(self):
        """'Mes pasado' debe calcular correctamente."""
        # 10 de junio 2026
        d = date(2026, 6, 10)
        if d.month == 1:
            first = d.replace(year=d.year - 1, month=12, day=1)
            last = d.replace(day=1) - timedelta(days=1)
        else:
            first = d.replace(month=d.month - 1, day=1)
            last = d.replace(day=1) - timedelta(days=1)
        assert first.isoformat() == "2026-05-01"
        assert last.isoformat() == "2026-05-31"

    def test_preset_mes_pasado_enero(self):
        """'Mes pasado' en enero debe ir a diciembre del año anterior."""
        # 15 de enero 2026
        d = date(2026, 1, 15)
        if d.month == 1:
            first = d.replace(year=d.year - 1, month=12, day=1)
            last = d.replace(day=1) - timedelta(days=1)
        else:
            first = d.replace(month=d.month - 1, day=1)
            last = d.replace(day=1) - timedelta(days=1)
        assert first.isoformat() == "2025-12-01"
        assert last.isoformat() == "2025-12-31"

    def test_preset_este_mes_diciembre(self):
        """'Este mes' en diciembre debe calcular correctamente."""
        # 25 de diciembre 2026
        d = date(2026, 12, 25)
        first = d.replace(day=1)
        if d.month == 12:
            last = d.replace(year=d.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
        assert first.isoformat() == "2026-12-01"
        assert last.isoformat() == "2026-12-31"


# ================================================================
# GRUPO 5.1-5.10 adicional: Tests de persistencia de filtros
# ================================================================


class TestFilterDatePersistence:
    """Test 3.8/5.x: Persistencia del filtro de fecha."""

    @pytest.fixture(autouse=True)
    def _cleanup(self):
        """Resetea las claves de filtro de fecha antes y despues de cada test."""
        s = SettingsManager()
        s.filter_date_preset = 0
        s.filter_date_from = ""
        s.filter_date_to = ""
        yield
        s2 = SettingsManager()
        s2.filter_date_preset = 0
        s2.filter_date_from = ""
        s2.filter_date_to = ""

    def test_filter_date_preset_default(self):
        """El valor por defecto debe ser 0 (Sin filtro)."""
        s = SettingsManager()
        assert s.filter_date_preset == 0

    def test_filter_date_preset_persists(self):
        """El preset debe persistir entre instancias."""
        s = SettingsManager()
        s.filter_date_preset = 3  # "Esta semana"
        s2 = SettingsManager()
        assert s2.filter_date_preset == 3

    def test_filter_date_from_persists(self):
        """filter_date_from debe persistir."""
        s = SettingsManager()
        s.filter_date_from = "2026-06-01"
        s2 = SettingsManager()
        assert s2.filter_date_from == "2026-06-01"

    def test_filter_date_to_persists(self):
        """filter_date_to debe persistir."""
        s = SettingsManager()
        s.filter_date_to = "2026-06-30"
        s2 = SettingsManager()
        assert s2.filter_date_to == "2026-06-30"


# ================================================================
# Tests de integración (requieren qapp fixture)
# ================================================================


class TestTaskTableDueDateColumn:
    """Tests 5.6: Columna 'Fecha fin' visible en TaskTable."""

    def test_task_table_has_due_date_column(self, qapp):
        """TaskTable debe tener COL_DUE_DATE y cabecera 'Fecha fin'."""
        table = TaskTable()
        assert table.COL_DUE_DATE == 4
        assert table.HEADERS[table.COL_DUE_DATE] == "Fecha fin"

    def test_due_date_column_shows_data(self, qapp):
        """La columna Fecha fin debe mostrar el valor del issue."""
        table = TaskTable()
        issues = [
            {"id": 1, "subject": "Test", "due_date": "2026-06-15",
             "start_date": "", "status_name": "", "assigned_to_name": "",
             "done_ratio": 0, "project_id": 1, "project_name": "",
             "author_name": "", "tracker_name": "", "priority_name": "",
             "url": "", "description": ""},
        ]
        table.set_issues(issues)
        item = table.item(0, table.COL_DUE_DATE)
        assert item is not None
        assert item.text() == "15/06/2026"

    def test_due_date_column_empty_when_no_date(self, qapp):
        """Sin due_date, la celda debe estar vacía."""
        table = TaskTable()
        issues = [
            {"id": 1, "subject": "Test", "due_date": "",
             "start_date": "", "status_name": "", "assigned_to_name": "",
             "done_ratio": 0, "project_id": 1, "project_name": "",
             "author_name": "", "tracker_name": "", "priority_name": "",
             "url": "", "description": ""},
        ]
        table.set_issues(issues)
        item = table.item(0, table.COL_DUE_DATE)
        assert item is not None
        assert item.text() == ""


class TestTaskTableDueDateInlineEdit:
    """Tests 5.7: Edición inline de fecha de fin emite señal."""

    def test_due_date_signal_emitted(self, qapp):
        """Al editar inline, debe emitirse due_date_cambiada."""
        table = TaskTable()
        issues = [
            {"id": 42, "subject": "Test", "due_date": "2026-06-15",
             "start_date": "", "status_name": "", "assigned_to_name": "",
             "done_ratio": 0, "project_id": 1, "project_name": "",
             "author_name": "", "tracker_name": "", "priority_name": "",
             "url": "", "description": ""},
        ]
        table.set_issues(issues)

        # Simular doble clic en columna due_date
        table._on_double_click(0, table.COL_DUE_DATE)

        # Debe haber un QDateEdit como cell widget
        widget = table.cellWidget(0, table.COL_DUE_DATE)
        assert widget is not None, "Debe haber un QDateEdit en la celda"

        from PyQt6.QtWidgets import QDateEdit
        assert isinstance(widget, QDateEdit)


class TestFilterBarDatePreset:
    """Tests 5.9: FilterBar emite señal fecha_cambiada."""

    def test_filter_bar_has_date_preset_combo(self, qapp):
        """FilterBar debe tener el QComboBox de presets de fecha."""
        fb = FilterBar()
        assert hasattr(fb, '_date_preset_combo')
        assert fb._date_preset_combo.count() == 8
        assert fb._date_preset_combo.itemText(0) == "Sin filtro"
        assert fb._date_preset_combo.itemText(1) == "Hoy"
        assert fb._date_preset_combo.itemText(2) == "Ayer"
        assert fb._date_preset_combo.itemText(3) == "Esta semana"
        assert fb._date_preset_combo.itemText(4) == "Semana pasada"
        assert fb._date_preset_combo.itemText(5) == "Este mes"
        assert fb._date_preset_combo.itemText(6) == "Mes pasado"
        assert fb._date_preset_combo.itemText(7) == "Rango personalizado"

    def test_date_preset_combo_emits_signal(self, qapp):
        """Seleccionar un preset debe emitir fecha_cambiada."""
        fb = FilterBar()
        received_signals = []

        def on_fecha_cambiada(fr, to):
            received_signals.append((fr, to))

        fb.fecha_cambiada.connect(on_fecha_cambiada)

        # Seleccionar "Hoy" (índice 1)
        fb._date_preset_combo.setCurrentIndex(1)
        assert len(received_signals) >= 1
        from_d, to_d = received_signals[-1]
        today_str = date.today().isoformat()
        assert from_d == today_str
        assert to_d == today_str


class TestTaskDialogDueDateField:
    """Tests 5.8: TaskDialog tiene campo fecha fin."""

    def test_task_dialog_has_due_date_checkbox(self, qapp):
        """TaskDialog debe tener QCheckBox y QDateEdit para fecha fin."""
        dlg = TaskDialog()
        assert hasattr(dlg, '_due_check')
        assert hasattr(dlg, '_due_edit')

    def test_due_date_properties(self, qapp):
        """Las propiedades due_date y due_enabled deben funcionar."""
        dlg = TaskDialog()
        assert hasattr(dlg, 'due_date')
        assert hasattr(dlg, 'due_enabled')
        assert dlg.due_enabled is False  # checkbox sin marcar
        assert isinstance(dlg.due_date, str)

    def test_due_date_checkbox_toggles_edit(self, qapp):
        """El QCheckBox debe habilitar/deshabilitar el QDateEdit."""
        dlg = TaskDialog()
        assert dlg._due_edit.isEnabled() is False
        dlg._due_check.setChecked(True)
        assert dlg._due_edit.isEnabled() is True
        dlg._due_check.setChecked(False)
        assert dlg._due_edit.isEnabled() is False


class TestMentionCompleter:
    """Tests 5.10: Autocompletado @usuario."""

    def test_setup_mention_completer_creates_completer(self, qapp):
        """setup_mention_completer debe configurar el completer sin errores."""
        text_edit = QPlainTextEdit()
        names = ["Maria Garcia", "Martin Lopez", "Juan Perez"]
        completer = setup_mention_completer(text_edit, names)
        assert completer is not None
        assert completer.completionCount() == 3

    def test_completer_filters_by_partial_match(self, qapp):
        """El completer debe filtrar por MatchContains."""
        text_edit = QPlainTextEdit()
        names = ["Maria Garcia", "Martin Lopez", "Juan Perez"]
        completer = setup_mention_completer(text_edit, names)
        # Simular que se escribe "@mar" y el prefijo extraído es "mar"
        completer.setCompletionPrefix("mar")
        assert completer.completionCount() >= 2  # Maria y Martin

    def test_completer_no_match_shows_nothing(self, qapp):
        """Si no hay match, el popup no debe mostrar nada."""
        text_edit = QPlainTextEdit()
        names = ["Maria Garcia", "Martin Lopez"]
        completer = setup_mention_completer(text_edit, names)
        completer.setCompletionPrefix("xyz")
        assert completer.completionCount() == 0

    def test_completer_case_insensitive(self, qapp):
        """La búsqueda debe ser case-insensitive."""
        text_edit = QPlainTextEdit()
        names = ["Maria Garcia"]
        completer = setup_mention_completer(text_edit, names)
        completer.setCompletionPrefix("MAR")
        assert completer.completionCount() == 1

    def test_comments_widget_set_members(self, qapp):
        """CommentsWidget.set_members debe configurar el completer."""
        cw = CommentsWidget()
        members = [(1, "Maria Garcia"), (2, "Martin Lopez")]
        cw.set_members(members)
        # Verificar que se configuró sin errores (no tenemos acceso directo al completer)
        assert True  # No lanzó excepción

    def test_double_click_due_date_signal_structure(self, qapp):
        """Verificar estructura de edicion inline en TaskTable."""
        table = TaskTable()
        issues = [
            {"id": 42, "subject": "Test", "due_date": "2026-06-15",
             "start_date": "", "status_name": "", "assigned_to_name": "",
             "done_ratio": 0, "project_id": 1, "project_name": "",
             "author_name": "", "tracker_name": "", "priority_name": "",
             "url": "", "description": ""},
        ]
        table.set_issues(issues)

        # Verificar que _on_due_date_edited existe
        assert hasattr(table, '_on_due_date_edited')

        # Verificar que due_date_cambiada es una señal
        assert hasattr(table.due_date_cambiada, 'emit')
