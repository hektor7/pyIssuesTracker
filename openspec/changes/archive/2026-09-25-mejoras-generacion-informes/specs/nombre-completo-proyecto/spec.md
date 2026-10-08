## MODIFIED Requirements

### Requirement: Nombre completo en el filtro de proyectos
El combo de proyectos del `FilterBar` (y cualquier `MultiSelectCombo` de proyectos del sistema, incluido el del informe) SHALL mostrar el nombre completo con la ruta de ancestros, en lugar de la indentación con espacios. Cuando el nombre completo no quepa en el control, al pasar el ratón sobre el texto del botón (con una única selección) o sobre cada ítem de la lista desplegable SHALL mostrarse un tooltip con el nombre completo.

#### Scenario: Filtro con subproyectos homónimos
- **WHEN** el usuario despliega el filtro "Proyecto"
- **THEN** la lista muestra `Proyecto padre 1 > Soporte` y `Proyecto padre 2 > Soporte` como opciones distintas

#### Scenario: Tooltip en un ítem de la lista desplegable
- **WHEN** un proyecto tiene un nombre completo largo que no cabe y el usuario pasa el ratón sobre su ítem en el filtro de proyecto
- **THEN** aparece un tooltip con el nombre completo del proyecto

#### Scenario: Tooltip en el botón con selección única
- **WHEN** el filtro de proyecto tiene seleccionado un único proyecto con nombre largo y el usuario pasa el ratón sobre el botón
- **THEN** aparece un tooltip con el nombre completo del proyecto seleccionado

#### Scenario: Tooltip en el combo de proyectos del informe
- **WHEN** el usuario despliega el combo de proyectos del `ReportDialog` y pasa el ratón sobre un ítem de nombre largo
- **THEN** aparece un tooltip con el nombre completo del proyecto