"""M4 trajectory export + privacy filters."""

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
from aura_build.orch import OrchConfig, run_episode
from aura_build.schema import SCHEMA_VERSION, validate_episode
from aura_build.trajectory import TrajectoryWriter


def _write_jsonl(path: Path, episodes: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for ep in episodes:
            fh.write(json.dumps(ep, ensure_ascii=False) + "\n")


def test_redact_strips_abs_paths_and_secrets():
    ep = run_episode("x", OrchConfig(seed=1, n_worldlines=2, attach_prove=False)).episode
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
    jsonl = tmp_path / "trajectories" / "a.jsonl"
    ep = run_episode(
        "export me",
        OrchConfig(
            seed=2,
            n_worldlines=2,
            workspace_dir=tmp_path / "ws",
            harness_root=tmp_path / ".aura-build",
        ),
    ).episode
    # Force an absolute path into runtime for filter check.
    ep["runtime"]["aura_ref"] = str(tmp_path / "fake-aura")
    TrajectoryWriter(jsonl).append(ep)

    out_json = tmp_path / "out" / "batch.json"
    result = export_trajectories(
        inputs=[jsonl],
        out_json=out_json,
        want_parquet=False,
        cwd=tmp_path,
    )
    assert result.stats.episodes_exported == 1
    assert result.stats.redacted is True
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) == 1
    validate_episode(data[0])
    assert data[0]["privacy"]["redacted"] is True
    blob = out_json.read_text(encoding="utf-8")
    assert str(tmp_path / "fake-aura") not in blob
    assert data[0]["runtime"].get("incr_proven") is False


def test_export_include_raw_keeps_paths(tmp_path: Path):
    jsonl = tmp_path / "e.jsonl"
    ep = run_episode("raw", OrchConfig(seed=3, n_worldlines=1, attach_prove=False)).episode
    ep["runtime"]["aura_ref"] = "/workspace/keep-me"
    TrajectoryWriter(jsonl).append(ep)
    out_json = tmp_path / "raw.json"
    result = export_trajectories(
        inputs=[jsonl],
        out_json=out_json,
        include_raw=True,
        want_parquet=False,
    )
    assert result.stats.redacted is False
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data[0]["runtime"]["aura_ref"] == "/workspace/keep-me"
    # Source episode may still have privacy.redacted=false
    assert data[0]["privacy"].get("redacted") is False


def test_collect_default_globs(tmp_path: Path):
    traj = tmp_path / "trajectories"
    traj.mkdir()
    (traj / "one.jsonl").write_text("{}\n", encoding="utf-8")
    ab = tmp_path / ".aura-build" / "trajectories"
    ab.mkdir(parents=True)
    (ab / "two.jsonl").write_text("{}\n", encoding="utf-8")
    paths = collect_jsonl_paths(cwd=tmp_path)
    names = sorted(p.name for p in paths)
    assert names == ["one.jsonl", "two.jsonl"]


def test_export_skips_invalid_line(tmp_path: Path):
    jsonl = tmp_path / "mixed.jsonl"
    good = run_episode("ok", OrchConfig(seed=4, n_worldlines=1)).episode
    _write_jsonl(jsonl, [])
    with jsonl.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(good) + "\n")
        fh.write("{not-json\n")
        fh.write(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "episode_id": "bad",
                    "ts_start": "t",
                    "ts_end": "t",
                    "prompt": "x",
                    "runtime": {"mode": "simulated"},
                    "harness": {"l3_online": False},
                    "worldlines": [],
                    "selected_id": "missing",
                }
            )
            + "\n"
        )
    result = export_trajectories(
        inputs=[jsonl],
        out_json=tmp_path / "out.json",
        want_parquet=False,
    )
    assert result.stats.episodes_exported == 1
    assert result.stats.episodes_skipped_invalid >= 1


def test_write_parquet_degrades_or_writes(tmp_path: Path):
    ep = run_episode("pq", OrchConfig(seed=5, n_worldlines=1)).episode
    path, reason = write_parquet([ep], tmp_path / "x.parquet")
    if path is None:
        assert reason is not None
        assert "pandas" in reason or "pyarrow" in reason
    else:
        assert path.exists()
        assert reason is None


def test_cli_export(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from aura_build.cli import main

    monkeypatch.chdir(tmp_path)
    traj = tmp_path / "trajectories"
    traj.mkdir()
    ep = run_episode("cli-export", OrchConfig(seed=6, n_worldlines=2)).episode
    ep["runtime"]["aura_ref"] = "/workspace/cli-aura"
    TrajectoryWriter(traj / "ep.jsonl").append(ep)
    out = tmp_path / "batch.json"
    rc = main(
        [
            "export",
            str(traj / "ep.jsonl"),
            "--out",
            str(out),
            "--no-parquet",
        ]
    )
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["privacy"]["redacted"] is True
    assert "/workspace/cli-aura" not in out.read_text(encoding="utf-8")
