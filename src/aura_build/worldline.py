"""Worldline API (M2): parent snapshot → N candidates with stable refs.

Honesty
-------
This module models **shared-workspace candidate refs**, not fiber-live FlatAST
multi-worldline concurrency. Losers are discarded in the trajectory record;
winners keep a stable ref under a shared workspace directory.

Session model (also written into trajectory ``runtime.session_model``):

- ``shared_workspace_subprocess`` — default M2: one workspace dir, still one
  subprocess (or simulated eval) per candidate. Prefer this over N unrelated
  cold shells / git worktrees.
- ``long_lived_aura`` — reserved for a future single Aura process that hosts
  multiple evals; not claimed until a real long-lived session exists.

Do **not** read ``stable_ref`` presence as proof of fiber-live worldlines.
"""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SESSION_SHARED_SUBPROCESS = "shared_workspace_subprocess"
SESSION_LONG_LIVED_AURA = "long_lived_aura"


@dataclass
class StableRef:
    """Stable identifier for a candidate on the shared workspace."""

    ref_id: str
    parent_ref: str | None
    workspace_relpath: str
    kind: str = "candidate"  # parent | candidate

    def to_dict(self) -> dict[str, Any]:
        return {
            "ref_id": self.ref_id,
            "parent_ref": self.parent_ref,
            "workspace_relpath": self.workspace_relpath,
            "kind": self.kind,
        }


@dataclass
class DiscardRecord:
    """Documented loser from select-best (trajectory first-class)."""

    id: str
    reason: str
    fitness: float | None = None
    stable_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "reason": self.reason,
            "fitness": self.fitness,
            "stable_ref": self.stable_ref,
        }


@dataclass
class WorldlineWorkspace:
    """Shared workspace for parent → N-candidate fan-out.

    Layout::

        <root>/
          meta.json
          parent/          # parent snapshot marker
          candidates/
            wl-0/
            wl-1/
            ...
    """

    root: Path
    parent: StableRef
    candidates: dict[str, StableRef] = field(default_factory=dict)
    discarded: list[DiscardRecord] = field(default_factory=list)
    session_model: str = SESSION_SHARED_SUBPROCESS
    episode_token: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    @classmethod
    def create(
        cls,
        root: Path | str,
        *,
        n_candidates: int = 3,
        session_model: str = SESSION_SHARED_SUBPROCESS,
        parent_id: str = "wl-parent",
    ) -> WorldlineWorkspace:
        """Create parent snapshot + N candidate dirs with stable refs."""
        root_p = Path(root)
        if n_candidates < 1:
            raise ValueError("n_candidates must be >= 1")
        if session_model not in (SESSION_SHARED_SUBPROCESS, SESSION_LONG_LIVED_AURA):
            raise ValueError(f"unknown session_model: {session_model!r}")

        root_p.mkdir(parents=True, exist_ok=True)
        parent_dir = root_p / "parent"
        parent_dir.mkdir(exist_ok=True)
        (parent_dir / "SNAPSHOT").write_text(
            f"parent_id={parent_id}\n", encoding="utf-8"
        )

        parent = StableRef(
            ref_id=parent_id,
            parent_ref=None,
            workspace_relpath="parent",
            kind="parent",
        )
        ws = cls(
            root=root_p,
            parent=parent,
            session_model=session_model,
        )
        cand_root = root_p / "candidates"
        cand_root.mkdir(exist_ok=True)
        for i in range(n_candidates):
            cid = f"wl-{i}"
            rel = f"candidates/{cid}"
            (root_p / rel).mkdir(parents=True, exist_ok=True)
            marker = root_p / rel / "REF"
            marker.write_text(
                f"ref_id={cid}\nparent_ref={parent_id}\n", encoding="utf-8"
            )
            ws.candidates[cid] = StableRef(
                ref_id=cid,
                parent_ref=parent_id,
                workspace_relpath=rel,
                kind="candidate",
            )
        ws._write_meta()
        return ws

    def path_for(self, ref_id: str) -> Path:
        if ref_id == self.parent.ref_id:
            return self.root / self.parent.workspace_relpath
        if ref_id not in self.candidates:
            raise KeyError(f"unknown worldline ref: {ref_id!r}")
        return self.root / self.candidates[ref_id].workspace_relpath

    def fork_note(self, ref_id: str, summary: str) -> dict[str, Any]:
        """Record a mutation note on a candidate (filesystem + return dict)."""
        ref = self.candidates[ref_id]
        note_path = self.root / ref.workspace_relpath / "mutation.json"
        payload = {
            "op": "worldline_fork",
            "target_id": f"stable:{ref.ref_id}",
            "summary": summary,
            "parent_ref": ref.parent_ref,
            "stable_ref": ref.ref_id,
            "workspace_relpath": ref.workspace_relpath,
        }
        note_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return payload

    def discard(self, ref_id: str, *, reason: str, fitness: float | None = None) -> None:
        """Mark a loser; keep dir for audit but record discard in meta."""
        if ref_id not in self.candidates:
            raise KeyError(f"unknown worldline ref: {ref_id!r}")
        ref = self.candidates[ref_id]
        rec = DiscardRecord(
            id=ref_id,
            reason=reason,
            fitness=fitness,
            stable_ref=ref.ref_id,
        )
        self.discarded.append(rec)
        discard_flag = self.root / ref.workspace_relpath / "DISCARDED"
        discard_flag.write_text(
            json.dumps(rec.to_dict(), indent=2) + "\n", encoding="utf-8"
        )
        self._write_meta()

    def discard_losers(
        self,
        selected_id: str,
        fitness_by_id: dict[str, float],
        *,
        reason: str = "lower_fitness",
    ) -> list[DiscardRecord]:
        """Discard every candidate except ``selected_id``; return records."""
        out: list[DiscardRecord] = []
        for cid in list(self.candidates):
            if cid == selected_id:
                continue
            self.discard(
                cid,
                reason=reason,
                fitness=fitness_by_id.get(cid),
            )
            out.append(self.discarded[-1])
        return out

    def to_runtime_fields(self) -> dict[str, Any]:
        """Fields merged into episode ``runtime`` for honesty / replay."""
        return {
            "workspace": str(self.root.resolve()),
            "session_model": self.session_model,
            "parent_ref": self.parent.ref_id,
            "stable_refs": [r.to_dict() for r in self.candidates.values()],
            "incr_proven": False,
        }

    def _write_meta(self) -> None:
        meta = {
            "episode_token": self.episode_token,
            "session_model": self.session_model,
            "parent": self.parent.to_dict(),
            "candidates": {k: v.to_dict() for k, v in self.candidates.items()},
            "discarded": [d.to_dict() for d in self.discarded],
            "incr_proven": False,
            "honesty": (
                "shared workspace + stable refs; not fiber-live FlatAST; "
                "incr_proven=false until storm-still-incr is measured"
            ),
        }
        (self.root / "meta.json").write_text(
            json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


    @classmethod
    def load(cls, root: Path | str) -> "WorldlineWorkspace":
        """Reload workspace from ``meta.json`` (ACP / TUI status)."""
        root_p = Path(root)
        meta_path = root_p / "meta.json"
        if not meta_path.is_file():
            raise FileNotFoundError(f"workspace meta not found: {meta_path}")
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        parent_raw = data.get("parent") or {}
        parent = StableRef(
            ref_id=str(parent_raw.get("ref_id") or "wl-parent"),
            parent_ref=parent_raw.get("parent_ref"),
            workspace_relpath=str(parent_raw.get("workspace_relpath") or "parent"),
            kind=str(parent_raw.get("kind") or "parent"),
        )
        candidates: dict[str, StableRef] = {}
        for cid, raw in (data.get("candidates") or {}).items():
            if not isinstance(raw, dict):
                continue
            candidates[str(cid)] = StableRef(
                ref_id=str(raw.get("ref_id") or cid),
                parent_ref=raw.get("parent_ref"),
                workspace_relpath=str(
                    raw.get("workspace_relpath") or f"candidates/{cid}"
                ),
                kind=str(raw.get("kind") or "candidate"),
            )
        discarded: list[DiscardRecord] = []
        for d in data.get("discarded") or []:
            if not isinstance(d, dict):
                continue
            discarded.append(
                DiscardRecord(
                    id=str(d.get("id")),
                    reason=str(d.get("reason") or "discarded"),
                    fitness=d.get("fitness"),
                    stable_ref=d.get("stable_ref"),
                )
            )
        ws = cls(
            root=root_p,
            parent=parent,
            candidates=candidates,
            discarded=discarded,
            session_model=str(
                data.get("session_model") or SESSION_SHARED_SUBPROCESS
            ),
            episode_token=str(data.get("episode_token") or uuid.uuid4().hex[:12]),
        )
        return ws

    def save_meta(self) -> None:
        """Public alias for persisting workspace meta (ACP discard)."""
        self._write_meta()


def cleanup_workspace(root: Path | str, *, missing_ok: bool = True) -> None:
    """Remove a workspace tree (tests / ephemeral runs)."""
    p = Path(root)
    if p.exists():
        shutil.rmtree(p)
    elif not missing_ok:
        raise FileNotFoundError(p)
