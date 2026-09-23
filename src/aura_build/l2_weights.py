"""L2 offline specialist weights — metadata artifact plug (M5).

M5 posture
----------
- Resolve by ``weights_id``; optionally load stub metadata from
  ``.aura-build/weights/<id>.json`` (``id``, ``created``, ``notes`` only).
- Offline promotion writes that JSON after gating an export corpus
  (refuses any episode with ``l3_online=true``).
- **No training loop**, no tensor/mmap load, no online L3 updates.
- ``stub=True`` always while artifacts are metadata-only (no weight bytes).
  ``artifact_present=True`` when the JSON file was loaded.

Honesty
-------
- Do not set ``stub=False`` until real weight bytes load (deferred past M5).
- Do not flip ``incr_proven``.
- Do not promote from online L3 episodes into default L2 sets.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aura_build.harness import default_root

__all__ = [
    "L2PromoteError",
    "L2WeightsRef",
    "artifact_path",
    "list_l2_artifacts",
    "load_l2_artifact",
    "promote_l2_offline",
    "resolve_l2_weights",
    "weights_dir",
]

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class L2PromoteError(ValueError):
    """Offline L2 promotion refused (bad id, L3 corpus, or IO)."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _aura_build_root(root: Path | str | None) -> Path:
    """Normalize to the ``.aura-build`` directory.

    Accepts ``None`` (cwd/.aura-build), a path to ``.aura-build``, or a
    harness_root that already points at ``.aura-build``.
    """
    if root is None:
        return default_root()
    r = Path(root)
    if r.name == ".aura-build":
        return r
    # harness_root in this project is already `.aura-build` (may not exist yet).
    # Heuristic: if it looks like an aura-build state dir, use as-is.
    if (
        (r / "harness.json").exists()
        or (r / "memory").is_dir()
        or (r / "weights").is_dir()
        or (r / "session.json").exists()
    ):
        return r
    return r / ".aura-build"


def weights_dir(root: Path | str | None = None) -> Path:
    """Return ``<aura-build-root>/weights``."""
    return _aura_build_root(root) / "weights"


def artifact_path(weights_id: str, root: Path | str | None = None) -> Path:
    """Path for stub metadata JSON: ``.aura-build/weights/<id>.json``."""
    wid = _require_safe_id(weights_id)
    return weights_dir(root) / f"{wid}.json"


def _require_safe_id(weights_id: str) -> str:
    wid = str(weights_id).strip()
    if not wid or wid.lower() in ("null", "none"):
        raise L2PromoteError("weights_id is empty")
    if not _SAFE_ID.match(wid) or ".." in wid or "/" in wid or "\\" in wid:
        raise L2PromoteError(
            f"unsafe weights_id {weights_id!r} "
            "(allowed: alphanumeric, dot, underscore, dash)"
        )
    return wid


def _safe_id_or_none(weights_id: str | None) -> str | None:
    if weights_id is None:
        return None
    wid = str(weights_id).strip()
    if not wid or wid.lower() in ("null", "none"):
        return None
    if not _SAFE_ID.match(wid) or ".." in wid or "/" in wid or "\\" in wid:
        return None
    return wid


@dataclass(frozen=True)
class L2WeightsRef:
    """Reference to offline specialist weights (metadata stub in M5)."""

    weights_id: str
    loaded: bool
    stub: bool = True
    artifact_present: bool = False
    created: str | None = None
    notes: str = (
        "stub: resolve by model id only; metadata JSON under "
        ".aura-build/weights/<id>.json; no training; no tensor load"
    )
    artifact_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_l2_artifact(
    weights_id: str,
    root: Path | str | None = None,
) -> L2WeightsRef | None:
    """Load metadata stub from ``.aura-build/weights/<id>.json`` if present.

    Returns None when the file is missing. Always ``stub=True`` (no tensors).
    """
    wid = _safe_id_or_none(weights_id)
    if wid is None:
        return None
    path = weights_dir(root) / f"{wid}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    file_id = str(data.get("id") or data.get("weights_id") or wid).strip()
    if file_id != wid:
        return None
    created = data.get("created")
    created_s = str(created) if created is not None else None
    notes_raw = data.get("notes")
    notes = (
        str(notes_raw)
        if notes_raw is not None
        else "metadata artifact; stub=True (no tensor bytes)"
    )
    return L2WeightsRef(
        weights_id=wid,
        loaded=True,
        stub=True,
        artifact_present=True,
        created=created_s,
        notes=notes,
        artifact_path=str(path),
    )


def resolve_l2_weights(
    weights_id: str | None,
    root: Path | str | None = None,
) -> L2WeightsRef | None:
    """Return an L2 ref when ``weights_id`` is set; else None.

    Prefer on-disk metadata under ``.aura-build/weights/<id>.json``.
    If absent, acknowledge the id with ``artifact_present=False``, ``stub=True``.
    """
    wid = _safe_id_or_none(weights_id)
    if wid is None:
        if weights_id is None:
            return None
        raw = str(weights_id).strip()
        if not raw or raw.lower() in ("null", "none"):
            return None
        return L2WeightsRef(
            weights_id=raw,
            loaded=True,
            stub=True,
            artifact_present=False,
        )

    loaded = load_l2_artifact(wid, root=root)
    if loaded is not None:
        return loaded
    return L2WeightsRef(
        weights_id=wid,
        loaded=True,
        stub=True,
        artifact_present=False,
        notes=(
            "stub: id acknowledged; no .aura-build/weights/<id>.json yet; "
            "promote offline via aura-build l2 promote"
        ),
    )


def list_l2_artifacts(root: Path | str | None = None) -> list[L2WeightsRef]:
    """List metadata artifacts under ``.aura-build/weights/``."""
    d = weights_dir(root)
    if not d.is_dir():
        return []
    out: list[L2WeightsRef] = []
    for path in sorted(d.glob("*.json")):
        ref = load_l2_artifact(path.stem, root=root)
        if ref is not None:
            out.append(ref)
    return out


def _export_has_l3_online(export_path: Path) -> list[str]:
    """Return episode ids that set ``l3_online=true``."""
    text = export_path.read_text(encoding="utf-8")
    text_stripped = text.strip()
    if text_stripped.startswith("["):
        episodes = json.loads(text_stripped)
        if not isinstance(episodes, list):
            raise L2PromoteError(f"export is not a JSON array: {export_path}")
    else:
        episodes = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            episodes.append(json.loads(line))

    bad: list[str] = []
    for i, ep in enumerate(episodes):
        if not isinstance(ep, dict):
            continue
        harness = ep.get("harness") or {}
        if isinstance(harness, dict) and harness.get("l3_online") is True:
            eid = ep.get("episode_id") or f"index:{i}"
            bad.append(str(eid))
    return bad


def promote_l2_offline(
    weights_id: str,
    *,
    notes: str = "",
    root: Path | str | None = None,
    export_path: Path | str | None = None,
    created: str | None = None,
    overwrite: bool = False,
) -> L2WeightsRef:
    """Write offline metadata stub under ``.aura-build/weights/<id>.json``.

    If ``export_path`` is given, refuses when any episode has ``l3_online=true``.
    Never trains; never loads tensors; never sets ``stub=False``.
    """
    wid = _require_safe_id(weights_id)
    if export_path is not None:
        ep = Path(export_path)
        if not ep.is_file():
            raise L2PromoteError(f"export not found: {ep}")
        bad = _export_has_l3_online(ep)
        if bad:
            raise L2PromoteError(
                "refuse offline L2 promote: export contains l3_online=true "
                f"episodes: {bad[:5]}"
            )

    path = artifact_path(wid, root=root)
    if path.exists() and not overwrite:
        raise L2PromoteError(
            f"artifact already exists: {path} (pass overwrite=True to replace)"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": wid,
        "created": created or _utc_now(),
        "notes": notes
        or "offline metadata stub; stub=True; no tensor bytes; no online L3",
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    ref = load_l2_artifact(wid, root=root)
    if ref is None:
        raise L2PromoteError(f"wrote {path} but failed to reload")
    return ref
