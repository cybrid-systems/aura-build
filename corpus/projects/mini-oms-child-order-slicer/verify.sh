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
  'market-clock.aura'
  'venue-registry.aura'
  'order-types.aura'
  'accounts.aura'
  'slicer-pov.aura'
  'slicer-twap.aura'
  'slicer-vwap.aura'
  'slicer-liqseek.aura'
  'router.aura'
  'fill-sim.aura'
  'risk-monitor.aura'
  'allocator-fifo.aura'
  'allocator-prorata.aura'
  'allocator-filledqty.aura'
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
printf '%s\n' "$out" | grep -qE 'PARENT_ID[[:space:]]*=[[:space:]]*P\-0001' || ok=0
printf '%s\n' "$out" | grep -qE 'PARENT_SIDE[[:space:]]*=[[:space:]]*BUY' || ok=0
printf '%s\n' "$out" | grep -qE 'PARENT_QTY[[:space:]]*=[[:space:]]*10000' || ok=0
printf '%s\n' "$out" | grep -qE 'STRATEGY_CHOSEN[[:space:]]*=[[:space:]]*LIQSEEK' || ok=0
printf '%s\n' "$out" | grep -qE 'NUM_CHILDREN[[:space:]]*=[[:space:]]*5' || ok=0
printf '%s\n' "$out" | grep -qE 'TOTAL_CHILD_QTY[[:space:]]*=[[:space:]]*10000' || ok=0
printf '%s\n' "$out" | grep -qE 'FILLED_CHILD_QTY[[:space:]]*=[[:space:]]*6396' || ok=0
printf '%s\n' "$out" | grep -qE 'COMPLETION_PCT[[:space:]]*=[[:space:]]*63\.96' || ok=0
printf '%s\n' "$out" | grep -qE 'VENUES_USED[[:space:]]*=[[:space:]]*ARCA,BATS,DARK1,IEX,NYSE' || ok=0
printf '%s\n' "$out" | grep -qE 'AVG_FILL_PX[[:space:]]*=[[:space:]]*49\.9' || ok=0
printf '%s\n' "$out" | grep -qE 'NUM_FILLS[[:space:]]*=[[:space:]]*5' || ok=0
printf '%s\n' "$out" | grep -qE 'RISK_BREACHED[[:space:]]*=[[:space:]]*FALSE' || ok=0
printf '%s\n' "$out" | grep -qE 'ALLOC_RULE[[:space:]]*=[[:space:]]*PRO\-RATA' || ok=0
printf '%s\n' "$out" | grep -qE 'ALLOC_ACCOUNTS[[:space:]]*=[[:space:]]*ACC\-A,ACC\-B,ACC\-C' || ok=0
printf '%s\n' "$out" | grep -qE 'ALLOC_TOTAL_FILLED[[:space:]]*=[[:space:]]*6396' || ok=0
printf '%s\n' "$out" | grep -qE 'ALLOC_CHECKSUM[[:space:]]*=[[:space:]]*OK' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
