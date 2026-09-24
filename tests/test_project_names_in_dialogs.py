"""Tests de nombres completos de proyecto ("Padre > Hijo") en los diálogos.

Cubre los huecos W2 (TaskDialog), W3 (ProjectSelectDialog) y W4 (SettingsDialog):
los diálogos deben mostrar el nombre completo del proyecto y distinguir
proyectos que comparten el mismo nombre de hoja (p. ej. "Soporte").
"""

from PyQt6.QtCore import Qt

from app.dialogs.task_dialog import TaskDialog
from app.dialogs.settings_dialog import SettingsDialog
from app.main_window import ProjectSelectDialog
from app.services.settings_manager import SettingsManager

PROJECTS = [
    (42, "Proyecto padre 1 > Soporte"),
    (43, "Proyecto padre 2 > Soporte"),
]


class TestTaskDialogProjectNames:
    """W2: TaskDialog muestra el nombre completo en alta y edición."""

    def test_alta_muestra_nombres_completos_distinguibles(self, qapp):
        """En alta, el combo de proyecto contiene ambas cadenas completas y
        no hay dos entradas idénticas (se distinguen por el padre)."""
        dlg = TaskDialog(projects=PROJECTS)

        assert dlg._project_combo.count() == 2
        assert dlg._project_combo.itemText(0) == "Proyecto padre 1 > Soporte"
        assert dlg._project_combo.itemText(1) == "Proyecto padre 2 > Soporte"
        assert dlg._project_combo.itemData(0) == 42
        assert dlg._project_combo.itemData(1) == 43
        # No debe aparecer una entrada "Soporte" suelta ni dos entradas iguales
        texts = [dlg._project_combo.itemText(i) for i in range(dlg._project_combo.count())]
        assert "Soporte" not in texts
        assert len(set(texts)) == len(texts)

    def test_edicion_selecciona_nombre_completo(self, qapp):
        """En edición, el combo de proyecto muestra seleccionado el nombre
        completo del proyecto de la tarea (project_id=43)."""
        task_data = {
            "id": 9,
            "project_id": 43,
            "tracker_id": 1,
            "priority_id": 2,
            "status_id": 1,
            "subject": "Tarea existente",
            "description": "",
        }
        dlg = TaskDialog(projects=PROJECTS, task_data=task_data)

        assert dlg._project_combo.currentData() == 43
        assert dlg._project_combo.currentText() == "Proyecto padre 2 > Soporte"


class TestProjectSelectDialogProjectNames:
    """W3: ProjectSelectDialog muestra el nombre completo y resuelve el id."""

    def test_muestra_nombres_completos_distinguibles(self, qapp):
        """Las opciones del combo muestran ambas cadenas completas y son
        distinguibles entre sí."""
        dlg = ProjectSelectDialog(PROJECTS)

        assert dlg._combo.count() == 2
        assert dlg._combo.itemText(0) == "Proyecto padre 1 > Soporte"
        assert dlg._combo.itemText(1) == "Proyecto padre 2 > Soporte"
        texts = [dlg._combo.itemText(i) for i in range(dlg._combo.count())]
        assert "Soporte" not in texts
        assert len(set(texts)) == len(texts)

    def test_seleccionar_proyecto_43_devuelve_su_id(self, qapp):
        """Al seleccionar la opción del proyecto 43, selected_project_id == 43."""
        dlg = ProjectSelectDialog(PROJECTS)

        dlg._combo.setCurrentIndex(1)

        assert dlg.selected_project_id == 43


class TestSettingsDialogProjectNames:
    """W4: SettingsDialog muestra el nombre completo en la lista de
    proyectos de notificación."""

    def test_lista_notificaciones_muestra_nombres_completos(self, qapp):
        """Los items de la lista de notificación (ignorando el item 0 "Todos")
        muestran los nombres completos de los proyectos."""
        settings = SettingsManager()
        dlg = SettingsDialog(settings, projects=PROJECTS)

        assert dlg._notif_projects_list.count() == 3
        # Item 0 = "[TODOS]"
        assert dlg._notif_projects_list.item(0).text() == "[TODOS]"
        # Items 1 y 2 = proyectos con nombre completo
        assert dlg._notif_projects_list.item(1).text() == "Proyecto padre 1 > Soporte"
        assert dlg._notif_projects_list.item(2).text() == "Proyecto padre 2 > Soporte"
        assert dlg._notif_projects_list.item(1).data(Qt.ItemDataRole.UserRole) == 42
        assert dlg._notif_projects_list.item(2).data(Qt.ItemDataRole.UserRole) == 43