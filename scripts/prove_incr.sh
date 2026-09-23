#!/usr/bin/env bash
# Thin wrapper: aura-build prove-incr (fail-closed refuse is exit 0).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
VENV="${ROOT}/.venv"
if [[ ! -d "$VENV" ]]; then
  "$PYTHON" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install -e ".[dev]" -q

exec aura-build prove-incr "$@"
