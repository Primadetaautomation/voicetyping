#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

REPO_URL="https://github.com/Primadetaautomation/voicetyping.git"
MIN_PYTHON="3.10"

# ── kleuren ─────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

header()  { echo -e "\n${BOLD}═══ $1 ═══${NC}"; }
ok()      { echo -e "  ${GREEN}✓${NC} $1"; }
warn()    { echo -e "  ${YELLOW}!${NC} $1"; }
fail()    { echo -e "  ${RED}✗${NC} $1"; }

# ── banner ──────────────────────────────────────────────
echo -e "${BOLD}"
echo "╔═══════════════════════════════════╗"
echo "║     Voice Typer - Installatie     ║"
echo "║         macOS                     ║"
echo "╚═══════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Python check ────────────────────────────────────
header "Python controleren"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  fail "Python niet gevonden."
  echo ""
  echo "  Installeer Python 3.10+ via:"
  echo "    brew install python3"
  echo "  of download van https://www.python.org/downloads/"
  echo ""
  read -r -n 1 -p "Druk op een toets om af te sluiten..."
  echo
  exit 1
fi

PYTHON_VERSION=$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$("$PYTHON_BIN" -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$("$PYTHON_BIN" -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
  fail "Python $PYTHON_VERSION gevonden, maar 3.10+ is vereist."
  echo ""
  echo "  Update Python via:"
  echo "    brew install python3"
  echo "  of download van https://www.python.org/downloads/"
  echo ""
  read -r -n 1 -p "Druk op een toets om af te sluiten..."
  echo
  exit 1
fi

ok "Python $PYTHON_VERSION ($PYTHON_BIN)"

# ── 2. Virtuele omgeving ───────────────────────────────
header "Virtuele omgeving"

if [ ! -d ".venv" ]; then
  echo "  Virtuele omgeving maken..."
  "$PYTHON_BIN" -m venv .venv
  ok "Aangemaakt"
else
  ok "Bestaat al"
fi

source .venv/bin/activate

# ── 3. Dependencies ────────────────────────────────────
header "Dependencies installeren"

python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q
ok "Alle packages geïnstalleerd"

# ── 4. Configuratie ────────────────────────────────────
header "Configuratie"

CONFIG_PATH="$HOME/.voice-typer.toml"
if [ -f "$CONFIG_PATH" ]; then
  ok "Config bestaat al op $CONFIG_PATH"
  echo ""
  read -r -p "  Settings openen om aan te passen? (y/N): " OPEN_SETTINGS
  OPEN_SETTINGS="${OPEN_SETTINGS:-N}"
  if [[ "$OPEN_SETTINGS" =~ ^[Yy]$ ]]; then
    python voice_typer.py settings
  fi
else
  echo "  Geen config gevonden. Settings venster openen..."
  echo ""
  python voice_typer.py settings
  if [ -f "$CONFIG_PATH" ]; then
    ok "Configuratie opgeslagen"
  else
    warn "Geen configuratie opgeslagen. Je kunt later alsnog draaien:"
    echo "    python voice_typer.py settings"
  fi
fi

# ── 5. macOS permissies ────────────────────────────────
header "macOS Permissies (belangrijk!)"

echo -e "  Voice Typer heeft deze permissies nodig:"
echo -e "  Ga naar ${BOLD}Systeeminstellingen > Privacy en beveiliging${NC}"
echo ""
echo "  1. Microfoon        → zet je terminal app AAN"
echo "  2. Toegankelijkheid → zet je terminal app AAN"
echo "  3. Invoerbewaking   → zet je terminal app AAN"
echo ""
warn "Zonder deze permissies werkt opname en typen niet!"

# ── klaar ──────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}═══ Installatie voltooid! ═══${NC}"
echo ""
echo "  Starten: dubbelklik start_mac.command"
echo "  Of:      cd $SCRIPT_DIR && .venv/bin/python voice_typer.py run"
echo ""
echo "  Settings wijzigen: .venv/bin/python voice_typer.py settings"
echo ""
read -r -n 1 -p "Druk op een toets om af te sluiten..."
echo
