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
  'types.aura'
  'registry.aura'
  'mta.aura'
  'bilateral.aura'
  'novation.aura'
  'paythrough.aura'
  'netting.aura'
  'mts.aura'
  'settlement.aura'
  'efficiency.aura'
  'report.aura'
  'compliance.aura'
  'calendar.aura'
  'currency.aura'
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
printf '%s\n' "$out" | grep -qE 'VALUE_DATE[[:space:]]*=[[:space:]]*2025\-03\-17' || ok=0
printf '%s\n' "$out" | grep -qE 'TRADE_COUNT[[:space:]]*=[[:space:]]*8' || ok=0
printf '%s\n' "$out" | grep -qE 'GROSS_OBLIGATIONS[[:space:]]*=[[:space:]]*63500' || ok=0
printf '%s\n' "$out" | grep -qE 'NET_OBLIGATIONS[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'NETTING_EFFICIENCY[[:space:]]*=[[:space:]]*1\.0' || ok=0
printf '%s\n' "$out" | grep -qE 'COUNTERPARTY_COUNT[[:space:]]*=[[:space:]]*1' || ok=0
printf '%s\n' "$out" | grep -qE 'CLEARED_COUNT[[:space:]]*=[[:space:]]*1' || ok=0
printf '%s\n' "$out" | grep -qE 'UNCLEARED_COUNT[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'MTA_FILTERED_COUNT[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'SETTLEMENT_INSTRUCTION_COUNT[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'LARGEST_SINGLE_NET_PAYMENT[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'NOVATION_APPLIED[[:space:]]*=[[:space:]]*8' || ok=0
printf '%s\n' "$out" | grep -qE 'PAY_THROUGH_TIER_DEPTH[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'REPORT_BIC[[:space:]]*=[[:space:]]*REGBIC01' || ok=0
printf '%s\n' "$out" | grep -qE 'COMPLIANCE_CHECK[[:space:]]*=[[:space:]]*PASS' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
