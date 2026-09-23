#!/usr/bin/env bash
# Honest smoke: host unit tests always; Aura kernel episodes when AURA_BIN healthy.
# No Python orch green path. AURA_BUILD_FORCE_PYTHON is deprecated (refuse only).
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

# Host-only pytest (no FORCE_PYTHON orch). Kernel tests skip if Aura missing.
python -m pytest -q

# Discover Aura binary
LIVE_AURA="${AURA_BIN:-}"
if [[ -z "$LIVE_AURA" ]]; then
  for c in \
    /workspace/aura-redis/.deps/aura/build/aura \
    /workspace/aura-grok/build/aura \
    /workspace/aura-redis-ci/.deps/aura/build/aura
  do
    if [[ -x "$c" ]]; then LIVE_AURA="$c"; break; fi
  done
fi

# --help always
aura-build --help >/dev/null
aura-build run --help >/dev/null

# Deprecated FORCE_PYTHON must refuse orch (not silent green)
set +e
AURA_BUILD_FORCE_PYTHON=1 aura-build run --prompt "deprecated" --mode simulated >/tmp/aura_force.out 2>/tmp/aura_force.err
frc=$?
set -e
test "$frc" -eq 2
grep -q 'python_deprecated\|aura-build run' /tmp/aura_force.err

# export also refuses without Aura (no host redaction)
set +e
AURA_BUILD_FORCE_PYTHON=1 aura-build export --out /tmp/aura_force_export.json --no-parquet >/tmp/aura_force_exp.out 2>/tmp/aura_force_exp.err
frc=$?
set -e
test "$frc" -eq 2
grep -q 'python_deprecated\|aura-build export' /tmp/aura_force_exp.err

# Prove refuse without Aura (honest fail-closed, no storm orch)
PROVE_ROOT="${ROOT}/trajectories/_smoke_prove"
rm -rf "$PROVE_ROOT"
mkdir -p "$PROVE_ROOT"
env -u AURA_BIN AURA_BUILD_FORCE_PYTHON=1 aura-build prove-incr --cycles 2 --worldlines 1 \
  --aura-bin /nonexistent/aura-missing \
  --no-fiber-probe \
  --harness-root "$PROVE_ROOT" \
  --out "$PROVE_ROOT/prove-incr-latest.json" | tee "$PROVE_ROOT/prove.out"
grep -q 'incr_proven=False' "$PROVE_ROOT/prove.out"
grep -q 'python_deprecated\|aura_binary_missing\|aura_unhealthy\|aura_glibcxx' "$PROVE_ROOT/prove.out"
python - <<PYPROVE
import json
from pathlib import Path
p = Path(r"$PROVE_ROOT/prove-incr-latest.json")
data = json.loads(p.read_text())
assert data["incr_proven"] is False
assert data["measured"] is False
assert data.get("fiber_live") is False
assert data.get("kernel") == "python_deprecated"
print("smoke ok prove refuse (no Python orch):", p)
PYPROVE

aura-build doctor --skip-probe --harness-root "$PROVE_ROOT" | grep -q 'incr_proven=False'

if [[ -z "${LIVE_AURA}" || ! -x "$LIVE_AURA" ]]; then
  echo "smoke: host tests + refuse path OK; skip Aura kernel episodes (no AURA_BIN)"
  echo "smoke ok (host-only; set AURA_BIN for full kernel smoke)"
  exit 0
fi

export AURA_BIN="$LIVE_AURA"
echo "smoke: Aura kernel episodes via AURA_BIN=$AURA_BIN"

SMOKE_ROOT="${ROOT}/trajectories/_smoke_root"
rm -rf "$SMOKE_ROOT"
mkdir -p "$SMOKE_ROOT"

OUT="${ROOT}/trajectories/smoke.jsonl"
rm -f "$OUT"
aura-build run --prompt "smoke select-best" --seed 1 --mode simulated \
  --harness-root "$SMOKE_ROOT" --out "$OUT"

OUT2="${ROOT}/trajectories/smoke_aura_repo.jsonl"
rm -f "$OUT2"
WS="${ROOT}/trajectories/_smoke_ws"
rm -rf "$WS"
aura-build run --prompt "smoke aura-repo profile" --seed 2 --mode simulated \
  --profile aura-repo --no-live-build --worldlines 3 \
  --workspace "$WS" --keep-workspace \
  --harness-root "$SMOKE_ROOT" \
  --out "$OUT2"

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

aura-build memory set --profile smoke --key demo --value anti-postman --harness-root "$HROOT"
aura-build memory get --profile smoke --key demo --harness-root "$HROOT" | grep -q anti-postman

EXPORT_JSON="${ROOT}/trajectories/smoke_export.json"
rm -f "$EXPORT_JSON" "${ROOT}/trajectories/smoke_export.parquet"
aura-build export "$OUT" "$OUT2" "$OUT3" "$OUT4" \
  --out "$EXPORT_JSON" --no-parquet

aura-build l2 promote --id specialist.smoke.v0 --notes "smoke metadata" \
  --from-export "$EXPORT_JSON" --harness-root "$HROOT" --overwrite
aura-build l2 show --id specialist.smoke.v0 --harness-root "$HROOT" | grep -q 'artifact_present=True'
aura-build l2 list --harness-root "$HROOT" | grep -q specialist.smoke.v0

OUT5="${ROOT}/trajectories/smoke_l2.jsonl"
rm -f "$OUT5"
aura-build run --prompt "smoke l2 metadata" --seed 5 --mode simulated \
  --l2-weights-id specialist.smoke.v0 --harness-root "$HROOT" --out "$OUT5"

aura-build acp start --prompt "smoke session" --harness-root "$HROOT" \
  --workspace "$WS"
ACP_STATUS=$(aura-build acp status --harness-root "$HROOT")
echo "$ACP_STATUS" | grep -q 'incr_proven=False'
echo "$ACP_STATUS" | grep -q 'fiber_live=False\|fiber_live=false'
echo "$ACP_STATUS" | grep -q 'kernel=aura'
TUI_STATUS=$(aura-build tui --harness-root "$HROOT")
echo "$TUI_STATUS" | grep -q 'aura-build tui\|incr_proven=False'
echo "$TUI_STATUS" | grep -q 'kernel=aura'
aura-build acp hooks | grep -q start_session
aura-build acp worldlines --traj "$OUT2" | grep -q candidate
aura-build acp discard --workspace "$WS" --ref wl-1 --reason smoke_discard | tee /tmp/acp_discard.out | grep -q 'fiber_live=false\|fiber_live=False'
aura-build acp promote --id specialist.acp.smoke.v0 --notes smoke --harness-root "$HROOT" | grep -q 'kernel=aura\|stub='

# Live prove-incr on healthy Aura
LIVE_ROOT="${ROOT}/trajectories/_smoke_prove_live"
rm -rf "$LIVE_ROOT"
mkdir -p "$LIVE_ROOT"
set +e
aura-build prove-incr --cycles 2 --worldlines 1 \
  --aura-bin "$LIVE_AURA" \
  --no-fiber-probe \
  --harness-root "$LIVE_ROOT" \
  --out "$LIVE_ROOT/prove-incr-latest.json" \
  --json >"$LIVE_ROOT/prove.out" 2>"$LIVE_ROOT/prove.err"
set -e
export ROOT
export LIVE_ROOT
python - <<'PYLIVE'
import json
import os
from pathlib import Path
from aura_build.schema import validate_episode

p = Path(os.environ["LIVE_ROOT"]) / "prove-incr-latest.json"
if not p.is_file():
    print("smoke skip live incr_proven: no report (aura unhealthy?)")
else:
    data = json.loads(p.read_text())
    print(
        "smoke live prove:",
        "incr_proven=", data.get("incr_proven"),
        "measured=", data.get("measured"),
        "reason=", data.get("reason"),
    )
    if data.get("measured") and data.get("aura_healthy"):
        assert data["incr_proven"] is True, data
        assert data["cycles_incr_valid"] == data["cycles_completed"]
        print("smoke ok live incr_proven=true")
    else:
        print("smoke ok live refuse (Aura not fully healthy):", data.get("reason"))

# Validate kernel episodes
root = Path(os.environ["ROOT"])
for rel, expect_profile, expect_harness in [
    ("trajectories/smoke.jsonl", False, None),
    ("trajectories/smoke_aura_repo.jsonl", True, None),
    ("trajectories/smoke_harness_canary.jsonl", False, "discard"),
    ("trajectories/smoke_harness_reject.jsonl", False, "heal"),
    ("trajectories/smoke_l2.jsonl", False, None),
]:
    path = root / rel
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    assert len(lines) == 1, (rel, lines)
    ep = json.loads(lines[0])
    validate_episode(ep)
    assert ep["runtime"]["mode"] in ("simulated", "aura")
    assert ep["runtime"].get("kernel") == "aura", ep["runtime"]
    assert ep["runtime"].get("incr_proven", False) is False
    assert ep["runtime"].get("fiber_live", False) is False
    if expect_profile:
        assert ep["runtime"]["profile"]["id"] == "aura-repo"
        assert len(ep["worldlines"]) >= 2
    if expect_harness is not None:
        assert ep["harness"]["outcome"] == expect_harness
    print("smoke ok:", path)

export_path = root / "trajectories/smoke_export.json"
exported = json.loads(export_path.read_text())
assert isinstance(exported, list) and len(exported) >= 4
for ep in exported:
    validate_episode(ep)
    assert ep["privacy"].get("redacted") is True
print("smoke ok export:", export_path, "n=", len(exported))
print("smoke ok all (host + Aura kernel)")
PYLIVE

echo "smoke ok all (host unit + Aura kernel episodes)"
