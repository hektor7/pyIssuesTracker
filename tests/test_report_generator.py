import zipfile
from datetime import date, datetime

import pytest
from odf import table
from odf.opendocument import load

from app.services.report_generator import (
    ReportGenerator, sanitize_sheet_name,
    REPORT_FIELDS, DEFAULT_FIELD_KEYS, REPORT_COLUMNS,
)

# Claves canónicas de los 18 campos del informe (cambio mejoras-generacion-informes)
EXPECTED_FIELD_KEYS = [
    "id", "proyecto", "tracker", "titulo", "descripcion", "estado", "prioridad",
    "asignado_a", "creado_por", "fecha_creacion", "fecha_inicio",
    "fecha_fin", "progreso", "categoria", "ultima_modificacion",
    "usuarios_implicados", "url", "comentarios",
]


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


class TestReportFields:
    """Tests del catálogo REPORT_FIELDS (tarea 1.1)."""

    def test_report_fields_contiene_18_claves_en_orden_canonico(self):
        """REPORT_FIELDS debe tener las 18 claves en el orden canónico."""
        assert [key for key, _ in REPORT_FIELDS] == EXPECTED_FIELD_KEYS
        assert len(REPORT_FIELDS) == 18

    def test_default_field_keys_incluye_todas_las_claves(self):
        """DEFAULT_FIELD_KEYS debe contener todas las claves en orden canónico."""
        assert DEFAULT_FIELD_KEYS == EXPECTED_FIELD_KEYS

    def test_report_columns_son_las_etiquetas_por_compatibilidad(self):
        """REPORT_COLUMNS debe seguir siendo la lista de etiquetas (18)."""
        assert REPORT_COLUMNS == [label for _, label in REPORT_FIELDS]
        assert len(REPORT_COLUMNS) == 18


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

    def test_multiline_value_genera_varios_parrafos_en_la_celda(self, tmp_path):
        """Un valor str con \\n debe generar un text:P por línea en la misma celda."""
        gen = ReportGenerator(["Comentarios"])
        gen.add_row(["línea 1\nlínea 2\nlínea 3"])
        out = tmp_path / "informe.ods"
        gen.write(str(out))
        with zipfile.ZipFile(out) as zf:
            content = zf.read("content.xml").decode("utf-8")
        # 1 párrafo de la cabecera + 3 líneas de la celda de datos
        assert content.count("<text:p") == 4
        # Las tres líneas se conservan en el contenido
        assert "línea 1" in content
        assert "línea 2" in content
        assert "línea 3" in content

    def test_multiline_value_no_rompe_valores_simples(self, tmp_path):
        """Un valor sin \\n sigue generando un único text:P en la celda."""
        gen = ReportGenerator(["Texto"])
        gen.add_row(["Hola"])
        out = tmp_path / "informe.ods"
        gen.write(str(out))
        with zipfile.ZipFile(out) as zf:
            content = zf.read("content.xml").decode("utf-8")
        # 1 párrafo de cabecera + 1 párrafo de datos
        assert content.count("<text:p") == 2