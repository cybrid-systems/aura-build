"""Honest refuse for deleted Python orch / product reimplementations."""

from __future__ import annotations

import sys

KERNEL_TAG = "python_deprecated"


def force_python_requested() -> bool:
    import os

    raw = os.environ.get("AURA_BUILD_FORCE_PYTHON", "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def refuse(cmd: str, *, reason: str = "python_orch_removed") -> int:
    """Print clear refuse and exit non-zero. Never fake an episode/storm."""
    msg = (
        f"error: aura-build {cmd}: kernel={KERNEL_TAG} reason={reason}\n"
        f"  Product orch/worldline/prove/harness/acp/tui live in aura/*.aura.\n"
        f"  Set AURA_BIN (+ GCC16 libstdc++ sidecar) and retry.\n"
        f"  AURA_BUILD_FORCE_PYTHON is debug-only/deprecated and does not restore orch."
    )
    print(msg, file=sys.stderr)
    print(f"kernel={KERNEL_TAG}", file=sys.stderr)
    return 2
