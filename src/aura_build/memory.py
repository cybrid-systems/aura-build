"""Thin host memory JSON I/O (product memory is aura/memory.aura)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryNote:
    profile: str
    key: str
    value: Any
    updated: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "key": self.key,
            "value": self.value,
            "updated": self.updated,
        }


class MemoryStore:
    """Per-profile JSON notes under ``root/<profile>.json``."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, profile: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in profile) or "default"
        return self.root / f"{safe}.json"

    def _load(self, profile: str) -> dict[str, Any]:
        p = self._path(profile)
        if not p.is_file():
            return {}
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def _save(self, profile: str, data: dict[str, Any]) -> None:
        self._path(profile).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def get(self, profile: str, key: str) -> Any | None:
        notes = self._load(profile).get("notes") or {}
        if not isinstance(notes, dict) or key not in notes:
            return None
        entry = notes[key]
        if isinstance(entry, dict) and "value" in entry:
            return entry["value"]
        return entry

    def set(self, profile: str, key: str, value: Any) -> MemoryNote:
        data = self._load(profile)
        notes = data.setdefault("notes", {})
        if not isinstance(notes, dict):
            notes = {}
            data["notes"] = notes
        note = MemoryNote(profile=profile, key=key, value=value, updated=_utc_now())
        notes[key] = {"value": value, "updated": note.updated}
        data["profile"] = profile
        self._save(profile, data)
        return note

    def list_notes(self, profile: str) -> dict[str, Any]:
        return self._load(profile).get("notes") or {}


def host_cli(
    op: str,
    *,
    root: Path,
    profile: str = "default",
    key: str = "",
    value: str = "",
    json_value: bool = False,
) -> int:
    """Thin host memory I/O when Aura kernel is unavailable."""
    store = MemoryStore(root=root / "memory")
    if op == "get":
        val = store.get(profile, key)
        if val is None:
            print("null")
            return 1
        print(json.dumps(val, ensure_ascii=False) if not isinstance(val, str) else val)
        return 0
    if op == "set":
        parsed: Any = value
        if json_value:
            parsed = json.loads(value)
        note = store.set(profile, key, parsed)
        print(json.dumps(note.to_dict(), ensure_ascii=False))
        return 0
    if op == "list":
        notes = store.list_notes(profile)
        print(json.dumps(notes, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    return 2
