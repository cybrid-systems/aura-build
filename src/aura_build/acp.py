"""Agent Control Plane (ACP) hooks — thin host surface (M5).

Shape inspired by grok-build (headless → CI → ACP/TUI), **not** postman
physics and **not** a coding-agent chrome moat. Soft ≠ Restricted.

Hooks (wired to existing CLI / libraries where possible)
--------------------------------------------------------
| Hook              | Meaning                         | Wire-up                          |
|-------------------|---------------------------------|----------------------------------|
| start_session     | open a dogfood session marker   | writes `.aura-build/session.json`|
| list_worldlines   | show candidates from last ep/ws | last traj JSONL / workspace meta |
| promote           | offline L2 metadata promote     | `l2.promote_l2_offline`          |
| discard           | mark worldline loser / L2 skip  | workspace DISCARDED or refuse     |
| export            | batch trajectory export         | `aura-build export` / export API |

Headless ``run`` / ``export`` / harness canary remain the SSOT. ACP does not
claim fiber-live FlatAST, ``incr_proven=true``, or online L3.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aura_build.harness import default_root, load_harness
from aura_build.l2_weights import (
    L2PromoteError,
    list_l2_artifacts,
    promote_l2_offline,
    resolve_l2_weights,
)
from aura_build.worldline import WorldlineWorkspace

__all__ = [
    "ACP_HOOKS",
    "SessionStatus",
    "acp_discard_worldline",
    "acp_export_hint",
    "acp_list_worldlines",
    "acp_promote_l2",
    "acp_start_session",
    "acp_status",
    "describe_hooks",
    "find_last_trajectory",
    "session_path",
]

ACP_HOOKS: dict[str, str] = {
    "start_session": (
        "Write/refresh `.aura-build/session.json`; optional prompt note. "
        "Does not run an episode — use `aura-build run` for that."
    ),
    "list_worldlines": (
        "List worldlines from session workspace meta or last trajectory JSONL."
    ),
    "promote": (
        "Offline L2 metadata promote → `.aura-build/weights/<id>.json`. "
        "Refuses corpora with `l3_online=true`. Alias: `aura-build l2 promote`."
    ),
    "discard": (
        "Mark a worldline loser in a shared workspace (DISCARDED flag). "
        "Not fiber-live; audit-only."
    ),
    "export": (
        "Batch-export trajectories (privacy ON by default). "
        "Alias: `aura-build export`."
    ),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _root(root: Path | str | None) -> Path:
    if root is None:
        return default_root()
    r = Path(root)
    if r.name == ".aura-build":
        return r
    if (
        (r / "harness.json").exists()
        or (r / "session.json").exists()
        or (r / "weights").is_dir()
        or (r / "memory").is_dir()
    ):
        return r
    return r / ".aura-build"


def session_path(root: Path | str | None = None) -> Path:
    return _root(root) / "session.json"


def describe_hooks() -> dict[str, str]:
    """Return ACP hook → description map (for CLI / docs)."""
    return dict(ACP_HOOKS)


@dataclass
class SessionStatus:
    """Thin session snapshot for TUI/ACP status."""

    session_id: str | None = None
    started: str | None = None
    prompt: str | None = None
    last_traj_path: str | None = None
    last_episode_id: str | None = None
    harness_id: str | None = None
    harness_routing: str | None = None
    l2_weights_id: str | None = None
    l2_artifact_present: bool = False
    workspace: str | None = None
    worldline_count: int | None = None
    hooks: dict[str, str] = field(default_factory=describe_hooks)
    honesty: dict[str, Any] = field(
        default_factory=lambda: {
            "incr_proven": False,
            "fiber_live": False,
            "l3_online": False,
            "l2_stub_metadata_only": True,
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def find_last_trajectory(
    search_roots: list[Path] | None = None,
) -> Path | None:
    """Newest ``*.jsonl`` under trajectories/ or `.aura-build/`."""
    roots = search_roots or [
        Path.cwd() / "trajectories",
        default_root(),
    ]
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix == ".jsonl":
            candidates.append(root)
            continue
        candidates.extend(root.rglob("*.jsonl"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _last_episode(traj: Path | None) -> dict[str, Any] | None:
    if traj is None or not traj.is_file():
        return None
    last: dict[str, Any] | None = None
    for line in traj.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            last = obj
    return last


def acp_start_session(
    *,
    prompt: str | None = None,
    root: Path | str | None = None,
    workspace: Path | str | None = None,
    episode_id: str | None = None,
    traj_path: Path | str | None = None,
) -> SessionStatus:
    """Create/refresh session marker under `.aura-build/session.json`."""
    r = _root(root)
    r.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    sp = session_path(r)
    if sp.is_file():
        try:
            existing = json.loads(sp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = {}
    session_id = existing.get("session_id") or f"sess-{_utc_now().replace(':', '')[:15]}"
    payload = {
        "session_id": session_id,
        "started": existing.get("started") or _utc_now(),
        "updated": _utc_now(),
        "prompt": prompt if prompt is not None else existing.get("prompt"),
        "workspace": str(workspace) if workspace is not None else existing.get("workspace"),
        "last_episode_id": episode_id or existing.get("last_episode_id"),
        "last_traj_path": (
            str(traj_path) if traj_path is not None else existing.get("last_traj_path")
        ),
    }
    sp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return acp_status(root=r)


def acp_status(
    *,
    root: Path | str | None = None,
    traj_search: list[Path] | None = None,
) -> SessionStatus:
    """Assemble session + harness + last traj status."""
    r = _root(root)
    status = SessionStatus()
    sp = session_path(r)
    if sp.is_file():
        try:
            data = json.loads(sp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        status.session_id = data.get("session_id")
        status.started = data.get("started")
        status.prompt = data.get("prompt")
        status.workspace = data.get("workspace")
        status.last_episode_id = data.get("last_episode_id")
        status.last_traj_path = data.get("last_traj_path")

    try:
        h = load_harness(r)
        status.harness_id = h.harness_id
        status.harness_routing = h.routing
        status.l2_weights_id = h.l2_weights_id
        status.worldline_count = h.worldline_count
    except Exception:
        pass

    if status.l2_weights_id:
        ref = resolve_l2_weights(status.l2_weights_id, root=r)
        if ref is not None:
            status.l2_artifact_present = ref.artifact_present

    traj = None
    if status.last_traj_path:
        p = Path(status.last_traj_path)
        if p.is_file():
            traj = p
    if traj is None:
        traj = find_last_trajectory(traj_search)
    if traj is not None:
        status.last_traj_path = str(traj)
        ep = _last_episode(traj)
        if ep:
            status.last_episode_id = status.last_episode_id or ep.get("episode_id")
            if status.worldline_count is None:
                status.worldline_count = len(ep.get("worldlines") or [])

    return status


def acp_list_worldlines(
    *,
    root: Path | str | None = None,
    workspace: Path | str | None = None,
    traj_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List worldlines from workspace meta.json or last trajectory episode."""
    if workspace is not None:
        ws_path = Path(workspace)
        meta = ws_path / "meta.json"
        if meta.is_file():
            data = json.loads(meta.read_text(encoding="utf-8"))
            out: list[dict[str, Any]] = []
            parent = data.get("parent")
            if isinstance(parent, dict):
                out.append({"role": "parent", **parent})
            for cid, cref in (data.get("candidates") or {}).items():
                if isinstance(cref, dict):
                    out.append({"role": "candidate", "id": cid, **cref})
                else:
                    out.append({"role": "candidate", "id": cid, "stable_ref": cref})
            for d in data.get("discarded") or []:
                if isinstance(d, dict):
                    out.append({"role": "discarded", **d})
            return out
        # Try loading as WorldlineWorkspace
        try:
            ws = WorldlineWorkspace.load(ws_path)
            rows = [
                {"role": "parent", **ws.parent.to_dict()},
            ]
            for cid, ref in ws.candidates.items():
                rows.append({"role": "candidate", "id": cid, **ref.to_dict()})
            for d in ws.discarded:
                rows.append({"role": "discarded", **d.to_dict()})
            return rows
        except Exception:
            pass

    traj = Path(traj_path) if traj_path else find_last_trajectory()
    ep = _last_episode(traj)
    if not ep:
        return []
    rows = []
    selected = ep.get("selected_id")
    for w in ep.get("worldlines") or []:
        if not isinstance(w, dict):
            continue
        rows.append(
            {
                "role": "selected" if w.get("id") == selected else "candidate",
                "id": w.get("id"),
                "parent_id": w.get("parent_id"),
                "stable_ref": w.get("stable_ref"),
                "fitness": (w.get("eval") or {}).get("fitness"),
            }
        )
    for d in ep.get("discarded") or []:
        if isinstance(d, dict):
            rows.append({"role": "discarded", **d})
    return rows


def acp_promote_l2(
    weights_id: str,
    *,
    notes: str = "",
    root: Path | str | None = None,
    export_path: Path | str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """ACP promote hook → offline L2 metadata only."""
    ref = promote_l2_offline(
        weights_id,
        notes=notes,
        root=_root(root),
        export_path=export_path,
        overwrite=overwrite,
    )
    return ref.to_dict()


def acp_discard_worldline(
    ref_id: str,
    *,
    workspace: Path | str,
    reason: str = "acp_discard",
    fitness: float | None = None,
) -> dict[str, Any]:
    """Mark a candidate discarded in a shared workspace (audit flag)."""
    ws = WorldlineWorkspace.load(Path(workspace))
    ws.discard(ref_id, reason=reason, fitness=fitness)
    ws.save_meta()
    return {
        "discarded": ref_id,
        "reason": reason,
        "workspace": str(workspace),
        "fiber_live": False,
    }


def acp_export_hint() -> str:
    """Documented CLI wire-up for export hook."""
    return "aura-build export --out trajectories/export.json"


def list_weights_summary(root: Path | str | None = None) -> list[dict[str, Any]]:
    return [r.to_dict() for r in list_l2_artifacts(root=_root(root))]


# Re-export error for CLI
__all__ += ["L2PromoteError", "list_weights_summary"]
