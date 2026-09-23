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
    assert st["serve_mode"] in ("sync", "async")
    assert "serve_async_soft_ready" in st
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
    assert timing["cold_spawns"] == 0  # session path never cold-spawns aura
    assert timing["cold_compare_spawns"] == 6
    assert out.is_file()
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["runtime"]["session_model"] == SESSION_SERVE
    assert ep["runtime"]["incr_proven"] is False
    assert ep["runtime"]["fiber_live"] is False
    # Soft --serve: cross-session shared AST measured false (never env-elevated)
    assert ep["runtime"]["serve_cross_session_shared_ast"] is False
    assert "serve_mode" in ep["runtime"]
    assert summary["serve_mode"] in ("sync", "async")
    assert summary["serve_same_session_mutate_ok"] is True
    assert summary["honesty"]["path_kind"] == "mutate_rebind"
    assert ep["runtime"]["dogfood"]["path_kind"] == "mutate_rebind"
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


def test_env_cannot_elevate_shared_ast(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AURA_BUILD_SERVE_SHARED_AST must not stamp serve_cross_session_shared_ast."""
    monkeypatch.setenv("AURA_BUILD_SERVE_SHARED_AST", "1")
    sess = start_session(harness_root=tmp_path)
    st = session_status(harness_root=tmp_path)
    assert st["serve_attach_ok"] is True
    assert st["serve_cross_session_shared_ast"] is False
    # Soft Ready (#4047): prefer async when measured ok; never env-fake shared_ast
    assert st["serve_mode"] in ("sync", "async")
    soft = st.get("serve_async_soft_ready") or {}
    if soft.get("ok"):
        assert st["serve_mode"] == "async"
    assert st.get("serve_same_session_mutate_ok") is True
    stop_session(harness_root=tmp_path)


def test_probe_serve_async_soft_ready_measured() -> None:
    from aura_build.serve_session import probe_serve_async_soft_ready

    bin_path = resolve_aura_bin(None)
    assert bin_path
    got = probe_serve_async_soft_ready(bin_path)
    # Aura #4047 Soft Ready tips: ok=true → async preferred.
    # Pre-#4047 tips: refuse with fail_bits=0x10 / sync preferred.
    if got["ok"]:
        assert got["serve_mode_preferred"] == "async"
        assert got["reason"] in (
            "soft_ready_alive_timeout_ok",
            "soft_ready_profile_4047",
            "soft_ready_ok",
        )
    else:
        assert got["serve_mode_preferred"] == "sync"
        assert got["reason"] in (
            "soft_ready_refused",
            "soft_ready_refused_after_timeout",
            "soft_ready_inconclusive",
        )
        if got["reason"] == "soft_ready_refused":
            assert got.get("fail_bits") == "0x10"


def test_decode_soft_ready_fail_bits_0x10() -> None:
    from aura_build.serve_session import decode_soft_ready_fail_bits

    got = decode_soft_ready_fail_bits("0x10")
    assert got["mask"] == 0x10
    assert got["bits"] == [4]
    assert got["names"] == ["defaults_missing_soft"]
    assert got["soft_defaults_only"] is True


def test_probe_fail_bits_decoded() -> None:
    from aura_build.serve_session import (
        decode_soft_ready_fail_bits,
        probe_serve_async_soft_ready,
    )

    bin_path = resolve_aura_bin(None)
    assert bin_path
    got = probe_serve_async_soft_ready(bin_path)
    if got["ok"]:
        # Soft Ready path: no refuse fail_bits; decoder still honest for 0x10
        decoded = decode_soft_ready_fail_bits("0x10")
        assert decoded.get("soft_defaults_only") is True
        assert "defaults_missing_soft" in (decoded.get("names") or [])
    else:
        assert got.get("fail_bits") == "0x10"
        decoded = got.get("fail_bits_decoded") or {}
        assert decoded.get("soft_defaults_only") is True
        assert "defaults_missing_soft" in (decoded.get("names") or [])


def test_pursue_session_mutate_rebind(tmp_path: Path) -> None:
    from aura_build.serve_session import run_pursue_session

    out = tmp_path / "pursue.jsonl"
    summary = run_pursue_session(
        goal="emit GREET=aura on serve",
        min_fitness=0.8,
        max_rounds=2,
        worldlines=3,
        harness_root=tmp_path,
        out=out,
        seed=7,
    )
    assert summary["ok"] is True
    assert summary["goal_met"] is True
    assert summary["stop_reason"] == "goal_met"
    assert summary["session_model"] == SESSION_SERVE
    assert summary["path_kind"] == "mutate_rebind"
    assert summary["worldline_backend"] == "serve_mutate_rebind"
    assert summary["cold_spawns"] == 0
    assert summary["serve_mode"] in ("sync", "async")
    soft_ok = summary.get("serve_async_soft_ready_ok")
    if soft_ok:
        assert summary["serve_mode"] == "async"
    else:
        assert summary["serve_mode"] == "sync"
        assert summary["serve_async_soft_ready_fail_bits"] == "0x10"
    assert summary["serve_cross_session_shared_ast"] is False
    assert summary["serve_same_session_mutate_ok"] is True
    assert out.is_file()
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["runtime"]["session_model"] == SESSION_SERVE
    assert ep["runtime"]["worldline_backend"] == "serve_mutate_rebind"
    assert ep["runtime"]["dogfood"]["cold_spawns"] == 0
    stop_session(harness_root=tmp_path)
