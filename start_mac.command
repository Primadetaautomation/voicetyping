#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f ".venv/bin/python" ]; then
  echo "Geen virtuele omgeving gevonden."
  echo "Run eerst install_mac.command"
  read -r -n 1 -p "Druk op een toets om af te sluiten..."
  echo
  exit 1
fi

source .venv/bin/activate

echo "Voice Typer wordt gestart..."
python voice_typer.py run
