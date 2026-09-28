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


def test_runtime_ok_regex_parses_materialize_line():
    from aura_build.self_evolve_runtime import _RUNTIME_OK_RE

    line = (
        "RUNTIME_OK selected=9 observed=9 src_len=33 "
        "wrote=aura/self_evolve_stamp.aura gen=1 materialize=current-source "
        "incr_proven=false fiber_live=false kernel=aura"
    )
    m = _RUNTIME_OK_RE.search(line)
    assert m is not None
    assert m.group("selected") == "9"
    assert m.group("observed") == "9"
    assert m.group("src_len") == "33"
    assert m.group("wrote") == "aura/self_evolve_stamp.aura"


def test_stamp_after_runtime_has_current_source_unparse():
    from pathlib import Path
    from aura_build.stamp_banner import stamp_banner_agrees

    stamp = Path("aura/self_evolve_stamp.aura")
    if not stamp.is_file():
        return
    text = stamp.read_text(encoding="utf-8")
    if "materialize=current-source" not in text:
        return  # older string-built stamp in some checkouts
    assert stamp_banner_agrees(text)
    assert "incr_proven=false" in text and '"incr_proven" #f' in text
    # fiber_live may be true (serve denseness measured) or false (oneshot fallback)
    assert (
        ("; fiber_live=true" in text and '"fiber_live" #t' in text)
        or ("; fiber_live=false" in text and '"fiber_live" #f' in text)
    )
    assert "(define cand" in text or "(define (cand" in text


def test_build_stamp_body_fiber_live_banner():
    from aura_build.self_evolve_runtime import _build_stamp_body
    from aura_build.stamp_banner import stamp_banner_agrees

    src = "(define cand\n  (lambda ()\n    9))"
    body = _build_stamp_body(
        src=src,
        traj="t1",
        gen=1,
        selected=9,
        observed=9,
        src_len=len(src),
        fiber_live=True,
        worldline_backend="fiber_graph",
        denseness_note="soft_ready_async_denseness_4048",
    )
    assert "; fiber_live=true" in body
    assert '"fiber_live" #t' in body
    assert "worldline_backend=fiber_graph" in body
    assert stamp_banner_agrees(body)
    assert "materialize=current-source" in body


def test_build_stamp_body_oneshot_fiber_false():
    from aura_build.self_evolve_runtime import _build_stamp_body
    from aura_build.stamp_banner import stamp_banner_agrees

    src = "(define cand\n  (lambda ()\n    2))"
    body = _build_stamp_body(
        src=src,
        traj="t2",
        gen=1,
        selected=2,
        observed=2,
        src_len=len(src),
        fiber_live=False,
        worldline_backend="oneshot_mutate",
        denseness_note="fallback",
    )
    assert "; fiber_live=false" in body
    assert '"fiber_live" #f' in body
    assert stamp_banner_agrees(body)


def test_helper_candidates_export_pick_best():
    from aura_build.self_evolve_runtime import _HELPER_CANDIDATES

    assert len(_HELPER_CANDIDATES) >= 2
    for name, src in _HELPER_CANDIDATES:
        assert "pick-best" in src
        assert "(export pick-best)" in src
        assert name


def test_ends_helper_candidates_export_ends_with():
    from aura_build.self_evolve_runtime import _ENDS_HELPER_CANDIDATES

    assert len(_ENDS_HELPER_CANDIDATES) >= 2
    for name, src in _ENDS_HELPER_CANDIDATES:
        assert "ends-with?" in src
        assert "(export ends-with?)" in src
        assert name


def test_starts_helper_candidates_export_starts_with():
    from aura_build.self_evolve_runtime import _STARTS_HELPER_CANDIDATES

    assert len(_STARTS_HELPER_CANDIDATES) >= 2
    for name, src in _STARTS_HELPER_CANDIDATES:
        assert "starts-with?" in src
        assert "(export starts-with?)" in src
        assert name


def test_contains_helper_candidates_export_contains():
    from aura_build.self_evolve_runtime import _CONTAINS_HELPER_CANDIDATES

    assert len(_CONTAINS_HELPER_CANDIDATES) >= 2
    for name, src in _CONTAINS_HELPER_CANDIDATES:
        assert "contains?" in src
        assert "(export contains?)" in src
        assert name
