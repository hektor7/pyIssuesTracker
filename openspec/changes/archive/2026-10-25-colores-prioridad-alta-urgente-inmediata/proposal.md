## Why

La tabla de tareas solo distingue dos niveles de prioridad por color: "Inmediata" (`RGB(200, 0, 0)`) y "Urgente" (`RGB(180, 20, 20)`). Ambos son rojos muy próximos entre sí, de modo que en la práctica no se percibe la diferencia entre ellos, y la prioridad "Alta" —que también exige atención— no recibe ningún resaltado y se confunde con "Normal" y "Baja".

El resultado es una escala cromática incompleta e ilegible: el usuario no puede estimar la urgencia de una fila de un vistazo.

## What Changes

- **Se introduce una escala de tres niveles** con intensidad creciente y luminancia decreciente: "Alta" → naranja tirando a rojo, "Urgente" → rojo, "Inmediata" → rojo más oscuro.
- **Se reasigna la paleta actual**: "Urgente" hereda el rojo que antes identificaba a "Inmediata" y "Alta" ocupa un nuevo escalón naranja rojizo. "Normal" y "Baja" siguen sin color.
- **Se mantiene el texto blanco** en las tres prioridades, con contraste verificado.
- **Se unifica el tratamiento de la barra de progreso**: la columna "Progreso %" aplica el mismo fondo de prioridad y texto blanco en los tres niveles, no solo en dos.

## Capabilities

### New Capabilities

<!-- Ninguna capacidad nueva: el cambio se limita a refinar capacidades existentes -->

### Modified Capabilities

- `resaltado-prioridad-alta`: pasa de dos niveles de resaltado (Inmediata, Urgente) con rojos casi idénticos a tres niveles diferenciados (Alta naranja rojizo, Urgente rojo, Inmediata rojo oscuro), todos con texto blanco.
- `barra-progreso`: el requisito de compatibilidad con el resaltado de prioridad alta se extiende a la prioridad "Alta", y deja de hablar de "fondo rojo" para hablar del color del resaltado de la fila.

## Impact

- **`app/widgets/task_table.py`**: constantes `_BG_INMEDIATA` / `_BG_URGENTE` reasignadas, nueva constante `_BG_ALTA`, y ampliación de `_priority_bg()` para reconocer "alta"/"high". `_PRIORITY_NAME_RANK` no requiere cambios.
- **`tests/test_task_table_render.py`**: constantes de color actualizadas, nueva constante para "Alta" y cobertura de los tres niveles (incluidos alias en inglés).
- **`MANUAL.md`**: descripción del resaltado actualizada a tres niveles.
- **`openspec/specs/resaltado-prioridad-alta/spec.md`** y **`openspec/specs/barra-progreso/spec.md`**: deltas de requisitos.
- Sin impacto en la API de Redmine, en dependencias externas, en la persistencia ni en la ordenación por prioridad.
