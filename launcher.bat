@echo off
setlocal enabledelayedexpansion

:: ================================================================
:: PyIssuesTracker - Lanzador Windows 10/11
:: Detecta Python, crea/recrea venv, instala dependencias y ejecuta
:: ================================================================

title PyIssuesTracker
cd /d "%~dp0"

set VENV_DIR=.venv
set PYTHON_EXE=
set REQUIREMENTS_FILE=requirements.txt
set MAIN_SCRIPT=main.py

:: Leer version desde app\__init__.py si existe
set APP_VERSION=0.0.0
if exist "app\__init__.py" (
    for /f "tokens=2 delims== " %%a in ('findstr "__version__" "app\__init__.py" 2^>nul') do (
        set APP_VERSION=%%~a
        set APP_VERSION=!APP_VERSION:"=!
    )
)

echo ======================================
echo   PyIssuesTracker v!APP_VERSION! - Windows
echo ======================================
echo.

:: ---- Detectar Python ----
call :find_python python3
if "%PYTHON_EXE%"=="" call :find_python python
if "%PYTHON_EXE%"=="" (
    echo [ERROR] No se encontro Python en el PATH.
    echo         Instala Python 3.9 o superior desde https://python.org
    echo         y asegurate de marcar "Add Python to PATH".
    pause
    exit /b 1
)
echo [OK] Python encontrado: %PYTHON_EXE%
for /f "tokens=*" %%i in ('"%PYTHON_EXE%" --version 2^>^&1') do echo       %%i
echo.

:: ---- Verificar/Crear venv ----
set VENV_PYTHON=%VENV_DIR%\Scripts\python.exe
set VENV_PIP=%VENV_DIR%\Scripts\pip.exe
set NEED_CREATE=0

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" --version >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Entorno virtual corrupto. Recreando...
        set NEED_CREATE=1
    ) else (
        echo [OK] Entorno virtual existente.
    )
) else (
    set NEED_CREATE=1
)

if "!NEED_CREATE!"=="1" (
    echo [INFO] Creando entorno virtual...
    if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%"
    "%PYTHON_EXE%" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        echo         Asegurate de tener instalado Python con soporte venv.
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado.
)

:: ---- Verificar pip ----
if not exist "%VENV_PIP%" (
    echo [INFO] Instalando pip en el entorno virtual...
    "%VENV_PYTHON%" -m ensurepip --upgrade >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar pip.
        pause
        exit /b 1
    )
)
echo.

:: ---- Instalar/actualizar dependencias ----
if exist "%REQUIREMENTS_FILE%" (
    echo [INFO] Verificando dependencias...
    "%VENV_PYTHON%" -c "import PyQt6, httpx, packaging" 2>nul
    if errorlevel 1 (
        echo [INFO] Instalando dependencias...
        "%VENV_PIP%" install --quiet -r "%REQUIREMENTS_FILE%"
        if errorlevel 1 (
            echo [ERROR] Fallo la instalacion de dependencias.
            echo         Prueba manualmente: pip install -r %REQUIREMENTS_FILE%
            pause
            exit /b 1
        )
        echo [OK] Dependencias instaladas.
    ) else (
        echo [OK] Dependencias ya instaladas.
    )
)
echo.

:: ---- Ejecutar ----
echo [INFO] Iniciando PyIssuesTracker...
start "" "%VENV_PYTHON%" "%MAIN_SCRIPT%"
goto :eof

:: ================================================================
:: Funcion: buscar Python en PATH y verificar version >= 3.9
:: ================================================================
:find_python
where %~1 >nul 2>&1
if errorlevel 1 exit /b 1
for /f "tokens=2 delims= " %%v in ('"%~1 -c "import sys; print(sys.version_info[0])" 2^>^&1') do (
    if %%v LSS 3 (
        exit /b 1
    )
    set PYTHON_EXE=%~1
    exit /b 0
)
exit /b 1
