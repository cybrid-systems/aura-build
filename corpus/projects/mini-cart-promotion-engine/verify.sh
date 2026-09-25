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
  'catalog.aura'
  'cart.aura'
  'promotion.aura'
  'registry.aura'
  'eligibility.aura'
  'stacking.aura'
  'evaluator.aura'
  'ledger.aura'
  'totals.aura'
  'format.aura'
  'rules/aura_rules_pct.aura'
  'rules/aura_rules_fixed.aura'
  'rules/aura_rules_bxgy.aura'
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
printf '%s\n' "$out" | grep -qE 'SUBTOTAL_CENTS[[:space:]]*=[[:space:]]*29500' || ok=0
printf '%s\n' "$out" | grep -qE 'ELIGIBLE_PROMOTIONS[[:space:]]*=[[:space:]]*BXGY1\|FIX500\|PCT10' || ok=0
printf '%s\n' "$out" | grep -qE 'STACKED_PROMOTIONS[[:space:]]*=[[:space:]]*BXGY1\|FIX500\|PCT10' || ok=0
printf '%s\n' "$out" | grep -qE 'EXCLUDED_PROMOTIONS[[:space:]]*=[[:space:]]*THRESH5000' || ok=0
printf '%s\n' "$out" | grep -qE 'DISCOUNT_CENTS[[:space:]]*=[[:space:]]*6400' || ok=0
printf '%s\n' "$out" | grep -qE 'FINAL_TOTAL_CENTS[[:space:]]*=[[:space:]]*23100' || ok=0
printf '%s\n' "$out" | grep -qE 'COUPONS_REDEEMED[[:space:]]*=[[:space:]]*BXGY1,FIX500,PCT10' || ok=0
printf '%s\n' "$out" | grep -qE 'LEDGER_COUNT[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'LEDGER_PCT10_USES[[:space:]]*=[[:space:]]*1' || ok=0
printf '%s\n' "$out" | grep -qE 'LEDGER_FIX500_USES[[:space:]]*=[[:space:]]*1' || ok=0
printf '%s\n' "$out" | grep -qE 'LEDGER_BXGY1_USES[[:space:]]*=[[:space:]]*1' || ok=0
printf '%s\n' "$out" | grep -qE 'CATALOG_SIZE[[:space:]]*=[[:space:]]*4' || ok=0
printf '%s\n' "$out" | grep -qE 'CART_LINE_COUNT[[:space:]]*=[[:space:]]*9' || ok=0
printf '%s\n' "$out" | grep -qE 'RULE_COUNT[[:space:]]*=[[:space:]]*4' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
