#!/usr/bin/env bash
# Exit 0 iff candidate defines queue-* across 4 files and prints exact lines.
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

FILES=(buf.aura lease.aura ops.aura main.aura)
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

BUF="$DIR/buf.aura"
LEASE="$DIR/lease.aura"
OPS="$DIR/ops.aura"
MAIN="$DIR/main.aura"
src="$(cat "$BUF" "$LEASE" "$OPS" "$MAIN")"

if ! printf '%s\n' "$(cat "$BUF")" | grep -qE '\(define[[:space:]]+\(queue-init\b'; then
  echo "verify fail: buf.aura must define (queue-init …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$BUF")" | grep -qE '\(define[[:space:]]+\(queue-enqueue\b'; then
  echo "verify fail: buf.aura must define (queue-enqueue …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$LEASE")" | grep -qE '\(define[[:space:]]+\(queue-lease\b'; then
  echo "verify fail: lease.aura must define (queue-lease …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$LEASE")" | grep -qE '\(define[[:space:]]+\(queue-tick\b'; then
  echo "verify fail: lease.aura must define (queue-tick …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$OPS")" | grep -qE '\(define[[:space:]]+\(queue-ack\b'; then
  echo "verify fail: ops.aura must define (queue-ack …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$OPS")" | grep -qE '\(define[[:space:]]+\(queue-nack\b'; then
  echo "verify fail: ops.aura must define (queue-nack …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$OPS")" | grep -qE '\(define[[:space:]]+\(queue-status\b'; then
  echo "verify fail: ops.aura must define (queue-status …)" >&2
  exit 1
fi
# main must call key ops (not only display hardcoded lines)
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(queue-lease\b'; then
  echo "verify fail: main.aura must call (queue-lease …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(queue-tick\b'; then
  echo "verify fail: main.aura must call (queue-tick …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(queue-ack\b'; then
  echo "verify fail: main.aura must call (queue-ack …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(queue-nack\b|\(queue-status\b'; then
  echo "verify fail: main.aura must call queue-nack / queue-status" >&2
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

# Honest Aura 4-file CLI
out="$("$AURA_BIN" "$BUF" "$LEASE" "$OPS" "$MAIN" 2>&1)" || true
printf '%s\n' "$out"

expect_lines=(
  "ENQ=2"
  "LEASE_A=j1"
  "LEASE_B=j2"
  "LEASE_MISS=miss"
  "ACK_OK=1"
  "NACK_STATUS=pending"
  "AFTER_TICK=pending"
  "DONE=1"
  "COUNT=4"
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
  echo "verify ok ENQ=2 LEASE_A=j1 LEASE_B=j2 LEASE_MISS=miss ACK_OK=1 NACK_STATUS=pending AFTER_TICK=pending DONE=1 COUNT=4"
  exit 0
fi
echo "verify fail (expected 9 queue lines + buf/lease/ops defines + main calls)" >&2
exit 1
