#!/usr/bin/env bash
# Exit 0 iff candidate defines (kv-set)/(kv-get) and prints GET_a=1 / GET_b=2 / MISS=nil / GET_c=3.
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
if ! printf '%s\n' "$src" | grep -qE '\(define[[:space:]]+\(kv-set[[:space:]]'; then
  echo "verify fail: missing (define (kv-set …)" >&2
  exit 1
fi
if ! printf '%s\n' "$src" | grep -qE '\(define[[:space:]]+\(kv-get[[:space:]]'; then
  echo "verify fail: missing (define (kv-get …)" >&2
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
printf '%s\n' "$out" | grep -qE 'GET_a[[:space:]]*=[[:space:]]*1' || ok=0
printf '%s\n' "$out" | grep -qE 'GET_b[[:space:]]*=[[:space:]]*2' || ok=0
printf '%s\n' "$out" | grep -qE 'MISS[[:space:]]*=[[:space:]]*nil' || ok=0
printf '%s\n' "$out" | grep -qE 'GET_c[[:space:]]*=[[:space:]]*3' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok GET_a=1 GET_b=2 MISS=nil GET_c=3"
  exit 0
fi
echo "verify fail (expected GET_a=1 / GET_b=2 / MISS=nil / GET_c=3 + define kv-set/kv-get)" >&2
exit 1
