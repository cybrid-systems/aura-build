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
  'event.aura'
  'tape.aura'
  'book.aura'
  'book_ops.aura'
  'idmap.aura'
  'queue.aura'
  'match.aura'
  'cancel.aura'
  'trade.aura'
  'tape_out.aura'
  'stats.aura'
  'book_view.aura'
  'counters.aura'
  'engine.aura'
  'scenario.aura'
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
printf '%s\n' "$out" | grep -qE 'TICKER[[:space:]]*=[[:space:]]*AURA' || ok=0
printf '%s\n' "$out" | grep -qE 'EVENTS[[:space:]]*=[[:space:]]*8' || ok=0
printf '%s\n' "$out" | grep -qE 'ORDERS_NEW[[:space:]]*=[[:space:]]*7' || ok=0
printf '%s\n' "$out" | grep -qE 'ORDERS_CANCELLED[[:space:]]*=[[:space:]]*1' || ok=0
printf '%s\n' "$out" | grep -qE 'ORDERS_OPEN_RESTING[[:space:]]*=[[:space:]]*1' || ok=0
printf '%s\n' "$out" | grep -qE 'ORDERS_FULLY_FILLED[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'TRADES[[:space:]]*=[[:space:]]*4' || ok=0
printf '%s\n' "$out" | grep -qE 'TRADE_VOLUME[[:space:]]*=[[:space:]]*6' || ok=0
printf '%s\n' "$out" | grep -qE 'TRADE_NOTIONAL[[:space:]]*=[[:space:]]*298' || ok=0
printf '%s\n' "$out" | grep -qE 'VWAP[[:space:]]*=[[:space:]]*49\.666666666666664' || ok=0
printf '%s\n' "$out" | grep -qE 'BEST_BID_PRICE[[:space:]]*=[[:space:]]*' || ok=0
printf '%s\n' "$out" | grep -qE 'BEST_BID_QTY[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'BEST_ASK_PRICE[[:space:]]*=[[:space:]]*48' || ok=0
printf '%s\n' "$out" | grep -qE 'BEST_ASK_QTY[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'TOP_LEVEL[[:space:]]*=[[:space:]]*\-\-\-\-\ \ \|\ \ 48x0' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
