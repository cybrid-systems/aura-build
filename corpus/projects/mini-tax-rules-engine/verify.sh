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
  'rates.aura'
  'jurisdiction.aura'
  'override.aura'
  'exemption.aura'
  'rules.aura'
  'resolver.aura'
  'line.aura'
  'invoice.aura'
  'compute.aura'
  'format.aura'
  'sample.aura'
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
printf '%s\n' "$out" | grep -qE 'COUNTRY_CODE[[:space:]]*=[[:space:]]*US' || ok=0
printf '%s\n' "$out" | grep -qE 'COUNTRY_RATE[[:space:]]*=[[:space:]]*0\.00' || ok=0
printf '%s\n' "$out" | grep -qE 'STATE_CODE[[:space:]]*=[[:space:]]*CA' || ok=0
printf '%s\n' "$out" | grep -qE 'STATE_RATE[[:space:]]*=[[:space:]]*0\.05' || ok=0
printf '%s\n' "$out" | grep -qE 'CITY_CODE[[:space:]]*=[[:space:]]*SF' || ok=0
printf '%s\n' "$out" | grep -qE 'CITY_RATE[[:space:]]*=[[:space:]]*0\.07' || ok=0
printf '%s\n' "$out" | grep -qE 'EFFECTIVE_RATE[[:space:]]*=[[:space:]]*0\.12' || ok=0
printf '%s\n' "$out" | grep -qE 'EXEMPTIONS_APPLIED[[:space:]]*=[[:space:]]*3' || ok=0
printf '%s\n' "$out" | grep -qE 'LINE_COUNT[[:space:]]*=[[:space:]]*4' || ok=0
printf '%s\n' "$out" | grep -qE 'SUBTOTAL[[:space:]]*=[[:space:]]*840\.00' || ok=0
printf '%s\n' "$out" | grep -qE 'TAX_TOTAL[[:space:]]*=[[:space:]]*85\.00' || ok=0
printf '%s\n' "$out" | grep -qE 'GRAND_TOTAL[[:space:]]*=[[:space:]]*925\.00' || ok=0
printf '%s\n' "$out" | grep -qE 'LINE_0_TAX[[:space:]]*=[[:space:]]*18\.75' || ok=0
printf '%s\n' "$out" | grep -qE 'LINE_1_TAX[[:space:]]*=[[:space:]]*5\.00' || ok=0
printf '%s\n' "$out" | grep -qE 'LINE_2_TAX[[:space:]]*=[[:space:]]*11\.25' || ok=0
printf '%s\n' "$out" | grep -qE 'LINE_3_TAX[[:space:]]*=[[:space:]]*50\.00' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
