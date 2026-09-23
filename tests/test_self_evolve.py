"""self-evolve: CI-safe refuse + --no-push/--no-commit paths."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from aura_build.cli import build_parser, main
from aura_build.kernel import KernelResult
from aura_build.self_evolve_host import git_commit_and_maybe_push, run_host_verify


def test_parser_lists_self_evolve():
    help_text = build_parser().format_help()
    assert "self-evolve" in help_text


def test_self_evolve_refuses_with_force_python(monkeypatch, tmp_path):
    monkeypatch.setenv("AURA_BUILD_FORCE_PYTHON", "1")
    rc = main(
        [
            "self-evolve",
            "--prompt",
            "ci refuse",
            "--no-push",
            "--no-commit",
            "--verify",
            "none",
            "--harness-root",
            str(tmp_path),
        ]
    )
    assert rc == 2


def test_host_verify_none_ok(tmp_path):
    got = run_host_verify(tmp_path, "none")
    assert got["ok"] is True
    assert got["exit_code"] == 0


def test_git_commit_no_push(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "stamp.txt").write_text("x\n", encoding="utf-8")
    res = git_commit_and_maybe_push(
        tmp_path,
        message="test stamp",
        paths=["stamp.txt"],
        no_push=True,
    )
    assert res["ok"] is True
    assert res.get("pushed") is False
    assert res.get("committed") or res.get("reason") in {
        "committed_no_push",
        "nothing_to_commit",
        "committed",
    }


def test_self_evolve_no_push_mocked_kernel(monkeypatch, tmp_path):
    monkeypatch.delenv("AURA_BUILD_FORCE_PYTHON", raising=False)
    resp = {
        "ok": True,
        "commit_ready": True,
        "traj_id": "traj-test",
        "harness_mid": "mid-test",
        "commit_message": (
            "self-evolve: traj=traj-test mid=mid-test "
            "kernel=aura incr_proven=false fiber_live=false"
        ),
        "materialized": [],
        "honesty": {"incr_proven": False, "fiber_live": False},
        "reason": "verify_green",
        "kernel": "aura",
    }
    kr = KernelResult(
        ok=True,
        exit_code=0,
        stdout="self_evolve ok=true kernel=aura\n",
        stderr="",
        response=resp,
        via="aura",
    )

    monkeypatch.setattr("aura_build.cli.prefer_aura_kernel", lambda: True)
    monkeypatch.setattr(
        "aura_build.cli.try_invoke_aura",
        lambda cmd, env, **kw: kr,
    )
    monkeypatch.setattr(
        "aura_build.cli.run_host_verify",
        lambda *a, **k: {
            "ok": True,
            "reason": "verify_skipped",
            "exit_code": 0,
            "mode": "none",
        },
    )
    calls: list[dict] = []

    def _fake_git(repo, **kw):
        calls.append(kw)
        return {
            "ok": True,
            "reason": "committed_no_push",
            "committed": True,
            "pushed": False,
            "tip": "deadbeef",
        }

    monkeypatch.setattr("aura_build.cli.git_commit_and_maybe_push", _fake_git)
    rc = main(
        [
            "self-evolve",
            "--prompt",
            "mocked",
            "--no-push",
            "--verify",
            "none",
            "--harness-root",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert calls and calls[0].get("no_push") is True
