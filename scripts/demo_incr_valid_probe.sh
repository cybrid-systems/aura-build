#!/usr/bin/env bash
# Demo: Aura incr-valid probe contract → prove-incr can set incr_proven=true.
# Requires a healthy Aura binary (+ GCC16 libstdc++ sidecar on host boxes).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

AURA_BIN="${AURA_BIN:-}"
if [[ -z "$AURA_BIN" ]]; then
  for c in \
    /workspace/aura-redis/.deps/aura/build/aura \
    /workspace/aura-grok/build/aura \
    /workspace/aura-redis-ci/.deps/aura/build/aura
  do
    if [[ -x "$c" ]]; then AURA_BIN="$c"; break; fi
  done
fi
if [[ -z "${AURA_BIN}" || ! -x "$AURA_BIN" ]]; then
  echo "demo: no aura binary — cannot show incr_proven=true" >&2
  echo "set AURA_BIN or install sidecar (scripts/fetch-gcc16-libstdcxx.sh)" >&2
  exit 1
fi

export AURA_BIN
export AURA_SANDBOX="${AURA_SANDBOX:-off}"
export AURA_PIPELINE_STRICT="${AURA_PIPELINE_STRICT:-0}"

echo "== 1) Aura program probe (expect AURA_BUILD_INCR_VALID 1) =="
"$AURA_BIN" "$ROOT/scripts/aura_m1_mutate_eval.aura" | tee /tmp/aura-build-incr-demo.out
grep -E 'AURA_BUILD_INCR_VALID 1|AURA_INCR_VALID=1' /tmp/aura-build-incr-demo.out

echo
echo "== 2) prove-incr (expect incr_proven=true when signal present) =="
PYTHON="${PYTHON:-python3}"
VENV="${ROOT}/.venv"
if [[ ! -d "$VENV" ]]; then
  "$PYTHON" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install -e ".[dev]" -q

OUT="${ROOT}/trajectories/_demo_incr"
mkdir -p "$OUT"
aura-build prove-incr --cycles 2 --worldlines 1 \
  --aura-bin "$AURA_BIN" \
  --no-fiber-probe \
  --harness-root "$OUT" \
  --out "$OUT/prove-incr-latest.json" --json | tee "$OUT/prove.out"

python - <<PY
import json
from pathlib import Path
data = json.loads(Path(r"$OUT/prove-incr-latest.json").read_text())
print("incr_proven=", data["incr_proven"])
print("measured=", data["measured"])
print("reason=", data["reason"])
print("cycles_incr_valid=", data["cycles_incr_valid"], "/", data["cycles_completed"])
assert data["measured"] is True
assert data["aura_healthy"] is True
if not data["incr_proven"]:
    raise SystemExit(
        "demo refused: expected incr_proven=true after Aura probe; "
        f"reason={data['reason']!r}"
    )
print("demo ok: incr_proven=true via Aura compile:epoch / jit-stats delta")
PY
