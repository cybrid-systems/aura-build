#!/usr/bin/env bash
# Exit 0 iff candidate defines cache-init/set/get/tick and prints exact cache lines.
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

FILES=(store.aura ops.aura main.aura)
if [[ -d "$ARG" ]]; then
  DIR="$ARG"
elif [[ -f "$ARG" ]]; then
  DIR="$(cd "$(dirname "$ARG")" && pwd)"
else
  echo "verify fail: not a file or directory: $ARG" >&2
  exit 2
fi

missing=0
for f in "${FILES[@]}"; do
  if [[ ! -f "$DIR/$f" ]]; then
    echo "verify fail: missing $f in $DIR" >&2
    missing=1
  fi
done
if [[ "$missing" -ne 0 ]]; then
  exit 1
fi

STORE="$DIR/store.aura"
OPS="$DIR/ops.aura"
MAIN="$DIR/main.aura"
src="$(cat "$STORE" "$OPS" "$MAIN")"

if ! printf '%s\n' "$src" | grep -qE '\(define[[:space:]]+\(cache-init\b'; then
  echo "verify fail: missing (define (cache-init …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$STORE")" | grep -qE '\(define[[:space:]]+\(cache-set\b'; then
  echo "verify fail: store.aura must define (cache-set …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$OPS")" | grep -qE '\(define[[:space:]]+\(cache-get\b'; then
  echo "verify fail: ops.aura must define (cache-get …)" >&2
  exit 1
fi
if ! printf '%s\n' "$src" | grep -qE '\(define[[:space:]]+\(cache-tick\b'; then
  echo "verify fail: missing (define (cache-tick …)" >&2
  exit 1
fi
# main must call cache-get and cache-tick (not only display hardcoded lines)
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(cache-get\b'; then
  echo "verify fail: main.aura must call (cache-get …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(cache-tick\b|\(cache-set\b'; then
  echo "verify fail: main.aura must call cache-tick / cache-set (scenario ops)" >&2
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

# Honest Aura 3-file CLI
out="$("$AURA_BIN" "$STORE" "$OPS" "$MAIN" 2>&1)" || true
printf '%s\n' "$out"

# Line-oriented expect (order + content); report each mismatch for repair
expect_lines=(
  "GET_A=1"
  "GET_MISS=miss"
  "GET_B=2"
  "TTL_EXPIRED=miss"
  "COUNT=2"
)
ok=1
# Strip empty trailing lines for comparison
mapfile -t got_lines < <(printf '%s\n' "$out" | sed '/^$/d')
for i in "${!expect_lines[@]}"; do
  exp="${expect_lines[$i]}"
  # Allow optional whitespace around '='
  exp_re="$(printf '%s' "$exp" | sed -E 's/=/[[:space:]]*=[[:space:]]*/')"
  got="${got_lines[$i]:-}"
  if ! printf '%s\n' "$got" | grep -qE "^${exp_re}$"; then
    if printf '%s\n' "$out" | grep -qE "${exp_re}"; then
      echo "verify mismatch line $((i+1)): expected '$exp' at position $((i+1)), got '${got:-(missing)}' (token present elsewhere)" >&2
    else
      echo "verify mismatch line $((i+1)): expected '$exp', got '${got:-(missing)}'" >&2
    fi
    ok=0
  fi
done
for exp in "${expect_lines[@]}"; do
  exp_re="$(printf '%s' "$exp" | sed -E 's/=/[[:space:]]*=[[:space:]]*/')"
  printf '%s\n' "$out" | grep -qE "$exp_re" || ok=0
done
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b'; then
  echo "verify fail: aura runtime error in output" >&2
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok GET_A=1 GET_MISS=miss GET_B=2 TTL_EXPIRED=miss COUNT=2"
  exit 0
fi
echo "verify fail (expected GET_A=1 / GET_MISS=miss / GET_B=2 / TTL_EXPIRED=miss / COUNT=2 + store cache-init/set + ops cache-get/tick + main calls)" >&2
exit 1
