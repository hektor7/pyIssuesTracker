#!/bin/bash
# Genera notas de release desde los commits entre dos tags.
# Uso: ./scripts/release-notes.sh [tag_anterior] [tag_actual]
# Si no se especifican, usa los dos últimos tags.

set -euo pipefail

PREVIOUS="${1:-$(git tag --sort=-creatordate | head -2 | tail -1)}"
CURRENT="${2:-$(git tag --sort=-creatordate | head -1)}"

if [ -z "$PREVIOUS" ] || [ -z "$CURRENT" ]; then
    echo "Error: no se encontraron tags. Crea al menos dos tags primero."
    exit 1
fi

echo "## Notas de release $CURRENT"
echo ""

# Capturar commits en arrays para evitar problemas de subshell
mapfile -t FEATS < <(git log "$PREVIOUS..$CURRENT" --no-merges --pretty=format:"- %s (%h)" | grep "^-\s*feat:" || true)
mapfile -t FIXES < <(git log "$PREVIOUS..$CURRENT" --no-merges --pretty=format:"- %s (%h)" | grep "^-\s*fix:" || true)
mapfile -t OTHER < <(git log "$PREVIOUS..$CURRENT" --no-merges --pretty=format:"- %s (%h)" | grep -vE "^-\s*(feat:|fix:)" || true)

if [ ${#FEATS[@]} -gt 0 ]; then
    echo "### Novedades"
    printf '%s\n' "${FEATS[@]}"
    echo ""
fi

if [ ${#FIXES[@]} -gt 0 ]; then
    echo "### Correcciones"
    printf '%s\n' "${FIXES[@]}"
    echo ""
fi

if [ ${#OTHER[@]} -gt 0 ]; then
    echo "### Otros"
    printf '%s\n' "${OTHER[@]}"
    echo ""
fi

echo "🔗 https://github.com/hektor7/pyIssuesTracker/releases/new?tag=$CURRENT"
