#!/bin/bash
# Lanceur CR Reunion — gère automatiquement PYTHONPATH et le venv
DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$DIR"
exec "$DIR/.venv/bin/python" "$DIR/src/main.py" "$@"
