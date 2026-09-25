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
  'money.aura'
  'date.aura'
  'plan.aura'
  'account.aura'
  'journal.aura'
  'proration.aura'
  'subscription.aura'
  'ledger.aura'
  'posting.aura'
  'scenario.aura'
  'report.aura'
  'print.aura'
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
printf '%s\n' "$out" | grep -qE 'SUB_COUNT[[:space:]]*=[[:space:]]*2' || ok=0
printf '%s\n' "$out" | grep -qE 'PLAN_A_MONTHLY_CENTS[[:space:]]*=[[:space:]]*4900' || ok=0
printf '%s\n' "$out" | grep -qE 'PLAN_B_MONTHLY_CENTS[[:space:]]*=[[:space:]]*9900' || ok=0
printf '%s\n' "$out" | grep -qE 'PERIOD_DAYS[[:space:]]*=[[:space:]]*30' || ok=0
printf '%s\n' "$out" | grep -qE 'JOURNAL_LINES[[:space:]]*=[[:space:]]*125' || ok=0
printf '%s\n' "$out" | grep -qE 'TOTAL_DEBITS_CENTS[[:space:]]*=[[:space:]]*28105' || ok=0
printf '%s\n' "$out" | grep -qE 'TOTAL_CREDITS_CENTS[[:space:]]*=[[:space:]]*24619' || ok=0
printf '%s\n' "$out" | grep -qE 'ACCT_AR_BALANCE_CENTS[[:space:]]*=[[:space:]]*21619' || ok=0
printf '%s\n' "$out" | grep -qE 'ACCT_REV_PLAN_A_BALANCE_CENTS[[:space:]]*=[[:space:]]*\-3649' || ok=0
printf '%s\n' "$out" | grep -qE 'ACCT_REV_PLAN_B_BALANCE_CENTS[[:space:]]*=[[:space:]]*\-15984' || ok=0
printf '%s\n' "$out" | grep -qE 'ACCT_CREDIT_BALANCE_CENTS[[:space:]]*=[[:space:]]*1500' || ok=0
printf '%s\n' "$out" | grep -qE 'LEDGER_BALANCED[[:space:]]*=[[:space:]]*false' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
