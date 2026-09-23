#!/usr/bin/env bash
# Run the Aura kernel (aura/main.aura). Thin host helper for dogfood.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

resolve_bin() {
  if [[ -n "${AURA_BIN:-}" && -x "${AURA_BIN}" ]]; then echo "$AURA_BIN"; return; fi
  for c in \
    /workspace/aura-redis/.deps/aura/build/aura \
    /workspace/aura-grok/build/aura \
    /workspace/aura-redis-ci/.deps/aura/build/aura
  do
    if [[ -x "$c" ]]; then echo "$c"; return; fi
  done
  if command -v aura >/dev/null 2>&1; then command -v aura; return; fi
  echo ""
}

AURA_BIN="$(resolve_bin)"
if [[ -z "$AURA_BIN" ]]; then
  echo "error: aura binary not found (set AURA_BIN)" >&2
  exit 2
fi

# GCC16 libstdc++ sidecar
if [[ -z "${AURA_LIBSTDCXX_DIR:-}" ]]; then
  for d in \
    /workspace/aura-redis/.deps/gcc16-libstdcxx \
    /workspace/aura-grok/.deps/gcc16-libstdcxx \
    /workspace/aura-redis-ci/.deps/gcc16-libstdcxx
  do
    if [[ -f "$d/libstdc++.so.6" ]]; then export AURA_LIBSTDCXX_DIR="$d"; break; fi
  done
fi
if [[ -n "${AURA_LIBSTDCXX_DIR:-}" ]]; then
  export LD_LIBRARY_PATH="${AURA_LIBSTDCXX_DIR}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

export AURA_SANDBOX="${AURA_SANDBOX:-off}"
export AURA_PIPELINE_STRICT="${AURA_PIPELINE_STRICT:-0}"
export AURA_BIN
export AURA_BUILD_REPO_ROOT="$ROOT"
export AURA_PATH="${ROOT}/aura:${AURA_PATH:-}"
# Prefer redis/grok stdlib on AURA_PATH
for lib in \
  /workspace/aura-redis/.deps/aura/lib \
  /workspace/aura-grok/lib
do
  if [[ -d "$lib/std" ]]; then
    export AURA_PATH="${ROOT}/aura:${lib}${AURA_PATH:+:$AURA_PATH}"
    break
  fi
done

export AURA_BUILD_CMD="${AURA_BUILD_CMD:-run}"
exec "$AURA_BIN" "$ROOT/aura/main.aura"
