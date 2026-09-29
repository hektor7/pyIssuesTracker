"""Tests de carga de trackers del proyecto en TaskDialog (modo creación).

Cubren el requisito "Trackers del proyecto en el diálogo de creación" de la
spec manejo-errores-api: al seleccionar un proyecto, el combo de tracker se
puebla con los trackers de ESE proyecto; si no tiene ninguno, se avisa y se
impide el envío; si la consulta falla o no devuelve lista, NO se bloquea.
"""

from unittest.mock import MagicMock

from app.dialogs.task_dialog import TaskDialog


class TestTaskDialogTrackersProyecto:
    """Trackers del proyecto en el diálogo de creación (tareas 6.1 y 6.2)."""

    def _redmine(self, **overrides):
        redmine = MagicMock()
        redmine.get_project_issue_categories.return_value = []
        redmine.get_project_memberships.return_value = []
        redmine.get_project_custom_fields.return_value = []
        for key, value in overrides.items():
            setattr(redmine, key, value)
        return redmine

    def test_proyecto_con_trackers_puebla_combo(self, qapp):
        """Al seleccionar un proyecto con trackers, el combo se puebla con ellos."""
        redmine = self._redmine(
            get_project_trackers=MagicMock(return_value=[(1, "Bug"), (2, "Feature")])
        )
        dlg = TaskDialog(
            projects=[(5, "Destino")],
            default_project_id=5,
            redmine_client=redmine,
        )
        datos = [
            dlg._tracker_combo.itemData(i)
            for i in range(dlg._tracker_combo.count())
        ]
        assert datos == [1, 2]
        assert dlg._sin_trackers_label.isHidden() is True
        assert dlg._ok_button.isEnabled() is True

    def test_proyecto_sin_trackers_avisa_y_deshabilita_ok(self, qapp):
        """Lista vacía confirmada → aviso visible y botón OK deshabilitado."""
        redmine = self._redmine(
            get_project_trackers=MagicMock(return_value=[])
        )
        dlg = TaskDialog(
            projects=[(5, "Destino")],
            default_project_id=5,
            redmine_client=redmine,
        )
        assert dlg._sin_trackers_label.isHidden() is False
        assert dlg._ok_button.isEnabled() is False

    def test_consulta_fallida_no_bloquea(self, qapp):
        """Si get_project_trackers lanza, el diálogo NO se bloquea (fail-open)."""
        redmine = self._redmine(
            get_project_trackers=MagicMock(side_effect=RuntimeError("API caída"))
        )
        dlg = TaskDialog(
            projects=[(5, "Destino")],
            default_project_id=5,
            redmine_client=redmine,
        )
        assert dlg._sin_trackers_label.isHidden() is True
        assert dlg._ok_button.isEnabled() is True

    def test_mock_sin_get_project_trackers_no_bloquea(self, qapp):
        """Un mock sin get_project_trackers (devuelve MagicMock, no lista)
        no debe bloquear el diálogo ni alterar la property tracker_id."""
        redmine = self._redmine()
        dlg = TaskDialog(
            projects=[(5, "Destino")],
            default_project_id=5,
            redmine_client=redmine,
        )
        assert dlg._ok_button.isEnabled() is True
        assert dlg.tracker_id == 1  # property intacta (currentData() or 1)

    def test_cambiar_a_proyecto_con_trackers_tras_uno_sin(self, qapp):
        """Al cambiar de un proyecto sin trackers a uno con trackers, el OK
        se vuelve a habilitar y el aviso se oculta."""
        redmine = self._redmine(
            get_project_trackers=MagicMock(return_value=[])
        )
        dlg = TaskDialog(
            projects=[(5, "Sin trackers"), (6, "Con trackers")],
            default_project_id=5,
            redmine_client=redmine,
        )
        assert dlg._ok_button.isEnabled() is False
        # El proyecto 6 sí tiene trackers
        redmine.get_project_trackers.return_value = [(1, "Bug")]
        dlg._set_combo_data(dlg._project_combo, 6)
        dlg._on_project_changed()
        assert dlg._ok_button.isEnabled() is True
        assert dlg._sin_trackers_label.isHidden() is True