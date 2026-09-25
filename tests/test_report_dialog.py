"""Tests del ReportDialog (tarea 4.1 del cambio add-ods-report-export).

Cubre: construcción del diálogo, precarga de proyectos preseleccionados,
lectura de las propiedades de filtros, roles por defecto y validación
del rango de fechas de creación.
"""
from unittest.mock import patch

import pytest
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import QDialog, QGroupBox

from app.dialogs.report_dialog import ReportDialog
from app.services.report_generator import REPORT_FIELDS, DEFAULT_FIELD_KEYS
from app.widgets.multi_select_combo import MultiSelectCombo


PROJECTS = [(1, "Proyecto A"), (2, "Proyecto B"), (3, "Proyecto C")]
USERS = [(10, "Ana"), (11, "Luis"), (12, "Marta")]
STATUSES = [(1, "Nueva"), (2, "En curso"), (3, "Resuelta")]


@pytest.fixture
def dialog(qapp):
    """Crea un ReportDialog con proyectos y usuarios de ejemplo."""
    return ReportDialog(PROJECTS, USERS, parent=None)


class TestConstruccion:
    """(a) Construcción del diálogo con proyectos y usuarios."""

    def test_se_crea_con_proyectos_y_usuarios(self, dialog):
        """El diálogo se construye sin errores y expone las propiedades."""
        assert dialog.windowTitle() == "Generar informe"
        assert dialog.selected_project_ids == []
        assert dialog.selected_user_ids == []
        assert dialog.selected_roles == ["creador", "actualizador", "participante"]

    def test_usuarios_cargados_en_el_combo(self, dialog):
        """El MultiSelectCombo de usuarios contiene los usuarios pasados."""
        items = dialog._users_combo._items
        assert items == USERS

    def test_proyectos_cargados_en_el_combo(self, dialog):
        """El MultiSelectCombo de proyectos contiene los proyectos pasados."""
        items = dialog._projects_combo._items
        assert items == PROJECTS

    def test_roles_marcados_por_defecto(self, dialog):
        """Los tres checkboxes de rol están marcados por defecto."""
        for cb in dialog._roles_checkboxes.values():
            assert cb.isChecked()


class TestPrecargaProyectos:
    """(b) Precarga de proyectos preseleccionados."""

    def test_preselecciona_proyectos(self, qapp):
        """Si se pasan preselected_project_ids, quedan seleccionados."""
        dlg = ReportDialog(PROJECTS, USERS, preselected_project_ids=[1, 3], parent=None)
        assert dlg.selected_project_ids == [1, 3]

    def test_sin_preseleccion_todos(self, dialog):
        """Sin preselección, la selección de proyectos es 'Todos' ([])."""
        assert dialog.selected_project_ids == []


class TestFechasCreacion:
    """(c) created_from/created_to: None por defecto e ISO al activar."""

    def test_none_por_defecto(self, dialog):
        """Con los checkboxes desactivados, las fechas son None."""
        assert dialog.created_from is None
        assert dialog.created_to is None

    def test_iso_al_activar_desde(self, dialog):
        """Al activar el checkbox 'desde' se devuelve la fecha en ISO."""
        dialog._from_check.setChecked(True)
        dialog._from_date.setDate(QDate(2026, 1, 1))
        assert dialog.created_from == "2026-01-01"

    def test_iso_al_activar_hasta(self, dialog):
        """Al activar el checkbox 'hasta' se devuelve la fecha en ISO."""
        dialog._to_check.setChecked(True)
        dialog._to_date.setDate(QDate(2026, 3, 31))
        assert dialog.created_to == "2026-03-31"

    def test_desactivar_checkbox_vuelve_a_none(self, dialog):
        """Al desactivar el checkbox, la fecha vuelve a None."""
        dialog._from_check.setChecked(True)
        dialog._from_date.setDate(QDate(2026, 1, 1))
        dialog._from_check.setChecked(False)
        assert dialog.created_from is None


class TestRoles:
    """(d) selected_roles por defecto contiene los tres roles."""

    def test_roles_por_defecto(self, dialog):
        assert set(dialog.selected_roles) == {"creador", "actualizador", "participante"}

    def test_roles_filtrados_al_desmarcar(self, dialog):
        """Al desmarcar un rol, deja de aparecer en selected_roles."""
        dialog._roles_checkboxes["creador"].setChecked(False)
        assert "creador" not in dialog.selected_roles
        assert set(dialog.selected_roles) == {"actualizador", "participante"}


class TestValidacionRoles:
    """(e2) Sin roles marcados, accept() avisa y no acepta el diálogo."""

    def test_sin_roles_no_acepta(self, dialog):
        """Si se desmarcan los tres roles, accept() muestra warning y no acepta."""
        for cb in dialog._roles_checkboxes.values():
            cb.setChecked(False)

        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()

        mock_warning.assert_called_once()
        assert dialog.result() != QDialog.DialogCode.Accepted

    def test_con_al_menos_un_rol_acepta(self, dialog):
        """Con al menos un rol marcado, accept() acepta sin warning."""
        dialog._roles_checkboxes["creador"].setChecked(False)
        dialog._roles_checkboxes["actualizador"].setChecked(False)

        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()

        mock_warning.assert_not_called()
        assert dialog.result() == QDialog.DialogCode.Accepted


class TestValidacionRango:
    """(e) Un rango inválido impide aceptar el diálogo."""

    def test_rango_invalido_no_acepta(self, dialog):
        """Si desde > hasta, accept() muestra warning y no acepta."""
        dialog._from_check.setChecked(True)
        dialog._to_check.setChecked(True)
        dialog._from_date.setDate(QDate(2026, 5, 1))
        dialog._to_date.setDate(QDate(2026, 1, 1))

        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()

        mock_warning.assert_called_once()
        assert dialog.result() != QDialog.DialogCode.Accepted

    def test_rango_valido_acepta(self, dialog):
        """Si desde <= hasta, accept() acepta sin warning."""
        dialog._from_check.setChecked(True)
        dialog._to_check.setChecked(True)
        dialog._from_date.setDate(QDate(2026, 1, 1))
        dialog._to_date.setDate(QDate(2026, 3, 31))

        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()

        mock_warning.assert_not_called()
        assert dialog.result() == QDialog.DialogCode.Accepted


class TestSeleccionTodos:
    """(f) selected_project_ids/selected_user_ids devuelven [] con 'Todos'."""

    def test_proyectos_todos_devuelve_vacio(self, dialog):
        assert dialog.selected_project_ids == []

    def test_usuarios_todos_devuelve_vacio(self, dialog):
        assert dialog.selected_user_ids == []

    def test_seleccionar_usuarios_devuelve_ids(self, dialog):
        """Al seleccionar usuarios concretos se devuelven sus IDs."""
        dialog._users_combo.set_selected_ids([10, 12])
        assert dialog.selected_user_ids == [10, 12]

    def test_seleccionar_proyectos_devuelve_ids(self, dialog):
        """Al seleccionar proyectos concretos se devuelven sus IDs."""
        dialog._projects_combo.set_selected_ids([2])
        assert dialog.selected_project_ids == [2]


class TestCamposInforme:
    """(g) Selección de campos del informe (cambio informe-campos-seleccionables)."""

    def test_grupo_con_18_casillas_todas_marcadas(self, dialog):
        """El grupo 'Campos del informe' tiene una casilla por campo, todas marcadas."""
        assert len(dialog._field_checkboxes) == 18
        assert set(dialog._field_checkboxes) == {key for key, _ in REPORT_FIELDS}
        for cb in dialog._field_checkboxes.values():
            assert cb.isChecked()

    def test_selected_fields_devuelve_claves_en_orden_canonico(self, dialog):
        """selected_fields devuelve todas las claves en el orden de REPORT_FIELDS."""
        assert dialog.selected_fields == DEFAULT_FIELD_KEYS

    def test_selected_fields_incluye_descripcion_por_defecto(self, dialog):
        """selected_fields incluye 'descripcion' por defecto, justo tras 'titulo'."""
        assert "descripcion" in dialog.selected_fields
        assert dialog.selected_fields.index("descripcion") == (
            dialog.selected_fields.index("titulo") + 1
        )

    def test_desmarcar_reduce_selected_fields(self, dialog):
        """Al desmarcar casillas, selected_fields se reduce y mantiene el orden."""
        dialog._field_checkboxes["url"].setChecked(False)
        dialog._field_checkboxes["comentarios"].setChecked(False)
        assert dialog.selected_fields == [
            key for key, _ in REPORT_FIELDS if key not in ("url", "comentarios")
        ]
        assert len(dialog.selected_fields) == 16

    def test_sin_campos_marcados_no_acepta(self, dialog):
        """Si se desmarcan todos los campos, accept() avisa y no acepta."""
        for cb in dialog._field_checkboxes.values():
            cb.setChecked(False)

        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()

        mock_warning.assert_called_once()
        assert dialog.result() != QDialog.DialogCode.Accepted

    def test_con_campos_marcados_acepta(self, dialog):
        """Con campos marcados, accept() acepta sin warning."""
        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dialog.accept()

        mock_warning.assert_not_called()
        assert dialog.result() == QDialog.DialogCode.Accepted


class TestCamposPersonalizados:
    """Subgrupo 'Campos personalizados' del ReportDialog (cambio informe-campos-personalizados)."""

    def test_subgrupo_con_casillas_desmarcadas(self, qapp):
        """Con custom_fields, aparecen las casillas desmarcadas."""
        dlg = ReportDialog(
            PROJECTS, USERS, parent=None,
            custom_fields=[(7, "Cliente"), (9, "Sprint")],
        )
        assert set(dlg._custom_field_checkboxes) == {"cf_7", "cf_9"}
        for cb in dlg._custom_field_checkboxes.values():
            assert not cb.isChecked()

    def test_selected_fields_incluye_cf_al_marcar(self, qapp):
        """Al marcar campos personalizados, selected_fields los incluye tras los estándar."""
        dlg = ReportDialog(
            PROJECTS, USERS, parent=None,
            custom_fields=[(7, "Cliente"), (9, "Sprint")],
        )
        dlg._custom_field_checkboxes["cf_7"].setChecked(True)
        dlg._custom_field_checkboxes["cf_9"].setChecked(True)
        assert dlg.selected_fields == DEFAULT_FIELD_KEYS + ["cf_7", "cf_9"]

    def test_orden_respeta_custom_fields(self, qapp):
        """El orden de los cf_<id> sigue el orden de custom_fields."""
        dlg = ReportDialog(
            PROJECTS, USERS, parent=None,
            custom_fields=[(9, "Sprint"), (7, "Cliente")],
        )
        dlg._custom_field_checkboxes["cf_9"].setChecked(True)
        dlg._custom_field_checkboxes["cf_7"].setChecked(True)
        assert dlg.selected_fields == DEFAULT_FIELD_KEYS + ["cf_9", "cf_7"]

    def test_sin_campos_personalizados_no_hay_subgrupo(self, dialog):
        """Sin custom_fields, no existe el subgrupo de campos personalizados."""
        assert not dialog._custom_field_checkboxes

    def test_validacion_cuenta_campos_personalizados(self, qapp):
        """Con solo un campo personalizado marcado, accept() acepta."""
        dlg = ReportDialog(
            PROJECTS, USERS, parent=None,
            custom_fields=[(7, "Cliente")],
        )
        for cb in dlg._field_checkboxes.values():
            cb.setChecked(False)
        dlg._custom_field_checkboxes["cf_7"].setChecked(True)

        with patch("app.dialogs.report_dialog.QMessageBox.warning") as mock_warning:
            dlg.accept()

        mock_warning.assert_not_called()
        assert dlg.result() == QDialog.DialogCode.Accepted


class TestCamposPersonalizadosRecalculables:
    """El subgrupo de campos personalizados se recalcula al cambiar la selección de proyectos."""

    def test_cambio_de_proyecto_llama_al_provider_y_reconstruye(self, qapp):
        """Al cambiar la selección, se llama al provider con los ids y se reconstruyen las casillas."""
        def provider(project_ids):
            if project_ids == [1]:
                return [(7, "Cliente")]
            return [(9, "Sprint")]

        dlg = ReportDialog(
            PROJECTS, USERS, parent=None,
            custom_fields=[(7, "Cliente")],
            custom_fields_provider=provider,
        )
        assert set(dlg._custom_field_checkboxes) == {"cf_7"}

        dlg._projects_combo.set_selected_ids([2])
        assert set(dlg._custom_field_checkboxes) == {"cf_9"}
        assert dlg._custom_fields == [(9, "Sprint")]

    def test_marcado_previo_se_preserva_si_el_campo_sigue_existiendo(self, qapp):
        """Si el campo marcado sigue existiendo tras recargar, se mantiene marcado."""
        def provider(project_ids):
            return [(7, "Cliente"), (9, "Sprint")]

        dlg = ReportDialog(
            PROJECTS, USERS, parent=None,
            custom_fields=[(7, "Cliente"), (9, "Sprint")],
            custom_fields_provider=provider,
        )
        dlg._custom_field_checkboxes["cf_7"].setChecked(True)

        dlg._projects_combo.set_selected_ids([1])
        assert dlg._custom_field_checkboxes["cf_7"].isChecked()
        assert not dlg._custom_field_checkboxes["cf_9"].isChecked()

    def test_marcado_se_pierde_si_el_campo_desaparece(self, qapp):
        """Si el campo marcado ya no existe tras recargar, desaparece de la selección."""
        def provider(project_ids):
            return [(9, "Sprint")] if project_ids == [2] else [(7, "Cliente")]

        dlg = ReportDialog(
            PROJECTS, USERS, parent=None,
            custom_fields=[(7, "Cliente")],
            custom_fields_provider=provider,
        )
        dlg._custom_field_checkboxes["cf_7"].setChecked(True)

        dlg._projects_combo.set_selected_ids([2])
        assert set(dlg._custom_field_checkboxes) == {"cf_9"}
        assert "cf_7" not in dlg.selected_fields

    def test_provider_que_falla_deja_sin_campos_personalizados(self, qapp):
        """Si el provider lanza una excepción, el subgrupo queda vacío sin romper el diálogo."""
        def provider(project_ids):
            raise RuntimeError("boom")

        dlg = ReportDialog(
            PROJECTS, USERS, parent=None,
            custom_fields=[(7, "Cliente")],
            custom_fields_provider=provider,
        )
        dlg._projects_combo.set_selected_ids([1])
        assert dlg._custom_fields == []
        assert not dlg._custom_field_checkboxes


class TestFiltroEstado:
    """Filtro por estado de la tarea del informe (tareas 11.1-11.3)."""

    def test_grupo_estado_existe_con_todas_por_defecto(self, qapp):
        """El grupo 'Estado de la tarea' existe con _status_combo y 'Todas' por defecto."""
        dlg = ReportDialog(PROJECTS, USERS, statuses=STATUSES, parent=None)
        assert hasattr(dlg, "_status_combo")
        assert isinstance(dlg._status_combo, MultiSelectCombo)
        assert dlg.selected_status_ids == []

    def test_seleccionar_un_estado_devuelve_su_id(self, qapp):
        """Al marcar un estado, selected_status_ids == [id]."""
        dlg = ReportDialog(PROJECTS, USERS, statuses=STATUSES, parent=None)
        dlg._status_combo.set_selected_ids([2])
        assert dlg.selected_status_ids == [2]

    def test_seleccionar_varios_estados_lista_ordenada(self, qapp):
        """Al marcar varios estados, selected_status_ids es la lista ordenada."""
        dlg = ReportDialog(PROJECTS, USERS, statuses=STATUSES, parent=None)
        dlg._status_combo.set_selected_ids([3, 1])
        assert dlg.selected_status_ids == [1, 3]

    def test_catalogo_vacio_solo_todas(self, qapp):
        """Con catálogo de estados vacío, el grupo muestra solo 'Todas'."""
        dlg = ReportDialog(PROJECTS, USERS, statuses=[], parent=None)
        ids = [
            dlg._status_combo._list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(dlg._status_combo._list.count())
        ]
        assert ids == [MultiSelectCombo.ALL]
        assert dlg.selected_status_ids == []

    def test_sin_statuses_el_grupo_muestra_solo_todas(self, dialog):
        """Sin statuses (None), el grupo muestra solo 'Todas'."""
        ids = [
            dialog._status_combo._list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(dialog._status_combo._list.count())
        ]
        assert ids == [MultiSelectCombo.ALL]
        assert dialog.selected_status_ids == []


class TestGruposDialogo:
    """El ReportDialog muestra los cinco grupos de filtros (tarea 15.1)."""

    def test_cinco_grupos_con_sus_titulos(self, dialog):
        """Existen los cinco QGroupBox con los títulos esperados."""
        titles = [
            g.title()
            for g in dialog.findChildren(QGroupBox)
            if g.title()
        ]
        for expected in [
            "Campos del informe",
            "Usuarios implicados",
            "Fechas de creación",
            "Estado de la tarea",
            "Proyectos",
        ]:
            assert expected in titles


class TestTooltipsCombos:
    """Tooltips con el nombre completo en los combos del diálogo (tareas 15.2-15.3)."""

    def test_combo_proyectos_tooltip_nombre_completo(self, qapp):
        """Cada ítem del combo de proyectos tiene tooltip con el nombre completo."""
        dlg = ReportDialog(
            [(1, "Padre muy largo > Hijo muy largo"), (2, "Otro")],
            USERS, parent=None,
        )
        for i in range(dlg._projects_combo._list.count()):
            item = dlg._projects_combo._list.item(i)
            assert item.toolTip() == item.text()

    def test_combo_usuarios_tooltip_nombre_largo(self, qapp):
        """Cada ítem del combo de usuarios tiene tooltip con el nombre del usuario."""
        dlg = ReportDialog(
            PROJECTS,
            [(10, "Un nombre de usuario muy largo para el combo"), (11, "Ana")],
            parent=None,
        )
        for i in range(dlg._users_combo._list.count()):
            item = dlg._users_combo._list.item(i)
            assert item.toolTip() == item.text()