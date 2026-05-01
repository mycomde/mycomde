#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  Market Heatmap — Mac Launcher
#  Double-click this file (or run it in Terminal) to start.
# ─────────────────────────────────────────────────────────────

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MARKET HEATMAP — STARTUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Check Python 3 ──────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo ""
    echo "  ERROR: Python 3 is not installed."
    echo ""
    echo "  Install it from: https://www.python.org/downloads/"
    echo "  Then run this script again."
    read -p "  Press Enter to close..."
    exit 1
fi

echo "  Python: $(python3 --version)"

# ── Create .env if missing ───────────────────────────────────
if [ ! -f ".env" ]; then
    echo ""
    echo "  First-time setup: creating .env file..."
    cp .env.example .env
    echo "  Created .env — open it and add your Polygon.io API key."
    echo ""
    echo "  How to get a FREE API key:"
    echo "  1. Go to https://finnhub.io and click 'Get free API key'"
    echo "  2. Sign up (no credit card needed)"
    echo "  3. Copy your API key from your Finnhub dashboard"
    echo "  4. Open the .env file in this folder"
    echo "  5. Replace 'your_api_key_here' with your real key"
    echo "  6. Run this script again"
    echo ""
    read -p "  Press Enter to close..."
    exit 0
fi

# ── Create virtual environment if missing ─────────────────────
if [ ! -d "venv" ]; then
    echo ""
    echo "  First-time setup: installing dependencies..."
    echo "  (This only happens once — takes about 1 minute)"
    echo ""
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    echo "  Dependencies installed."
else
    source venv/bin/activate
fi

# ── Open browser after 3 seconds ─────────────────────────────
(sleep 3 && open "http://127.0.0.1:8050") &

# ── Start dashboard ───────────────────────────────────────────
echo ""
echo "  Starting dashboard..."
echo "  Your browser will open automatically."
echo "  To stop: press Ctrl+C"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 dashboard.py
