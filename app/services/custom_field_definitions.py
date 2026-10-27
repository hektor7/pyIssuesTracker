"""Parseo puro del formulario HTML de nueva incidencia de Redmine.

Este módulo no importa :mod:`app.services.redmine_client` para evitar un ciclo
de importaciones: la dirección de dependencia es ``redmine_client`` →
``custom_field_definitions``.

Tabla de controles reconocidos (nombre ``issue[custom_field_values][N]``):

===============================  ===========================================
Control                          Resultado
===============================  ===========================================
``<select>`` simple, valores     ``list``, ``multiple=False``, etiquetas en
iguales a sus etiquetas          orden
``<select multiple>`` o nombre   ``list``, ``multiple=True``
con sufijo ``[]``
``<select>`` no múltiple con     ``bool``, ``multiple=False``, sin opciones
valores no vacíos ``1`` y ``0``
``<textarea>`` sin sufijo        ``text``, ``multiple=False``
``<input type="date">``          ``date``, ``multiple=False``
``<input type="number">``        ``int``, ``multiple=False``
``<input type="text">``          ``string``, ``multiple=False``
``checkbox`` + ``hidden`` con    ``bool``, ``multiple=False``, sin opciones
el mismo nombre sin ``[]``
===============================  ===========================================

Precedencia:

1. Un ``<input type="hidden">`` nunca produce una definición propia. Solo se
   consume si comparte el nombre exacto sin ``[]`` con un ``checkbox``; en ese
   caso ambos forman el par booleano. El ``hidden`` sin pareja, con o sin
   sufijo ``[]``, se descarta y no se clasifica como ``string``.
2. En un ``<select>`` no múltiple, la comprobación ``1``/``0`` (``bool``) se
   evalúa antes del discriminador de lista. En un ``<select multiple>`` o con
   sufijo ``[]``, ``1``/``0`` se resuelve como ``list`` con
   ``multiple=True``.
3. Un ``<select>`` reconocido prevalece sobre cualquier ``input``,
   ``textarea`` o par booleano del mismo id, porque es la única señal que
   aporta ``multiple`` y ``possible_values``. Entre los dos restantes, el par
   ``checkbox`` + ``hidden`` prevalece sobre un ``input``/``textarea`` del
   mismo id, que nunca aparece junto a él en el HTML real de Redmine.
4. Entre controles del mismo tipo prevalece la primera aparición reconocida;
   un segundo control del mismo id no sobrescribe la definición aceptada.
5. El diccionario devuelto conserva el orden de primera aparición de cada id
   en el documento, también entre tipos distintos; un ``select`` posterior no
   adelanta la posición del campo.

Limitaciones inevitables del HTML:

- Los campos ``int``/``float`` reales y las fechas de versiones antiguas de
  Redmine se renderizan como ``<input type="text">`` y se resuelven como
  ``string``: el HTML no permite distinguirlos sin heurísticas frágiles.
- Los grupos de radios y de checkboxes con sufijo ``[]`` no se reconocen,
  incluidas las listas con ``edit_tag_style = check_box``.
- El sufijo ``[]`` solo se admite en ``<select>``; un ``input`` o
  ``textarea`` con sufijo se descarta.
- Los campos de otro tracker o los controles que no aparecen en el formulario
  no pueden resolverse. Tampoco se obtienen ``is_required``,
  ``default_value``, ``visible`` ni ``editable`` desde HTML.
- No se reparan datos corrompidos ni se normalizan valores ya guardados.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

_FIELD_NAME_RE = re.compile(
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
    position: int
    multiple: bool = False
    options: list[_Option] = field(default_factory=list)


class _IssueFormParser(HTMLParser):
    """Parser mínimo de los controles de campos personalizados."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.fields: dict[int, ParsedCustomField] = {}
        self._select: _Select | None = None
        self._option: _Option | None = None
        self._option_text: list[str] = []
        self._select_candidates: dict[int, ParsedCustomField] = {}
        self._text_candidates: dict[int, ParsedCustomField] = {}
        self._checkbox_positions: dict[int, int] = {}
        self._hidden_positions: dict[int, int] = {}
        self._positions: dict[int, int] = {}
        self._sequence = 0

    # -- Eventos del parser -------------------------------------------------

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self._sequence += 1
        posicion = self._sequence

        if tag == "select":
            # Un select anidado o sin cerrar es HTML malformado: se descarta.
            self._discard_select()
            atributos = dict(attrs)
            coincidencia = _FIELD_NAME_RE.match(atributos.get("name") or "")
            if not coincidencia:
                self._select = None
                return
            self._select = _Select(
                field_id=int(coincidencia.group("id")),
                position=posicion,
                multiple=bool(coincidencia.group("multiple"))
                or "multiple" in atributos,
            )
        elif tag == "textarea":
            atributos = dict(attrs)
            coincidencia = _FIELD_NAME_RE.match(atributos.get("name") or "")
            if coincidencia and not coincidencia.group("multiple"):
                self._record_text(
                    int(coincidencia.group("id")), "text", posicion
                )
        elif tag == "input":
            atributos = dict(attrs)
            coincidencia = _FIELD_NAME_RE.match(atributos.get("name") or "")
            tipo = (atributos.get("type") or "").strip().lower()
            nombre_sin_sufijo = bool(coincidencia) and not coincidencia.group(
                "multiple"
            )
            if tipo == "hidden":
                # El ``hidden`` nunca produce una definición propia: solo se
                # consume si forma el par booleano con un ``checkbox``.
                if nombre_sin_sufijo:
                    field_id = int(coincidencia.group("id"))
                    self._hidden_positions.setdefault(field_id, posicion)
                    if field_id in self._checkbox_positions:
                        # El par se completa aquí: su posición es la primera
                        # aparición real del id entre ambos controles.
                        self._record_position(
                            field_id,
                            min(
                                self._checkbox_positions[field_id],
                                self._hidden_positions[field_id],
                            ),
                        )
                return
            if tipo == "checkbox":
                # Un checkbox aislado no se reconoce; se consume solo si tiene
                # un ``hidden`` pareja del mismo nombre sin sufijo.
                if nombre_sin_sufijo:
                    field_id = int(coincidencia.group("id"))
                    self._checkbox_positions.setdefault(field_id, posicion)
                    if field_id in self._hidden_positions:
                        self._record_position(
                            field_id,
                            min(
                                self._checkbox_positions[field_id],
                                self._hidden_positions[field_id],
                            ),
                        )
                return
            formato = {
                "date": "date",
                "number": "int",
                "text": "string",
            }.get(tipo)
            if nombre_sin_sufijo and formato is not None:
                self._record_text(
                    int(coincidencia.group("id")), formato, posicion
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

    def _record_position(self, field_id: int, posicion: int) -> None:
        """Conserva la primera aparición real del id en el documento.

        La posición puede descubrirse tarde (por ejemplo, al completarse el
        par booleano), por lo que se queda con el menor valor visto.
        """
        actual = self._positions.get(field_id)
        if actual is None or posicion < actual:
            self._positions[field_id] = posicion

    def _record_text(
        self, field_id: int, field_format: str, posicion: int
    ) -> None:
        """Registra un candidato ``input``/``textarea`` y su posición.

        Prevalece la primera aparición reconocida del id para ese tipo de
        control; un segundo control del mismo id no la sobrescribe.
        """
        if field_id in self._text_candidates:
            return
        self._text_candidates[field_id] = ParsedCustomField(
            field_format=field_format
        )
        self._record_position(field_id, posicion)

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
        if self._select.field_id in self._select_candidates:
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

        field_id = self._select.field_id
        definicion: ParsedCustomField | None = None

        # La heurística 1/0 tiene prioridad sobre el discriminador de lista,
        # pero solo para un select NO múltiple: en múltiple, 1/0 es una lista.
        valores = {valor for valor, _ in opciones}
        if valores == {"1", "0"} and not self._select.multiple:
            definicion = ParsedCustomField(
                field_format="bool",
                multiple=False,
                possible_values=[],
            )
        elif opciones and all(valor == etiqueta for valor, etiqueta in opciones):
            # Discriminador: solo es una lista seleccionable si cada valor no
            # vacío coincide con su etiqueta. Los desplegables de user/version/
            # enumeration usan un id como valor y quedan fuera.
            definicion = ParsedCustomField(
                field_format="list",
                multiple=self._select.multiple,
                possible_values=[etiqueta for _, etiqueta in opciones],
            )
        # Un select que no cumple el discriminador (ids de user/version/
        # enumeration) no se reconoce: el campo quedará sin resolver.

        if definicion is not None:
            self._select_candidates[field_id] = definicion
            self._record_position(field_id, self._select.position)
        self._select = None

    def flush_pending(self) -> None:
        """Descarta los controles abiertos y fusiona los candidatos.

        Un ``<select>`` sin ``</select>`` es HTML malformado y no debe
        producir un campo reconocido.
        """
        self._discard_select()
        self._merge_candidates()

    def _merge_candidates(self) -> None:
        """Elige la definición ganadora por id y ordena por el documento.

        Precedencia: ``select`` > par ``checkbox`` + ``hidden`` >
        ``input``/``textarea``. El orden del diccionario devuelto es el de la
        primera aparición real de cada id, también entre tipos distintos.
        """
        ganadores = dict(self._select_candidates)
        # El par checkbox + hidden del mismo id sin sufijo es un booleano core
        # y prevalece sobre un input/textarea del mismo id. Su posición ya se
        # registró al completarse el par.
        for field_id in self._checkbox_positions.keys() & self._hidden_positions:
            ganadores.setdefault(
                field_id, ParsedCustomField(field_format="bool")
            )
        for field_id, definicion in self._text_candidates.items():
            ganadores.setdefault(field_id, definicion)
        self.fields = {
            field_id: ganadores[field_id]
            for field_id in sorted(ganadores, key=self._positions.__getitem__)
        }

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
