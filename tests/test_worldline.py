"""M2 WorldlineWorkspace: parent → N candidates, discard losers."""

from __future__ import annotations

from pathlib import Path

import pytest

from aura_build.worldline import (
    SESSION_SHARED_SUBPROCESS,
    WorldlineWorkspace,
    cleanup_workspace,
)


def test_create_parent_and_candidates(tmp_path: Path):
    ws = WorldlineWorkspace.create(tmp_path / "ws", n_candidates=3)
    assert ws.parent.ref_id == "wl-parent"
    assert ws.parent.parent_ref is None
    assert set(ws.candidates) == {"wl-0", "wl-1", "wl-2"}
    for cid, ref in ws.candidates.items():
        assert ref.parent_ref == "wl-parent"
        assert (ws.root / ref.workspace_relpath / "REF").is_file()
        assert ref.kind == "candidate"
    assert ws.session_model == SESSION_SHARED_SUBPROCESS
    meta = (ws.root / "meta.json").read_text()
    assert "incr_proven" in meta
    assert '"incr_proven": false' in meta.lower() or '"incr_proven": false' in meta


def test_fork_note_and_discard(tmp_path: Path):
    ws = WorldlineWorkspace.create(tmp_path / "ws", n_candidates=2)
    note = ws.fork_note("wl-0", summary="edit A")
    assert note["op"] == "worldline_fork"
    assert note["stable_ref"] == "wl-0"
    assert (ws.path_for("wl-0") / "mutation.json").is_file()

    ws.discard("wl-1", reason="lower_fitness", fitness=0.1)
    assert len(ws.discarded) == 1
    assert ws.discarded[0].id == "wl-1"
    assert (ws.path_for("wl-1") / "DISCARDED").is_file()


def test_discard_losers(tmp_path: Path):
    ws = WorldlineWorkspace.create(tmp_path / "ws", n_candidates=3)
    recs = ws.discard_losers("wl-1", {"wl-0": 0.2, "wl-1": 0.9, "wl-2": 0.4})
    assert {r.id for r in recs} == {"wl-0", "wl-2"}
    assert all(r.reason == "lower_fitness" for r in recs)


def test_runtime_fields_honest(tmp_path: Path):
    ws = WorldlineWorkspace.create(tmp_path / "ws", n_candidates=2)
    fields = ws.to_runtime_fields()
    assert fields["session_model"] == SESSION_SHARED_SUBPROCESS
    assert fields["incr_proven"] is False
    assert fields["parent_ref"] == "wl-parent"
    assert len(fields["stable_refs"]) == 2


def test_cleanup(tmp_path: Path):
    root = tmp_path / "gone"
    WorldlineWorkspace.create(root, n_candidates=1)
    assert root.exists()
    cleanup_workspace(root)
    assert not root.exists()


def test_rejects_zero_candidates(tmp_path: Path):
    with pytest.raises(ValueError):
        WorldlineWorkspace.create(tmp_path / "ws", n_candidates=0)
