#!/usr/bin/env bash
# Exit 0 iff candidate Aura program prints GREET=aura (exact token present).
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
if printf '%s\n' "$out" | grep -qE 'GREET[[:space:]]*=[[:space:]]*aura' \
  && ! printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b'; then
  echo "verify ok GREET=aura"
  exit 0
fi
echo "verify fail (expected GREET=aura)" >&2
exit 1
