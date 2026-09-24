"""Tests del helper build_project_full_names (cambio nombre-completo-proyecto-y-doble-ordenacion)."""

from types import SimpleNamespace

from app.utils.projects import build_project_full_names


def _proj(pid, name, parent_id=None):
    return SimpleNamespace(id=pid, name=name, parent_id=parent_id)


class TestBuildProjectFullNames:
    """build_project_full_names compone la ruta de ancestros unida por ' > '."""

    def test_raiz_sin_padre_usa_su_propio_nombre(self):
        projects = [_proj(1, "Raíz")]
        result = build_project_full_names(projects)
        assert result == {1: "Raíz"}

    def test_un_nivel_padre_hijo(self):
        projects = [
            _proj(1, "Padre"),
            _proj(2, "Hijo", parent_id=1),
        ]
        result = build_project_full_names(projects)
        assert result[2] == "Padre > Hijo"
        assert result[1] == "Padre"

    def test_dos_niveles_raiz_intermedio_hijo(self):
        projects = [
            _proj(1, "Raíz"),
            _proj(2, "Intermedio", parent_id=1),
            _proj(3, "Hijo", parent_id=2),
        ]
        result = build_project_full_names(projects)
        assert result[3] == "Raíz > Intermedio > Hijo"

    def test_homonimos_bajo_padres_distintos_tienen_rutas_distintas(self):
        projects = [
            _proj(1, "Proyecto A"),
            _proj(2, "Proyecto B"),
            _proj(3, "Soporte", parent_id=1),
            _proj(4, "Soporte", parent_id=2),
        ]
        result = build_project_full_names(projects)
        assert result[3] == "Proyecto A > Soporte"
        assert result[4] == "Proyecto B > Soporte"
        assert result[3] != result[4]

    def test_parent_id_ausente_de_la_lista_usa_nombre_propio(self):
        projects = [
            _proj(1, "Hijo", parent_id=999),  # 999 no está en la lista
        ]
        result = build_project_full_names(projects)
        assert result[1] == "Hijo"

    def test_parent_id_ausente_con_ancestros_conocidos(self):
        """Si un ancestro intermedio falta, usa los ancestros conocidos y se detiene."""
        projects = [
            _proj(1, "Raíz"),
            _proj(2, "Hijo", parent_id=999),  # 999 no está en la lista
            _proj(3, "Nieto", parent_id=2),
        ]
        result = build_project_full_names(projects)
        assert result[3] == "Hijo > Nieto"

    def test_ciclo_no_entra_en_bucle_infinito(self):
        """Un ciclo en parent_id no debe provocar un bucle infinito."""
        projects = [
            _proj(1, "A", parent_id=2),
            _proj(2, "B", parent_id=1),
        ]
        result = build_project_full_names(projects)
        # Ambos deben resolverse sin colgarse y conservar su nombre propio
        assert 1 in result and 2 in result
        assert "A" in result[1]
        assert "B" in result[2]