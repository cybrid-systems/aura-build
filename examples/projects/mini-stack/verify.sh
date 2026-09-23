#!/usr/bin/env bash
# Exit 0 iff candidate defines stack-push/pop/top/size and prints TOP=30 / POP=30 / TOP2=20 / SIZE=2 / EMPTY=0.
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
# Structural: named helpers required (reject bare display-literal hardcode).
# Use \b so zero-arity forms like (define (stack-pop) ...) match (not only "name ").
src="$(cat "$CAND")"
for fn in stack-push stack-pop stack-top stack-size; do
  if ! printf '%s\n' "$src" | grep -qE "\(define[[:space:]]+\(${fn}\\b"; then
    echo "verify fail: missing (define (${fn} …)" >&2
    exit 1
  fi
done
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
printf '%s\n' "$out" | grep -qE 'TOP[[:space:]]*=[[:space:]]*30' || ok=0
printf '%s\n' "$out" | grep -qE 'POP[[:space:]]*=[[:space:]]*30' || ok=0
printf '%s\n' "$out" | grep -qE 'TOP2[[:space:]]*=[[:space:]]*20' || ok=0
printf '%s\n' "$out" | grep -qE 'SIZE[[:space:]]*=[[:space:]]*2' || ok=0
printf '%s\n' "$out" | grep -qE 'EMPTY[[:space:]]*=[[:space:]]*0' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok TOP=30 POP=30 TOP2=20 SIZE=2 EMPTY=0"
  exit 0
fi
echo "verify fail (expected TOP=30 / POP=30 / TOP2=20 / SIZE=2 / EMPTY=0 + define stack-push/pop/top/size)" >&2
exit 1
