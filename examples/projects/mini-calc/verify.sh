#!/usr/bin/env bash
# Exit 0 iff candidate defines (add)/(mul) and prints ADD=7 / MUL=12 / MIX=17.
set -euo pipefail
CAND="${1:-}"
if [[ -z "$CAND" || ! -f "$CAND" ]]; then
  echo "usage: verify.sh <candidate.aura>" >&2
  exit 2
fi
if [[ -z "${AURA_BIN:-}" || ! -x "${AURA_BIN}" ]]; then
  echo "error: set AURA_BIN to a working Aura binary" >&2
  exit 2
fi
# Structural: named helpers required (reject bare display-literal hardcode)
src="$(cat "$CAND")"
if ! printf '%s\n' "$src" | grep -qE '\(define[[:space:]]+\(add[[:space:]]'; then
  echo "verify fail: missing (define (add …)" >&2
  exit 1
fi
if ! printf '%s\n' "$src" | grep -qE '\(define[[:space:]]+\(mul[[:space:]]'; then
  echo "verify fail: missing (define (mul …)" >&2
  exit 1
fi
# GCC16 sidecar (same layout as aura-build scripts)
if [[ -z "${AURA_LIBSTDCXX_DIR:-}" ]]; then
  for d in \
    /workspace/aura-redis/.deps/gcc16-libstdcxx \
    /workspace/aura-grok/.deps/gcc16-libstdcxx
  do
    if [[ -f "$d/libstdc++.so.6" ]]; then
      export AURA_LIBSTDCXX_DIR="$d"
      export LD_LIBRARY_PATH="${d}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
      break
    fi
  done
fi
export AURA_SANDBOX="${AURA_SANDBOX:-off}"
out="$("$AURA_BIN" "$CAND" 2>&1)" || true
printf '%s\n' "$out"
ok=1
printf '%s\n' "$out" | grep -qE 'ADD[[:space:]]*=[[:space:]]*7' || ok=0
printf '%s\n' "$out" | grep -qE 'MUL[[:space:]]*=[[:space:]]*12' || ok=0
printf '%s\n' "$out" | grep -qE 'MIX[[:space:]]*=[[:space:]]*17' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok ADD=7 MUL=12 MIX=17"
  exit 0
fi
echo "verify fail (expected ADD=7 / MUL=12 / MIX=17 + define add/mul)" >&2
exit 1
