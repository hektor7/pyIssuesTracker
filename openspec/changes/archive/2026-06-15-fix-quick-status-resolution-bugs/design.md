## Context

Las cuatro regresiones identificadas tienen causas específicas en commits recientes:

| Bug | Commit | Causa |
|-----|--------|-------|
| #1 | `507f07d` + `29a93ad` | `NoContextMenu` en `QProgressBar` insuficiente; conflicto con `sort_item` |
| #2 | `9a218d6` | Manejo HTTP 422 ahora visible (antes `raise_for_status()` lanzaba excepción no capturada) |
| #3 | `e666347` | Campo `due_date` obligatorio en payload de `complete_issue` rechazado por Redmine |
| #4 | `017e423` | `assigned_to_id` nunca se extrajo del JSON ni se precargó en el diálogo |

## Goals / Non-Goals

**Goals:**
- Restaurar la funcionalidad del menú contextual de progreso en el `QProgressBar`
- Mejorar el mensaje de error en cambio de estado para que el usuario entienda la causa (workflow)
- Corregir el payload de `complete_issue` para que no incluya `due_date` cuando no es necesario
- Mostrar la persona asignada en el diálogo de edición al hacer doble clic

**Non-Goals:**
- No se modifica la lógica de filtrado de estados por workflow (la API de Redmine no expone fácilmente los workflows por issue)
- No se añaden nuevas funcionalidades a los menús contextuales
- No se modifica la estructura de la base de datos ni la API REST

## Decisions

### Decisión 1: Solución para el menú contextual en QProgressBar

**Alternativa A**: Mantener `NoContextMenu` y usar `installEventFilter` para reenviar el evento al `TaskTable`.
**Alternativa B**: Eliminar `setCellWidget` y volver a texto plano con formateo visual (como antes de `e252671`).
**Alternativa C**: Conectar `customContextMenuRequested` del propio `QProgressBar` a la señal del `TaskTable`.

**Decisión**: **Alternativa C** — Es la más limpia y la que requiere menos cambios. Se elimina `bar.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)` y en su lugar se conecta la señal `customContextMenuRequested` del `QProgressBar` para que emita la señal del `TaskTable` con las coordenadas mapeadas al viewport. Además, se verifica que el `sort_item` (introducido en `29a93ad`) no interfiera con `rowAt()`/`columnAt()`.

Código:
```python
# En _create_progress_bar, reemplazar NoContextMenu con:
bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
bar.customContextMenuRequested.connect(
    lambda pos: self.customContextMenuRequested.emit(
        bar.mapTo(self.viewport(), pos)
    )
)
```

### Decisión 2: Mensaje de error descriptivo en cambio de estado

**Alternativa A**: Capturar `RedmineValidationError` y mostrar mensaje genérico.
**Alternativa B**: Capturar `RedmineValidationError` y mostrar mensaje explicativo sobre workflows.
**Alternativa C**: Pre-filtrar estados por workflow usando la API de Redmine.

**Decisión**: **Alternativa B** — Capturar `RedmineValidationError` específicamente y mostrar un mensaje que explique la causa probable (workflow del tracker). La Alternativa C requeriría una llamada adicional a la API por cada issue (`/issues/{id}.json?include=allowed_statuses`) lo cual es costoso e innecesario.

### Decisión 3: Corrección del due_date en complete_issue

**Alternativa A**: Eliminar completamente `due_date` del payload.
**Alternativa B**: Hacer `due_date` condicional: solo incluirlo si el issue ya tiene `due_date`.
**Alternativa C**: Consultar los campos permitidos del tracker antes de enviar.

**Decisión**: **Alternativa B (variante: try-retry)** — Se intenta siempre incluir `date.today()` como `due_date` en el primer intento. Si Redmine rechaza con `RedmineValidationError` (HTTP 422), se reintenta la petición sin el campo `due_date`. Esto es más resiliente: permite completar issues que soportan el campo aunque no lo tuvieran previamente, y cubre el caso de instancias de Redmine que lo rechazan sin verificación previa.

### Decisión 4: Precarga de assigned_to_id en el diálogo

**Alternativa A**: Añadir `assigned_to_id` al `task_data` y precargarlo en `_populate_fields`.
**Alternativa B**: Pasar el objeto `issue` completo al `TaskDialog` en lugar de un `task_data` aplanado.

**Decisión**: **Alternativa A** — Añadir `assigned_to_id` a `task_data` en `_editar_tarea` (extrayéndolo de `data.get("assigned_to", {}).get("id", 0)`) y precargarlo en `_populate_fields` del `TaskDialog`. La Alternativa B requeriría refactorizar significativamente `TaskDialog` y rompería la interfaz actual.

## Risks / Trade-offs

- **[Riesgo] eventFilter en QProgressBar podría interferir con tooltips**: Si el `QProgressBar` tiene tooltips, el `eventFilter` no debe interferir con otros eventos de ratón → **Mitigación**: Solo reenviar `QEvent.Type.ContextMenu`.
- **[Riesgo] Intento inicial con due_date podría ser rechazado en algunos trackers**: Algunas instancias de Redmine pueden rechazar `due_date` aunque el issue no tenga uno → **Mitigación**: Se reintenta sin `due_date` al capturar `RedmineValidationError` en `_completar_tarea`. Además se muestra mensaje descriptivo si ambos intentos fallan.
- **[Riesgo] assigned_to_id podría ser 0 si el issue no tiene asignado**: `data.get("assigned_to", {}).get("id", 0)` devuelve 0 → **Mitigación**: La función `_set_combo_data` con valor 0 selecciona la opción "Sin asignar", que es el comportamiento correcto.
