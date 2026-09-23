#!/usr/bin/env bash
# Optional M1 Aura smoke: skip (exit 0) when aura binary unavailable.
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

AURA_BIN_RESOLVED="${AURA_BIN:-}"
if [[ -z "$AURA_BIN_RESOLVED" ]]; then
  for c in \
    /workspace/aura-grok/build/aura \
    /workspace/aura-redis/.deps/aura/build/aura \
    "$(command -v aura 2>/dev/null || true)"; do
    if [[ -n "$c" && -x "$c" ]]; then
      AURA_BIN_RESOLVED="$c"
      break
    fi
  done
fi

if [[ -z "${AURA_BIN_RESOLVED}" ]]; then
  echo "aura_smoke: SKIP — no aura binary (set AURA_BIN to enable)"
  exit 0
fi

if ! python - <<PY
from aura_build.runtime import probe_aura
ok, err = probe_aura(r"${AURA_BIN_RESOLVED}")
print("probe:", ok, err or "")
raise SystemExit(0 if ok else 3)
PY
then
  echo "aura_smoke: SKIP — aura present but probe failed (glibc/deps?): ${AURA_BIN_RESOLVED}"
  exit 0
fi

OUT="${ROOT}/trajectories/aura_smoke.jsonl"
rm -f "$OUT"
aura-build run --prompt "aura m1 smoke" --seed 1 --mode aura \
  --aura-bin "$AURA_BIN_RESOLVED" \
  --aura-ref "${AURA_REF:-/workspace/aura-grok}" \
  --worldlines 2 --out "$OUT"

python - <<PY
import json
from pathlib import Path
from aura_build.schema import validate_episode
p = Path(r"$OUT")
ep = json.loads(p.read_text().splitlines()[0])
validate_episode(ep)
assert ep["runtime"]["mode"] == "aura", ep["runtime"]
print("aura_smoke ok mode=aura selected=", ep["selected_id"])
PY
