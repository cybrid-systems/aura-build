"""M5 L2 offline metadata artifact + promote gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aura_build.l2_weights import (
    L2PromoteError,
    list_l2_artifacts,
    load_l2_artifact,
    promote_l2_offline,
    resolve_l2_weights,
)
from aura_build.orch import OrchConfig, run_episode
from aura_build.schema import validate_episode


def test_resolve_none():
    assert resolve_l2_weights(None) is None
    assert resolve_l2_weights("") is None
    assert resolve_l2_weights("null") is None


def test_resolve_stub_by_id_no_artifact(tmp_path: Path):
    root = tmp_path / ".aura-build"
    ref = resolve_l2_weights("specialist.compile.v0", root=root)
    assert ref is not None
    assert ref.weights_id == "specialist.compile.v0"
    assert ref.loaded is True
    assert ref.stub is True
    assert ref.artifact_present is False


def test_load_and_promote_metadata(tmp_path: Path):
    root = tmp_path / ".aura-build"
    ref = promote_l2_offline(
        "specialist.stub.v0",
        notes="demo metadata",
        root=root,
        created="2026-09-23T00:00:00+00:00",
    )
    assert ref.stub is True
    assert ref.artifact_present is True
    assert ref.created == "2026-09-23T00:00:00+00:00"
    assert "demo metadata" in ref.notes
    path = Path(ref.artifact_path)
    assert path.is_file()
    data = json.loads(path.read_text())
    assert data == {
        "created": "2026-09-23T00:00:00+00:00",
        "id": "specialist.stub.v0",
        "notes": "demo metadata",
    }

    loaded = load_l2_artifact("specialist.stub.v0", root=root)
    assert loaded is not None
    assert loaded.artifact_present is True
    assert loaded.stub is True

    resolved = resolve_l2_weights("specialist.stub.v0", root=root)
    assert resolved is not None
    assert resolved.artifact_present is True

    listed = list_l2_artifacts(root=root)
    assert len(listed) == 1
    assert listed[0].weights_id == "specialist.stub.v0"


def test_promote_refuses_l3_online_export(tmp_path: Path):
    root = tmp_path / ".aura-build"
    export = tmp_path / "export.json"
    export.write_text(
        json.dumps(
            [
                {
                    "episode_id": "ep-ok",
                    "harness": {"l3_online": False},
                },
                {
                    "episode_id": "ep-bad",
                    "harness": {"l3_online": True},
                },
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(L2PromoteError, match="l3_online"):
        promote_l2_offline(
            "specialist.from.export",
            root=root,
            export_path=export,
        )
    assert not (root / "weights" / "specialist.from.export.json").exists()


def test_promote_accepts_clean_export(tmp_path: Path):
    root = tmp_path / ".aura-build"
    export = tmp_path / "export.json"
    export.write_text(
        json.dumps([{"episode_id": "ep-ok", "harness": {"l3_online": False}}]),
        encoding="utf-8",
    )
    ref = promote_l2_offline(
        "specialist.clean.v0",
        root=root,
        export_path=export,
        notes="gated",
    )
    assert ref.artifact_present is True
    assert ref.stub is True


def test_episode_records_l2_ref_with_artifact(tmp_path: Path):
    root = tmp_path / ".aura-build"
    promote_l2_offline("specialist.demo.v0", notes="from test", root=root)
    result = run_episode(
        "l2 stub",
        OrchConfig(
            seed=5,
            n_worldlines=2,
            l2_weights_id="specialist.demo.v0",
            harness_root=root,
        ),
    )
    validate_episode(result.episode)
    assert result.episode["harness"]["l2_weights_id"] == "specialist.demo.v0"
    assert result.episode["harness"]["l2_ref"]["stub"] is True
    assert result.episode["harness"]["l2_ref"]["artifact_present"] is True
    assert result.episode["runtime"]["incr_proven"] is False


def test_refuse_unsafe_id(tmp_path: Path):
    with pytest.raises(L2PromoteError):
        promote_l2_offline("../etc/passwd", root=tmp_path / ".aura-build")
