#!/usr/bin/env bash
# Exit 0 iff candidate defines 2PC across 7 files and prints exact lines.
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

FILES=(log.aura part-a.aura part-b.aura vote.aura coord.aura recover.aura main.aura)
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

LOG="$DIR/log.aura"
PARTA="$DIR/part-a.aura"
PARTB="$DIR/part-b.aura"
VOTE="$DIR/vote.aura"
COORD="$DIR/coord.aura"
RECOVER="$DIR/recover.aura"
MAIN="$DIR/main.aura"

need_def() {
  local file="$1" name="$2" label="$3"
  if ! printf '%s\n' "$(cat "$file")" | grep -qE "\(define[[:space:]]+\(${name}\\b"; then
    echo "verify fail: ${label} must define (${name} …)" >&2
    return 1
  fi
  return 0
}

need_def "$LOG" "log-init" "log.aura" || exit 1
need_def "$LOG" "log-append" "log.aura" || exit 1
need_def "$LOG" "log-last" "log.aura" || exit 1
need_def "$PARTA" "a-init" "part-a.aura" || exit 1
need_def "$PARTA" "a-prepare" "part-a.aura" || exit 1
need_def "$PARTA" "a-commit" "part-a.aura" || exit 1
need_def "$PARTA" "a-abort" "part-a.aura" || exit 1
need_def "$PARTA" "a-state" "part-a.aura" || exit 1
need_def "$PARTB" "b-init" "part-b.aura" || exit 1
need_def "$PARTB" "b-prepare" "part-b.aura" || exit 1
need_def "$PARTB" "b-commit" "part-b.aura" || exit 1
need_def "$PARTB" "b-abort" "part-b.aura" || exit 1
need_def "$PARTB" "b-state" "part-b.aura" || exit 1
need_def "$VOTE" "collect-votes" "vote.aura" || exit 1
need_def "$COORD" "coord-init" "coord.aura" || exit 1
need_def "$COORD" "coord-run" "coord.aura" || exit 1
need_def "$RECOVER" "recover-from-log" "recover.aura" || exit 1

# main must call key ops (not only display hardcoded lines)
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(coord-run\b'; then
  echo "verify fail: main.aura must call (coord-run …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(recover-from-log\b'; then
  echo "verify fail: main.aura must call (recover-from-log …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(a-state\b'; then
  echo "verify fail: main.aura must probe (a-state …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(b-state\b'; then
  echo "verify fail: main.aura must probe (b-state …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(log-last\b'; then
  echo "verify fail: main.aura must call (log-last …)" >&2
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

# Honest Aura 7-file CLI
out="$("$AURA_BIN" "$LOG" "$PARTA" "$PARTB" "$VOTE" "$COORD" "$RECOVER" "$MAIN" 2>&1)" || true
printf '%s\n' "$out"

expect_lines=(
  "RUN1=commit"
  "STATE1=committed"
  "RUN2=abort"
  "STATE2=aborted"
  "LOG=abort"
  "RECOVER=aborted"
  "POISON=abort"
  "COUNT=5"
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
  echo "verify ok RUN1=commit STATE1=committed RUN2=abort STATE2=aborted LOG=abort RECOVER=aborted POISON=abort COUNT=5"
  exit 0
fi
echo "verify fail (expected 8 2pc lines + log/part/vote/coord/recover defines + main calls)" >&2
exit 1
