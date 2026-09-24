"""Utilidades para proyectos Redmine.

Contiene la composición del nombre completo de un proyecto a partir de su
jerarquía de ancestros (decisión D1 del cambio nombre-completo-proyecto-y-doble-ordenacion).
"""

# Límite de saltos al subir por parent_id para protegerse de ciclos corruptos.
_MAX_HOPS = 50


def build_project_full_names(projects) -> dict[int, str]:
    """Compone el nombre completo de cada proyecto uniendo la ruta de ancestros con ' > '.

    Para cada proyecto sube por ``parent_id`` hasta la raíz y une los nombres
    con `` > `` (raíz primero). Si un ``parent_id`` no está en la lista, se
    detiene y usa los ancestros conocidos. Si no tiene padre, el nombre es el
    propio. Protege contra ciclos con un máximo de saltos razonable.

    En caso de ciclo (un proyecto que acaba apuntando a un ancestro ya
    recorrido), la subida se corta al alcanzar los ``_MAX_HOPS`` saltos y se
    devuelve la ruta parcial acumulada hasta ese punto, sin entrar en bucle
    infinito ni repetir nombres.

    Args:
        projects: Lista de objetos con atributos ``id``, ``name`` y ``parent_id``
            (p. ej. ``RedmineProject``).

    Returns:
        dict[int, str]: Mapa ``id -> nombre completo``.
    """
    by_id = {p.id: p for p in projects}
    result: dict[int, str] = {}
    for p in projects:
        names = [p.name]
        current = p
        hops = 0
        while current.parent_id is not None and hops < _MAX_HOPS:
            parent = by_id.get(current.parent_id)
            if parent is None:
                break
            names.append(parent.name)
            current = parent
            hops += 1
        result[p.id] = " > ".join(reversed(names))
    return result