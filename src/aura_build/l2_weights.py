"""L2 offline specialist weight stub — resolve by model id only.

M3/M4 posture
-------------
- ``resolve_l2_weights(id)`` returns a stub ref (``stub=True``).
- **No training loop**, no tensor load, no download, no online L3 updates.
- Trajectory / harness record ``l2_weights_id`` + ``l2_ref`` so offline jobs
  and future promotion have a stable hook.

Where real weights would plug (M5+ / offline jobs — not in this package yet)
---------------------------------------------------------------------------
1. **Artifact store** — e.g. ``.aura-build/l2/<weights_id>/`` or an object
   store key equal to ``weights_id`` (safetensors / onnx / pickle — TBD).
2. **Manifest** — ``manifest.json`` beside the blob: trainer, corpus export
   SHA, metrics, ``incr_proven`` honesty flags, retention_class.
3. **Loader hook** — replace the body of ``resolve_l2_weights`` (or add
   ``load_l2_weights(ref) -> WeightsHandle``) to mmap/read the artifact and
   set ``loaded=True, stub=False``. Callers in orch keep using the same
   ``weights_id`` string; only the resolver grows.
4. **Promotion** — offline eval against exported trajectories
   (``aura-build export``); never promote from ``l3_online=true`` episodes
   into default L2 sets without an explicit quarantine path.

Until that loader exists, ``stub=True`` means "id acknowledged only".
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
    """Reference to offline specialist weights (stub until a real loader)."""

    weights_id: str
    loaded: bool
    stub: bool = True
    notes: str = (
        "stub: resolve by model id only; no training; "
        "real artifact would plug at resolve_l2_weights / load_l2_weights"
    )

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
