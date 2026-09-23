"""L2 offline metadata host helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aura_build.l2_weights import (
    L2PromoteError,
    list_l2_artifacts,
    promote_l2_offline,
    resolve_l2_weights,
)
from aura_build.schema import SCHEMA_VERSION


def _ep():
    return {
        "schema_version": SCHEMA_VERSION,
        "episode_id": "e1",
        "ts_start": "2026-01-01T00:00:00+00:00",
        "ts_end": "2026-01-01T00:00:01+00:00",
        "prompt": "x",
        "runtime": {"mode": "simulated", "incr_proven": False},
        "harness": {"l3_online": False},
        "worldlines": [{"id": "wl-0", "eval": {"fitness": 1.0}}],
        "selected_id": "wl-0",
    }


def test_promote_and_resolve(tmp_path: Path):
    ref = promote_l2_offline("specialist.stub.v0", notes="n", root=tmp_path)
    assert ref.stub is True
    assert ref.artifact_present is True
    got = resolve_l2_weights("specialist.stub.v0", root=tmp_path)
    assert got is not None
    assert got.weights_id == "specialist.stub.v0"
    ids = [r.weights_id for r in list_l2_artifacts(tmp_path)]
    assert "specialist.stub.v0" in ids


def test_promote_from_export_gates_l3(tmp_path: Path):
    export = tmp_path / "export.json"
    bad = _ep()
    bad["harness"]["l3_online"] = True
    export.write_text(json.dumps([bad]), encoding="utf-8")
    with pytest.raises(L2PromoteError):
        promote_l2_offline(
            "bad.l3",
            root=tmp_path,
            export_path=export,
        )
    good = tmp_path / "good.json"
    good.write_text(json.dumps([_ep()]), encoding="utf-8")
    ref = promote_l2_offline(
        "good.from.export",
        root=tmp_path,
        export_path=good,
        notes="ok",
    )
    assert ref.artifact_present is True
