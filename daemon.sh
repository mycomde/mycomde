#!/bin/bash
# Runs dashboard silently for background data collection.
# Started automatically by macOS at login via LaunchAgent.
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec python3 dashboard.py
