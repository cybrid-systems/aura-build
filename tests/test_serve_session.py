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
    # Soft #4047 B may measure True on sync / sync side-probe; never require False.
    assert isinstance(st["serve_cross_session_shared_ast"], bool)
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
    # Soft #4047 B: shared_ast bool from measurement only (never env-elevated)
    assert isinstance(ep["runtime"]["serve_cross_session_shared_ast"], bool)
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
    # Env AURA_BUILD_SERVE_SHARED_AST=1 must not invent True when Soft measured False.
    # Soft #4047 B may measure True on async — that is honest, not env elevation.
    marker = read_marker(tmp_path) or {}
    probe = marker.get("shared_ast_probe") or {}
    measured = bool(probe.get("serve_cross_session_shared_ast"))
    assert st["serve_cross_session_shared_ast"] is measured
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
    # Soft may select set_code_eval or mutate_rebind; both are honest serve paths.
    assert summary["path_kind"] in ("mutate_rebind", "set_code_eval")
    assert summary["worldline_backend"] in (
        "serve_mutate_rebind",
        "serve_set_code_eval",
        "serve_eval_source",
    ) or str(summary.get("worldline_backend") or "").startswith("serve_")
    assert summary["cold_spawns"] == 0
    assert summary["serve_mode"] in ("sync", "async")
    soft_ok = summary.get("serve_async_soft_ready_ok")
    if soft_ok:
        assert summary["serve_mode"] == "async"
    else:
        assert summary["serve_mode"] == "sync"
        assert summary["serve_async_soft_ready_fail_bits"] == "0x10"
    assert isinstance(summary["serve_cross_session_shared_ast"], bool)
    assert summary["serve_same_session_mutate_ok"] is True
    assert out.is_file()
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["runtime"]["session_model"] == SESSION_SERVE
    assert str(ep["runtime"].get("worldline_backend") or "").startswith("serve_")
    assert ep["runtime"]["dogfood"]["cold_spawns"] == 0
    stop_session(harness_root=tmp_path)


def test_is_session_transient_tokens():
    from aura_build.serve_session import is_session_transient

    assert is_session_transient("serve_sock_missing")
    assert is_session_transient("err:serve_session_timeout")
    assert is_session_transient("serve_sock_empty")
    assert is_session_transient("serve_sock_error:Connection refused")
    assert is_session_transient("timeout")
    assert not is_session_transient("ok")
    assert not is_session_transient("closure")
    assert not is_session_transient(None)


def test_stop_quiet_none_ok():
    from aura_build.serve_session import stop_quiet

    stop_quiet(None)  # must not raise


def test_session_reuse_same_bin(tmp_path: Path) -> None:
    """Alive same-bin holder is reused (高速进化); force=True cold-restarts."""
    stop_session(harness_root=tmp_path)
    sess1 = start_session(harness_root=tmp_path, force=False)
    assert sess1.alive()
    pid1 = sess1.pid
    mode1 = getattr(sess1, "attach_mode", None)
    assert mode1 in ("cold", None) or mode1 == "cold"
    sess2 = start_session(harness_root=tmp_path, force=False)
    assert sess2.pid == pid1
    assert getattr(sess2, "attach_mode", None) == "reuse"
    marker = read_marker(tmp_path)
    assert marker is not None
    assert marker.get("attach_mode") == "reuse"
    # force restarts
    sess3 = start_session(harness_root=tmp_path, force=True)
    assert sess3.alive()
    assert sess3.pid != pid1
    assert getattr(sess3, "attach_mode", None) == "cold"
    stop_session(harness_root=tmp_path)


def test_soft_ready_cache_roundtrip(tmp_path: Path) -> None:
    from aura_build.serve_session import (
        load_cached_soft_ready,
        save_cached_soft_ready,
        resolve_aura_bin,
    )

    bin_path = resolve_aura_bin(None)
    assert bin_path
    probe = {
        "ok": True,
        "serve_mode_preferred": "async",
        "reason": "unit_test_stub",
    }
    save_cached_soft_ready(tmp_path, bin_path, probe)
    got = load_cached_soft_ready(tmp_path, bin_path)
    assert got is not None
    assert got["ok"] is True
    assert got["cached"] is True
    assert got["reason"] == "unit_test_stub"
    # Never invent: missing ok rejected
    bad = tmp_path / "soft_ready_cache.json"
    bad.write_text('{"bin": {}, "probe": {"reason": "no_ok"}}\n', encoding="utf-8")
    assert load_cached_soft_ready(tmp_path, bin_path) is None


def test_ensure_session_ready_ping_ok(tmp_path, monkeypatch):
    from aura_build import serve_session as ss

    class _Sess:
        harness_root = tmp_path
        aura_bin = "/fake/aura"

        def ping(self, *, timeout_s=3.0):
            return True

    sess = _Sess()
    out, meta = ss.ensure_session_ready(sess, aura_bin="/fake/aura", harness_root=tmp_path)
    assert out is sess
    assert meta["via"] == "ping_ok"
    assert meta["ok"] is True


def test_ensure_session_ready_restart_when_ping_fails(tmp_path, monkeypatch):
    from aura_build import serve_session as ss

    class _Dead:
        harness_root = tmp_path
        aura_bin = "/fake/aura"

        def ping(self, *, timeout_s=3.0):
            return False

    class _Fresh:
        harness_root = tmp_path
        aura_bin = "/fake/aura"

        def ping(self, *, timeout_s=3.0):
            return True

    monkeypatch.setattr(ss, "attach_session", lambda **kw: None)
    monkeypatch.setattr(ss, "restart_session", lambda **kw: _Fresh())
    dead = _Dead()
    out, meta = ss.ensure_session_ready(dead, aura_bin="/fake/aura", harness_root=tmp_path)
    assert isinstance(out, _Fresh)
    assert meta["via"] == "restart"
    assert meta["ok"] is True
