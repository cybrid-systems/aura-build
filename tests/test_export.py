"""Host export adapter: redaction + JSON array (+ optional Parquet)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aura_build.export import (
    collect_jsonl_paths,
    export_trajectories,
    redact_episode,
    write_parquet,
)
from aura_build.schema import SCHEMA_VERSION, validate_episode


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
            {
                "id": "wl-0",
                "eval": {"fitness": 0.9},
                "mutations": [{"summary": "noop"}],
            },
            {
                "id": "wl-1",
                "eval": {"fitness": 0.5},
                "mutations": [{"summary": "noop"}],
            },
        ],
        "selected_id": "wl-0",
    }
    ep.update(overrides)
    return ep


def _write_jsonl(path: Path, episodes: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for ep in episodes:
            fh.write(json.dumps(ep, ensure_ascii=False) + "\n")


def test_redact_strips_abs_paths_and_secrets():
    ep = _sample_episode()
    ep["runtime"]["aura_ref"] = "/workspace/aura-grok"
    ep["runtime"]["workspace"] = "/tmp/aura-build-ws/abc"
    ep["prompt"] = "use api_key=sk-secretvalue1234567890 and Bearer tok_abc12345"
    ep["worldlines"][0]["mutations"][0]["summary"] = (
        "edit /home/box/secret/file.py with password=hunter2"
    )
    out = redact_episode(ep)
    validate_episode(out)
    assert out["privacy"]["redacted"] is True
    assert out["privacy"]["export_filter"] == "m4.default"
    assert out["runtime"]["aura_ref"] == "<redacted:path:aura-grok>"
    assert out["runtime"]["workspace"].startswith("<redacted:path:")
    assert "sk-secretvalue" not in out["prompt"]
    assert "<redacted:secret>" in out["prompt"]
    assert "/home/box" not in json.dumps(out)
    assert "hunter2" not in json.dumps(out)
    assert out["runtime"].get("incr_proven") is False
    assert out["harness"]["l3_online"] is False


def test_export_json_array_default_redact(tmp_path: Path):
    src = tmp_path / "a.jsonl"
    ep = _sample_episode()
    ep["runtime"]["workspace"] = "/secret/ws"
    _write_jsonl(src, [ep])
    out = tmp_path / "export.json"
    result = export_trajectories(
        inputs=[src],
        out_json=out,
        redact=True,
        want_parquet=False,
    )
    assert result.stats.episodes_exported == 1
    assert result.stats.redacted is True
    data = json.loads(out.read_text())
    assert isinstance(data, list) and len(data) == 1
    validate_episode(data[0])
    assert data[0]["privacy"]["redacted"] is True
    assert "/secret/ws" not in json.dumps(data)


def test_export_include_raw(tmp_path: Path):
    src = tmp_path / "a.jsonl"
    ep = _sample_episode()
    ep["runtime"]["workspace"] = "/keep/me"
    _write_jsonl(src, [ep])
    out = tmp_path / "export.json"
    result = export_trajectories(
        inputs=[src],
        out_json=out,
        include_raw=True,
        redact=False,
        want_parquet=False,
    )
    data = json.loads(out.read_text())
    assert data[0]["runtime"]["workspace"] == "/keep/me"
    assert result.stats.redacted is False


def test_collect_jsonl_paths(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    traj = tmp_path / "trajectories"
    traj.mkdir()
    f = traj / "x.jsonl"
    _write_jsonl(f, [_sample_episode()])
    found = collect_jsonl_paths(cwd=tmp_path)
    assert any(p.name == "x.jsonl" for p in found)


def test_write_parquet_optional(tmp_path: Path):
    eps = [_sample_episode()]
    pq = tmp_path / "out.parquet"
    path, reason = write_parquet(eps, pq)
    if path is None:
        assert reason
        pytest.skip(reason)
    assert path.is_file()
