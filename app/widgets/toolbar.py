from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QToolBar, QWidget


class IssueToolbar(QToolBar):
    nuevo_clicked = pyqtSignal()
    editar_clicked = pyqtSignal()
    asignar_clicked = pyqtSignal()
    completar_clicked = pyqtSignal()
    rechazar_clicked = pyqtSignal()
    refrescar_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Barra de acciones", parent)
        self.setMovable(False)
        self.setFloatable(False)
        self._setup_actions()

    def _setup_actions(self):
        self._action_nuevo = QAction("➕ Nuevo", self)
        self._action_nuevo.setToolTip("Crear nueva tarea")
        self._action_nuevo.triggered.connect(self.nuevo_clicked.emit)
        self.addAction(self._action_nuevo)

        self._action_editar = QAction("✏️ Editar", self)
        self._action_editar.setToolTip("Editar tarea seleccionada (o doble clic)")
        self._action_editar.triggered.connect(self.editar_clicked.emit)
        self.addAction(self._action_editar)

        self._action_asignar = QAction("👤 Asignar", self)
        self._action_asignar.setToolTip("Asignar tarea a ti mismo o a otro usuario")
        self._action_asignar.triggered.connect(self.asignar_clicked.emit)
        self.addAction(self._action_asignar)

        self._action_completar = QAction("✅ Completada", self)
        self._action_completar.setToolTip("Marcar como completada (100% progreso, resuelta, fecha fin)")
        self._action_completar.triggered.connect(self.completar_clicked.emit)
        self.addAction(self._action_completar)

        self._action_rechazar = QAction("❌ Rechazar", self)
        self._action_rechazar.setToolTip("Rechazar tarea con comentario")
        self._action_rechazar.triggered.connect(self.rechazar_clicked.emit)
        self.addAction(self._action_rechazar)

        self.addSeparator()

        spacer = QWidget()
        spacer.setMinimumWidth(20)
        self.addWidget(spacer)

        self._action_refrescar = QAction("🔄 Refrescar", self)
        self._action_refrescar.setToolTip("Refrescar lista de tareas")
        self._action_refrescar.triggered.connect(self.refrescar_clicked.emit)
        self.addAction(self._action_refrescar)
