#!/usr/bin/env bash
# Simulated CI / local smoke (no Aura required): venv, pytest, episodes, harness canary, export.
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

# M3: harness canary (AUTOPROMOTE off → discard) + reject bad L1
HROOT="${ROOT}/trajectories/_smoke_harness"
rm -rf "$HROOT"
mkdir -p "$HROOT"
OUT3="${ROOT}/trajectories/smoke_harness_canary.jsonl"
rm -f "$OUT3"
aura-build harness-mutate \
  --prompt "smoke harness canary" --seed 3 \
  --set worldline_count=4 \
  --fitness-weight tests=0.8 \
  --harness-root "$HROOT" \
  --out "$OUT3"

OUT4="${ROOT}/trajectories/smoke_harness_reject.jsonl"
rm -f "$OUT4"
set +e
aura-build harness-mutate \
  --prompt "smoke harness reject" --seed 4 \
  --set worldline_count=0 \
  --harness-root "$HROOT" \
  --out "$OUT4"
rc=$?
set -e
test "$rc" -eq 1

# memory roundtrip
aura-build memory set --profile smoke --key demo --value anti-postman --harness-root "$HROOT"
aura-build memory get --profile smoke --key demo --harness-root "$HROOT" | grep -q anti-postman

# M4: batch export (JSON always; Parquet optional)
EXPORT_JSON="${ROOT}/trajectories/smoke_export.json"
rm -f "$EXPORT_JSON" "${ROOT}/trajectories/smoke_export.parquet"
aura-build export "$OUT" "$OUT2" "$OUT3" "$OUT4" \
  --out "$EXPORT_JSON" --no-parquet

python - <<PY
import json
from pathlib import Path
from aura_build.schema import validate_episode

def check(path, *, expect_profile=False, expect_harness_outcome=None, expect_accepted=None):
    p = Path(path)
    lines = [ln for ln in p.read_text().splitlines() if ln.strip()]
    assert len(lines) == 1, lines
    ep = json.loads(lines[0])
    validate_episode(ep)
    assert ep["runtime"]["mode"] in ("simulated", "aura"), ep["runtime"]
    assert ep["runtime"].get("incr_proven", False) is False
    if expect_profile:
        assert ep["runtime"]["profile"]["id"] == "aura-repo"
        assert ep["runtime"]["session_model"] == "shared_workspace_subprocess"
        assert len(ep["worldlines"]) >= 2
        assert len(ep["discarded"]) == len(ep["worldlines"]) - 1
        assert all(w.get("stable_ref") for w in ep["worldlines"])
    if expect_harness_outcome is not None:
        assert ep["harness"]["outcome"] == expect_harness_outcome
        assert ep["harness"]["mid"]
        ops = [a["op"] for a in ep["harness"]["actions"]]
        assert "propose" in ops and "canary" in ops
        assert expect_harness_outcome in ops
        assert ep["harness"]["l3_online"] is False
        if expect_accepted is not None:
            canary = [a for a in ep["harness"]["actions"] if a["op"] == "canary"][0]
            assert canary["accepted"] is expect_accepted
    print("smoke ok:", path)

check(r"$OUT", expect_profile=False)
check(r"$OUT2", expect_profile=True)
check(r"$OUT3", expect_harness_outcome="discard", expect_accepted=True)
check(r"$OUT4", expect_harness_outcome="heal", expect_accepted=False)

export_path = Path(r"$EXPORT_JSON")
exported = json.loads(export_path.read_text())
assert isinstance(exported, list) and len(exported) >= 4, len(exported)
for ep in exported:
    validate_episode(ep)
    assert ep["privacy"].get("redacted") is True
    assert ep["runtime"].get("incr_proven", False) is False
    assert ep["harness"]["l3_online"] is False
print("smoke ok export:", export_path, "n=", len(exported))
print("smoke ok all (M0–M4)")
PY
