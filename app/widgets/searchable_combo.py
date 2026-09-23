"""Helper compartido para combos buscables (editable + QCompleter MatchContains).

Extraído de TaskDialog para reutilizarlo en ProjectSelectDialog y evitar la
duplicación del patrón combo editable con autocompletado por teclado.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QCompleter, QSizePolicy


def make_searchable_combo() -> QComboBox:
    """Crea un QComboBox editable con QCompleter para búsqueda por teclado (MatchContains).

    Usa QCompleter([], combo) en lugar de QCompleter(combo) para que el modelo
    del completer no dependa del modelo del combo (que se destruye al hacer clear()).
    El caller debe actualizar el modelo llamando a update_completer_model(combo).
    """
    combo = QComboBox()
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    completer = QCompleter([], combo)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    combo.setCompleter(completer)
    combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    # Guardar referencia explícita al completer para acceso posterior
    combo._completer = completer
    return combo


def update_completer_model(combo: QComboBox):
    """Sincroniza el modelo del QCompleter con los items actuales del combo."""
    completer = getattr(combo, '_completer', None)
    if completer:
        names = [combo.itemText(i) for i in range(combo.count())]
        completer.model().setStringList(names)