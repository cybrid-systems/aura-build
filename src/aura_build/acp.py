"""Deleted Python ACP product logic. Hooks live in aura/acp.aura."""

from __future__ import annotations

from aura_build.deprecated import KERNEL_TAG, refuse

# Host corpus gate for `l2 promote --from-export` still uses l2_weights.
from aura_build.l2_weights import L2PromoteError  # re-export for cli

__all__ = ["KERNEL_TAG", "L2PromoteError", "refuse"]
