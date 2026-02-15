#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Python niet gevonden. Installeer eerst Python 3."
  read -r -n 1 -p "Druk op een toets om af te sluiten..."
  echo
  exit 1
fi

echo "Gebruik Python via: $PYTHON_BIN"

if [ ! -d ".venv" ]; then
  echo "Virtuele omgeving maken..."
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

CONFIG_PATH="$HOME/.voice-typer.toml"
if [ -f "$CONFIG_PATH" ]; then
  echo "Config bestaat al op $CONFIG_PATH"
  read -r -p "Setup opnieuw draaien? (y/N): " RUN_SETUP
  RUN_SETUP="${RUN_SETUP:-N}"
  if [[ "$RUN_SETUP" =~ ^[Yy]$ ]]; then
    python voice_typer.py setup
  fi
else
  python voice_typer.py setup
fi

echo
echo "Installatie klaar."
echo "Start nu met: start_mac.command"
read -r -n 1 -p "Druk op een toets om af te sluiten..."
echo
