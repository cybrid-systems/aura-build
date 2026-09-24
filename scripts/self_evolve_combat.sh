#!/usr/bin/env bash
# self_evolve_combat.sh — thin wrapper → `aura-build self-evolve combat`
# SSOT: docs/self-evolve-combat.md
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
AB="${AB:-$ROOT/.venv/bin/aura-build}"
AURA_BIN="${AURA_BIN:-/workspace/aura-grok/build_soft4054/aura}"
export AURA_BIN
OUT_DIR="${OUT_DIR:-scratch/self_evolve_combat}"
PROJECT="${PROJECT:-examples/projects/mini-saga}"
ROUNDS="${ROUNDS:-8}"
EXPLORE="${EXPLORE:-3}"
ENV_FILE="${ENV_FILE:-$HOME/.config/aura-build/minimax.env}"

EXTRA=(--start-session --project "$PROJECT" --max-rounds "$ROUNDS"
       --fiber-explore "$EXPLORE" --worldlines "$EXPLORE"
       --out-dir "$OUT_DIR" --aura-bin "$AURA_BIN" --json --no-push)
if [[ -f "$ENV_FILE" ]]; then
  EXTRA+=(--env-file "$ENV_FILE" --fiber-llm)
else
  EXTRA+=(--explore-tools rule,intent --no-fiber-llm)
fi
if [[ "${COMBAT_STOP:-0}" == "1" ]]; then
  EXTRA+=(--stop-session)
fi
if [[ "${CONCURRENT_LLM:-0}" == "1" ]]; then
  EXTRA+=(--concurrent-llm)
fi
exec "$AB" self-evolve combat "${EXTRA[@]}" "$@"
