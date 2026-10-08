## Why

Actualmente cambiar el progreso de una tarea, reasignarla o modificar su estado requiere abrir el diálogo de edición completo (doble clic), lo que implica varios clics y esperas de carga (checklists, comentarios, etc.). Un menú contextual sobre las columnas de progreso, asignado y estado permitiría cambios rápidos sin salir de la vista principal, agilizando significativamente el flujo de trabajo diario.

Además, los usuarios repiten frecuentemente las mismas asignaciones (las mismas 3-5 personas). Tener un acceso rápido a las "personas frecuentes" evita tener que buscar en listas largas cada vez.

## What Changes

- **Menú contextual en `TaskTable`**: se habilita `customContextMenuRequested` para detectar clic derecho. Según la columna clickeada, se muestra un menú distinto.
- **Columna Progreso**: menú con opciones 0%, 20%, 40%, 60%, 80%, 100%. Al seleccionar, diálogo de confirmación. Al confirmar, se actualiza la tarea vía API.
- **Columna Asignado a**: menú con "Asignarme a mí" + separador + lista de "personas frecuentes" (últimas 5 personas usadas en asignaciones/ediciones). Si no hay frecuentes, se muestra opción deshabilitada "No hay personas frecuentes". Al seleccionar, diálogo de confirmación.
- **Columna Estado**: menú con todos los estados disponibles. Al seleccionar, diálogo de confirmación. Al confirmar, se actualiza la tarea vía API.
- **Almacenamiento de personas frecuentes**: se guardan en `QSettings` los IDs de los últimos 5 usuarios a los que se ha asignado una tarea (desde `AssignDialog`, `TaskDialog`, o el nuevo menú contextual). Se actualizan automáticamente al asignar.

## Capabilities

### New Capabilities
- `menu-contextual-progreso`: Clic derecho en la columna de progreso muestra opciones de 0% a 100% en incrementos de 20%, con confirmación previa.
- `menu-contextual-asignado`: Clic derecho en la columna de asignado muestra "Asignarme a mí" y las 5 últimas personas frecuentes, con almacenamiento automático en QSettings.
- `menu-contextual-estado`: Clic derecho en la columna de estado muestra todos los estados disponibles para cambio rápido, con confirmación previa.

### Modified Capabilities
<!-- Ninguna -->

## Impact

- **`app/widgets/task_table.py`**: Añadir `customContextMenuRequested`, nueva señal `cambio_rapido` (o señales específicas), método `_show_context_menu()` que despache según columna.
- **`app/main_window.py`**: Conectar nuevas señales, implementar handlers para cambio de progreso, asignación rápida (con actualización de frecuentes) y cambio de estado.
- **`app/services/settings_manager.py`**: Nuevas propiedades `frequent_people` (lectura/escritura de lista de IDs en QSettings).
- **`app/utils/constants.py`**: Nueva clave `SETTINGS_KEY_FREQUENT_PEOPLE`.
- Sin impacto en API de Redmine (se usan los métodos existentes `update_issue`, `assign_issue`, `complete_issue`).
