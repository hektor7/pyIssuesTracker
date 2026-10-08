## Purpose

Definir la carga paginada de proyectos desde la API de Redmine en PyIssuesTracker: obtener todos los proyectos sin límite fijo (con tope de seguridad), preservando la jerarquía padre/hijo y mostrando el nombre completo `Padre > Hijo` en el filtro de proyectos.

## Requirements

### Requirement: Carga paginada de proyectos
El sistema SHALL cargar todos los proyectos disponibles desde la API de Redmine usando paginación, sin estar limitado a un máximo fijo de 200 proyectos.

#### Scenario: Instancia con más de 200 proyectos
- **WHEN** la instancia de Redmine tiene 350 proyectos
- **THEN** el sistema obtiene todos los 350 proyectos mediante múltiples peticiones paginadas
- **AND** todos los proyectos aparecen disponibles en el combo de filtro de proyectos

#### Scenario: Instancia con pocos proyectos
- **WHEN** la instancia de Redmine tiene menos de 100 proyectos
- **THEN** el sistema obtiene todos los proyectos en una sola petición (sin paginación adicional)

#### Scenario: Límite de seguridad ante paginación infinita
- **WHEN** la API devuelve resultados continuamente (por un bug o mala configuración)
- **THEN** el sistema se detiene tras 20 páginas (2000 proyectos) como máximo

### Requirement: Proyectos con jerarquía en paginación
El sistema SHALL preservar la información de jerarquía de proyectos (padre/hijo) al cargar proyectos paginados, mostrando cada proyecto con su nombre completo con la ruta de ancestros (`Padre > Hijo`) en el combo de filtro, en lugar de la indentación con espacios.

#### Scenario: Proyectos con subproyectos en múltiples páginas
- **WHEN** un proyecto padre está en la página 1 y su subproyecto en la página 2
- **THEN** la jerarquía se reconstruye correctamente y el subproyecto aparece como `Padre > Hijo` en el combo de filtro

#### Scenario: Subproyectos homónimos
- **WHEN** dos subproyectos comparten el nombre "Soporte" bajo padres distintos
- **THEN** el combo de filtro los muestra como `Padre 1 > Soporte` y `Padre 2 > Soporte`, siendo distinguibles