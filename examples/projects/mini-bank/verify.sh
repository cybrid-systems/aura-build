#!/usr/bin/env bash
# Exit 0 iff candidate dir (or files) define credit/debit/balance and print A/B/A2/B2/OK.
set -euo pipefail
ARG="${1:-}"
if [[ -z "$ARG" ]]; then
  echo "usage: verify.sh <candidate_dir|main.aura>" >&2
  exit 2
fi
if [[ -z "${AURA_BIN:-}" || ! -x "${AURA_BIN}" ]]; then
  echo "error: set AURA_BIN to a working Aura binary" >&2
  exit 2
fi

# Resolve lib.aura + main.aura
if [[ -d "$ARG" ]]; then
  LIB="$ARG/lib.aura"
  MAIN="$ARG/main.aura"
elif [[ -f "$ARG" ]]; then
  DIR="$(cd "$(dirname "$ARG")" && pwd)"
  LIB="$DIR/lib.aura"
  MAIN="$ARG"
  # If only a single concatenated program was passed, still require sibling lib
  if [[ ! -f "$LIB" && "$(basename "$ARG")" == "program.aura" ]]; then
    echo "verify fail: multi-file project needs lib.aura + main.aura" >&2
    exit 1
  fi
else
  echo "verify fail: not a file or directory: $ARG" >&2
  exit 2
fi

if [[ ! -f "$LIB" || ! -f "$MAIN" ]]; then
  echo "verify fail: need both lib.aura and main.aura (got lib=$LIB main=$MAIN)" >&2
  exit 1
fi

# Structural: helpers in lib (or joined sources)
src="$(cat "$LIB" "$MAIN")"
for fn in credit debit balance; do
  if ! printf '%s\n' "$src" | grep -qE "\(define[[:space:]]+\(${fn}\\b"; then
    echo "verify fail: missing (define (${fn} …)" >&2
    exit 1
  fi
done
# Reject main-only hardcode: lib must contain at least one of the defines
libsrc="$(cat "$LIB")"
if ! printf '%s\n' "$libsrc" | grep -qE '\(define[[:space:]]+\((credit|debit|balance)\b'; then
  echo "verify fail: lib.aura must define credit/debit/balance (not main-only hardcode)" >&2
  exit 1
fi

# GCC16 sidecar
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

# Honest Aura multi-file CLI (not concat pretend-modules)
out="$("$AURA_BIN" "$LIB" "$MAIN" 2>&1)" || true
printf '%s\n' "$out"
ok=1
printf '%s\n' "$out" | grep -qE 'A[[:space:]]*=[[:space:]]*100' || ok=0
printf '%s\n' "$out" | grep -qE 'B[[:space:]]*=[[:space:]]*50' || ok=0
printf '%s\n' "$out" | grep -qE 'A2[[:space:]]*=[[:space:]]*70' || ok=0
printf '%s\n' "$out" | grep -qE 'B2[[:space:]]*=[[:space:]]*80' || ok=0
printf '%s\n' "$out" | grep -qE 'OK[[:space:]]*=[[:space:]]*1' || ok=0
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b'; then
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok A=100 B=50 A2=70 B2=80 OK=1"
  exit 0
fi
echo "verify fail (expected A=100 / B=50 / A2=70 / B2=80 / OK=1 + lib credit/debit/balance)" >&2
exit 1
