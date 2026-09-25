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
  'facts_nexus.aura'
  'facts_products.aura'
  'facts_exemptions.aura'
  'facts_jurisdictions.aura'
  'facts_customers.aura'
  'facts_invoice.aura'
  'resolve_jurisdiction.aura'
  'apply_exemption.aura'
  'compute_line_tax.aura'
  'round_money.aura'
  'audit_log.aura'
  'invoice_aggregate.aura'
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
printf '%s\n' "$out" | grep -qE 'INVOICE_ID[[:space:]]*=[[:space:]]*INV\-2026\-0001' || ok=0
printf '%s\n' "$out" | grep -qE 'LINE_COUNT[[:space:]]*=[[:space:]]*8' || ok=0
printf '%s\n' "$out" | grep -qE 'TAXABLE_LINES[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'EXEMPT_LINES[[:space:]]*=[[:space:]]*8' || ok=0
printf '%s\n' "$out" | grep -qE 'ZERO_TAX_LINES[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'SUBTOTAL_CENTS[[:space:]]*=[[:space:]]*42794' || ok=0
printf '%s\n' "$out" | grep -qE 'TAX_TOTAL_CENTS[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'GRAND_TOTAL_CENTS[[:space:]]*=[[:space:]]*42794' || ok=0
printf '%s\n' "$out" | grep -qE 'JURISDICTIONS_RESOLVED[[:space:]]*=[[:space:]]*CA\-LA,NH\-NONE,OR\-NONE,WA\-SEA' || ok=0
printf '%s\n' "$out" | grep -qE 'EXEMPTION_CERTS_APPLIED[[:space:]]*=[[:space:]]*NONPROFIT_501C3,RESALE' || ok=0
printf '%s\n' "$out" | grep -qE 'ORIGIN_BASED_LINES[[:space:]]*=[[:space:]]*2' || ok=0
printf '%s\n' "$out" | grep -qE 'DESTINATION_BASED_LINES[[:space:]]*=[[:space:]]*0' || ok=0
printf '%s\n' "$out" | grep -qE 'AUDIT_HASH[[:space:]]*=[[:space:]]*c5b31468c9baaf9a' || ok=0
printf '%s\n' "$out" | grep -qE 'RESOLUTION_OK[[:space:]]*=[[:space:]]*\#t' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b|parse error|type error'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok"
  exit 0
fi
echo "verify fail" >&2
exit 1
