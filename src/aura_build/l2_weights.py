"""M3 L2 offline specialist weight stub — resolve by model id only.

No training, no tensor load, no download. Records the weights id into the
harness / trajectory so later milestones (M4 RL export + real specialist
promotion) have a stable hook.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

__all__ = [
    "L2WeightsRef",
    "resolve_l2_weights",
]


@dataclass(frozen=True)
class L2WeightsRef:
    """Stub reference to offline specialist weights."""

    weights_id: str
    loaded: bool
    stub: bool = True
    notes: str = "M3 stub: resolve by model id only; no training"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_l2_weights(weights_id: str | None) -> L2WeightsRef | None:
    """Return a stub ref when ``weights_id`` is set; else None.

    Always ``loaded=True`` for a non-empty id (identity acknowledged), with
    ``stub=True`` so callers do not claim real weights are in memory.
    """
    if weights_id is None:
        return None
    wid = str(weights_id).strip()
    if not wid or wid.lower() in ("null", "none"):
        return None
    return L2WeightsRef(weights_id=wid, loaded=True, stub=True)
