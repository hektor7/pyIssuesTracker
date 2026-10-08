## 1. Base compartida: RedmineClient

- [x] 1.1 Añadir método `upload_file(file_path: str) -> dict` que haga `POST /uploads.json` con `Content-Type: application/octet-stream`
- [x] 1.2 Añadir parámetro `uploads: list[dict] | None = None` al método `create_issue()` para incluirlo en el payload
- [x] 1.3 Manejar errores HTTP 404/405 en `upload_file` con mensaje descriptivo

## 2. Preselección de proyecto según filtro activo

- [x] 2.1 Añadir parámetro `default_project_id: int = 0` al constructor de `TaskDialog`
- [x] 2.2 En `_populate_fields()`, invocar `_set_combo_data` con el proyecto por defecto si `default_project_id > 0`
- [x] 2.3 Asegurar que al preseleccionar proyecto se carguen también las categorías asociadas
- [x] 2.4 En `MainWindow._nueva_tarea()`, obtener el proyecto del filtro activo y pasarlo como `default_project_id`

## 3. Selector de asignado en el diálogo

- [x] 3.1 Añadir parámetro `members: list[tuple[int, str]]` al constructor de `TaskDialog`
- [x] 3.2 Añadir combo "Asignado a" en el grupo "Detalles" con `QCompleter` y filtro `MatchContains`
- [x] 3.3 Implementar `_load_members_for_project()` que recargue los miembros al cambiar de proyecto
- [x] 3.4 Exponer propiedad `assigned_to_id` que devuelva el ID del miembro seleccionado
- [x] 3.5 En `MainWindow._nueva_tarea()`, obtener los miembros del proyecto filtrado y pasarlos al diálogo; recoger `assigned_to_id` y pasarlo a `create_issue()`

## 4. Adjuntar documentos al crear tarea

- [x] 4.1 Añadir sección "Documentos adjuntos" en `TaskDialog` visible en modo creación con botón "Añadir archivo"
- [x] 4.2 Conectar botón a `QFileDialog.getOpenFileNames()` para selección múltiple
- [x] 4.3 Mostrar lista de archivos seleccionados con nombre y tamaño, con opción de eliminar cada uno
- [x] 4.4 En `_validate_and_accept()`, subir los archivos mediante `RedmineClient.upload_file()` y almacenar tokens
- [x] 4.5 Exponer propiedad `upload_tokens` con la lista de tokens generados
- [x] 4.6 En `MainWindow._nueva_tarea()`, recoger `upload_tokens` y pasarlos a `create_issue()` como parámetro `uploads`
- [x] 4.7 Manejar errores de subida: mostrar mensaje al usuario si falla un archivo y permitir reintentar o cancelar
