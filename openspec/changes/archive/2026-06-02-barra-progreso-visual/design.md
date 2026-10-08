## Context

Actualmente la celda de progreso en `TaskTable.set_issues()` (línea 113) crea un `QTableWidgetItem(f"{progress}%")` con color verde si es 100%, amarillo si >0%, o blanco si hay fondo rojo de prioridad alta.

El objetivo es reemplazarlo por un `QProgressBar` que ocupe toda la celda y muestre el porcentaje visualmente.

## Goals / Non-Goals

**Goals:**
- Mostrar una barra de progreso `QProgressBar` en la columna de progreso.
- Mantener los colores semánticos: verde (completado), naranja (en progreso), gris (sin empezar).
- Mantener la compatibilidad con el fondo rojo de prioridades altas.

**Non-Goals:**
- No se modifica ninguna otra columna.
- No se añade interacción con la barra (solo visualización).

## Decisions

### 1. Usar `setCellWidget()` con `QProgressBar`

**Alternativa considerada:** Implementar un delegate pintado a mano.
**Decisión:** Usar `QProgressBar` nativo de Qt vía `setCellWidget()`.

**Razón:** Es más simple, mantenible, y Qt ya maneja el renderizado, accesibilidad y temas. No hay penalización de rendimiento para el volumen de filas esperado (< 500).

### 2. Colores de la barra mediante stylesheet

**Decisión:** Aplicar estilos condicionales al `QProgressBar`:

| Progreso | Estilo |
|----------|--------|
| 100% | `QProgressBar::chunk { background: #2e7d32; }` (verde oscuro) |
| >0% | `QProgressBar::chunk { background: #f57c00; }` (naranja) |
| 0% | `QProgressBar::chunk { background: #bdbdbd; }` (gris) |
| Urgente/Inmediata | Fondo rojo (`background: #c80000` o `#b41414`), texto blanco forzado con `color: white;` |

**Razón:** Los estilos se aplican por instancia, sin afectar a otras celdas. La paleta de colores es consistente con los colores de texto actuales (darkGreen, darkYellow).

### 3. Altura y ajuste de la barra

**Decisión:** Fijar `setFixedHeight(20)` para que la barra no desborde la fila. Configurar `setTextVisible(True)` para mostrar "XX%" dentro de la barra.

**Razón:** La altura estándar de fila es ~25px. Una barra de 20px deja margen suficiente. El texto visible ayuda en temas donde el color de la barra no sea suficientemente distintivo.

### 4. Mantener lógica de prioridad: barra sobre fondo rojo

**Decisión:** Igual que ahora, si `bg_color` existe (prioridad urgente/inmediata), el `QProgressBar` recibe un stylesheet adicional con `background-color: rgb(200,0,0); color: white;` (o el color correspondiente).

**Razón:** Consistencia con el resto de celdas de la fila que ya muestran fondo rojo + texto blanco.

## Risks / Trade-offs

- **[Riesgo] `setCellWidget()` puede tener peor rendimiento que `QTableWidgetItem`** → El volumen de filas es bajo (< 500). No se espera impacto perceptible.
- **[Trade-off] La barra ocupa más espacio visual** → Se compensa con mejor legibilidad. El ancho de columna ya es fijo (`ResizeToContents`).
