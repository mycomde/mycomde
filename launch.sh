#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MARKET HEATMAP — STARTUP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! command -v python3 &>/dev/null; then
    echo "  ERROR: Python 3 is not installed."
    read -p "  Press Enter to close..."
    exit 1
fi
echo "  Python: $(python3 --version)"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env — add your FINVIZ_API_KEY"
    read -p "  Press Enter to close..."
    exit 0
fi
if [ ! -d "venv" ]; then
    echo "  Installing dependencies..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
else
    source venv/bin/activate
fi
(sleep 3 && open "http://127.0.0.1:8050") &
echo ""
echo "  Starting dashboard... Brave will open automatically."
echo "  To stop: press Ctrl+C"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 dashboard.py
