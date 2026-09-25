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
  'state.aura'
  'time.aura'
  'hold.aura'
  'reservation.aura'
  'restock.aura'
  'oversell.aura'
  'invariants.aura'
  'concurrency.aura'
  'report.aura'
  'hash.aura'
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
printf '%s\n' "$out" | grep -qE 'RESERVATIONS_TOTAL[[:space:]]*=[[:space:]]*9' || ok=0
printf '%s\n' "$out" | grep -qE 'RESERVATIONS_HELD[[:space:]]*=[[:space:]]*6' || ok=0
printf '%s\n' "$out" | grep -qE 'RESERVATIONS_EXPIRED[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'RESERVATIONS_RELEASED[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'RESTOCK_EVENTS[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'RESTOCK_UNITS_ADDED[[:space:]]*=[[:space:]]*15' || ok=0
printf '%s\n' "$out" | grep -qE 'OVERSELL_BLOCKED[[:space:]]*=[[:space:]]*6' || ok=0
printf '%s\n' "$out" | grep -qE 'STOCK_SKU_A_FINAL[[:space:]]*=[[:space:]]*47' || ok=0
printf '%s\n' "$out" | grep -qE 'STOCK_SKU_B_FINAL[[:space:]]*=[[:space:]]*13' || ok=0
printf '%s\n' "$out" | grep -qE 'STOCK_SKU_C_FINAL[[:space:]]*=[[:space:]]*7' || ok=0
printf '%s\n' "$out" | grep -qE 'ACTIVE_HOLDS_FINAL[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'INVENTORY_INVARIANT_OK[[:space:]]*=[[:space:]]*true' || ok=0
printf '%s\n' "$out" | grep -qE 'LEDGER_ENTRIES[[:space:]]*=[[:space:]]*18' || ok=0
printf '%s\n' "$out" | grep -qE 'HASH_RESERVATIONS_TOTAL[[:space:]]*=[[:space:]]*569814308' || ok=0
printf '%s\n' "$out" | grep -qE 'HASH_OVERSELL_BLOCKED[[:space:]]*=[[:space:]]*2246263005' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
