## ADDED Requirements

### Requirement: Nombre de proyecto con la ruta de ancestros
El sistema SHALL construir, para cada proyecto, un nombre visible formado por los nombres de sus proyectos ancestros desde la raíz hasta el propio proyecto, unidos por el separador ` > ` (ej. `Proyecto padre 1 > Soporte`). El nombre SHALL recalcularse a partir de la jerarquía padre/hijo devuelta por la API.

#### Scenario: Proyecto anidado en un padre
- **WHEN** el proyecto "Soporte" (id 42) tiene como padre el proyecto "Proyecto padre 1"
- **THEN** su nombre visible es `Proyecto padre 1 > Soporte`

#### Scenario: Proyecto anidado en dos niveles
- **WHEN** el proyecto "Soporte" (id 42) tiene como padre el proyecto "Intermedio" (id 10), que a su vez es hijo de "Raíz" (id 5)
- **THEN** su nombre visible es `Raíz > Intermedio > Soporte`

#### Scenario: Proyecto raíz
- **WHEN** un proyecto no tiene padre
- **THEN** su nombre visible es su propio nombre, sin separador

#### Scenario: Proyectos homónimos bajo padres distintos
- **WHEN** existen dos proyectos "Soporte" con ids 42 y 43, hijos de "Proyecto padre 1" y "Proyecto padre 2" respectivamente
- **THEN** sus nombres visibles son `Proyecto padre 1 > Soporte` y `Proyecto padre 2 > Soporte`
- **AND** son distinguibles entre sí

#### Scenario: Padre no disponible
- **WHEN** el `parent_id` de un proyecto apunta a un proyecto que no está en la lista cargada
- **THEN** su nombre visible es su propio nombre, sin fallar

### Requirement: Nombre completo en el listado de tareas
La columna "Proyecto" de la tabla de tareas y el tooltip de la fila SHALL mostrar el nombre completo con la ruta de ancestros del proyecto de cada tarea.

#### Scenario: Dos subproyectos homónimos en el listado
- **WHEN** el listado contiene una tarea del proyecto 42 y otra del proyecto 43 (ambos llamados "Soporte" bajo padres distintos)
- **THEN** la columna "Proyecto" muestra `Proyecto padre 1 > Soporte` y `Proyecto padre 2 > Soporte` respectivamente
- **AND** el tooltip de cada fila muestra el nombre completo del proyecto

### Requirement: Nombre completo en el diálogo de alta/edición de tarea
El combo de proyecto del `TaskDialog` SHALL listar los proyectos con su nombre completo con la ruta de ancestros, tanto en modo creación como en modo edición.

#### Scenario: Alta de tarea con proyectos homónimos
- **WHEN** el usuario abre el `TaskDialog` y despliega el combo de proyecto
- **THEN** las opciones muestran `Proyecto padre 1 > Soporte` y `Proyecto padre 2 > Soporte`, no `Soporte` repetido

#### Scenario: Edición de tarea preselecciona el nombre completo
- **WHEN** el usuario edita una tarea del proyecto 43
- **THEN** el combo de proyecto muestra seleccionado `Proyecto padre 2 > Soporte`

### Requirement: Nombre completo en el filtro de proyectos
El combo de proyectos del `FilterBar` SHALL mostrar el nombre completo con la ruta de ancestros, en lugar de la indentación con espacios.

#### Scenario: Filtro con subproyectos homónimos
- **WHEN** el usuario despliega el filtro "Proyecto"
- **THEN** la lista muestra `Proyecto padre 1 > Soporte` y `Proyecto padre 2 > Soporte` como opciones distintas

### Requirement: Nombre completo al enviar una tarea a otro proyecto
El diálogo de selección de proyecto destino de "Mover a otro proyecto..." SHALL listar los proyectos con su nombre completo con la ruta de ancestros.

#### Scenario: Elección de destino entre homónimos
- **WHEN** el usuario elige "Mover a otro proyecto..." y despliega el combo de destino
- **THEN** las opciones muestran el nombre completo de cada proyecto
- **AND** puede distinguir y seleccionar el subproyecto correcto

### Requirement: Aplicación consistente del nombre completo
Todas las vistas que consumen la lista de proyectos del sistema SHALL usar el mismo nombre completo, incluida la lista de proyectos de notificaciones de la ventana de Ajustes.

#### Scenario: Lista de notificaciones en Ajustes
- **WHEN** el usuario abre Ajustes y consulta la lista de proyectos de notificación
- **THEN** cada proyecto aparece con su nombre completo con la ruta de ancestros