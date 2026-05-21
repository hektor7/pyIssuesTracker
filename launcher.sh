#!/usr/bin/env bash
# ================================================================
# PyIssuesTracker - Lanzador Linux (Mint, XFCE, KDE, GNOME, etc.)
# Detecta Python, crea venv, instala dependencias y ejecuta
# ================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"
MAIN_SCRIPT="main.py"
APP_NAME="PyIssuesTracker"
APP_VERSION="0.1.1"

# ---- Colores ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}  ${APP_NAME} v${APP_VERSION} - Linux${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

# ---- Detectar Python ----
PYTHON_EXE=""
for candidate in python3 python3.10 python3.9 python3.11 python3.12 python; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ] 2>/dev/null; then
            PYTHON_EXE="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON_EXE" ]; then
    echo -e "${RED}[ERROR] No se encontro Python >= 3.8 en el PATH.${NC}"
    echo "        Instala Python 3.8+ con: sudo apt install python3"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python encontrado: $PYTHON_EXE"
"$PYTHON_EXE" --version
echo ""

# ---- Crear venv si no existe ----
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo -e "${YELLOW}[INFO]${NC} Creando entorno virtual..."
    "$PYTHON_EXE" -m venv "$VENV_DIR" || {
        echo -e "${RED}[ERROR]${NC} No se pudo crear el entorno virtual."
        echo "        Instala venv con: sudo apt install python3-venv"
        exit 1
    }
    echo -e "${GREEN}[OK]${NC} Entorno virtual creado."
else
    echo -e "${GREEN}[OK]${NC} Entorno virtual existente."
fi

# ---- Rutas del venv ----
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# ---- Instalar/actualizar dependencias ----
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${YELLOW}[INFO]${NC} Verificando dependencias..."
    if ! "$VENV_PYTHON" -c "import PyQt6, httpx, packaging" 2>/dev/null; then
        echo -e "${YELLOW}[INFO]${NC} Instalando dependencias..."
        "$VENV_PIP" install --quiet -r "$REQUIREMENTS_FILE" || {
            echo -e "${RED}[ERROR]${NC} Fallo la instalacion de dependencias."
            echo "        Para diagnosticar: $VENV_PIP install -r $REQUIREMENTS_FILE"
            exit 1
        }
        echo -e "${GREEN}[OK]${NC} Dependencias instaladas."
    else
        echo -e "${GREEN}[OK]${NC} Dependencias ya instaladas."
    fi
fi

echo ""

# ---- XFCE / Mint: asegurar compatibilidad con tray icon ----
# Algunos entornos necesitan sni-qt o configuracion extra
if [ -n "${XDG_CURRENT_DESKTOP:-}" ]; then
    case "$XDG_CURRENT_DESKTOP" in
        XFCE|X-Cinnamon|MATE)
            export QT_QPA_PLATFORMTHEME=gtk2 2>/dev/null || true
            ;;
    esac
fi
export PYTHONUNBUFFERED=1

# ---- Ejecutar ----
echo -e "${YELLOW}[INFO]${NC} Iniciando PyIssuesTracker..."
"$VENV_PYTHON" "$MAIN_SCRIPT" &
disown
