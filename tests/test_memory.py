"""Thin host MemoryStore JSON I/O."""

from __future__ import annotations

from pathlib import Path

from aura_build.memory import MemoryStore


def test_memory_roundtrip(tmp_path: Path):
    store = MemoryStore(tmp_path / "memory")
    store.set("smoke", "demo", "anti-postman")
    assert store.get("smoke", "demo") == "anti-postman"
    notes = store.list_notes("smoke")
    assert "demo" in notes
