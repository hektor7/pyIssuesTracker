## Why

Al crear una nueva tarea desde la aplicación, no se está registrando correctamente en Redmine y no se muestra ningún mensaje de error que permita diagnosticar el problema. Adicionalmente, se han identificado varias carencias de usabilidad que dificultan el trabajo diario: no se puede modificar el tracker en edición, no se visualiza el tipo de tarea en el grid, el límite de proyectos en el filtro es insuficiente y el orden de asignación no prioriza al usuario actual.

## What Changes

- **Corrección de errores en la creación de tareas**: Mejorar el manejo de errores de la API de Redmine al crear y editar tareas, capturando respuestas de error HTTP (422, 500, etc.) y mostrando mensajes descriptivos al usuario, incluyendo los errores de validación devueltos por la API.
- **Habilitar modificación del tracker en edición**: Permitir cambiar el campo tracker (tipo de tarea) desde la pantalla de edición de una tarea existente.
- **Añadir columna de tracker en el grid**: Mostrar el tipo de tarea (Bug, Feature, Support, etc.) como una columna visible en la tabla principal de issues.
- **Aumentar límite de proyectos en el filtro**: Eliminar o ampliar el límite de 200 proyectos en la carga del filtro, implementando paginación para soportar instancias de Redmine con gran cantidad de proyectos.
- **Priorizar "yo mismo" en asignación**: Al crear una tarea, mostrar la opción "Asignado a mí" como primera opción (después de "Sin asignar"), o colocar al usuario actual al inicio de la lista de miembros.

## Capabilities

### New Capabilities

- `manejo-errores-api`: Captura y visualización de errores de la API de Redmine (errores HTTP, validación, red) con mensajes descriptivos para el usuario.
- `columna-tracker-grid`: Visualización del tipo de tarea (tracker) como columna en la tabla de issues.
- `paginacion-proyectos`: Carga paginada de proyectos desde la API de Redmine para soportar más de 200 proyectos.
- `asignacion-prioritaria-usuario`: Priorización del usuario actual en la lista de asignación de tareas.

### Modified Capabilities

<!-- No se modifican specs existentes; todas son capacidades nuevas -->

## Impact

- **app/services/redmine_client.py**: Modificar `get_projects()` para soportar paginación. Mejorar `create_issue()` y `update_issue()` para propagar errores de validación de la API.
- **app/main_window.py**: Mejorar el manejo de errores en `_nueva_tarea()` y `_editar_tarea()` para capturar y mostrar errores específicos de la API.
- **app/dialogs/task_dialog.py**: Revisar y corregir el combo de tracker en modo edición para que sea modificable. Modificar `_populate_members()` para ordenar los miembros con el usuario actual primero.
- **app/widgets/task_table.py**: Añadir nueva columna `COL_TRACKER` y actualizar `set_issues()` para recibir y mostrar el nombre del tracker.
- **app/widgets/filter_bar.py**: Actualizar `populate_projects()` para manejar la carga paginada desde el cliente.
