"""Utilidades de formateo de fechas.

La API de Redmine usa formato ISO (YYYY-MM-DD) y timestamps ISO 8601
(YYYY-MM-DDTHH:MM:SSZ), pero la UI muestra formato europeo (DD/MM/YYYY)
y fecha/hora compacta (DD/MM/YY HH:MM).
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


def iso_datetime_to_display(iso_str: str) -> str:
    """Convierte timestamp ISO 8601 a formato 'DD/MM/YY HH:MM'.

    Soporta: 'YYYY-MM-DDTHH:MM:SSZ', 'YYYY-MM-DDTHH:MM:SS+XX:XX',
    'YYYY-MM-DD'. Si no tiene hora, muestra solo la fecha.
    Retorna cadena vacía si iso_str está vacío o no es parseable.
    """
    if not iso_str or not iso_str.strip():
        return ""

    s = iso_str.strip()
    try:
        # Separar fecha y hora por 'T' o espacio
        if "T" in s:
            date_part, time_part = s.split("T", 1)
        elif " " in s:
            date_part, time_part = s.split(" ", 1)
        else:
            date_part = s
            time_part = ""

        # Parsear fecha: YYYY-MM-DD -> DD/MM/YY
        parts = date_part.split("-")
        if len(parts) != 3:
            return iso_str
        year = parts[0][2:] if len(parts[0]) >= 4 else parts[0]  # 2 últimos dígitos
        display_date = f"{parts[2]}/{parts[1]}/{year}"

        # Parsear hora si existe: HH:MM:SS[.fff][Z|+XX:XX|-XX:XX]
        if time_part:
            # Eliminar timezone y fracciones de segundo
            time_clean = time_part
            for sep in ("+", "-", "Z"):
                idx = time_clean.find(sep)
                if idx > 0:
                    time_clean = time_clean[:idx]
                    break
            # Tomar solo HH:MM
            time_parts = time_clean.split(":")
            if len(time_parts) >= 2:
                display_time = f"{time_parts[0]}:{time_parts[1]}"
                return f"{display_date} {display_time}"
            # Si solo tiene horas, mostrar igual
            return f"{display_date} {time_clean}"

        return display_date
    except (ValueError, IndexError):
        return iso_str
