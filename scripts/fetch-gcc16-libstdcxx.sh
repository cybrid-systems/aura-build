#!/usr/bin/env bash
# Extract GCC 16 libstdc++ (GLIBCXX_3.4.35) from the Aura toolchain image
# so a host with only GCC 14 / libstdc++.so.6.0.33 can run a prebuilt aura.
#
# Does NOT set incr_proven. Sidecar is for LD_LIBRARY_PATH / aura-build probe.
# Default dest is under aura-redis/.deps/ (gitignored) — do not commit .so files.
set -euo pipefail

IMAGE="${AURA_TOOLCHAIN_IMAGE:-ghcr.io/cybrid-systems/dev:v1.0.7}"
DEST="${AURA_LIBSTDCXX_DIR:-/workspace/aura-redis/.deps/gcc16-libstdcxx}"

if ! command -v docker >/dev/null 2>&1; then
  echo "fetch-gcc16-libstdcxx: docker not found" >&2
  exit 1
fi

DOCKER=(docker)
if ! docker info >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1 && sudo -n docker info >/dev/null 2>&1; then
    DOCKER=(sudo -n docker)
  else
    echo "fetch-gcc16-libstdcxx: cannot talk to docker daemon (try sudo / group)" >&2
    exit 1
  fi
fi

mkdir -p "$DEST"
echo "fetch-gcc16-libstdcxx: copying libstdc++ from $IMAGE → $DEST"
"${DOCKER[@]}" run --rm -v "$DEST:/out" --entrypoint bash "$IMAGE" -c '
set -euo pipefail
cp -a /lib/x86_64-linux-gnu/libstdc++.so.6.0.35 /out/
# matching libgcc often required alongside
if [[ -f /lib/x86_64-linux-gnu/libgcc_s.so.1 ]]; then
  cp -a /lib/x86_64-linux-gnu/libgcc_s.so.1 /out/
fi
'
ln -sfn libstdc++.so.6.0.35 "$DEST/libstdc++.so.6"

# verify symbol
if ! strings "$DEST/libstdc++.so.6.0.35" | grep -q '^GLIBCXX_3.4.35$'; then
  echo "fetch-gcc16-libstdcxx: extracted lib missing GLIBCXX_3.4.35" >&2
  exit 1
fi

echo "fetch-gcc16-libstdcxx: OK"
echo "  export AURA_LIBSTDCXX_DIR=$DEST   # optional; aura-build auto-discovers this path"
echo "  aura-build doctor --json"
echo "  aura-build prove-incr --json"
