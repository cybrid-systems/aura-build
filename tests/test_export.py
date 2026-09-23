"""Host Parquet adapter only — JSON+redaction is aura/export.aura."""

from __future__ import annotations

from pathlib import Path

import pytest

from aura_build.export import episodes_from_json_array, write_parquet
from aura_build.schema import SCHEMA_VERSION


def _sample_episode(**overrides) -> dict:
    ep = {
        "schema_version": SCHEMA_VERSION,
        "episode_id": "ep-test-1",
        "ts_start": "2026-01-01T00:00:00+00:00",
        "ts_end": "2026-01-01T00:00:01+00:00",
        "prompt": "demo",
        "runtime": {
            "mode": "simulated",
            "kernel": "aura",
            "incr_proven": False,
            "fiber_live": False,
        },
        "harness": {"l3_online": False, "actions": []},
        "worldlines": [
            {"id": "wl-0", "eval": {"fitness": 0.9}, "mutations": [{"summary": "noop"}]},
            {"id": "wl-1", "eval": {"fitness": 0.5}, "mutations": [{"summary": "noop"}]},
        ],
        "selected_id": "wl-0",
        "privacy": {"redacted": True, "retention_class": "dogfood"},
    }
    ep.update(overrides)
    return ep


def test_episodes_from_json_array(tmp_path: Path):
    path = tmp_path / "export.json"
    import json

    path.write_text(json.dumps([_sample_episode()]), encoding="utf-8")
    eps = episodes_from_json_array(path)
    assert len(eps) == 1
    assert eps[0]["episode_id"] == "ep-test-1"


def test_write_parquet_optional(tmp_path: Path):
    eps = [_sample_episode()]
    pq = tmp_path / "out.parquet"
    path, reason = write_parquet(eps, pq)
    if path is None:
        assert reason
        pytest.skip(reason)
    assert path.is_file()


def test_cli_export_refuses_without_aura(tmp_path: Path, monkeypatch):
    from aura_build.cli import main

    monkeypatch.setenv("AURA_BUILD_FORCE_PYTHON", "1")
    rc = main(
        [
            "export",
            "--out",
            str(tmp_path / "x.json"),
            "--no-parquet",
        ]
    )
    assert rc == 2
