#!/usr/bin/env bash
# Smoke: pytest (Python fallback SSOT) + CLI episodes.
# When AURA_BIN healthy, CLI prefer Aura kernel (runtime.kernel=aura).
# Fail-closed prove-incr still uses missing-bin Python path.
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
AURA_BUILD_FORCE_PYTHON=1 python -m pytest -q

# Isolated harness root so dogfood `.aura-build/prove-incr-latest.json`
# (possibly incr_proven=true) does not attach into simulated smoke episodes.
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

# M5: L2 offline metadata + TUI/ACP stubs
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
# When Aura healthy, ACP should report kernel=aura (FORCE_PYTHON path checked in pytest)
if [[ -n "${AURA_BIN:-}" && -x "${AURA_BIN}" ]]; then
  echo "$ACP_STATUS" | grep -q 'kernel=aura'
fi
aura-build tui --harness-root "$HROOT" | grep -q 'aura-build tui'
aura-build acp hooks | grep -q start_session
aura-build acp worldlines --traj "$OUT2" | grep -q candidate
# discard one loser in retained workspace (wl-1 exists from 3-worldline fan-out)
aura-build acp discard --workspace "$WS" --ref wl-1 --reason smoke_discard | tee /tmp/acp_discard.out | grep -q 'fiber_live=false'
aura-build acp promote --id specialist.acp.smoke.v0 --notes smoke --harness-root "$HROOT" | grep -q 'kernel=aura\|stub='


# Post-M5: prove-incr fail-closed + doctor (Aura may be missing/GLIBCXX — still exit 0)
PROVE_ROOT="${ROOT}/trajectories/_smoke_prove"
rm -rf "$PROVE_ROOT"
mkdir -p "$PROVE_ROOT"
# Force missing bin so CI is deterministic fail-closed (do not depend on host Aura)
env -u AURA_BIN aura-build prove-incr --cycles 2 --worldlines 1 \
  --aura-bin /nonexistent/aura-missing \
  --no-fiber-probe \
  --harness-root "$PROVE_ROOT" \
  --out "$PROVE_ROOT/prove-incr-latest.json" | tee "$PROVE_ROOT/prove.out"
grep -q 'incr_proven=False' "$PROVE_ROOT/prove.out"
grep -q 'aura_binary_missing\|aura_glibcxx_mismatch\|aura_unhealthy\|aura_probe' "$PROVE_ROOT/prove.out" \
  || grep -q 'incr_proven=False' "$PROVE_ROOT/prove.out"
aura-build doctor --skip-probe --harness-root "$PROVE_ROOT" | grep -q 'incr_proven=False'
python - <<PYPROVE
import json
from pathlib import Path
p = Path(r"$PROVE_ROOT/prove-incr-latest.json")
data = json.loads(p.read_text())
assert data["incr_proven"] is False
assert data["measured"] is False
assert data.get("fiber_live") is False
print("smoke ok prove-incr fail-closed:", p)
PYPROVE

# Auto-attach prove honesty into traj (default ON); env alone cannot elevate
OUT_ATTACH="${ROOT}/trajectories/smoke_attach.jsonl"
rm -f "$OUT_ATTACH"
env AURA_BUILD_INCR_VALID=1 AURA_BUILD_FIBER_SESSION_OK=1 \
  aura-build run --prompt "smoke attach prove" --seed 7 --mode simulated \
  --worldlines 2 --harness-root "$PROVE_ROOT" --out "$OUT_ATTACH"
python - <<PYATTACH
import json
from pathlib import Path
from aura_build.schema import validate_episode
p = Path(r"$OUT_ATTACH")
ep = json.loads([ln for ln in p.read_text().splitlines() if ln.strip()][0])
validate_episode(ep)
rt = ep["runtime"]
assert rt["incr_proven"] is False
assert rt["measured"] is False
assert rt["fiber_live"] is False
pi = rt["prove_incr"]
for k in ("incr_proven", "measured", "fiber_live", "session_model", "reason"):
    assert k in pi, k
assert "env_ignored_unproven" in pi["env_notes"]
assert "env_fiber_ignored_unproven" in pi["env_notes"]
assert pi["attached"] is True
print("smoke ok attach-prove (env ignored):", p)
PYATTACH

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
# Default --attach-prove: fields present; still false
ep0 = json.loads([ln for ln in Path(r"$OUT").read_text().splitlines() if ln.strip()][0])
assert "prove_incr" in ep0["runtime"]
assert ep0["runtime"]["prove_incr"]["attached"] is True
assert ep0["runtime"]["incr_proven"] is False
print("smoke ok default attach fields on", r"$OUT")
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

# M5 L2 episode
p5 = Path(r"$OUT5")
ep5 = json.loads([ln for ln in p5.read_text().splitlines() if ln.strip()][0])
validate_episode(ep5)
assert ep5["harness"]["l2_ref"]["stub"] is True
assert ep5["harness"]["l2_ref"]["artifact_present"] is True
assert ep5["runtime"].get("incr_proven", False) is False
print("smoke ok l2:", p5)

print("smoke ok all (M0–M5 + Post-M5 prove-incr + attach)")
PY

# Optional: when Aura binary is healthy, demo incr_proven=true via real probe.
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
if [[ -n "${LIVE_AURA}" && -x "$LIVE_AURA" ]]; then
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
  export LIVE_ROOT
  python - <<'PYLIVE'
import json
import os
from pathlib import Path
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
PYLIVE
else
  echo "smoke skip live incr_proven demo (no AURA_BIN)"
fi

echo "smoke ok all (M0–M5 + Post-M5 prove-incr + attach + optional live)"
