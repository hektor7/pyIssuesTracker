"""Utilidades de formateo de fechas.

La API de Redmine usa formato ISO (YYYY-MM-DD), pero la UI muestra
formato europeo (DD/MM/YYYY). Estas funciones convierten entre ambos.
"""


def iso_to_display(iso_str: str) -> str:
    """Convierte 'YYYY-MM-DD' (o vacío) a 'DD/MM/YYYY' (o vacío)."""
    if not iso_str or not iso_str.strip():
        return ""
    try:
        parts = iso_str.strip().split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
        return iso_str
    except (ValueError, IndexError):
        return iso_str


def display_to_iso(display_str: str) -> str:
    """Convierte 'DD/MM/YYYY' (o vacío) a 'YYYY-MM-DD' (o vacío)."""
    if not display_str or not display_str.strip():
        return ""
    try:
        parts = display_str.strip().split("/")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return display_str
    except (ValueError, IndexError):
        return display_str
