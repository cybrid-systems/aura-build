#!/usr/bin/env bash
# Simulated CI / local smoke (no Aura required): venv, pytest, episodes.
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

OUT2="${ROOT}/trajectories/smoke_aura_repo.jsonl"
rm -f "$OUT2"
WS="${ROOT}/trajectories/_smoke_ws"
rm -rf "$WS"
aura-build run --prompt "smoke aura-repo profile" --seed 2 --mode simulated \
  --profile aura-repo --no-live-build --worldlines 3 \
  --workspace "$WS" --keep-workspace \
  --out "$OUT2"

python - <<PY
import json
from pathlib import Path
from aura_build.schema import validate_episode

def check(path, *, expect_profile=False):
    p = Path(path)
    lines = [ln for ln in p.read_text().splitlines() if ln.strip()]
    assert len(lines) == 1, lines
    ep = json.loads(lines[0])
    validate_episode(ep)
    assert ep["runtime"]["mode"] == "simulated", ep["runtime"]
    assert ep["runtime"].get("incr_proven", False) is False
    if expect_profile:
        assert ep["runtime"]["profile"]["id"] == "aura-repo"
        assert ep["runtime"]["session_model"] == "shared_workspace_subprocess"
        assert len(ep["worldlines"]) >= 2
        assert len(ep["discarded"]) == len(ep["worldlines"]) - 1
        assert all(w.get("stable_ref") for w in ep["worldlines"])
    print("smoke ok:", path, "mode=simulated", "profile" if expect_profile else "plain")

check(r"$OUT", expect_profile=False)
check(r"$OUT2", expect_profile=True)
print("smoke ok all")
PY
