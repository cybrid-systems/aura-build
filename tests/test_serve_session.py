"""Host-managed long-lived aura --serve session + verify fallback honesty."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from aura_build.runtime import resolve_aura_bin
from aura_build.serve_session import (
    SESSION_SERVE,
    SESSION_SHARED,
    attach_session,
    clear_marker,
    prefer_session_verify,
    read_marker,
    run_session_dogfood,
    session_status,
    start_session,
    stop_session,
    write_marker,
)


pytestmark = pytest.mark.skipif(
    not resolve_aura_bin(None),
    reason="Aura binary unavailable",
)


def test_session_start_status_stop(tmp_path: Path) -> None:
    stop_session(harness_root=tmp_path)
    sess = start_session(harness_root=tmp_path)
    assert sess.alive()
    marker = read_marker(tmp_path)
    assert marker is not None
    assert marker["pid"] == sess.pid
    assert marker["session_model"] == SESSION_SERVE
    st = session_status(harness_root=tmp_path)
    assert st["serve_attach_ok"] is True
    assert st["eval_available"] is True
    assert st["session_model"] == SESSION_SERVE
    assert st["serve_cross_session_shared_ast"] is False
    # Env alone does not invent ok when process dead
    stop_session(harness_root=tmp_path)
    st2 = session_status(harness_root=tmp_path)
    assert st2["serve_attach_ok"] is False
    assert st2["session_model"] == SESSION_SHARED


def test_env_cannot_fake_serve_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AURA_BUILD_SESSION", "1")
    clear_marker(tmp_path)
    # Fake marker with dead pid
    write_marker(
        {
            "pid": 999999,
            "session_model": SESSION_SERVE,
            "mode": "serve",
        },
        tmp_path,
    )
    st = session_status(harness_root=tmp_path)
    assert st["serve_attach_ok"] is False
    assert st["session_model"] == SESSION_SHARED
    # prefer flag is true but attach not ok
    assert prefer_session_verify(harness_root=tmp_path) is True


def test_in_session_verify_greet(tmp_path: Path) -> None:
    from aura_build.llm_dogfood import GREET_SUCCESS_RE, verify_aura_program

    sess = start_session(harness_root=tmp_path)
    prog = tmp_path / "greet.aura"
    prog.write_text('(display "GREET=aura")(newline)\n', encoding="utf-8")
    got = verify_aura_program(
        prog,
        expect_re=GREET_SUCCESS_RE,
        serve_session=sess,
        harness_root=tmp_path,
    )
    assert got["passed"] is True
    assert got["via"] == "serve_session"
    assert got["session_model"] == SESSION_SERVE
    # Second eval reuses same process (no cold spawn)
    prog2 = tmp_path / "greet2.aura"
    prog2.write_text('(display "GREET=wrong")(newline)\n', encoding="utf-8")
    bad = verify_aura_program(
        prog2,
        expect_re=GREET_SUCCESS_RE,
        serve_session=sess,
        harness_root=tmp_path,
    )
    assert bad["passed"] is False
    assert bad["via"] == "serve_session"
    stop_session(harness_root=tmp_path)


def test_verify_falls_back_cold_when_no_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from aura_build.llm_dogfood import GREET_SUCCESS_RE, verify_aura_program

    monkeypatch.setenv("AURA_BUILD_SESSION", "cold")
    stop_session(harness_root=tmp_path)
    clear_marker(tmp_path)
    prog = tmp_path / "greet.aura"
    prog.write_text('(display "GREET=aura")(newline)\n', encoding="utf-8")
    got = verify_aura_program(
        prog,
        expect_re=GREET_SUCCESS_RE,
        harness_root=tmp_path,
        prefer_session=False,
    )
    assert got["passed"] is True
    assert got["via"] == "aura_bin"
    assert got.get("session_model") == SESSION_SHARED


def test_session_dogfood_closed_loop(tmp_path: Path) -> None:
    out = tmp_path / "session_dogfood.jsonl"
    summary = run_session_dogfood(
        rounds=2,
        harness_root=tmp_path,
        out=out,
        compare_cold=True,
    )
    assert summary["ok"] is True
    assert summary["session_model"] == SESSION_SERVE
    assert summary["serve_session_ok"] is True
    timing = summary["timing"]
    assert timing["session_evals"] == 6  # 2 rounds × 3 wl
    assert timing["cold_spawns"] == 6
    assert out.is_file()
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["runtime"]["session_model"] == SESSION_SERVE
    assert ep["runtime"]["incr_proven"] is False
    assert ep["runtime"]["fiber_live"] is False
    assert ep["runtime"]["serve_cross_session_shared_ast"] is False
    stop_session(harness_root=tmp_path)


def test_cli_session_help() -> None:
    from aura_build.cli_parser import build_parser

    p = build_parser()
    help_text = p.format_help()
    assert "session" in help_text
    # subparsers
    ns = p.parse_args(["session", "status", "--json"])
    assert ns.cmd == "session"
    assert ns.session_cmd == "status"
