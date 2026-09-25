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
  'ids.aura'
  'handlers.aura'
  'services.aura'
  'compensator.aura'
  'orchestrator.aura'
  'extra1.aura'
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
printf '%s\n' "$out" | grep -qE 'SAGA_ID[[:space:]]*=[[:space:]]*SAGA\-0001' || ok=0
printf '%s\n' "$out" | grep -qE 'SAGA_STATUS[[:space:]]*=[[:space:]]*COMPLETED' || ok=0
printf '%s\n' "$out" | grep -qE 'STEP_AUDIT[[:space:]]*=[[:space:]]*auth:DONE;inventory\-hold:DONE;payment\-auth:DONE;payment\-capture:DONE;fulfillment\-kickoff:DONE' || ok=0
printf '%s\n' "$out" | grep -qE 'DUAL_WRITE_RISK[[:space:]]*=[[:space:]]*false' || ok=0
printf '%s\n' "$out" | grep -qE 'ORDER_ID[[:space:]]*=[[:space:]]*ORD\-0002' || ok=0
printf '%s\n' "$out" | grep -qE 'ORDER_STATE[[:space:]]*=[[:space:]]*FULFILLED' || ok=0
printf '%s\n' "$out" | grep -qE 'PAYMENT_ID[[:space:]]*=[[:space:]]*PAY\-0003' || ok=0
printf '%s\n' "$out" | grep -qE 'PAYMENT_STATE[[:space:]]*=[[:space:]]*CAPTURED' || ok=0
printf '%s\n' "$out" | grep -qE 'INVENTORY_HOLD_ID[[:space:]]*=[[:space:]]*HOLD\-0004' || ok=0
printf '%s\n' "$out" | grep -qE 'INVENTORY_HOLD_STATE[[:space:]]*=[[:space:]]*CONSUMED' || ok=0
printf '%s\n' "$out" | grep -qE 'FULFILLMENT_JOB_ID[[:space:]]*=[[:space:]]*FUL\-0005' || ok=0
printf '%s\n' "$out" | grep -qE 'FULFILLMENT_STATE[[:space:]]*=[[:space:]]*QUEUED' || ok=0
printf '%s\n' "$out" | grep -qE 'TOTAL_STEPS[[:space:]]*=[[:space:]]*5' || ok=0
printf '%s\n' "$out" | grep -qE 'COMPLETED_STEPS[[:space:]]*=[[:space:]]*5' || ok=0
printf '%s\n' "$out" | grep -qE 'COMPENSATED_STEPS[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'EXIT_CODE[[:space:]]*=[[:space:]]*0' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
