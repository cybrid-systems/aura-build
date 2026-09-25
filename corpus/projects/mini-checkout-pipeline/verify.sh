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
  'pipeline/contract.aura'
  'pipeline/state.aura'
  'pipeline/registry.aura'
  'cart/validate.aura'
  'pricing/compute.aura'
  'pricing/tax.aura'
  'payment/authorize.aura'
  'payment/capture.aura'
  'payment/void.aura'
  'fraud/score.aura'
  'fraud/decision.aura'
  'orders/commit.aura'
  'orders/cancel.aura'
  'saga/compensate.aura'
  'saga/orchestrator.aura'
  'samples/cart.aura'
  'samples/region.aura'
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
printf '%s\n' "$out" | grep -qE 'PIPELINE_VERSION[[:space:]]*=[[:space:]]*1\.0\.0' || ok=0
printf '%s\n' "$out" | grep -qE 'STAGES[[:space:]]*=[[:space:]]*validate,price,authorize,score,commit' || ok=0
printf '%s\n' "$out" | grep -qE 'OUTCOME[[:space:]]*=[[:space:]]*COMMITTED' || ok=0
printf '%s\n' "$out" | grep -qE 'ORDER_ID[[:space:]]*=[[:space:]]*None' || ok=0
printf '%s\n' "$out" | grep -qE 'ITEMS_BILLED[[:space:]]*=[[:space:]]*4' || ok=0
printf '%s\n' "$out" | grep -qE 'SUBTOTAL_CENTS[[:space:]]*=[[:space:]]*3698' || ok=0
printf '%s\n' "$out" | grep -qE 'TAX_CENTS[[:space:]]*=[[:space:]]*324' || ok=0
printf '%s\n' "$out" | grep -qE 'TOTAL_CENTS[[:space:]]*=[[:space:]]*4022' || ok=0
printf '%s\n' "$out" | grep -qE 'PAYMENT_AUTH[[:space:]]*=[[:space:]]*AUTH\-5E298B' || ok=0
printf '%s\n' "$out" | grep -qE 'FRAUD_SCORE[[:space:]]*=[[:space:]]*43' || ok=0
printf '%s\n' "$out" | grep -qE 'FRAUD_DECISION[[:space:]]*=[[:space:]]*ACCEPT' || ok=0
printf '%s\n' "$out" | grep -qE 'ROLLBACK_STAGES[[:space:]]*=[[:space:]]*NONE' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
