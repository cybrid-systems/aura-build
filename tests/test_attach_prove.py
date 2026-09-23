"""Auto-attach prove-incr honesty into orch trajectory metadata."""

from __future__ import annotations

import json
from pathlib import Path

from aura_build.cli import main
from aura_build.orch import OrchConfig, run_episode
from aura_build.prove_incr import (
    ENV_FIBER_SESSION_OK,
    ENV_INCR_VALID,
    ProveIncrReport,
    attach_prove_metadata,
    merge_prove_into_runtime,
    prove_or_refuse,
    write_report,
)
from aura_build.schema import validate_episode
from aura_build.trajectory import TrajectoryWriter
from aura_build.worldline import SESSION_LONG_LIVED_AURA, SESSION_SHARED_SUBPROCESS


def test_attach_defaults_without_report(tmp_path: Path):
    fields = attach_prove_metadata(root=tmp_path, environ={})
    assert fields["incr_proven"] is False
    assert fields["measured"] is False
    assert fields["fiber_live"] is False
    assert fields["session_model"] == SESSION_SHARED_SUBPROCESS
    assert fields["reason"] == "no_prove_incr_report"
    assert fields["attached"] is True
    assert fields["env_notes"] == []


def test_env_alone_cannot_force_incr_proven(tmp_path: Path):
    report = prove_or_refuse(
        force_unhealthy=True,
        unhealthy_reason="GLIBCXX_3.4.35 not found",
        aura_bin="/x",
        probe_fiber=False,
    )
    write_report(report, root=tmp_path)
    fields = attach_prove_metadata(
        root=tmp_path,
        environ={ENV_INCR_VALID: "1", ENV_FIBER_SESSION_OK: "1"},
    )
    assert fields["incr_proven"] is False
    assert fields["measured"] is False
    assert fields["fiber_live"] is False
    assert "env_ignored_unproven" in fields["env_notes"]
    assert "env_fiber_ignored_unproven" in fields["env_notes"]
    assert fields["session_model"] == SESSION_SHARED_SUBPROCESS


def test_env_alone_without_report_still_false(tmp_path: Path):
    fields = attach_prove_metadata(
        root=tmp_path,
        environ={ENV_INCR_VALID: "true", ENV_FIBER_SESSION_OK: "yes"},
    )
    assert fields["incr_proven"] is False
    assert fields["fiber_live"] is False
    assert "env_ignored_unproven" in fields["env_notes"]
    assert "env_fiber_ignored_unproven" in fields["env_notes"]


def test_attach_mirrors_proven_report(tmp_path: Path):
    report = ProveIncrReport(
        incr_proven=True,
        measured=True,
        reason="storm_still_incr_measured",
        aura_healthy=True,
        session_model=SESSION_SHARED_SUBPROCESS,
        fiber_live=False,
        cycles_requested=2,
        cycles_completed=2,
        cycles_ok=2,
        cycles_incr_valid=2,
    )
    write_report(report, root=tmp_path)
    fields = attach_prove_metadata(root=tmp_path, environ={})
    assert fields["incr_proven"] is True
    assert fields["measured"] is True
    assert fields["reason"] == "storm_still_incr_measured"
    assert fields["source"] == "prove-incr-latest"


def test_env_agrees_when_report_proven(tmp_path: Path):
    report = ProveIncrReport(
        incr_proven=True,
        measured=True,
        reason="storm_still_incr_measured",
        aura_healthy=True,
        fiber_live=True,
        session_model=SESSION_LONG_LIVED_AURA,
    )
    write_report(report, root=tmp_path)
    fields = attach_prove_metadata(
        root=tmp_path,
        environ={ENV_INCR_VALID: "1", ENV_FIBER_SESSION_OK: "1"},
    )
    assert fields["incr_proven"] is True
    assert fields["fiber_live"] is True
    assert "env_agrees_proven" in fields["env_notes"]
    assert "env_fiber_agrees" in fields["env_notes"]


def test_merge_does_not_invent_long_lived_without_fiber():
    runtime = {"mode": "simulated", "session_model": SESSION_LONG_LIVED_AURA}
    fields = {
        "incr_proven": False,
        "measured": False,
        "fiber_live": False,
        "session_model": SESSION_SHARED_SUBPROCESS,
        "reason": "x",
        "attached": True,
    }
    merge_prove_into_runtime(runtime, fields)
    assert runtime["session_model"] == SESSION_SHARED_SUBPROCESS
    assert runtime["incr_proven"] is False
    assert runtime["prove_incr"]["reason"] == "x"


def test_run_episode_attaches_fields(tmp_path: Path):
    report = prove_or_refuse(
        force_unhealthy=True,
        unhealthy_reason="GLIBCXX_3.4.35 not found",
        aura_bin="/x",
        probe_fiber=False,
    )
    write_report(report, root=tmp_path)
    result = run_episode(
        "attach me",
        OrchConfig(seed=1, n_worldlines=2, harness_root=tmp_path),
    )
    validate_episode(result.episode)
    rt = result.episode["runtime"]
    assert rt["incr_proven"] is False
    assert rt["measured"] is False
    assert rt["fiber_live"] is False
    assert "prove_incr" in rt
    assert rt["prove_incr"]["reason"] == "aura_glibcxx_mismatch"
    assert rt["prove_incr"]["attached"] is True
    assert rt.get("session_model") == SESSION_SHARED_SUBPROCESS


def test_run_episode_env_cannot_force_true(tmp_path: Path, monkeypatch):
    monkeypatch.setenv(ENV_INCR_VALID, "1")
    monkeypatch.setenv(ENV_FIBER_SESSION_OK, "1")
    report = prove_or_refuse(
        force_unhealthy=True,
        unhealthy_reason="missing",
        aura_bin=None,
        probe_fiber=False,
    )
    write_report(report, root=tmp_path)
    result = run_episode(
        "env gate",
        OrchConfig(seed=2, n_worldlines=2, harness_root=tmp_path),
    )
    rt = result.episode["runtime"]
    assert rt["incr_proven"] is False
    assert rt["fiber_live"] is False
    assert "env_ignored_unproven" in rt["prove_incr"]["env_notes"]


def test_attach_fields_in_traj_jsonl(tmp_path: Path):
    report = prove_or_refuse(
        force_unhealthy=True,
        unhealthy_reason="GLIBCXX",
        aura_bin="/x",
        probe_fiber=False,
    )
    write_report(report, root=tmp_path)
    out = tmp_path / "ep.jsonl"
    result = run_episode(
        "jsonl",
        OrchConfig(seed=3, n_worldlines=2, harness_root=tmp_path),
    )
    TrajectoryWriter(out).append(result.episode)
    line = out.read_text(encoding="utf-8").strip().splitlines()[0]
    ep = json.loads(line)
    validate_episode(ep)
    pi = ep["runtime"]["prove_incr"]
    for key in ("incr_proven", "measured", "fiber_live", "session_model", "reason"):
        assert key in pi
    assert ep["runtime"]["incr_proven"] is False
    assert pi["measured"] is False


def test_no_attach_prove_skips(tmp_path: Path):
    result = run_episode(
        "skip",
        OrchConfig(seed=4, n_worldlines=2, harness_root=tmp_path, attach_prove=False),
    )
    assert "prove_incr" not in result.episode["runtime"]
    # Still default false at top-level from _build_episode
    assert result.episode["runtime"].get("incr_proven", False) is False


def test_cli_run_attach_default(tmp_path: Path, monkeypatch):
    report = prove_or_refuse(
        force_unhealthy=True,
        unhealthy_reason="GLIBCXX",
        aura_bin="/x",
        probe_fiber=False,
    )
    write_report(report, root=tmp_path)
    out = tmp_path / "cli.jsonl"
    rc = main(
        [
            "run",
            "--prompt",
            "cli attach",
            "--seed",
            "5",
            "--worldlines",
            "2",
            "--mode",
            "simulated",
            "--harness-root",
            str(tmp_path),
            "--out",
            str(out),
            "--json",
        ]
    )
    assert rc == 0
    ep = json.loads(out.read_text().strip().splitlines()[0])
    assert ep["runtime"]["prove_incr"]["attached"] is True
    assert ep["runtime"]["incr_proven"] is False


def test_cli_no_attach_prove(tmp_path: Path):
    out = tmp_path / "cli2.jsonl"
    rc = main(
        [
            "run",
            "--prompt",
            "no attach",
            "--seed",
            "6",
            "--worldlines",
            "2",
            "--mode",
            "simulated",
            "--harness-root",
            str(tmp_path),
            "--out",
            str(out),
            "--no-attach-prove",
        ]
    )
    assert rc == 0
    ep = json.loads(out.read_text().strip().splitlines()[0])
    assert "prove_incr" not in ep["runtime"]
