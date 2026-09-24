#!/usr/bin/env bash
# Exit 0 iff candidate defines saga across 10 files and prints exact lines.
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

FILES=(idemp.aura journal.aura book.aura pay.aura ship.aura step.aura compensate.aura saga.aura query.aura main.aura)
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

IDEMP="$DIR/idemp.aura"
JOURNAL="$DIR/journal.aura"
BOOK="$DIR/book.aura"
PAY="$DIR/pay.aura"
SHIP="$DIR/ship.aura"
STEP="$DIR/step.aura"
COMP="$DIR/compensate.aura"
SAGA="$DIR/saga.aura"
QUERY="$DIR/query.aura"
MAIN="$DIR/main.aura"

need_def() {
  local file="$1" name="$2" label="$3"
  # Fixed-string match for "(define (<name>" — avoids ERE ? metachar issues
  if ! grep -Fq "(define (${name}" "$file"; then
    echo "verify fail: ${label} must define (${name} …)" >&2
    return 1
  fi
  return 0
}
need_def "$IDEMP" "idemp-init" "idemp.aura" || exit 1
need_def "$IDEMP" "idemp-seen?" "idemp.aura" || exit 1
need_def "$IDEMP" "idemp-mark" "idemp.aura" || exit 1
need_def "$JOURNAL" "journal-init" "journal.aura" || exit 1
need_def "$JOURNAL" "journal-append" "journal.aura" || exit 1
need_def "$JOURNAL" "journal-last" "journal.aura" || exit 1
need_def "$JOURNAL" "journal-has?" "journal.aura" || exit 1
need_def "$BOOK" "book-init" "book.aura" || exit 1
need_def "$BOOK" "book-reserve" "book.aura" || exit 1
need_def "$BOOK" "book-cancel" "book.aura" || exit 1
need_def "$BOOK" "book-state" "book.aura" || exit 1
need_def "$PAY" "pay-init" "pay.aura" || exit 1
need_def "$PAY" "pay-charge" "pay.aura" || exit 1
need_def "$PAY" "pay-refund" "pay.aura" || exit 1
need_def "$PAY" "pay-state" "pay.aura" || exit 1
need_def "$SHIP" "ship-init" "ship.aura" || exit 1
need_def "$SHIP" "ship-send" "ship.aura" || exit 1
need_def "$SHIP" "ship-recall" "ship.aura" || exit 1
need_def "$SHIP" "ship-state" "ship.aura" || exit 1
need_def "$STEP" "run-step" "step.aura" || exit 1
need_def "$COMP" "compensate-from" "compensate.aura" || exit 1
need_def "$SAGA" "saga-init" "saga.aura" || exit 1
need_def "$SAGA" "saga-run" "saga.aura" || exit 1
need_def "$QUERY" "saga-status" "query.aura" || exit 1

# main must call key ops (not only display hardcoded lines)
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(saga-run\b'; then
  echo "verify fail: main.aura must call (saga-run …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$MAIN")" | grep -qE '\(saga-status\b'; then
  echo "verify fail: main.aura must call (saga-status …)" >&2
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

# Honest Aura 10-file CLI
out="$("$AURA_BIN" "$IDEMP" "$JOURNAL" "$BOOK" "$PAY" "$SHIP" "$STEP" "$COMP" "$SAGA" "$QUERY" "$MAIN" 2>&1)" || true
printf '%s\n' "$out"

expect_lines=(
  "OK=committed"
  "ST1=held/charged/sent"
  "DUP=dup"
  "ST1B=held/charged/sent"
  "FAIL_PAY=aborted"
  "ST2=cancelled/none/none"
  "FAIL_SHIP=aborted"
  "ST3=cancelled/refunded/none"
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
  echo "verify ok OK=committed ST1=held/charged/sent DUP=dup ST1B=held/charged/sent FAIL_PAY=aborted ST2=cancelled/none/none FAIL_SHIP=aborted ST3=cancelled/refunded/none COUNT=4"
  exit 0
fi
echo "verify fail (expected 9 saga lines + idemp/journal/book/pay/ship/step/compensate/saga/query defines + main calls)" >&2
exit 1
