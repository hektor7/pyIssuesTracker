## 1. Corregir URL del boton "Abrir en Redmine"

- [x] 1.1 Normalizar `redmine_url` en el setter de `SettingsManager` (aplicar `.strip().rstrip("/")` y añadir `https://` si no tiene esquema)
- [x] 1.2 Corregir construccion de URL en `_cargar_issues()` (usar `urljoin` con barra asegurada, evitar `f"{base_url}/issues/{id}"` propenso a doble slash)
- [x] 1.3 Normalizar URL en el fallback de `_abrir_url_redmine()`
- [x] 1.4 Añadir accion "Abrir en Redmine" al menu contextual de `TaskTable`

## 2. Columna fecha de fin (due_date)

- [x] 2.1 Añadir campo `due_date: str = ""` al dataclass `RedmineIssue` en `redmine_client.py`
- [x] 2.2 Parsear `due_date` desde la respuesta JSON en `get_issues()`
- [x] 2.3 Añadir `COL_DUE_DATE = 3` en `TaskTable`, renumerar columnas posteriores (Estado=4, Asignado=5, Progreso=6, URL=7)
- [x] 2.4 Añadir cabecera "Fecha fin" y mostrar el valor en `set_issues()` (celda vacia si no hay fecha)
- [x] 2.5 Incluir `due_date` en el diccionario de datos de `_cargar_issues()` en `main_window.py`
- [x] 2.6 Implementar edicion inline en `TaskTable`: doble clic en celda "Fecha fin" muestra `QDateEdit`, al confirmar (Enter/foco perdido) llama a `update_issue(due_date=...)` via senal
- [x] 2.7 Emitir senal `due_date_cambiada(issue_id, due_date)` desde `TaskTable` y conectar en `main_window.py`

## 2b. Campo fecha de fin en TaskDialog

- [x] 2b.1 Añadir `QDateEdit` con `QCheckBox` de activacion al `TaskDialog` (nueva fila debajo de "Fecha inicio")
- [x] 2b.2 Precargar `due_date` en modo edicion desde `task_data`
- [x] 2b.3 Enviar `due_date` en `create_issue()` y `update_issue()` desde `main_window.py` al crear/editar tarea

## 3. Filtro por fecha con presets

- [x] 3.1 Añadir `QComboBox` de presets al `FilterBar`: "Sin filtro", "Hoy", "Ayer", "Esta semana", "Semana pasada", "Este mes", "Mes pasado", "Rango personalizado"
- [x] 3.2 Añadir dos `QDateEdit` (desde/hasta) al `FilterBar`, ocultos inicialmente, visibles solo con "Rango personalizado"
- [x] 3.3 Implementar calculo de rangos para cada preset usando `datetime.date`
- [x] 3.4 Emitir nueva señal `fecha_cambiada(due_date_from: str | None, due_date_to: str | None)`
- [x] 3.5 Añadir parametros `due_date_from` y `due_date_to` a `RedmineClient.get_issues()`
- [x] 3.6 Construir query string `due_date` con sintaxis `>=<` de Redmine en `get_issues()`
- [x] 3.7 Conectar senal `fecha_cambiada` en `main_window.py` y pasar parametros a `_cargar_issues()` → `get_issues()`
- [x] 3.8 Persistir seleccion de filtro de fecha en `SettingsManager` (nuevas claves en `constants.py`)

## 4. Autocompletado @usuario

- [x] 4.1 Crear funcion helper `create_mention_completer(plain_text_edit, members)` que configure un `QCompleter` con activacion por `@`
- [x] 4.2 Añadir `QCompleter` al campo de descripcion en `TaskDialog`, pasando la lista de miembros del proyecto
- [x] 4.3 Añadir `QCompleter` al campo de comentario en `CommentsWidget`, recibiendo miembros del proyecto
- [x] 4.4 Asegurar que `CommentsWidget` tiene acceso a los miembros (pasar parametro en constructor o setter)
- [x] 4.5 Implementar deteccion del token `@`: el completer se activa al escribir `@` y se desactiva al pulsar espacio o Escape

## 5. Tests

- [x] 5.1 Test unitario: normalizacion de URL en `SettingsManager.redmine_url` (barra final, sin esquema)
- [x] 5.2 Test unitario: construccion de URL en `_cargar_issues()` sin doble slash
- [x] 5.3 Test unitario: `RedmineIssue` incluye `due_date` y se parsea correctamente
- [x] 5.4 Test unitario: `get_issues()` envia `due_date` correcto con sintaxis `>=<`
- [x] 5.5 Test unitario: calculo de presets de fecha (hoy, ayer, esta semana, semana pasada, este mes, mes pasado)
- [x] 5.6 Test de integracion: columna "Fecha fin" visible en `TaskTable` con datos de prueba
- [x] 5.7 Test de integracion: edicion inline de fecha de fin emite senal con issue_id y due_date correctos
- [x] 5.8 Test de integracion: `TaskDialog` incluye campo "Fecha fin" y envia `due_date` al crear/editar
- [x] 5.9 Test de integracion: `FilterBar` emite senal `fecha_cambiada` con rango correcto al seleccionar preset
- [x] 5.10 Test de integracion: autocompletado @usuario muestra miembros del proyecto

## 6. Verificacion manual

- [x] 6.1 Verificar que "Abrir en Redmine" funciona con URL con y sin barra final, con y sin `https://`
- [x] 6.2 Verificar que la columna "Fecha fin" aparece, muestra fechas, y se puede editar inline
- [x] 6.3 Verificar que el campo "Fecha fin" funciona en crear y editar tarea
- [x] 6.4 Verificar que los presets de filtro de fecha filtran correctamente las tareas
- [x] 6.5 Verificar que el autocompletado @usuario funciona en descripcion y comentarios
