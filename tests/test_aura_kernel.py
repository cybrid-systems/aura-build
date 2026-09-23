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
