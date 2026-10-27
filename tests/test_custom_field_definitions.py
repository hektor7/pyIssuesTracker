"""Tests del parser HTML puro de definiciones de campos personalizados."""

import ast
from pathlib import Path

import pytest

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

    def test_select_multiple_1_0_se_resuelve_como_lista_no_bool(self):
        """Un select múltiple con 1/0 es una lista, no un booleano."""
        html = (
            '<select name="issue[custom_field_values][9][]" multiple="multiple">'
            '<option value=""></option>'
            '<option value="1">1</option>'
            '<option value="0">0</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            9: ParsedCustomField(
                field_format="list",
                multiple=True,
                possible_values=["1", "0"],
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


class TestControlesDeTextoYFecha:
    """Campos de texto, fecha y número renderizados como controles nativos."""

    def test_textarea_se_resuelve_como_text(self):
        """Un textarea de un campo personalizado se resuelve como texto."""
        html = (
            '<textarea name="issue[custom_field_values][7]">'
            "Texto libre"
            "</textarea>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            7: ParsedCustomField(
                field_format="text",
                multiple=False,
                possible_values=[],
            )
        }

    def test_input_date_se_resuelve_como_date(self):
        """Un input de tipo date se resuelve como fecha."""
        html = (
            '<input type="date" name="issue[custom_field_values][8]" '
            'value="2026-01-01">'
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            8: ParsedCustomField(
                field_format="date",
                multiple=False,
                possible_values=[],
            )
        }

    def test_input_number_se_resuelve_como_int(self):
        """Un input de tipo number se resuelve como entero."""
        html = (
            '<input type="number" name="issue[custom_field_values][9]" value="3">'
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            9: ParsedCustomField(
                field_format="int",
                multiple=False,
                possible_values=[],
            )
        }

    def test_input_text_se_resuelve_como_string(self):
        """Un input de tipo text se resuelve como texto corto."""
        html = (
            '<input type="text" name="issue[custom_field_values][10]" value="hola">'
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            10: ParsedCustomField(
                field_format="string",
                multiple=False,
                possible_values=[],
            )
        }

    @pytest.mark.parametrize("valor", ["12.75", "2026-01-01"])
    def test_valores_no_estandar_renderizados_como_texto_se_resuelven_como_string(
        self, valor
    ):
        """Un decimal o una fecha antigua como input text se resuelven string."""
        html = (
            f'<input type="text" name="issue[custom_field_values][19]" '
            f'value="{valor}">'
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado[19].field_format == "string"
        assert resultado[19].multiple is False
        assert resultado[19].possible_values == []


class TestPrecedenciaYOrden:
    """El `select` prevalece y el orden del documento se conserva."""

    def test_select_prevalece_sobre_input_del_mismo_id(self):
        """Un select reconocible gana a un input del mismo id."""
        html = (
            '<input type="text" name="issue[custom_field_values][3]" value="texto">'
            '<select name="issue[custom_field_values][3]">'
            '<option value=""></option>'
            '<option value="Baja">Baja</option>'
            '<option value="Alta">Alta</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            3: ParsedCustomField(
                field_format="list",
                multiple=False,
                possible_values=["Baja", "Alta"],
            )
        }

    def test_primera_aparicion_prevalece_entre_controles_del_mismo_tipo(self):
        """Dos inputs del mismo id conservan el primero; dos select también."""
        html_inputs = (
            '<input type="text" name="issue[custom_field_values][4]" value="texto">'
            '<input type="date" name="issue[custom_field_values][4]" '
            'value="2026-01-01">'
        )
        html_selects = (
            '<select name="issue[custom_field_values][5]">'
            '<option value="Primero">Primero</option>'
            "</select>"
            '<select name="issue[custom_field_values][5]">'
            '<option value="Segundo">Segundo</option>'
            "</select>"
        )

        resultado_inputs = parse_issue_form_custom_fields(html_inputs)
        resultado_selects = parse_issue_form_custom_fields(html_selects)

        assert resultado_inputs[4].field_format == "string"
        assert resultado_selects[5].possible_values == ["Primero"]

    def test_hidden_sigue_ignorado_con_los_nuevos_controles(self):
        """Un hidden ajeno al par booleano no altera el resultado."""
        base = (
            '<textarea name="issue[custom_field_values][7]"></textarea>'
            '<input type="date" name="issue[custom_field_values][8]">'
            '<input type="number" name="issue[custom_field_values][9]">'
            '<input type="text" name="issue[custom_field_values][10]">'
        )
        con_hidden = base + (
            '<input type="hidden" name="issue[custom_field_values][15]" value="">'
        )

        assert parse_issue_form_custom_fields(con_hidden) == (
            parse_issue_form_custom_fields(base)
        )
        assert 15 not in parse_issue_form_custom_fields(con_hidden)

    def test_controles_no_select_con_sufijo_corchetes_no_se_reconocen(self):
        """El sufijo [] solo tiene efecto en los select."""
        html = (
            '<input type="text" name="issue[custom_field_values][6][]" value="a">'
            '<textarea name="issue[custom_field_values][7][]"></textarea>'
        )

        assert parse_issue_form_custom_fields(html) == {}

    def test_orden_entre_tipos_preserva_el_documento(self):
        """Un textarea anterior a un select conserva su posición."""
        html = (
            '<textarea name="issue[custom_field_values][7]"></textarea>'
            '<select name="issue[custom_field_values][3]">'
            '<option value="Baja">Baja</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert list(resultado) == [7, 3]

        html_con_select_posterior = html + (
            '<select name="issue[custom_field_values][7]">'
            '<option value="Alta">Alta</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html_con_select_posterior)

        assert list(resultado) == [7, 3]
        assert resultado[7].field_format == "list"


    def test_par_bool_anterior_a_select_conserva_su_posicion(self):
        """Un checkbox+hidden inicial ordena el id antes que un select lejano."""
        html = (
            '<input type="checkbox" name="issue[custom_field_values][9]" value="1">'
            '<input type="hidden" name="issue[custom_field_values][9]" value="0">'
            '<select name="issue[custom_field_values][3]">'
            '<option value="Baja">Baja</option>'
            "</select>"
            '<select name="issue[custom_field_values][9]">'
            '<option value="Alta">Alta</option>'
            "</select>"
        )

        resultado = parse_issue_form_custom_fields(html)

        assert list(resultado) == [9, 3]
        assert resultado[9].field_format == "list"


    def test_par_bool_prevalece_sobre_input_del_mismo_id(self):
        """Ante un input y un par booleano del mismo id, gana el par."""
        html = (
            '<input type="text" name="issue[custom_field_values][9]" value="texto">'
            '<input type="checkbox" name="issue[custom_field_values][9]" value="1">'
            '<input type="hidden" name="issue[custom_field_values][9]" value="0">'
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado[9].field_format == "bool"


class TestBooleanoCore:
    """El booleano de Redmine core se renderiza como checkbox + hidden."""

    def test_bool_checkbox_con_hidden_se_resuelve_como_bool(self):
        html = (
            '<input type="checkbox" name="issue[custom_field_values][11]" value="1">'
            '<input type="hidden" name="issue[custom_field_values][11]" value="0">'
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            11: ParsedCustomField(
                field_format="bool",
                multiple=False,
                possible_values=[],
            )
        }

    def test_hidden_sin_sufijo_no_se_resuelve_como_string(self):
        """Un hidden sin checkbox pareja no es un campo string."""
        html = (
            '<input type="hidden" name="issue[custom_field_values][12]" value="0">'
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {}
        assert 12 not in resultado

    def test_checkbox_con_sufijo_corchetes_sigue_sin_reconocerse(self):
        """El par booleano exige el nombre exacto sin sufijo []."""
        html = (
            '<input type="checkbox" name="issue[custom_field_values][13][]" '
            'value="1">'
            '<input type="hidden" name="issue[custom_field_values][13][]" value="0">'
        )

        assert parse_issue_form_custom_fields(html) == {}


    def test_checkbox_sin_hidden_no_se_reconoce_como_bool(self):
        """Un checkbox sin hidden pareja no produce definición."""
        html = (
            '<input type="checkbox" name="issue[custom_field_values][14]" '
            'value="1">'
        )

        assert parse_issue_form_custom_fields(html) == {}

    def test_hidden_antes_del_checkbox_forma_el_par(self):
        """El orden hidden/checkbox es indiferente para el par booleano."""
        html = (
            '<input type="hidden" name="issue[custom_field_values][15]" value="0">'
            '<input type="checkbox" name="issue[custom_field_values][15]" '
            'value="1">'
        )

        resultado = parse_issue_form_custom_fields(html)

        assert resultado == {
            15: ParsedCustomField(
                field_format="bool",
                multiple=False,
                possible_values=[],
            )
        }


class TestControlesNoSoportados:
    """Radios y checkboxes con sufijo siguen fuera del alcance del parser."""

    def test_grupo_de_radios_no_se_reconoce(self):
        html = (
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
