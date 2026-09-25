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
  'data.aura'
  'invoice.aura'
  'aging.aura'
  'fee.aura'
  'promise.aura'
  'notice.aura'
  'writeoff.aura'
  'audit.aura'
  'state.aura'
  'runner.aura'
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
printf '%s\n' "$out" | grep -qE 'PORTFOLIO_INVOICES[[:space:]]*=[[:space:]]*11' || ok=0
printf '%s\n' "$out" | grep -qE 'PORTFOLIO_OPEN_BALANCE[[:space:]]*=[[:space:]]*901000' || ok=0
printf '%s\n' "$out" | grep -qE 'BUCKET_CURRENT[[:space:]]*=[[:space:]]*2' || ok=0
printf '%s\n' "$out" | grep -qE 'BUCKET_1_30[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'BUCKET_31_60[[:space:]]*=[[:space:]]*2' || ok=0
printf '%s\n' "$out" | grep -qE 'BUCKET_61_90[[:space:]]*=[[:space:]]*2' || ok=0
printf '%s\n' "$out" | grep -qE 'BUCKET_90_PLUS[[:space:]]*=[[:space:]]*2' || ok=0
printf '%s\n' "$out" | grep -qE 'REMINDERS_SENT[[:space:]]*=[[:space:]]*1' || ok=0
printf '%s\n' "$out" | grep -qE 'FIRM_NOTICES_SENT[[:space:]]*=[[:space:]]*4' || ok=0
printf '%s\n' "$out" | grep -qE 'FINAL_NOTICES_SENT[[:space:]]*=[[:space:]]*4' || ok=0
printf '%s\n' "$out" | grep -qE 'PROMISES_HONORED[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'PROMISES_BROKEN[[:space:]]*=[[:space:]]*2' || ok=0
printf '%s\n' "$out" | grep -qE 'LATE_FEES_COLLECTED[[:space:]]*=[[:space:]]*27140' || ok=0
printf '%s\n' "$out" | grep -qE 'WRITEOFFS[[:space:]]*=[[:space:]]*328000' || ok=0
printf '%s\n' "$out" | grep -qE 'AUDIT_ENTRIES[[:space:]]*=[[:space:]]*26' || ok=0
printf '%s\n' "$out" | grep -qE 'RUN_OK[[:space:]]*=[[:space:]]*\#t' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
