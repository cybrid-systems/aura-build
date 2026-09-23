"""M3 file-backed memory store."""

from __future__ import annotations

from pathlib import Path

from aura_build.memory import MemoryStore
from aura_build.orch import OrchConfig, memory_update, run_episode


def test_memory_set_get_list(tmp_path: Path):
    store = MemoryStore(root=tmp_path / "memory")
    store.set("user:alice", "pref", "anti-postman")
    assert store.get("user:alice", "pref") == "anti-postman"
    notes = store.list_notes("user:alice")
    assert "pref" in notes
    assert store.get("user:alice", "missing") is None


def test_memory_update_via_orch(tmp_path: Path):
    root = tmp_path / ".aura-build"
    written = memory_update(
        "default",
        {"hint": "stable-ref", "n": 2},
        root=root,
        mid="mid-test",
    )
    assert len(written) == 2
    store = MemoryStore(root=root / "memory")
    assert store.get("default", "hint") == "stable-ref"
    assert store.get("default", "n") == 2
    entry = store.list_notes("default")["hint"]
    assert entry["mid"] == "mid-test"


def test_run_episode_updates_memory_profile(tmp_path: Path):
    root = tmp_path / ".aura-build"
    result = run_episode(
        "memory touch",
        OrchConfig(
            seed=3,
            n_worldlines=2,
            memory_profile="ci-profile",
            harness_root=root,
        ),
    )
    store = MemoryStore(root=root / "memory")
    assert store.get("ci-profile", "last_selected_id") == result.selected.id
    assert result.episode["memory"]["profile_id"] == "ci-profile"
