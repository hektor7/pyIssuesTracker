"""Parseo puro del formulario HTML de nueva incidencia de Redmine.

Este módulo no importa :mod:`app.services.redmine_client` para evitar un ciclo
de importaciones: la dirección de dependencia es ``redmine_client`` →
``custom_field_definitions``.

Solo se reconocen los controles que necesita la resolución sin permisos de
administrador:

- ``<select>`` simple cuyos valores coinciden con sus etiquetas → ``list``.
- ``<select multiple>`` o con sufijo ``[]`` en el nombre → ``list`` múltiple.
- ``<select>`` con valores no vacíos exactamente ``1`` y ``0`` → ``bool``.

Cualquier otro control (``textarea``, ``input``, radios o checkboxes) se
ignora y el campo queda sin resolver.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

_SELECT_NAME_RE = re.compile(
    r"^issue\[custom_field_values\]\[(?P<id>\d+)\](?P<multiple>\[\])?$"
)


def _normalizar(texto: str) -> str:
    """Decodifica entidades HTML y recorta espacios de un texto."""
    return unescape(texto).strip()


@dataclass
class ParsedCustomField:
    """Definición parcial de un campo personalizado obtenida del HTML."""

    field_format: str = ""
    multiple: bool = False
    possible_values: list[str] = field(default_factory=list)


@dataclass
class _Option:
    """Opción de un ``<select>`` tal y como aparece en el HTML."""

    value: str | None
    text: str = ""


@dataclass
class _Select:
    """Acumulador de un ``<select>`` mientras se parsea."""

    field_id: int
    multiple: bool = False
    options: list[_Option] = field(default_factory=list)


class _IssueFormParser(HTMLParser):
    """Parser mínimo de los ``<select>`` de campos personalizados."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.fields: dict[int, ParsedCustomField] = {}
        self._select: _Select | None = None
        self._option: _Option | None = None
        self._option_text: list[str] = []

    # -- Eventos del parser -------------------------------------------------

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag == "select":
            # Un select anidado o sin cerrar es HTML malformado: se descarta.
            self._discard_select()
            atributos = dict(attrs)
            coincidencia = _SELECT_NAME_RE.match(atributos.get("name") or "")
            if not coincidencia:
                self._select = None
                return
            self._select = _Select(
                field_id=int(coincidencia.group("id")),
                multiple=bool(coincidencia.group("multiple"))
                or "multiple" in atributos,
            )
        elif tag == "option" and self._select is not None:
            self._flush_option()
            self._option = _Option(value=dict(attrs).get("value"))
            self._option_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "option":
            self._flush_option()
        elif tag == "select":
            self._flush_select()

    def handle_data(self, data: str) -> None:
        if self._option is not None:
            self._option_text.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._option is not None:
            self._option_text.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._option is not None:
            self._option_text.append(f"&#{name};")

    # -- Acumulación --------------------------------------------------------

    def _flush_option(self) -> None:
        if self._option is None or self._select is None:
            self._option = None
            self._option_text = []
            return
        texto = "".join(self._option_text).strip()
        self._select.options.append(
            _Option(value=self._option.value, text=texto)
        )
        self._option = None
        self._option_text = []

    def _flush_select(self) -> None:
        if self._select is None:
            return
        if self._option is not None:
            self._flush_option()

        # Si el id ya se reconoció antes, prevalece la primera aparición.
        if self._select.field_id in self.fields:
            self._select = None
            return

        opciones: list[tuple[str, str]] = []
        for opcion in self._select.options:
            valor = _normalizar(
                opcion.value if opcion.value is not None else opcion.text
            )
            if valor == "":
                continue
            opciones.append((valor, _normalizar(opcion.text)))

        # La heurística 1/0 tiene prioridad sobre el discriminador de lista:
        # el payload resultante ("1"/"0") es válido para ambos formatos.
        valores = {valor for valor, _ in opciones}
        if valores == {"1", "0"}:
            self.fields[self._select.field_id] = ParsedCustomField(
                field_format="bool",
                multiple=False,
                possible_values=[],
            )
        elif opciones and all(valor == etiqueta for valor, etiqueta in opciones):
            # Discriminador: solo es una lista seleccionable si cada valor no
            # vacío coincide con su etiqueta. Los desplegables de user/version/
            # enumeration usan un id como valor y quedan fuera.
            self.fields[self._select.field_id] = ParsedCustomField(
                field_format="list",
                multiple=self._select.multiple,
                possible_values=[etiqueta for _, etiqueta in opciones],
            )
        # Un select que no cumple el discriminador (ids de user/version/
        # enumeration) no se reconoce: el campo quedará sin resolver.
        self._select = None

    def flush_pending(self) -> None:
        """Descarta los controles que hayan quedado abiertos al terminar.

        Un ``<select>`` sin ``</select>`` es HTML malformado y no debe
        producir un campo reconocido.
        """
        self._discard_select()

    def _discard_select(self) -> None:
        self._select = None
        self._option = None
        self._option_text = []


def parse_issue_form_custom_fields(
    html: str,
) -> dict[int, ParsedCustomField]:
    """Extrae las definiciones parciales de los controles del formulario.

    Args:
        html: Cuerpo HTML del formulario de nueva incidencia.

    Returns:
        Diccionario ``id de campo → ParsedCustomField`` en orden de aparición.
        Devuelve ``{}`` si no hay controles reconocibles o el HTML es vacío.
    """
    parser = _IssueFormParser()
    try:
        parser.feed(html or "")
        parser.close()
    except Exception as error:  # pragma: no cover - defensa ante HTML extremo
        logger.debug("HTML de formulario no parseable: %s", error)
        return {}
    parser.flush_pending()
    return parser.fields
