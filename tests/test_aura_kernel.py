"""Aura kernel integration — skip cleanly when aura binary unavailable."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from aura_build.kernel import invoke_aura_kernel, kernel_available
from aura_build.schema import validate_episode

pytestmark = pytest.mark.skipif(
    not kernel_available()[0],
    reason="Aura binary/kernel unavailable",
)


def test_kernel_simulated_run(tmp_path: Path) -> None:
    out = tmp_path / "ep.jsonl"
    result = invoke_aura_kernel(
        "run",
        {
            "AURA_BUILD_PROMPT": "pytest kernel run",
            "AURA_BUILD_MODE": "simulated",
            "AURA_BUILD_SEED": "1",
            "AURA_BUILD_WORLDLINES": "3",
            "AURA_BUILD_OUT": str(out),
            "AURA_BUILD_ATTACH_PROVE": "1",
        },
        harness_root=tmp_path,
    )
    assert result.via == "aura"
    assert result.ok
    assert out.is_file()
    ep = json.loads(out.read_text().splitlines()[0])
    validate_episode(ep)
    assert ep["runtime"]["mode"] == "simulated"
    assert ep["runtime"].get("kernel") == "aura"
    assert ep["runtime"]["incr_proven"] is False
    assert ep["runtime"]["fiber_live"] is False
    assert "prove_incr" in ep["runtime"]


def test_kernel_prove_incr_honest(tmp_path: Path) -> None:
    result = invoke_aura_kernel(
        "prove-incr",
        {
            "AURA_BUILD_CYCLES": "2",
            "AURA_BUILD_WORLDLINES": "1",
        },
        harness_root=tmp_path,
    )
    assert result.via == "aura"
    report_path = tmp_path / "prove-incr-latest.json"
    assert report_path.is_file()
    report = json.loads(report_path.read_text())
    assert report["measured"] is True
    assert report["aura_healthy"] is True
    assert report["incr_proven"] is True
    assert report["fiber_live"] is False
    assert report["cycles_incr_valid"] == report["cycles_completed"]


def test_kernel_env_cannot_elevate_fiber(tmp_path: Path) -> None:
    # Write a refuse report, then run with fiber env — still false
    (tmp_path / "prove-incr-latest.json").write_text(
        json.dumps(
            {
                "schema_version": "prove_incr.v0",
                "incr_proven": False,
                "measured": False,
                "fiber_live": False,
                "session_model": "shared_workspace_subprocess",
                "reason": "fixture_refuse",
                "ts": "2026-01-01T00:00:00Z",
            }
        )
    )
    out = tmp_path / "ep.jsonl"
    env = os.environ.copy()
    # invoke_aura_kernel merges env_vars into subprocess env
    result = invoke_aura_kernel(
        "run",
        {
            "AURA_BUILD_PROMPT": "env gate",
            "AURA_BUILD_MODE": "simulated",
            "AURA_BUILD_SEED": "7",
            "AURA_BUILD_WORLDLINES": "2",
            "AURA_BUILD_OUT": str(out),
            "AURA_BUILD_ATTACH_PROVE": "1",
            "AURA_BUILD_INCR_VALID": "1",
            "AURA_BUILD_FIBER_SESSION_OK": "1",
        },
        harness_root=tmp_path,
    )
    assert result.ok
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["runtime"]["incr_proven"] is False
    assert ep["runtime"]["fiber_live"] is False
    notes = ep["runtime"]["prove_incr"].get("env_notes") or []
    assert "env_ignored_unproven" in notes
    assert "env_fiber_ignored_unproven" in notes


def test_kernel_harness_mutate_discard(tmp_path: Path) -> None:
    out = tmp_path / "ep.jsonl"
    result = invoke_aura_kernel(
        "harness-mutate",
        {
            "AURA_BUILD_PROMPT": "pytest harness canary",
            "AURA_BUILD_SEED": "1",
            "AURA_BUILD_OUT": str(out),
            "AURA_BUILD_HARNESS_PATCHES": '{"worldline_count": 4}',
            "AURA_BUILD_FITNESS_PATCHES": "{}",
            # FLAG unset → AUTOPROMOTE env alone; default OFF → discard
        },
        harness_root=tmp_path,
    )
    assert result.via == "aura"
    assert result.ok
    assert result.exit_code == 0
    assert out.is_file()
    ep = json.loads(out.read_text().splitlines()[0])
    validate_episode(ep)
    assert ep["runtime"].get("kernel") == "aura"
    assert ep["runtime"]["fiber_live"] is False
    assert ep["harness"]["outcome"] == "discard"
    assert ep["harness"]["committed"] is False
    assert ep["harness"]["autopropote"] is False


def test_kernel_harness_mutate_autopropote_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("AURA_BUILD_FORCE_PYTHON", raising=False)
    monkeypatch.setenv("AURA_BUILD_AUTOPROMOTE", "1")
    out = tmp_path / "ep.jsonl"
    result = invoke_aura_kernel(
        "harness-mutate",
        {
            "AURA_BUILD_PROMPT": "promote via env",
            "AURA_BUILD_SEED": "3",
            "AURA_BUILD_OUT": str(out),
            "AURA_BUILD_HARNESS_PATCHES": '{"routing": "auto"}',
            "AURA_BUILD_FITNESS_PATCHES": "{}",
            # no AURA_BUILD_AUTOPROMOTE_FLAG — env must win
        },
        harness_root=tmp_path,
    )
    assert result.via == "aura"
    assert result.exit_code == 0
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["runtime"]["kernel"] == "aura"
    assert ep["harness"]["outcome"] == "commit"
    assert ep["harness"]["committed"] is True
    harness_path = tmp_path / "harness.json"
    assert harness_path.is_file()
    cfg = json.loads(harness_path.read_text())
    assert cfg["routing"] == "auto"


def test_kernel_harness_mutate_heal_bad_l1(tmp_path: Path) -> None:
    out = tmp_path / "ep.jsonl"
    result = invoke_aura_kernel(
        "harness-mutate",
        {
            "AURA_BUILD_PROMPT": "bad L1",
            "AURA_BUILD_OUT": str(out),
            "AURA_BUILD_HARNESS_PATCHES": '{"worldline_count": 0}',
            "AURA_BUILD_FITNESS_PATCHES": "{}",
        },
        harness_root=tmp_path,
    )
    assert result.via == "aura"
    assert result.exit_code == 1
    assert result.response.get("accepted") is False
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["runtime"]["kernel"] == "aura"
    assert ep["harness"]["outcome"] == "heal"


def test_kernel_doctor(tmp_path: Path) -> None:
    # Seed a refuse report so honesty stays false
    (tmp_path / "prove-incr-latest.json").write_text(
        json.dumps(
            {
                "schema_version": "prove_incr.v0",
                "incr_proven": False,
                "measured": False,
                "fiber_live": False,
                "session_model": "shared_workspace_subprocess",
                "reason": "fixture_refuse",
                "ts": "2026-01-01T00:00:00Z",
            }
        )
    )
    result = invoke_aura_kernel("doctor", {}, harness_root=tmp_path)
    assert result.via == "aura"
    assert result.ok
    snap = result.response.get("snapshot") or {}
    honesty = snap.get("honesty") or {}
    assert honesty.get("incr_proven") is False
    assert honesty.get("fiber_live") is False


def test_kernel_harness_show(tmp_path: Path) -> None:
    result = invoke_aura_kernel("harness-show", {}, harness_root=tmp_path)
    assert result.via == "aura"
    assert result.ok
    h = result.response.get("harness") or {}
    assert h.get("harness_id") == "default"
    assert int(h.get("worldline_count", 0)) >= 1


def test_cli_harness_mutate_autopropote_env(tmp_path: Path, monkeypatch) -> None:
    """Thin host must not force AUTOPROMOTE_FLAG=0 (env alone can promote)."""
    from aura_build.cli import main

    monkeypatch.delenv("AURA_BUILD_FORCE_PYTHON", raising=False)
    monkeypatch.setenv("AURA_BUILD_AUTOPROMOTE", "1")
    out = tmp_path / "ep.jsonl"
    rc = main(
        [
            "harness-mutate",
            "--prompt",
            "cli promote env",
            "--seed",
            "5",
            "--set",
            "worldline_count=4",
            "--harness-root",
            str(tmp_path),
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["runtime"].get("kernel") == "aura"
    assert ep["harness"]["outcome"] == "commit"
    assert ep["harness"]["committed"] is True


def test_kernel_export_redacts(tmp_path: Path) -> None:
    from aura_build.orch import OrchConfig, run_episode
    from aura_build.trajectory import TrajectoryWriter

    jsonl = tmp_path / "ep.jsonl"
    ep = run_episode(
        "kernel export", OrchConfig(seed=9, n_worldlines=2, attach_prove=False)
    ).episode
    ep["runtime"]["aura_ref"] = "/workspace/aura-grok"
    ep["prompt"] = "api_key=sk-secretvalue1234567890 path=/home/box/secret"
    TrajectoryWriter(jsonl).append(ep)
    out = tmp_path / "export.json"
    result = invoke_aura_kernel(
        "export",
        {
            "AURA_BUILD_EXPORT_CWD": str(tmp_path),
            "AURA_BUILD_EXPORT_INPUTS": str(jsonl),
            "AURA_BUILD_EXPORT_OUT": str(out),
            "AURA_BUILD_EXPORT_INCLUDE_RAW": "0",
            "AURA_BUILD_EXPORT_STRICT": "0",
            "AURA_BUILD_EXPORT_WANT_PARQUET": "0",
        },
        harness_root=tmp_path,
    )
    assert result.via == "aura"
    assert result.ok
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) == 1
    validate_episode(data[0])
    assert data[0]["privacy"]["redacted"] is True
    assert data[0]["privacy"]["export_filter"] == "m4.default"
    blob = out.read_text(encoding="utf-8")
    assert "/workspace/aura-grok" not in blob
    assert "sk-secretvalue" not in blob
    assert "/home/box" not in blob
    assert data[0]["runtime"].get("incr_proven") is False
    assert data[0]["runtime"].get("fiber_live") in (False, None)
    meta = (result.response or {}).get("result") or {}
    assert meta.get("kernel") == "aura"
    assert meta.get("redacted") is True


def test_cli_export_force_python(tmp_path: Path, monkeypatch) -> None:
    from aura_build.cli import main
    from aura_build.orch import OrchConfig, run_episode
    from aura_build.trajectory import TrajectoryWriter

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AURA_BUILD_FORCE_PYTHON", "1")
    traj = tmp_path / "trajectories"
    traj.mkdir()
    ep = run_episode(
        "force python export", OrchConfig(seed=8, n_worldlines=1, attach_prove=False)
    ).episode
    ep["runtime"]["aura_ref"] = "/workspace/keep-force"
    TrajectoryWriter(traj / "ep.jsonl").append(ep)
    out = tmp_path / "batch.json"
    rc = main(
        [
            "export",
            str(traj / "ep.jsonl"),
            "--out",
            str(out),
            "--no-parquet",
            "--json",
        ]
    )
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["privacy"]["redacted"] is True
    assert "/workspace/keep-force" not in out.read_text(encoding="utf-8")
