"""L2 offline metadata — host corpus gate for ``l2 promote --from-export``.

Product show/list/promote (sans export gate) lives in ``aura/l2.aura``. This
module keeps the offline promote path that refuses ``l3_online=true`` corpora
and thin resolve/list JSON I/O when Aura is unavailable. Always ``stub=True``.
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
    "host_cli",
    "resolve_l2_weights",
    "weights_dir",
]

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class L2PromoteError(ValueError):
    """Offline L2 promotion refused (bad id, L3 corpus, or IO)."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _aura_build_root(root: Path | str | None) -> Path:
    if root is None:
        return default_root()
    r = Path(root)
    if r.name == ".aura-build":
        return r
    if (
        (r / "harness.json").exists()
        or (r / "memory").is_dir()
        or (r / "weights").is_dir()
        or (r / "session.json").exists()
    ):
        return r
    return r / ".aura-build"


def weights_dir(root: Path | str | None = None) -> Path:
    return _aura_build_root(root) / "weights"


def artifact_path(weights_id: str, root: Path | str | None = None) -> Path:
    return weights_dir(root) / f"{_require_safe_id(weights_id)}.json"


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
    weights_id: str
    loaded: bool
    stub: bool = True
    artifact_present: bool = False
    created: str | None = None
    notes: str = "stub metadata; no tensor load"
    artifact_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_l2_artifact(
    weights_id: str, root: Path | str | None = None
) -> L2WeightsRef | None:
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
    notes_raw = data.get("notes")
    return L2WeightsRef(
        weights_id=wid,
        loaded=True,
        stub=True,
        artifact_present=True,
        created=str(created) if created is not None else None,
        notes=str(notes_raw) if notes_raw is not None else "metadata stub; stub=True",
        artifact_path=str(path),
    )


def resolve_l2_weights(
    weights_id: str | None, root: Path | str | None = None
) -> L2WeightsRef | None:
    wid = _safe_id_or_none(weights_id)
    if wid is None:
        if weights_id is None:
            return None
        raw = str(weights_id).strip()
        if not raw or raw.lower() in ("null", "none"):
            return None
        return L2WeightsRef(weights_id=raw, loaded=True, stub=True, artifact_present=False)
    loaded = load_l2_artifact(wid, root=root)
    if loaded is not None:
        return loaded
    return L2WeightsRef(
        weights_id=wid,
        loaded=True,
        stub=True,
        artifact_present=False,
        notes="stub: id acknowledged; promote via aura-build l2 promote",
    )


def list_l2_artifacts(root: Path | str | None = None) -> list[L2WeightsRef]:
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
            if line:
                episodes.append(json.loads(line))
    bad: list[str] = []
    for i, ep in enumerate(episodes):
        if not isinstance(ep, dict):
            continue
        harness = ep.get("harness") or {}
        if isinstance(harness, dict) and harness.get("l3_online") is True:
            bad.append(str(ep.get("episode_id") or f"index:{i}"))
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
    """Write metadata stub; refuse l3_online=true export corpora."""
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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ref = load_l2_artifact(wid, root=root)
    if ref is None:
        raise L2PromoteError(f"wrote {path} but failed to reload")
    return ref


def host_cli(
    op: str,
    *,
    root: Path | str,
    weights_id: str = "",
    notes: str = "",
    from_export: Path | str | None = None,
    overwrite: bool = False,
    as_json: bool = False,
) -> int:
    """Thin host L2 metadata I/O / promote --from-export corpus gate."""
    import sys

    if op == "show":
        ref = resolve_l2_weights(weights_id, root=root)
        if ref is None:
            print("null")
            return 1
        if as_json:
            print(json.dumps(ref.to_dict(), indent=2, sort_keys=True))
        else:
            print(
                f"id={ref.weights_id} loaded={ref.loaded} stub={ref.stub} "
                f"artifact_present={ref.artifact_present} "
                f"created={ref.created or '-'} path={ref.artifact_path or '-'}"
            )
        return 0
    if op == "list":
        refs = list_l2_artifacts(root=root)
        payload = [r.to_dict() for r in refs]
        if as_json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            if not refs:
                print("l2 weights: (none)")
            for r in refs:
                print(
                    f"id={r.weights_id} stub={r.stub} "
                    f"created={r.created or '-'} path={r.artifact_path}"
                )
        return 0
    if op == "promote":
        try:
            ref = promote_l2_offline(
                weights_id,
                notes=notes,
                root=root,
                export_path=from_export,
                overwrite=overwrite,
            )
        except L2PromoteError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if as_json:
            print(json.dumps(ref.to_dict(), indent=2, sort_keys=True))
        else:
            tag = "python_host" if from_export is not None else ""
            extra = f" kernel={tag}" if tag else ""
            print(
                f"promoted id={ref.weights_id} stub={ref.stub} "
                f"artifact_present={ref.artifact_present} path={ref.artifact_path}"
                f"{extra}"
            )
        return 0
    return 2
