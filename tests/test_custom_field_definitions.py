"""Tests del parser HTML puro de definiciones de campos personalizados."""

import ast
from pathlib import Path

from app.services.custom_field_definitions import (
    ParsedCustomField,
    parse_issue_form_custom_fields,
)
import app.services.custom_field_definitions as modulo


FIXTURES = Path(__file__).parent / "fixtures" / "custom_field_forms"


def _fixture(nombre: str) -> str:
    """Lee una muestra de formulario HTML de `tests/fixtures`."""
    return (FIXTURES / nombre).read_text(encoding="utf-8")


class TestParseSelectSimple:
    """3.1: contrato y caso base de un `select` simple de lista."""

    def test_parsea_select_simple_como_lista(self):
        """Un select con opción vacía y valores iguales a etiquetas es list."""
        resultado = parse_issue_form_custom_fields(_fixture("select_simple_lista.html"))

        assert resultado == {
            3: ParsedCustomField(
                field_format="list",
                multiple=False,
                possible_values=["Causa A", "Causa B"],
            )
        }

    def test_contrato_devuelve_parsed_custom_field(self):
        """El resultado son instancias de la dataclass propia del módulo."""
        resultado = parse_issue_form_custom_fields(_fixture("select_simple_lista.html"))

        campo = resultado[3]
        assert isinstance(campo, ParsedCustomField)
        assert ParsedCustomField() == ParsedCustomField(
            field_format="", multiple=False, possible_values=[]
        )


class TestSelectMultiple:
    """3.3: `select multiple` y sufijo `[]` se resuelven como list múltiple."""

    def test_parsea_select_multiple_con_atributo_multiple(self):
        """El atributo `multiple` marca el campo como múltiple."""
        resultado = parse_issue_form_custom_fields(_fixture("select_multiple.html"))

        assert resultado == {
            4: ParsedCustomField(
                field_format="list",
                multiple=True,
                possible_values=["Rojo", "Verde"],
            )
        }

    def test_parsea_select_con_sufijo_corchetes(self):
        """El sufijo [] en el nombre también marca el campo como múltiple."""
        html = (
            '<select name="issue[custom_field_values][8][]">'
            '<option value=""></option>'
            '<option value="Uno">Uno</option>'
            '<option value="Dos">Dos</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            8: ParsedCustomField(
                field_format="list",
                multiple=True,
                possible_values=["Uno", "Dos"],
            )
        }


class TestSelectBooleano:
    """3.5: un select con valores 1 y 0 se resuelve como bool."""

    def test_select_con_valores_1_y_0_es_bool(self):
        """Las opciones 1/0 se clasifican como bool, no como lista."""
        resultado = parse_issue_form_custom_fields(_fixture("select_booleano.html"))

        assert resultado == {
            5: ParsedCustomField(
                field_format="bool",
                multiple=False,
                possible_values=[],
            )
        }

    def test_booleano_prevalece_sobre_discriminador_de_lista(self):
        """Aunque valor y etiqueta coincidan, 1/0 sigue siendo bool."""
        html = (
            '<select name="issue[custom_field_values][9]">'
            '<option value=""></option>'
            '<option value="1">1</option>'
            '<option value="0">0</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            9: ParsedCustomField(
                field_format="bool",
                multiple=False,
                possible_values=[],
            )
        }


class TestDiscriminadorLista:
    """3.7: solo es lista si valor y etiqueta coinciden tras normalizar."""

    def test_select_con_valor_igual_a_etiqueta_es_lista(self):
        """Entidades HTML y espacios se normalizan antes de comparar."""
        html = (
            '<select name="issue[custom_field_values][10]">'
            '<option value=""></option>'
            '<option value="  Opci&oacute;n A  ">  Opci&oacute;n A  </option>'
            '<option value="Opci&oacute;n B">Opci&oacute;n B</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            10: ParsedCustomField(
                field_format="list",
                multiple=False,
                possible_values=["Opción A", "Opción B"],
            )
        }

    def test_select_simple_con_opcion_vacia_sigue_siendo_lista(self):
        """La opción vacía se descarta pero no invalida la lista."""
        resultado = parse_issue_form_custom_fields(_fixture("select_simple_lista.html"))

        assert resultado[3].field_format == "list"
        assert resultado[3].multiple is False
        assert resultado[3].possible_values == ["Causa A", "Causa B"]


class TestDesplegablesNoLista:
    """3.9: user/version/enumeration no son listas de valores seleccionables."""

    def test_select_con_valores_de_id_no_es_lista(self):
        """value="10" con etiqueta "Ana" no cumple el discriminador."""
        resultado = parse_issue_form_custom_fields(_fixture("select_ids.html"))

        assert 6 not in resultado
        assert resultado == {}

    def test_variantes_user_version_enumeration_no_se_reconocen(self):
        """Los tres desplegables con id como valor quedan sin resolver."""
        html = (
            '<select name="issue[custom_field_values][11]">'
            '<option value="">&nbsp;</option>'
            '<option value="1">Usuario Uno</option>'
            "</select>"
            '<select name="issue[custom_field_values][12]">'
            '<option value=""></option>'
            '<option value="7">Versión 7</option>'
            "</select>"
            '<select name="issue[custom_field_values][13]">'
            '<option value=""></option>'
            '<option value="2">Enumeración dos</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {}


class TestFiltradoYOrden:
    """3.11: se ignoran controles ajenos y se conserva el primer duplicado."""

    def test_ignora_hidden_de_valor_vacio(self):
        """El hidden vacío que Redmine añade para múltiples no se reconoce."""
        html = (
            '<select name="issue[custom_field_values][14]">'
            '<option value=""></option>'
            '<option value="Sí">Sí</option>'
            '<option value="No">No</option>'
            "</select>"
            '<input type="hidden" name="issue[custom_field_values][15][]" value="">'
        )

        resultado = parse_issue_form_custom_fields(html)

        assert set(resultado) == {14}
        assert 15 not in resultado

    def test_ignora_controles_que_no_son_de_campos_personalizados(self):
        """Nombres ajenos al patrón issue[custom_field_values][id] se ignoran."""
        html = (
            '<select name="issue[tracker_id]">'
            '<option value="1">Bug</option>'
            "</select>"
            '<select name="issue[custom_field_values][texto]">'
            '<option value="A">A</option>'
            "</select>"
            '<input type="text" name="issue[subject]" value="Hola">'
        )

        assert parse_issue_form_custom_fields(html) == {}

    def test_conserva_orden_y_elimina_duplicados(self):
        """El orden de aparición se conserva y prevalece la primera aparición."""
        html = (
            '<select name="issue[custom_field_values][9]">'
            '<option value="Uno">Uno</option>'
            '<option value="Dos">Dos</option>'
            "</select>"
            '<select name="issue[custom_field_values][3]">'
            '<option value="Tres">Tres</option>'
            "</select>"
            '<select name="issue[custom_field_values][9]">'
            '<option value="Otro">Otro</option>'
            '<option value="Distinto">Distinto</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert list(resultado) == [9, 3]
        assert resultado[9].possible_values == ["Uno", "Dos"]

    def test_decodifica_entidades_html(self):
        """Las entidades HTML de etiquetas y valores se decodifican."""
        html = (
            '<select name="issue[custom_field_values][16]">'
            '<option value=""></option>'
            '<option value="A &amp; B">A &amp; B</option>'
            '<option value="Pe&ntilde;a">Pe&ntilde;a</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado[16].possible_values == ["A & B", "Peña"]


class TestRobustezHTML:
    """3.13: HTML vacío, malformado o de login no rompe el parser."""

    def test_html_vacio_devuelve_dict_vacio(self):
        assert parse_issue_form_custom_fields("") == {}

    def test_html_malformado_no_lanza(self):
        """Un select sin cerrar no se considera un campo reconocido."""
        html = (
            '<select name="issue[custom_field_values][3]">'
            '<option value="A">A</option>'
        )

        assert parse_issue_form_custom_fields(html) == {}

    def test_pagina_de_login_devuelve_dict_vacio(self):
        assert parse_issue_form_custom_fields(
            _fixture("login_sin_controles.html")
        ) == {}


class TestControlesNoSoportados:
    """3.15: el recorte deliberado del parser no reconoce otros controles."""

    def test_textarea_input_date_input_number_input_text_y_radios_no_se_reconocen(self):
        html = _fixture("textarea.html") + (
            '<input type="date" name="issue[custom_field_values][17]" value="2026-01-01">'
            '<input type="number" name="issue[custom_field_values][18]" value="3">'
            '<input type="text" name="issue[custom_field_values][19]" value="hola">'
            '<input type="radio" name="issue[custom_field_values][20]" value="1">'
            '<input type="radio" name="issue[custom_field_values][20]" value="0">'
        )

        assert parse_issue_form_custom_fields(html) == {}

    def test_grupo_de_checkboxes_no_se_reconoce(self):
        html = (
            '<input type="checkbox" name="issue[custom_field_values][21][]" value="A">'
            '<input type="checkbox" name="issue[custom_field_values][21][]" value="B">'
        )

        assert parse_issue_form_custom_fields(html) == {}


class TestDireccionDeDependencia:
    """3.16: el parser puro no importa el cliente de Redmine (sin ciclo)."""

    def test_modulo_de_parseo_no_importa_redmine_client(self):
        ruta = Path(modulo.__file__)
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))

        importados: list[str] = []
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                importados.extend(alias.name for alias in nodo.names)
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                importados.append(nodo.module)

        assert not any(
            nombre == "app.services.redmine_client"
            or nombre.startswith("app.services.redmine_client.")
            for nombre in importados
        )
