#!/usr/bin/env bash
# Simulated CI / local smoke (no Aura required): venv, pytest, one episode.
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
aura-build run --prompt "smoke select-best" --seed 1 --mode simulated --out "$OUT"
python - <<PY
import json
from pathlib import Path
from aura_build.schema import validate_episode
p = Path(r"$OUT")
lines = [ln for ln in p.read_text().splitlines() if ln.strip()]
assert len(lines) == 1, lines
ep = json.loads(lines[0])
validate_episode(ep)
assert ep["runtime"]["mode"] == "simulated", ep["runtime"]
print("smoke ok mode=simulated:", lines[0][:120], "...")
PY
