#!/usr/bin/env bash
# Exit 0 iff candidate defines mini-exchange across 15 files and prints exact lines.
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

FILES=(idemp.aura journal.aura ledger.aura fee.aura risk.aura book.aura match.aura order.aura settle.aura halt.aura snapshot.aura replay.aura query.aura exchange.aura main.aura)
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

need_def() {
  local file="$1" name="$2" label="$3"
  if ! grep -Fq "(define (${name}" "$file"; then
    echo "verify fail: ${label} must define (${name} …)" >&2
    return 1
  fi
  return 0
}
need_def "$DIR/idemp.aura" "idemp-init" "idemp.aura" || exit 1
need_def "$DIR/idemp.aura" "idemp-seen?" "idemp.aura" || exit 1
need_def "$DIR/idemp.aura" "idemp-mark" "idemp.aura" || exit 1
need_def "$DIR/journal.aura" "journal-init" "journal.aura" || exit 1
need_def "$DIR/journal.aura" "journal-append" "journal.aura" || exit 1
need_def "$DIR/ledger.aura" "ledger-init" "ledger.aura" || exit 1
need_def "$DIR/ledger.aura" "ledger-fund" "ledger.aura" || exit 1
need_def "$DIR/fee.aura" "fee-init" "fee.aura" || exit 1
need_def "$DIR/fee.aura" "fee-total" "fee.aura" || exit 1
need_def "$DIR/risk.aura" "risk-check" "risk.aura" || exit 1
need_def "$DIR/book.aura" "book-init" "book.aura" || exit 1
need_def "$DIR/book.aura" "book-add" "book.aura" || exit 1
need_def "$DIR/match.aura" "match-against" "match.aura" || exit 1
need_def "$DIR/order.aura" "order-place" "order.aura" || exit 1
need_def "$DIR/order.aura" "order-cancel" "order.aura" || exit 1
need_def "$DIR/settle.aura" "settle-fill" "settle.aura" || exit 1
need_def "$DIR/halt.aura" "halt-set" "halt.aura" || exit 1
need_def "$DIR/snapshot.aura" "snapshot-fp" "snapshot.aura" || exit 1
need_def "$DIR/replay.aura" "replay-run" "replay.aura" || exit 1
need_def "$DIR/query.aura" "query-left" "query.aura" || exit 1
need_def "$DIR/exchange.aura" "exchange-init" "exchange.aura" || exit 1
need_def "$DIR/exchange.aura" "exchange-place" "exchange.aura" || exit 1
need_def "$DIR/exchange.aura" "exchange-replay" "exchange.aura" || exit 1

if ! printf '%s\n' "$(cat "$DIR/main.aura")" | grep -qE '\(exchange-place\b'; then
  echo "verify fail: main.aura must call (exchange-place …)" >&2
  exit 1
fi
if ! printf '%s\n' "$(cat "$DIR/main.aura")" | grep -qE '\(exchange-replay\b|\(query-left\b'; then
  echo "verify fail: main.aura must call exchange-replay or query-left" >&2
  exit 1
fi

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

paths=()
for f in "${FILES[@]}"; do paths+=("$DIR/$f"); done
out="$("$AURA_BIN" "${paths[@]}" 2>&1)" || true
printf '%s\n' "$out"

expect_lines=(
  "FILL1=partial"
  "LEFT1=3"
  "RISK=reject"
  "STP=0"
  "CXL=cancelled"
  "HALT=halted"
  "REJ_HALT=reject"
  "RESUME=open"
  "DUP=dup"
  "REPLAY=ok"
  "EQ=1"
  "FEES=14"
  "COUNT=10"
)
ok=1
mapfile -t got_lines < <(printf '%s\n' "$out" | sed '/^$/d')
for i in "${!expect_lines[@]}"; do
  exp="${expect_lines[$i]}"
  exp_re="$(printf '%s' "$exp" | sed -E 's/=/[[:space:]]*=[[:space:]]*/')"
  got="${got_lines[$i]:-}"
  if ! printf '%s\n' "$got" | grep -qE "^${exp_re}$"; then
    echo "verify mismatch line $((i+1)): expected '$exp', got '${got:-(missing)}'" >&2
    ok=0
  fi
done
if printf '%s\n' "$out" | grep -qiE '\berror:|\bunbound variable\b'; then
  echo "verify fail: aura runtime error in output" >&2
  ok=0
fi
if [[ "$ok" -eq 1 ]]; then
  echo "verify ok FILL1=partial LEFT1=3 RISK=reject STP=0 CXL=cancelled HALT=halted REJ_HALT=reject RESUME=open DUP=dup REPLAY=ok EQ=1 FEES=14 COUNT=10"
  exit 0
fi
echo "verify fail (expected 13 exchange lines + structural defines)" >&2
exit 1
