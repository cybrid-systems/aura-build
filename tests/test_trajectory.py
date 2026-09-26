"""Tests for schema validation and JSONL writer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aura_build.schema import SCHEMA_VERSION, SchemaError, validate_episode
from aura_build.trajectory import TrajectoryWriter


def _minimal_episode(**overrides):
    base = {
        "schema_version": SCHEMA_VERSION,
        "episode_id": "ep-1",
        "ts_start": "2026-09-23T00:00:00+00:00",
        "ts_end": "2026-09-23T00:00:01+00:00",
        "prompt": "t",
        "runtime": {"mode": "simulated", "seed": 1},
        "harness": {"l1_strategy_id": "x", "l2_weights_id": None, "l3_online": False},
        "worldlines": [
            {
                "id": "wl-0",
                "parent_id": None,
                "mutations": [],
                "eval": {"fitness": 0.5, "passed": True, "metrics": {}, "notes": ""},
            }
        ],
        "selected_id": "wl-0",
        "selection_reason": "max_fitness",
        "privacy": {"redacted": False, "retention_class": "dogfood"},
    }
    base.update(overrides)
    return base


def test_validate_ok():
    validate_episode(_minimal_episode())


def test_validate_host_pytest():
    ep = _minimal_episode()
    ep["runtime"] = {
        "mode": "host_pytest",
        "kernel": "host",
        "fiber_live": False,
        "incr_proven": False,
        "llm_via": "host",
    }
    validate_episode(ep)


def test_validate_rejects_bad_version():
    with pytest.raises(SchemaError, match="schema_version"):
        validate_episode(_minimal_episode(schema_version="nope"))


def test_validate_rejects_bad_selected():
    with pytest.raises(SchemaError, match="selected_id"):
        validate_episode(_minimal_episode(selected_id="missing"))


def test_writer_append_and_read(tmp_path: Path):
    path = tmp_path / "e.jsonl"
    w = TrajectoryWriter(path)
    ep = _minimal_episode(prompt="hello")
    w.append(ep)
    rows = w.read_all()
    assert len(rows) == 1
    assert rows[0]["prompt"] == "hello"
    line = path.read_text(encoding="utf-8").strip()
    assert json.loads(line)["episode_id"] == ep["episode_id"]


def test_writer_rejects_invalid(tmp_path: Path):
    w = TrajectoryWriter(tmp_path / "bad.jsonl")
    with pytest.raises(SchemaError):
        w.append({"schema_version": "x"})
