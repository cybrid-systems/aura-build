#!/usr/bin/env bash
# M0 CI / local smoke: venv, install, pytest, one live run.
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

python -m pip install -U pip -q
python -m pip install -e ".[dev]" -q
python -m pytest -q

OUT="${ROOT}/trajectories/smoke.jsonl"
rm -f "$OUT"
aura-build run --prompt "smoke select-best" --seed 1 --out "$OUT"
python - <<PY
import json
from pathlib import Path
from aura_build.schema import validate_episode
p = Path(r"$OUT")
lines = [ln for ln in p.read_text().splitlines() if ln.strip()]
assert len(lines) == 1, lines
validate_episode(json.loads(lines[0]))
print("smoke ok:", lines[0][:120], "...")
PY
