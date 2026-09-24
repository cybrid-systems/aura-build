#!/usr/bin/env bash
# self_evolve_combat.sh — thin P1 stub for combat dogfood (SSOT: docs/self-evolve-combat.md)
# Does NOT replace stamp `aura-build self-evolve`. Soft attach required. --no-push default.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
AURA_BIN="${AURA_BIN:-/workspace/aura-grok/build_soft4048/aura}"
OUT_DIR="${OUT_DIR:-scratch/self_evolve_combat}"
PROJECT="${PROJECT:-examples/projects/mini-saga}"
ROUNDS="${ROUNDS:-8}"
EXPLORE="${EXPLORE:-3}"
ENV_FILE="${ENV_FILE:-$HOME/.config/aura-build/minimax.env}"
AB="${AB:-$ROOT/.venv/bin/aura-build}"
mkdir -p "$OUT_DIR"
TS="$(date +%Y%m%d-%H%M%S)"
TRAJ="$OUT_DIR/combat_${TS}.jsonl"

echo "[combat] AURA_BIN=$AURA_BIN"
echo "[combat] project=$PROJECT rounds=$ROUNDS fiber-explore=$EXPLORE"
# Kill Soft serve zombies (not aura_redis_server)
pkill -f '/aura .*--serve' 2>/dev/null || true
pkill -f 'build_soft.*/aura .*--serve' 2>/dev/null || true
sleep 1

export AURA_BIN
"$AB" session start --aura-bin "$AURA_BIN" --force --json | tee "$OUT_DIR/session_start_${TS}.json"
"$AB" session status --json | tee "$OUT_DIR/session_status_${TS}.json"

EXTRA=()
if [[ -f "$ENV_FILE" ]]; then
  EXTRA+=(--env-file "$ENV_FILE" --fiber-llm)
else
  echo "[combat] MiniMax env missing — rule/intent only (honest LLM skip)"
  EXTRA+=(--explore-tools rule,intent --no-fiber-llm)
fi

set +e
"$AB" llm-dogfood \
  --project "$PROJECT" \
  --prefer-session \
  --fiber-explore "$EXPLORE" \
  --worldlines "$EXPLORE" \
  --max-rounds "$ROUNDS" \
  --explore-tools "${EXPLORE_TOOLS:-rule,llm,intent}" \
  --out "$TRAJ" \
  --json \
  --aura-bin "$AURA_BIN" \
  "${EXTRA[@]}" \
  | tee "$OUT_DIR/combat_${TS}_stdout.json"
RC=$?
set -e

"$AB" session status --json | tee "$OUT_DIR/session_status_after_${TS}.json" || true
# leave session up for inspection unless COMBAT_STOP=1
if [[ "${COMBAT_STOP:-0}" == "1" ]]; then
  "$AB" session stop --json || true
fi
echo "[combat] traj=$TRAJ rc=$RC"
exit "$RC"
