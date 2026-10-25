## Context

`ProgressBarDelegate` (`app/widgets/task_table.py:37-123`) pinta la columna "Progreso %" de `TaskTable`. El flujo actual es:

1. Rellena la celda con el fondo de prioridad si existe, o con el fondo del tema si no (`:78-84`).
2. Dibuja la pista de la barra (`bar_rect`, con 4 px de margen horizontal y 5 vertical) con `track_color`, que es blanco `#ffffff` siempre que `priority_bg is not None or value > 0`, y `#bdbdbd` en el caso de barra vacía sin prioridad (`:88-96`).
3. Dibuja el tramo relleno (`chunk_rect`) proporcional al porcentaje, con color verde `#2e7d32` al 100 %, naranja `#f57c00` parcial, o ámbar `#ff9800` si hay prioridad (`:98-115`).
4. Dibuja el texto centrado en `cell_rect` en blanco si hay prioridad, o con `option.palette.color(QPalette.ColorRole.Text)` si no (`:117-122`).

El paso 4 es el defecto: el color se elige por prioridad o por tema, pero el texto se dibuja encima de la **pista**, que es blanca. Resultado comprobado con `grab()` en offscreen:

- Fila con prioridad: texto blanco sobre pista blanca → invisible.
- Tema oscuro sin prioridad: `Text` es blanco sobre pista blanca → invisible.

Es decir, el porcentaje solo es legible por casualidad: en tema claro y sin prioridad, donde `Text` es oscuro.

Además el relleno detrás del glifo **no es uniforme**: en un 50 % la mitad izquierda del texto puede caer sobre el tramo naranja y la mitad derecha sobre la pista blanca. Un único color de texto no puede contrastar con ambos.

## Goals / Non-Goals

**Goals:**

1. Que el porcentaje sea legible con contraste ≥ 4.5:1 (WCAG AA para texto normal) en las 4 combinaciones de tema × prioridad, y a cualquier porcentaje de 0 a 100.
2. Que la corrección no dependa del tema ni de la prioridad, sino del relleno real.
3. Mantener intactos el resaltado de prioridad, los colores del tramo relleno y la correspondencia barra-fila ya establecidos.
4. Cubrir el defecto con tests que fallen con la implementación actual (no tests de caracterización).

**Non-Goals:**

- No se cambia la paleta de prioridad ni los colores de la barra (verde/naranja/ámbar/gris).
- No se rediseña la barra (sin bordes nuevos, sin píldoras de fondo para el texto, sin cambiar el tamaño de la fila).
- No se toca `TaskTable` fuera del delegate.
- No se hace configurable el estilo de la barra.
- No se corrige la deriva documental de otros requisitos de `barra-progreso`.

## Decisions

### D1: el color del texto se elige por contraste contra el relleno, no por prioridad ni por tema

**Decisión:** añadir dos helpers al delegate:

- `_relative_luminance(color)` — luminancia relativa WCAG (umbral 0.03928, coeficientes 0.2126 / 0.7152 / 0.0722).
- `_text_color_for(background)` — devuelve blanco o `#333333`, el que maximice el contraste contra `background`.

Constante nueva: `TEXT_DARK = "#333333"` (luminancia 0.0331).

```
contraste_blanco = 1.05 / (L + 0.05)
contraste_oscuro = (L + 0.05) / (0.0331 + 0.05)
elegido = blanco si contraste_blanco >= contraste_oscuro, si no #333333
```

**Razón:** es determinista, no depende del tema ni del estado de la app, y se puede testear con una función pura.

### D2: dos pasadas con recorte para cubrir los tramos mixtos

**Decisión:** el texto se dibuja dos veces:

1. Con `setClipRect(bar_rect)` y color `_text_color_for(track_color)`.
2. Si existe `chunk_rect`, con `setClipRect(chunk_rect)` y color `_text_color_for(chunk_color)`.

Ambas pasadas dibujan el mismo texto centrado en `cell_rect` (se mantiene el centrado actual para no desplazar el número).

**Razón:** es la única forma de que un texto que cruza el límite pista/tramo tenga contraste correcto en cada mitad. El recorte hace el trabajo; no hay que calcular geometría del texto.

**Alternativa descartada:** un único color oscuro para todo. Falla al 100 %: el tramo verde `#2e7d32` tiene luminancia 0.155, y `#333333` sobre él da 2.46:1.

**Alternativa descartada:** píldora semitransparente oscura detrás del texto con texto blanco. Es más simple, pero en filas de 28 px con una barra útil de ~17 px de alto añade un elemento visual denso y cambia el aspecto de toda la columna.

**Alternativa descartada:** hacer la pista transparente para que el texto blanco caiga sobre el fondo de la fila. Funciona en las filas de prioridad, pero al 100 % el texto queda blanco sobre ámbar `#ff9800` (2.16:1) y en tema claro sobre fondo claro (1.0:1).

### D3: tabla de contraste resultante

| Relleno | Luminancia | Contraste con `#333333` | Contraste con blanco | Elegido |
|---|---|---|---|---|
| Pista blanca `#ffffff` | 1.000 | 12.63:1 | 1.00:1 | `#333333` |
| Pista vacía `#bdbdbd` | 0.509 | 6.73:1 | 1.88:1 | `#333333` |
| Tramo ámbar `#ff9800` (prioridad) | 0.437 | 5.86:1 | 2.16:1 | `#333333` |
| Tramo naranja `#f57c00` (parcial) | 0.338 | 4.67:1 | 2.70:1 | `#333333` |
| Tramo verde `#2e7d32` (100 %) | 0.155 | 2.46:1 | 5.13:1 | blanco |

**Razón:** el peor caso de la tabla es 4.67:1, por encima de 4.5:1. Ningún relleno queda cubierto por un color con contraste insuficiente.

### D4: el texto deja de depender del `foreground` del item

**Decisión:** el delegate no consulta `item.foreground()` ni `option.palette.color(Text)` para el porcentaje. El `foreground` blanco que `TaskTable._apply_issue_style()` aplica a las celdas de prioridad se mantiene (afecta a las demás columnas), pero deja de influir en esta.

**Razón:** mezclar dos fuentes de color para el mismo píxel es lo que produjo el defecto. La barra calcula su propio contraste.

**Consecuencia para los tests:** el test existente `test_progress_percentage_text_is_white_in_priority_rows` comprueba `item.foreground().color() == WHITE`, que seguirá pasando pero ya no describe el texto pintado. Debe reformularse para verificar el color realmente dibujado.

## Risks / Trade-offs

- **[Riesgo] Los dígitos cambian de color a mitad del número cuando el texto cruza el límite pista/tramo.** → Mitigación: cada mitad es legible por separado (D3), y el límite solo es visible en porcentajes intermedios. Se acepta: la legibilidad manda sobre la uniformidad cromática.
- **[Riesgo] Los tests de píxel son frágiles ante cambios de fuente, DPI o antialiasing.** → Mitigación: no comparar píxeles exactos en posiciones fijas; contar píxeles dentro de una tolerancia (±12 por canal) en una zona acotada y exigir un mínimo pequeño, además de testear la función pura `_text_color_for` por separado.
- **[Riesgo] El antialiasing puede producir píxeles intermedios que rompan una aserción de igualdad exacta.** → Mitigación: contar con tolerancia y umbral, nunca igualdad estricta del pixel central.
- **[Trade-off] El texto deja de ser blanco en las filas de prioridad**, que es lo que la spec vigente de `barra-progreso` afirma literalmente. → Mitigación: el requisito nuevo define legibilidad por contraste y prevalece; se documenta en el spec y en el proposal.
- **[Riesgo] Regresión en el resto del resaltado de prioridad si se toca más de la cuenta.** → Mitigación: el cambio se limita al bloque de pintado del texto; los tests existentes de `TestPriorityHighlight` y `TestProgressBarInPriorityRows` actúan de red.

## Migration Plan

1. Tests en rojo: unitarios del helper de color y de renderizado para tema oscuro y filas con prioridad.
2. Implementar `_relative_luminance`, `_text_color_for` y las dos pasadas con recorte.
3. Reformular el test que valida el rol `foreground` para que valide el color pintado.
4. Ejecutar la suite completa y regenerar la imagen de evidencia en ambos temas.

**Rollback:** revertir el bloque de pintado del texto en `ProgressBarDelegate`. Sin migración de datos ni cambios de API.

## Open Questions

- ¿Conviene además mostrar el porcentaje fuera de la barra (a su derecha) para eliminar por completo el problema del tramo mixto? Fuera de alcance: añadiría ancho a una columna ya estrecha.
- ¿Debe el texto adaptarse si el usuario cambia el tema en caliente? Se resuelve solo: el color se calcula en cada `paint()` a partir de los colores reales.
