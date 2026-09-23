"""Deleted: Python orch reimplementation. Product orch is aura/orch.aura."""

from __future__ import annotations

from aura_build.deprecated import KERNEL_TAG, refuse
from aura_build.runtime import AuraUnavailable

__all__ = ["AuraUnavailable", "KERNEL_TAG", "refuse_orch"]


def refuse_orch(cmd: str = "run") -> int:
    return refuse(cmd)
