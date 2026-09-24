import zipfile
from datetime import date, datetime

import pytest
from odf import table
from odf.opendocument import load

from app.services.report_generator import ReportGenerator, sanitize_sheet_name


class TestSanitizeSheetName:
    """Tests para sanitize_sheet_name (tarea 3.4)."""

    def test_removes_forbidden_characters(self):
        """Los caracteres prohibidos por ODF deben eliminarse o reemplazarse."""
        assert sanitize_sheet_name("Informe [2026]: Final?") == "Informe 2026 Final"
        assert "/" not in sanitize_sheet_name("a/b\\c")
        assert "\\" not in sanitize_sheet_name("a/b\\c")
        assert ":" not in sanitize_sheet_name("a:b")
        assert "*" not in sanitize_sheet_name("a*b")
        assert "?" not in sanitize_sheet_name("a?b")
        assert "[" not in sanitize_sheet_name("a[b")
        assert "]" not in sanitize_sheet_name("a]b")

    def test_empty_name_returns_informe(self):
        """Un nombre vacío o solo con caracteres prohibidos debe devolver 'Informe'."""
        assert sanitize_sheet_name("") == "Informe"
        assert sanitize_sheet_name("[]:*?/\\") == "Informe"

    def test_truncates_to_max_length(self):
        """El nombre debe truncarse a max_length (por defecto 31)."""
        long_name = "x" * 100
        assert len(sanitize_sheet_name(long_name)) == 31
        assert sanitize_sheet_name(long_name) == "x" * 31

    def test_strips_whitespace(self):
        """Los espacios al inicio y al final deben recortarse."""
        assert sanitize_sheet_name("  Informe  ") == "Informe"

    def test_removes_control_characters(self):
        """Los caracteres de control deben eliminarse."""
        assert sanitize_sheet_name("Info\r\n\x00\x07rme") == "Informe"


class TestReportGenerator:
    """Tests para ReportGenerator (tareas 3.2 y 3.3)."""

    def test_write_creates_valid_ods_with_content_xml(self, tmp_path):
        """write() debe crear un ODF válido (ZIP) que contenga content.xml."""
        gen = ReportGenerator(["ID", "Título"])
        gen.add_row([1, "Tarea A"])
        out = tmp_path / "informe.ods"
        written = gen.write(str(out))
        assert written == str(out)
        assert out.exists()
        with zipfile.ZipFile(out) as zf:
            assert "content.xml" in zf.namelist()

    def test_header_is_bold(self, tmp_path):
        """La fila de cabecera debe estar en negrita (font-weight='bold')."""
        gen = ReportGenerator(["ID", "Título"])
        gen.add_row([1, "Tarea A"])
        out = tmp_path / "informe.ods"
        gen.write(str(out))
        with zipfile.ZipFile(out) as zf:
            content = zf.read("content.xml").decode("utf-8")
        assert 'font-weight="bold"' in content

    def test_header_row_is_frozen(self, tmp_path):
        """La cabecera debe estar congelada (table:table-header-rows)."""
        gen = ReportGenerator(["ID", "Título"])
        gen.add_row([1, "Tarea A"])
        out = tmp_path / "informe.ods"
        gen.write(str(out))
        with zipfile.ZipFile(out) as zf:
            content = zf.read("content.xml").decode("utf-8")
        # Assert principal: el bloque congelado existe en content.xml
        assert "table:table-header-rows" in content
        # Comprobación adicional: al reabrir el ODS, la tabla tiene cabecera congelada
        doc = load(str(out))
        tables = doc.spreadsheet.getElementsByType(table.Table)
        assert len(tables) == 1
        assert len(tables[0].getElementsByType(table.TableHeaderRows)) == 1

    def test_number_of_data_rows(self, tmp_path):
        """Debe haber una fila por cada add_row además de la cabecera."""
        gen = ReportGenerator(["ID", "Título"])
        gen.add_row([1, "Tarea A"])
        gen.add_row([2, "Tarea B"])
        gen.add_row([3, "Tarea C"])
        out = tmp_path / "informe.ods"
        gen.write(str(out))
        with zipfile.ZipFile(out) as zf:
            content = zf.read("content.xml").decode("utf-8")
        # 1 cabecera + 3 datos = 4 filas de tabla
        assert content.count("<table:table-row") == 4

    def test_date_and_float_cell_types(self, tmp_path):
        """Las fechas deben ser celdas de tipo fecha y los números de tipo float."""
        gen = ReportGenerator(["Fecha", "Progreso", "Texto"])
        gen.add_row([date(2026, 9, 1), 50, "Hola"])
        gen.add_row([datetime(2026, 9, 2, 10, 30), 100, "Mundo"])
        out = tmp_path / "informe.ods"
        gen.write(str(out))
        with zipfile.ZipFile(out) as zf:
            content = zf.read("content.xml").decode("utf-8")
        assert 'office:value-type="date"' in content
        assert 'office:value-type="float"' in content

    def test_write_returns_path_and_creates_parent_dirs(self, tmp_path):
        """write() debe devolver la ruta escrita y crear directorios intermedios."""
        gen = ReportGenerator(["ID"])
        gen.add_row([1])
        out = tmp_path / "sub" / "dir" / "informe.ods"
        written = gen.write(str(out))
        assert written == str(out)
        assert out.exists()

    def test_sheet_name_is_sanitized(self, tmp_path):
        """El nombre de hoja debe sanearse antes de escribirse."""
        gen = ReportGenerator(["ID"], sheet_name="Informe [2026]: Final?")
        gen.add_row([1])
        out = tmp_path / "informe.ods"
        gen.write(str(out))
        with zipfile.ZipFile(out) as zf:
            content = zf.read("content.xml").decode("utf-8")
        assert "Informe 2026 Final" in content
        assert "Informe [2026]: Final?" not in content