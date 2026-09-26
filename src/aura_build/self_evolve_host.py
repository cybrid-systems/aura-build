"""Host edges for self-evolve: post-kernel verify + git commit/push.

Aura kernel owns mutate/select/materialize. Host only:
- optional heavier verify (smoke / prove-incr / kernel run)
- git add/commit/push (skipped with --no-push)
Never invents incr_proven / fiber_live.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_host_verify(
    repo: Path,
    mode: str,
    *,
    aura_bin: str | None = None,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Run host-side verify after Aura materialize. mode: none|smoke|prove|kernel|stamp."""
    mode = (mode or "smoke").strip().lower()
    if mode in ("none", "light", "skip"):
        return {"ok": True, "reason": "verify_skipped", "exit_code": 0, "mode": mode}

    env = os.environ.copy()
    if aura_bin:
        env["AURA_BIN"] = aura_bin

    if mode == "smoke":
        py = repo / ".venv" / "bin" / "python"
        exe = str(py) if py.is_file() else sys.executable
        cmd = [
            exe,
            "-m",
            "pytest",
            "-q",
            "tests/test_host_refuse.py",
            "tests/test_trajectory.py",
        ]
    elif mode == "prove":
        ab = repo / ".venv" / "bin" / "aura-build"
        exe = str(ab) if ab.is_file() else "aura-build"
        cmd = [exe, "prove-incr", "--cycles", "2", "--worldlines", "1", "--no-fiber-probe"]
        if harness_root is not None:
            cmd.extend(["--harness-root", str(harness_root)])
        if aura_bin:
            cmd.extend(["--aura-bin", aura_bin])
    elif mode == "stamp":
        from aura_build.stamp_banner import stamp_banner_agrees

        stamp = repo / "aura" / "self_evolve_stamp.aura"
        if not stamp.is_file() or not stamp_banner_agrees(stamp.read_text(encoding="utf-8")):
            return {
                "ok": False,
                "reason": "stamp_banner_mismatch",
                "exit_code": 1,
                "mode": "stamp",
            }
        return {"ok": True, "reason": "stamp_ok", "exit_code": 0, "mode": "stamp"}
    elif mode == "kernel":
        ab = repo / ".venv" / "bin" / "aura-build"
        exe = str(ab) if ab.is_file() else "aura-build"
        cmd = [
            exe,
            "run",
            "--prompt",
            "self-evolve host verify",
            "--mode",
            "simulated",
            "--worldlines",
            "2",
            "--seed",
            "7",
        ]
        if harness_root is not None:
            cmd.extend(["--harness-root", str(harness_root)])
        if aura_bin:
            cmd.extend(["--aura-bin", aura_bin])
    else:
        return {
            "ok": False,
            "reason": f"unknown_verify_mode:{mode}",
            "exit_code": 2,
            "mode": mode,
        }

    proc = subprocess.run(
        cmd, cwd=str(repo), env=env, capture_output=True, text=True, check=False
    )
    ok = proc.returncode == 0
    return {
        "ok": ok,
        "reason": f"{mode}_ok" if ok else f"{mode}_failed",
        "exit_code": proc.returncode,
        "mode": mode,
        "stdout": (proc.stdout or "")[-2000:],
        "stderr": (proc.stderr or "")[-2000:],
    }


def git_commit_and_maybe_push(
    repo: Path,
    *,
    message: str,
    paths: list[str],
    no_push: bool = True,
    remote: str = "origin",
    branch: str = "main",
) -> dict[str, Any]:
    """Stage paths, commit on main, optionally push. Returns result dict."""

    def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args, cwd=str(repo), capture_output=True, text=True, check=False
        )

    status = _run(["git", "status", "--porcelain"])
    if status.returncode != 0:
        return {"ok": False, "reason": "git_status_failed", "stderr": status.stderr}

    staged: list[str] = []
    for raw in paths:
        add = _run(["git", "add", "-A", "--", raw])
        if add.returncode == 0:
            staged.append(raw)

    diff = _run(["git", "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        return {
            "ok": True,
            "reason": "nothing_to_commit",
            "committed": False,
            "pushed": False,
            "staged": staged,
        }

    commit = _run(["git", "commit", "-m", message])
    if commit.returncode != 0:
        return {
            "ok": False,
            "reason": "git_commit_failed",
            "stderr": commit.stderr,
            "stdout": commit.stdout,
            "staged": staged,
        }

    tip = _run(["git", "rev-parse", "HEAD"])
    tip_sha = (tip.stdout or "").strip()
    out: dict[str, Any] = {
        "ok": True,
        "reason": "committed",
        "committed": True,
        "pushed": False,
        "tip": tip_sha,
        "staged": staged,
        "message": message,
    }
    if no_push:
        out["reason"] = "committed_no_push"
        return out

    push = _run(["git", "push", remote, branch])
    if push.returncode != 0:
        out["ok"] = False
        out["reason"] = "git_push_failed"
        out["stderr"] = push.stderr
        out["stdout"] = push.stdout
        return out
    out["pushed"] = True
    out["reason"] = "committed_and_pushed"
    return out
