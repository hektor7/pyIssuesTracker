## ADDED Requirements

### Requirement: Adjuntar documentos al crear tarea
El diálogo de nueva tarea SHALL permitir al usuario seleccionar uno o más archivos locales para adjuntarlos a la tarea al crearla.

#### Scenario: Selección de archivos
- **WHEN** el usuario hace clic en "Añadir archivo" en el diálogo de nueva tarea
- **THEN** se abre el selector de archivos nativo del sistema
- **AND** el usuario puede seleccionar múltiples archivos

#### Scenario: Lista de archivos pendientes
- **WHEN** el usuario selecciona uno o más archivos
- **THEN** los archivos seleccionados se muestran en una lista dentro del diálogo
- **AND** cada archivo muestra su nombre y tamaño

#### Scenario: Eliminar archivo de la lista
- **WHEN** el usuario hace clic en "Eliminar" junto a un archivo en la lista
- **THEN** el archivo se elimina de la lista de pendientes
- **AND** no se subirá al crear la tarea

#### Scenario: Subida de archivos al crear la tarea
- **WHEN** el usuario hace clic en "Aceptar" para crear la tarea
- **AND** hay archivos pendientes en la lista
- **THEN** cada archivo se sube a Redmine mediante `POST /uploads.json`
- **AND** los tokens de subida se incluyen en el payload de creación de la issue
- **AND** la tarea se crea con los documentos adjuntos

#### Scenario: Error en subida de archivo
- **WHEN** la subida de un archivo falla (error de red, archivo demasiado grande, servidor rechaza)
- **THEN** se muestra un mensaje de error al usuario indicando qué archivo falló
- **AND** se permite al usuario corregir el problema o cancelar
