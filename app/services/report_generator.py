"""Generador de informes ODS (OpenDocument Spreadsheet) con odfpy.

Módulo desacoplado de la UI: no importa PyQt y puede probarse sin QApplication.
"""
import os
import re
from datetime import date, datetime

from odf import style, table, text
from odf.opendocument import OpenDocumentSpreadsheet

# Caracteres prohibidos en nombres de hoja ODF ([ ] : * ? / \)
# más caracteres de control (C0 y DEL).
_FORBIDDEN_CHARS = re.compile(r'[\[\]:*?/\\\x00-\x1f\x7f]')

# Ancho mínimo/máximo de columna en cm y factor de conversión carácter -> cm
_MIN_COL_WIDTH_CM = 3.0
_MAX_COL_WIDTH_CM = 40.0
_CHAR_WIDTH_CM = 0.22

# Columnas del informe de tareas (orden establecido en el cambio add-ods-report-export)
REPORT_COLUMNS = [
    "ID", "Proyecto", "Tracker", "Título", "Estado", "Prioridad",
    "Asignado a", "Creado por", "Fecha de creación", "Fecha de inicio",
    "Fecha de fin", "% Progreso", "Categoría", "Última modificación",
    "Usuarios implicados",
]


def sanitize_sheet_name(name: str, max_length: int = 31) -> str:
    """Sanea un nombre de hoja para que sea válido en un documento ODF.

    Elimina los caracteres prohibidos por ODF ([ ] : * ? / \\) y los
    caracteres de control, recorta los espacios de los extremos y, si el
    resultado queda vacío, devuelve "Informe". Finalmente trunca a
    max_length caracteres.

    Args:
        name: Nombre de hoja propuesto.
        max_length: Longitud máxima permitida (por defecto 31, límite ODF).

    Returns:
        Nombre de hoja saneado.
    """
    cleaned = _FORBIDDEN_CHARS.sub("", name)
    cleaned = cleaned.strip()
    if not cleaned:
        cleaned = "Informe"
    return cleaned[:max_length]


class ReportGenerator:
    """Escribe un fichero ODS a partir de columnas y filas.

    La primera fila es la cabecera (en negrita y congelada) y cada llamada
    a add_row añade una fila de datos. Las fechas se escriben como celdas de
    tipo fecha ODF y los números como celdas de tipo float.
    """

    def __init__(self, columns: list[str], sheet_name: str = "Informe"):
        self._columns = list(columns)
        self._sheet_name = sanitize_sheet_name(sheet_name)
        self._rows: list[list] = []

    def add_row(self, values: list) -> None:
        """Añade una fila de datos al informe."""
        self._rows.append(list(values))

    def write(self, path) -> str:
        """Escribe el ODS en la ruta indicada y devuelve la ruta escrita.

        Crea los directorios intermedios si no existen.
        """
        parent = os.path.dirname(os.path.abspath(path))
        os.makedirs(parent, exist_ok=True)

        doc = OpenDocumentSpreadsheet()

        # Estilo de celda de cabecera: negrita
        bold_style = style.Style(name="Cabecera", family="table-cell")
        bold_style.addElement(style.TextProperties(fontweight="bold"))
        doc.automaticstyles.addElement(bold_style)

        tbl = table.Table(name=self._sheet_name)

        # Columnas con ancho razonable según el contenido
        for col_index in range(len(self._columns)):
            col_style = style.Style(name=f"col{col_index}", family="table-column")
            col_style.addElement(style.TableColumnProperties(
                columnwidth=self._column_width(col_index)
            ))
            doc.automaticstyles.addElement(col_style)
            tbl.addElement(table.TableColumn(stylename=col_style))

        # Cabecera congelada (table:table-header-rows) y en negrita
        header_rows = table.TableHeaderRows()
        header_row = table.TableRow()
        for col in self._columns:
            cell = table.TableCell(valuetype="string", stylename=bold_style)
            cell.addElement(text.P(text=str(col)))
            header_row.addElement(cell)
        header_rows.addElement(header_row)
        tbl.addElement(header_rows)

        # Filas de datos
        for values in self._rows:
            row = table.TableRow()
            for value in values:
                row.addElement(self._make_cell(value))
            tbl.addElement(row)

        doc.spreadsheet.addElement(tbl)
        doc.save(path)
        return path

    def _column_width(self, col_index: int) -> str:
        """Estima un ancho de columna (en cm) a partir del contenido."""
        max_len = len(str(self._columns[col_index]))
        for row in self._rows:
            if col_index < len(row):
                max_len = max(max_len, len(str(row[col_index])))
        width = max(_MIN_COL_WIDTH_CM, min(_MAX_COL_WIDTH_CM, max_len * _CHAR_WIDTH_CM))
        return f"{width:.1f}cm"

    @staticmethod
    def _make_cell(value):
        """Crea una celda ODF con el tipo adecuado según el valor."""
        if isinstance(value, bool):
            # bool es subclase de int en Python: tratarlo como texto
            cell = table.TableCell(valuetype="string")
            cell.addElement(text.P(text=str(value)))
            return cell
        if isinstance(value, datetime):
            cell = table.TableCell(
                valuetype="date",
                datevalue=value.strftime("%Y-%m-%dT%H:%M:%S"),
            )
            cell.addElement(text.P(text=value.strftime("%d/%m/%Y %H:%M")))
            return cell
        if isinstance(value, date):
            cell = table.TableCell(
                valuetype="date",
                datevalue=value.strftime("%Y-%m-%dT00:00:00"),
            )
            cell.addElement(text.P(text=value.strftime("%d/%m/%Y")))
            return cell
        if isinstance(value, (int, float)):
            cell = table.TableCell(valuetype="float", value=float(value))
            cell.addElement(text.P(text=str(value)))
            return cell
        cell = table.TableCell(valuetype="string")
        cell.addElement(text.P(text=str(value)))
        return cell