## Why

Cuatro carencias de UX impactan la productividad diaria: (1) el botón "Abrir en Redmine" genera URLs rotas (doble slash o sin protocolo) cuando la URL base tiene barra final o carece de esquema; (2) no se muestra la fecha de fin (`due_date`) en la tabla de tareas aunque Redmine la expone vía API; (3) no existe ningún filtro por fecha, obligando al usuario a buscar tareas visualmente; (4) al escribir comentarios o descripciones con `@usuario` no hay autocompletado, ralentizando la comunicación y aumentando errores tipográficos en las menciones.

## What Changes

- **Corregir** la construcción de la URL en el botón "Abrir en Redmine": normalizar la URL base (eliminar barra final, asegurar esquema `https://`) al guardar en `SettingsManager` y al construir la URL de la tarea. Añadir opción "Abrir en Redmine" al menú contextual de la tabla.
- **Añadir** columna "Fecha fin" (`due_date`) a la tabla de tareas con edición inline (doble clic abre un `QDateEdit` en la celda), extrayendo el campo `due_date` de la API de Redmine en `RedmineIssue`, `get_issues()` y `_cargar_issues()`. La edición persiste en Redmine vía `update_issue()`.
- **Añadir** campo "Fecha fin" en los diálogos de nueva tarea y edición de tarea (`TaskDialog`), permitiendo establecer/modificar `due_date` al crear o editar una tarea.
- **Añadir** filtro por fecha en el `FilterBar` con presets rápidos: *Hoy*, *Ayer*, *Esta semana* (lunes a domingo), *Semana pasada*, *Este mes*, *Mes pasado*. El filtro usará el campo `due_date` de Redmine. Los presets calcularán rangos de fecha automáticamente.
- **Añadir** autocompletado de `@usuario` en los campos de descripción (`TaskDialog`) y comentarios (`CommentsWidget`). Al escribir `@`, se mostrará un popup con los miembros del proyecto actual, filtrados por el texto tras la `@`. La API de Redmine ya procesa las menciones en el servidor; solo falta el soporte en el cliente.

## Capabilities

### New Capabilities

- `columna-fecha-fin`: Mostrar y editar inline la fecha de fin (`due_date`) en la tabla, y exponer el campo en los diálogos de nueva/editar tarea.
- `filtro-fecha`: Filtrar tareas por `due_date` con presets rápidos (Hoy, Ayer, Esta semana, Semana pasada, Este mes, Mes pasado) y opción de rango personalizado.
- `menciones-usuario`: Autocompletado de `@usuario` en los campos de descripción y comentarios, usando la lista de miembros del proyecto.

### Modified Capabilities

<!-- Ninguna spec existente modifica sus requisitos -->

## Impact

- **`app/services/redmine_client.py`**: añadir `due_date` al dataclass `RedmineIssue` y parsearlo en `get_issues()`; añadir parámetros `due_date_from`/`due_date_to` a `get_issues()`.
- **`app/widgets/task_table.py`**: añadir columna `COL_DUE_DATE`; mostrar `due_date` en la tabla; añadir "Abrir en Redmine" al menú contextual.
- **`app/widgets/filter_bar.py`**: añadir `QComboBox` de presets de fecha + `QDateEdit` para rango personalizado; nueva señal `fecha_cambiada`.
- **`app/widgets/comments_widget.py`**: añadir `QCompleter` con `@` trigger al `QPlainTextEdit` de comentarios.
- **`app/dialogs/task_dialog.py`**: añadir `QCompleter` con `@` trigger al `QPlainTextEdit` de descripción; añadir campo `QDateEdit` para `due_date`.
- **`app/main_window.py`**: conectar nuevo filtro de fecha, pasar `due_date_from`/`due_date_to` a `get_issues()`, normalizar URL al guardar configuración y al construir `url` en `_cargar_issues()`.
- **`app/services/settings_manager.py`**: añadir persistencia del filtro de fecha.
- **`app/utils/constants.py`**: añadir claves de configuración para el filtro de fecha.
