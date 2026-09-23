#!/usr/bin/env bash
# Exit 0 iff candidate defines route-register/route-lookup and prints exact router lines.
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

FILES=(table.aura match.aura main.aura)
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

TABLE="$DIR/table.aura"
MATCH="$DIR/match.aura"
MAIN="$DIR/main.aura"
src="$(cat "$TABLE" "$MATCH" "$MAIN")"

if ! printf '%s\n' "$src" | grep -qE '\(define[[:space:]]+\(route-register\b'; then
  echo "verify fail: missing (define (route-register …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MATCH")" | grep -qE '\(define[[:space:]]+\(route-lookup\b'; then
  echo "verify fail: match.aura must define (route-lookup …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MATCH")" | grep -qE 'substring|string-length'; then
  echo "verify fail: match.aura must implement prefix via substring/string-length" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$TABLE")" | grep -qE '\(define[[:space:]]+\(route-register\b'; then
  echo "verify fail: table.aura must define (route-register …) (not main-only hardcode)" >&2
  exit 1
fi
# main must call route-lookup (not only display hardcoded lines)
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(route-lookup\b'; then
  echo "verify fail: main.aura must call (route-lookup …)" >&2
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
out="$("$AURA_BIN" "$TABLE" "$MATCH" "$MAIN" 2>&1)" || true
printf '%s\n' "$out"

# Line-oriented expect (order + content); report each mismatch for repair
expect_lines=(
  "GET_SLASH=home"
  "GET_API=api"
  "GET_API_V1=api"
  "GET_API_V2=api"
  "POST_API=405"
  "MISS=404"
  "COUNT=5"
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
    # Also accept if line appears anywhere (order soft) but still flag order issues
    if printf '%s\n' "$out" | grep -qE "${exp_re}"; then
      echo "verify mismatch line $((i+1)): expected '$exp' at position $((i+1)), got '${got:-(missing)}' (token present elsewhere)" >&2
    else
      echo "verify mismatch line $((i+1)): expected '$exp', got '${got:-(missing)}'" >&2
    fi
    ok=0
  fi
done
# Also require all tokens present (belt + suspenders for soft order)
for exp in "${expect_lines[@]}"; do
  exp_re="$(printf '%s' "$exp" | sed -E 's/=/[[:space:]]*=[[:space:]]*/')"
  printf '%s\n' "$out" | grep -qE "$exp_re" || ok=0
done
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b'; then
  echo "verify fail: aura runtime error in output" >&2
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok GET_SLASH=home GET_API=api GET_API_V1=api GET_API_V2=api POST_API=405 MISS=404 COUNT=5"
  exit 0
fi
echo "verify fail (expected GET_SLASH=home / GET_API=api / GET_API_V1=api / GET_API_V2=api / POST_API=405 / MISS=404 / COUNT=5 + table route-register + match route-lookup + main calls)" >&2
exit 1
