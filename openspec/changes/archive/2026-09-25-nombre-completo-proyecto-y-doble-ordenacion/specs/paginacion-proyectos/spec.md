## MODIFIED Requirements

### Requirement: Proyectos con jerarquía en paginación
El sistema SHALL preservar la información de jerarquía de proyectos (padre/hijo) al cargar proyectos paginados, mostrando cada proyecto con su nombre completo con la ruta de ancestros (`Padre > Hijo`) en el combo de filtro, en lugar de la indentación con espacios.

#### Scenario: Proyectos con subproyectos en múltiples páginas
- **WHEN** un proyecto padre está en la página 1 y su subproyecto en la página 2
- **THEN** la jerarquía se reconstruye correctamente y el subproyecto aparece como `Padre > Hijo` en el combo de filtro

#### Scenario: Subproyectos homónimos
- **WHEN** dos subproyectos comparten el nombre "Soporte" bajo padres distintos
- **THEN** el combo de filtro los muestra como `Padre 1 > Soporte` y `Padre 2 > Soporte`, siendo distinguibles