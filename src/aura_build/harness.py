"""Host paths + AUTOPROMOTE env name (product harness lives in aura/harness.aura)."""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["AUTOPROMOTE_ENV", "autopropote_enabled", "default_root"]

AUTOPROMOTE_ENV = "AURA_BUILD_AUTOPROMOTE"


def default_root(cwd: Path | str | None = None) -> Path:
    """``.aura-build`` under cwd (or process cwd)."""
    base = Path(cwd) if cwd is not None else Path.cwd()
    return base / ".aura-build"


def autopropote_enabled(flag: bool | None = None) -> bool:
    """AUTOPROMOTE default OFF; explicit True or env=1 enables (Aura kernel reads env)."""
    if flag is True:
        return True
    if flag is False:
        return False
    raw = os.environ.get(AUTOPROMOTE_ENV, "").strip().lower()
    return raw in ("1", "true", "yes", "on")
