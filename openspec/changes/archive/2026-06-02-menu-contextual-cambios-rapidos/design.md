## Context

Actualmente `TaskTable` no tiene menú contextual. Los cambios de progreso, asignación y estado requieren abrir el `TaskDialog` mediante doble clic. El usuario quiere cambios rápidos desde la vista principal.

El proyecto ya cuenta con:
- `customContextMenuRequested` usado en `ChecklistWidget` como referencia de implementación
- `QSettings` accesible vía `SettingsManager` para persistencia
- Métodos `update_issue()` y `assign_issue()` en `RedmineClient` para cambios individuales

## Goals / Non-Goals

**Goals:**
- Menú contextual en columnas Progreso (incrementos 20%), Asignado a (yo + frecuentes), Estado (todos los estados).
- Confirmación para cambio de progreso.
- Persistencia automática de las 5 últimas personas usadas en asignaciones.
- Cambios instantáneos vía API sin abrir el diálogo de edición.

**Non-Goals:**
- No se modifica el `TaskDialog` ni el `AssignDialog`.
- No se añade confirmación para cambio de estado o asignación (solo progreso).
- No se implementa "deshacer" tras cambio rápido.

## Decisions

### 1. Una sola señal `cambio_rapido` con tipo de acción

**Alternativa considerada:** 3 señales separadas.
**Decisión:** Una señal `cambio_rapido = pyqtSignal(int, str, int)` con `(issue_id, tipo, valor)` donde tipo es `"progreso"`, `"asignado"`, `"estado"` y valor es el nuevo valor.

**Razón:** Más simple de conectar en `MainWindow` (un solo slot). El dispatch interno es mínimo.

### 2. Confirmación para todos los cambios rápidos

**Decisión:** Mostrar `QMessageBox.question` antes de ejecutar cualquier cambio rápido (progreso, asignación o estado).

**Razón:** Todos los cambios modifican el estado de la tarea en el servidor. Una confirmación uniforme evita cambios accidentales y proporciona una última oportunidad de verificación antes de la llamada a la API.

### 3. Personas frecuentes en QSettings

**Decisión:** Guardar en `QSettings` como string con IDs separados por coma (ej. `"5,12,3,8,15"`). La clave es `frequent/people`. Máximo 5 entradas, sin duplicados (el más reciente al frente).

**Razón:** QSettings ya se usa para todo. No requiere nueva dependencia. El formato CSV simple es suficiente para una lista corta de IDs.

### 4. Actualizar frecuentes al asignar desde cualquier punto

**Decisión:** Crear un método `_registrar_asignacion(user_id)` en `MainWindow` que se llame desde: `_asignar_tarea()`, después de `assign_issue()` exitoso en el menú contextual, y potencialmente desde `TaskDialog` (si se cambia el asignado al editar). No se registra si `user_id` es el propio usuario (`_current_user_id`).

**Razón:** Centraliza la lógica. Evita duplicar código en cada punto de asignación.

### 5. Menú contextual: detección por columna

**Decisión:** En `customContextMenuRequested(pos)`, usar `self.columnAt(pos.x())` para determinar la columna. Solo mostrar menú si la columna es `COL_PROGRESS`, `COL_ASSIGNED_TO` o `COL_STATUS`, y si hay una fila seleccionada.

**Razón:** Preciso y eficiente. No interfiere con el doble clic ni con otras interacciones.

### 6. Incrementos de progreso: 0%, 20%, 40%, 60%, 80%, 100%

**Decisión:** Seis opciones fijas. Al seleccionar, confirmar con diálogo: "¿Cambiar progreso de tarea #X al Y%?". Al confirmar, llamar a `update_issue(issue_id, done_ratio=Y)`.

**Razón:** Saltos de 20% son prácticos para cambios rápidos. Cubren todos los hitos significativos.

## Risks / Trade-offs

- **[Riesgo] El menú de estado puede tener muchas opciones** → En Redmine típico hay 5-10 estados. El menú es manejable. Si hubiera >15, se podría paginar, pero no es el caso.
- **[Trade-off] No hay confirmación para asignación/estado** → Se compensa con la inmediatez. El usuario puede deshacer con otro clic si se equivoca.
- **[Riesgo] Las personas frecuentes pueden quedar desactualizadas si un usuario abandona el proyecto** → Es aceptable. El ID se resuelve contra la lista de miembros del proyecto al mostrar el menú; si no se encuentra, se omite.
