#!/usr/bin/env bash
# Exit 0 iff candidate defines bus/pubsub across 5 files and prints exact lines.
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

FILES=(topic.aura sub.aura pub.aura deliver.aura main.aura)
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

TOPIC="$DIR/topic.aura"
SUB="$DIR/sub.aura"
PUB="$DIR/pub.aura"
DELIVER="$DIR/deliver.aura"
MAIN="$DIR/main.aura"

if ! printf '%s\n' "$(cat "$TOPIC")" | grep -qE '\(define[[:space:]]+\(bus-init\b'; then
  echo "verify fail: topic.aura must define (bus-init …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$TOPIC")" | grep -qE '\(define[[:space:]]+\(topic-create\b'; then
  echo "verify fail: topic.aura must define (topic-create …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$SUB")" | grep -qE '\(define[[:space:]]+\(subscribe\b'; then
  echo "verify fail: sub.aura must define (subscribe …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$SUB")" | grep -qE '\(define[[:space:]]+\(unsubscribe\b'; then
  echo "verify fail: sub.aura must define (unsubscribe …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$SUB")" | grep -qE '\(define[[:space:]]+\(sub-list\b'; then
  echo "verify fail: sub.aura must define (sub-list …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$PUB")" | grep -qE '\(define[[:space:]]+\(publish\b'; then
  echo "verify fail: pub.aura must define (publish …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$DELIVER")" | grep -qE '\(define[[:space:]]+\(poll\b'; then
  echo "verify fail: deliver.aura must define (poll …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$DELIVER")" | grep -qE '\(define[[:space:]]+\(pending-count\b'; then
  echo "verify fail: deliver.aura must define (pending-count …)" >&2
  exit 1
fi
# main must call key ops (not only display hardcoded lines)
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(subscribe\b'; then
  echo "verify fail: main.aura must call (subscribe …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(publish\b'; then
  echo "verify fail: main.aura must call (publish …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(poll\b'; then
  echo "verify fail: main.aura must call (poll …)" >&2
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

# Honest Aura 5-file CLI
out="$("$AURA_BIN" "$TOPIC" "$SUB" "$PUB" "$DELIVER" "$MAIN" 2>&1)" || true
printf '%s\n' "$out"

expect_lines=(
  "SUBS=2"
  "PUB=2"
  "POLL_A=hello"
  "POLL_B=hello"
  "POLL_MISS=miss"
  "AFTER_UNSUB=1"
  "POLL_A2=miss"
  "POLL_B2=world"
  "COUNT=3"
)
ok=1
mapfile -t got_lines < <(printf '%s\n' "$out" | sed '/^$/d')
for i in "${!expect_lines[@]}"; do
  exp="${expect_lines[$i]}"
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
  echo "verify ok SUBS=2 PUB=2 POLL_A=hello POLL_B=hello POLL_MISS=miss AFTER_UNSUB=1 POLL_A2=miss POLL_B2=world COUNT=3"
  exit 0
fi
echo "verify fail (expected 9 pubsub lines + topic/sub/pub/deliver defines + main calls)" >&2
exit 1
