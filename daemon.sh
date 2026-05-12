#!/bin/bash
# Runs dashboard silently for background data collection.
# Started automatically by macOS at login via LaunchAgent.
export PATH="/usr/local/bin:/usr/bin:/bin"
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec /usr/local/bin/python3 dashboard.py
