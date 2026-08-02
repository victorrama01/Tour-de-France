#!/usr/bin/env bash
set -euo pipefail

echo "== TourDeFrance macOS build =="

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "PyInstaller not found. Installing..."
  python3 -m pip install pyinstaller
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

ENTRY="src/tour_de_france/main.py"
if [[ ! -f "$ENTRY" ]]; then
  echo "Could not find entrypoint: $ENTRY" >&2
  exit 1
fi

BUNDLE_ARG="--onefile"
if [[ "${1:-}" == "--onedir" ]]; then
  BUNDLE_ARG="--onedir"
fi

CMD=(
  pyinstaller
  --noconfirm
  "$BUNDLE_ARG"
  --windowed
  --name TourDeFrance
  --paths src
)

if [[ -d "assets" ]]; then
  echo "Including assets directory: assets/"
  CMD+=(--add-data "assets:assets")
else
  echo "No assets/ directory found. Build will use fallback logo."
fi

CMD+=("$ENTRY")

echo "Running: ${CMD[*]}"
"${CMD[@]}"

echo
echo "Build complete."
if [[ "$BUNDLE_ARG" == "--onedir" ]]; then
  echo "Output: dist/TourDeFrance.app"
else
  echo "Output: dist/TourDeFrance.app"
fi
