#!/usr/bin/env bash
# Measured oracle. Expect lines come from ref/run_scenarios.py via tests.json.
set -euo pipefail
ARG="${1:-}"
if [[ -z "$ARG" ]]; then
  echo "usage: verify.sh <candidate_dir>" >&2
  exit 2
fi
if [[ -z "${AURA_BIN:-}" || ! -x "${AURA_BIN}" ]]; then
  echo "error: set AURA_BIN to a working Aura binary" >&2
  exit 2
fi
if [[ -d "$ARG" ]]; then
  DIR="$ARG"
else
  DIR="$(cd "$(dirname "$ARG")" && pwd)"
fi
FILES=(
  'util.aura'
  'lot.aura'
  'block.aura'
  'ledger.aura'
  'policy.aura'
  'pnl.aura'
  'reassign.aura'
  'report.aura'
  'main.aura'
)
args=()
for f in "${FILES[@]}"; do
  if [[ ! -f "$DIR/$f" ]]; then
    echo "verify fail: missing $f" >&2
    exit 1
  fi
  args+=("$DIR/$f")
done
export AURA_SANDBOX="${AURA_SANDBOX:-off}"
out="$("$AURA_BIN" "${args[@]}" 2>&1)" || true
printf '%s\n' "$out"
ok=1
printf '%s\n' "$out" | grep -qE 'INSTRUMENT[[:space:]]*=[[:space:]]*ACME' || ok=0
printf '%s\n' "$out" | grep -qE 'CLIENTS[[:space:]]*=[[:space:]]*4' || ok=0
printf '%s\n' "$out" | grep -qE 'LOTS_OPEN[[:space:]]*=[[:space:]]*5' || ok=0
printf '%s\n' "$out" | grep -qE 'BLOCKS[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'ALLOC_FIFO_FILLS[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'ALLOC_LIFO_FILLS[[:space:]]*=[[:space:]]*4' || ok=0
printf '%s\n' "$out" | grep -qE 'ALLOC_HIFO_FILLS[[:space:]]*=[[:space:]]*4' || ok=0
printf '%s\n' "$out" | grep -qE 'PNL_FIFO[[:space:]]*=[[:space:]]*1520\.0' || ok=0
printf '%s\n' "$out" | grep -qE 'PNL_LIFO[[:space:]]*=[[:space:]]*970\.0' || ok=0
printf '%s\n' "$out" | grep -qE 'PNL_HIFO[[:space:]]*=[[:space:]]*740\.0' || ok=0
printf '%s\n' "$out" | grep -qE 'WASH_FLAGS[[:space:]]*=[[:space:]]*11' || ok=0
printf '%s\n' "$out" | grep -qE 'REASSIGNED[[:space:]]*=[[:space:]]*2' || ok=0
printf '%s\n' "$out" | grep -qE 'LEDGER_TICKS[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'RUN_ID[[:space:]]*=[[:space:]]*mini\-trade\-allocation\-fifo\-001' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
