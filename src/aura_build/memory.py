"""M3 memory store: per-user/profile keyed notes (file-backed JSON).

Storage layout under ``.aura-build/memory/<safe_profile>.json``.
Updated via orch helpers or the ``aura-build memory`` CLI.
Not a vector DB; not fiber-live.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aura_build.harness import default_root

__all__ = [
    "MemoryStore",
    "MemoryNote",
    "safe_profile_id",
]


_SAFE = re.compile(r"[^A-Za-z0-9._:-]+")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_profile_id(profile_id: str) -> str:
    cleaned = _SAFE.sub("_", (profile_id or "default").strip()) or "default"
    return cleaned[:128]


@dataclass
class MemoryNote:
    key: str
    value: Any
    updated_at: str
    mid: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at,
        }
        if self.mid is not None:
            d["mid"] = self.mid
        return d


@dataclass
class MemoryStore:
    """Simple keyed notes per profile / user id."""

    root: Path = field(default_factory=lambda: default_root() / "memory")

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    def path_for(self, profile_id: str) -> Path:
        return self.root / f"{safe_profile_id(profile_id)}.json"

    def _load(self, profile_id: str) -> dict[str, Any]:
        path = self.path_for(profile_id)
        if not path.is_file():
            return {
                "profile_id": safe_profile_id(profile_id),
                "notes": {},
                "updated_at": None,
            }
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"corrupt memory file: {path}")
        data.setdefault("profile_id", safe_profile_id(profile_id))
        data.setdefault("notes", {})
        return data

    def _save(self, profile_id: str, data: dict[str, Any]) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.path_for(profile_id)
        data["profile_id"] = safe_profile_id(profile_id)
        data["updated_at"] = _utc_now()
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def list_notes(self, profile_id: str) -> dict[str, Any]:
        data = self._load(profile_id)
        return dict(data.get("notes") or {})

    def get(self, profile_id: str, key: str) -> Any | None:
        notes = self.list_notes(profile_id)
        entry = notes.get(key)
        if entry is None:
            return None
        if isinstance(entry, dict) and "value" in entry:
            return entry["value"]
        return entry

    def set(
        self,
        profile_id: str,
        key: str,
        value: Any,
        *,
        mid: str | None = None,
    ) -> MemoryNote:
        if not key or not str(key).strip():
            raise ValueError("memory key must be non-empty")
        data = self._load(profile_id)
        notes = dict(data.get("notes") or {})
        note = MemoryNote(key=key, value=value, updated_at=_utc_now(), mid=mid)
        notes[key] = note.to_dict()
        data["notes"] = notes
        self._save(profile_id, data)
        return note

    def update(
        self,
        profile_id: str,
        updates: dict[str, Any],
        *,
        mid: str | None = None,
    ) -> list[MemoryNote]:
        """Batch set keys; returns notes written."""
        out: list[MemoryNote] = []
        for k, v in updates.items():
            out.append(self.set(profile_id, k, v, mid=mid))
        return out

    def delete(self, profile_id: str, key: str) -> bool:
        data = self._load(profile_id)
        notes = dict(data.get("notes") or {})
        if key not in notes:
            return False
        del notes[key]
        data["notes"] = notes
        self._save(profile_id, data)
        return True
