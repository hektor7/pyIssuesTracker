## Context

`TaskTable` (`app/widgets/task_table.py`) es un `QTableWidget` que pinta el fondo de todas las celdas visibles de una fila según la prioridad de la issue. El mapeo está centralizado:

- `_BG_INMEDIATA = QColor(200, 0, 0)` y `_BG_URGENTE = QColor(180, 20, 20)` (líneas 286-287).
- `_priority_bg(priority_name)` (líneas 394-400) reconoce solo `inmediata/immediate` y `urgente/urgent`; cualquier otra prioridad devuelve `None`.
- `_apply_issue_style()` (líneas 402-409) aplica `setBackground(bg_color)` + `setForeground(Qt.GlobalColor.white)` a cada item de la fila.

El `ProgressBarDelegate` (líneas 37-123) lee el `BackgroundRole` del item de la columna Progreso: si hay fondo de prioridad, pinta la celda con ese color, dibuja la pista de la barra en blanco, el chunk en `CHUNK_PRIORITY = QColor("#ff9800")` y el porcentaje en blanco. Por tanto el delegate ya es genérico y funciona con cualquier color de fondo, incluido uno nuevo.

La prioridad "Alta" ya existe en `_PRIORITY_NAME_RANK` (`"alta": 2, "high": 2`) para la ordenación semántica, pero no en `_priority_bg()` para el pintado. Ese es el hueco funcional actual.

Restricción de dominio: los nombres de prioridad no están hardcodeados en el modelo; provienen del catálogo de Redmine (`/enumerations/issue_priorities.json`). El pintado debe seguir resolviéndose por **nombre** con alias ES/EN, nunca por id.

## Goals / Non-Goals

**Goals:**

1. Que las tres prioridades altas sean distinguibles de un vistazo, con una escala monótona de intensidad: Alta < Urgente < Inmediata.
2. Que el blanco del texto siga siendo legible en los tres fondos (objetivo: contraste ≥ 4.5:1, WCAG AA para texto normal).
3. Mantener intacto el comportamiento del resto del sistema: ordenación semántica, resaltado asociado a la tarea y no a la fila, y celdas cubiertas al 100 %.
4. Que la columna Progreso sea coherente con el nuevo nivel "Alta" sin tocar el delegate.

**Non-Goals:**

- No se modifica la paleta de temas (`main.py`, `QPalette`) ni los colores de estado/conexión.
- No se modifican los colores de la barra de progreso por porcentaje (verde 100 %, naranja parcial, gris 0 %) fuera de las filas con prioridad.
- No se añaden prioridades nuevas ni se cambia el catálogo de Redmine.
- No se hace configurable la paleta por el usuario (sin ajustes nuevos en `settings_manager`).
- No se toca la ordenación por prioridad ni `_PRIORITY_NAME_RANK`.

## Decisions

### D1: Escala de tres niveles con luminancia decreciente

**Decisión:**

| Prioridad | Fondo | Hex | Texto | Contraste vs blanco | Luminancia relativa |
|---|---|---|---|---|---|
| Alta | `RGB(198, 81, 0)` | `#C65100` | Blanco | ≈ 4.6:1 | 0.179 |
| Urgente | `RGB(200, 0, 0)` | `#C80000` | Blanco | ≈ 6.1:1 | 0.123 |
| Inmediata | `RGB(139, 0, 0)` | `#8B0000` | Blanco | ≈ 10.0:1 | 0.055 |
| Normal / Baja | sin fondo | — | color del tema | — | — |

**Razón:** la luminancia decrece de forma monótona (0.179 → 0.123 → 0.055), así que la escala se lee como "más oscuro = más urgente" además del cambio de tono (naranja → rojo → rojo oscuro). Se cubren dos señales redundantes (tono e intensidad), lo que ayuda también a personas con daltonismo rojo-verde a distinguir Alta de Urgente.

**Alternativa descartada:** `#E65100` (deep orange de Material) para Alta. Es más naranja y más vivo, pero su contraste con blanco es ≈ 3.8:1, insuficiente para texto de 13 px. Se prefiere `#C65100`, que es un naranja rojizo (vermilion/burnt orange) y alcanza ≈ 4.6:1.

**Alternativa descartada:** `#D2491A` para Alta (≈ 4.5:1). Se descarta porque su tono es más rojo (menor separación de tono frente a Urgente) y su luminancia (0.185) apenas difiere de la de `#C65100` (0.179), sin aportar ninguna ventaja de contraste; `#C65100` conserva mejor la lectura "naranja" frente al rojo de Urgente.

### D2: "Urgente" hereda el rojo que antes era de "Inmediata"

**Decisión:** `_BG_URGENTE` pasa de `RGB(180, 20, 20)` a `RGB(200, 0, 0)`; `_BG_INMEDIATA` pasa de `RGB(200, 0, 0)` a `RGB(139, 0, 0)`.

**Razón:** mantiene la familiaridad (el rojo que el usuario ya asociaba al nivel máximo sigue presente, un escalón por debajo) y abre el hueco superior para un rojo claramente más oscuro. Evita introducir dos rojos nuevos y conserva la coherencia con el histórico del proyecto.

### D3: "Alta" recibe el mismo tratamiento de barra de progreso, sin tocar el delegate

**Decisión:** no se modifica `ProgressBarDelegate`. Al devolver `_priority_bg()` un color también para "Alta", `_priority_background()` lo detecta vía `BackgroundRole` y la fila obtiene pista blanca, chunk `#ff9800` y texto blanco.

**Razón:** el delegate ya es agnóstico al color concreto; el chunk ámbar va dibujado sobre la pista **blanca** de la barra, no directamente sobre el fondo de la fila, por lo que sigue siendo visible aunque el fondo de la fila sea naranja. Cualquier cambio en el delegate sería complejidad sin beneficio.

**Alternativa descartada:** derivar el color del chunk del fondo de la fila (`bg.lighter(140)`). Sobre `#8B0000` produce un contraste chunk/fondo de apenas 2:1 y añade una regla nueva que hay que testear.

### D4: Correspondencia por nombre con alias ES/EN, no por id

**Decisión:** `_priority_bg()` amplía la comparación a `("alta", "high")`, en minúsculas y con `strip()`, igual que las dos existentes.

**Razón:** el nombre es el único dato que llega siempre a la tabla (`priority_name`) y el catálogo de Redmine es configurable por instancia; los ids no son estables entre instalaciones. Es el mismo criterio que ya usa `_PRIORITY_NAME_RANK`.

## Risks / Trade-offs

- **[Riesgo residual] "Alta" y "Urgente" pueden confundirse en pantallas con poca fidelidad de color.** El riesgo de contraste está resuelto: "Alta" subió de `#CC5500` (≈4.3:1) a `#C65100` (4.59:1), cumpliendo WCAG AA para texto normal. → Mitigación de lo que queda: la separación no depende solo del tono, también de la luminancia (0.179 vs 0.123) y de la separación por canal G (81 vs 0), que se mantiene en monitores de baja fidelidad.
- **[Riesgo] Tests existentes fijan los colores antiguos** (`RED_INMEDIATA = QColor(200,0,0)`, `RED_URGENTE = QColor(180,20,20)`) y fallarán. → Mitigación: el cambio es intencional y los tests se actualizan en la primera fase (TDD), no después.
- **[Riesgo] El texto de `MANUAL.md` y los specs vigentes quedan desalineados.** → Mitigación: se actualizan en el mismo cambio, incluida la nota de refrescar el `## Purpose` del spec al archivar.
- **[Trade-off] Tres niveles de resaltado saturan más la tabla** que dos. Se acepta porque el resaltado se limita a Alta/Urgente/Inmediata y el resto de filas conserva el tema.

## Migration Plan

1. Actualizar y ampliar los tests de resaltado en `tests/test_task_table_render.py` y confirmar que fallan (rojo).
2. Reasignar las constantes de color y añadir `_BG_ALTA` en `task_table.py`; ampliar `_priority_bg()`.
3. Verificar el delegate de progreso con la nueva fila "Alta" (sin cambios de código esperados).
4. Actualizar `MANUAL.md`.
5. Ejecutar la suite completa en headless (`QT_QPA_PLATFORM=offscreen`) y hacer verificación manual en tema claro y oscuro.

**Rollback:** revertir los cambios en `task_table.py` y en los tests. No hay migración de datos, ni persistencia, ni cambios de API implicados.

## Open Questions

- ¿Debería el chunk de la barra de progreso adoptar un color por nivel de prioridad (en lugar del ámbar fijo) para reforzar la escala? Fuera de alcance: actualmente va sobre pista blanca y se lee bien.
- ¿Debe el usuario poder configurar la paleta de prioridades? Fuera de alcance; hoy no hay ajuste equivalente para ningún otro color de la tabla.
