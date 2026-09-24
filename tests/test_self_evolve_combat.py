"""self-evolve combat: refuse without session; --help; dry-run CI-safe."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from aura_build.cli import build_parser, main
from aura_build.self_evolve_combat import (
    classify_findings,
    format_combat_line,
    require_serve_attach,
    run_combat,
    _stamp_honesty_from_summary,
)


def test_parser_lists_self_evolve_combat():
    help_text = build_parser().format_help()
    assert "self-evolve" in help_text
    args = build_parser().parse_args(["self-evolve", "combat", "--dry-run"])
    assert args.cmd == "self-evolve"
    assert args.self_evolve_cmd == "combat"
    assert args.dry_run is True


def test_combat_help_mentions_no_push_and_soft():
    # argparse --help exits; call format_help on combat subparser
    p = build_parser()
    # Walk to combat subparser
    se = None
    for action in p._subparsers._group_actions:  # noqa: SLF001
        for name, sp in action.choices.items():
            if name == "self-evolve":
                se = sp
                break
    assert se is not None
    combat = None
    for action in se._subparsers._group_actions:  # noqa: SLF001
        for name, sp in action.choices.items():
            if name == "combat":
                combat = sp
                break
    assert combat is not None
    text = combat.format_help()
    assert "serve_attach" in text or "Soft" in text or "combat" in text
    assert "--no-push" in text or "--push" in text
    assert "--dry-run" in text
    assert "--start-session" in text


def test_stamp_path_unchanged_when_no_combat_subcommand():
    args = build_parser().parse_args(
        ["self-evolve", "--prompt", "keep-stamp", "--no-push", "--no-commit"]
    )
    assert args.cmd == "self-evolve"
    assert getattr(args, "self_evolve_cmd", None) is None
    assert args.prompt == "keep-stamp"
    assert args.no_push is True


def test_combat_refuse_without_session(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("AURA_BIN", raising=False)

    def _fake_status(**kw):
        return {
            "serve_attach_ok": False,
            "session_model": "shared",
            "serve_mode": "sync",
            "serve_cross_session_shared_ast": False,
            "serve_same_session_mutate_ok": False,
            "aura_bin": None,
            "pid": None,
        }

    with patch("aura_build.serve_session.session_status", _fake_status):
        rc = main(
            [
                "self-evolve",
                "combat",
                "--harness-root",
                str(tmp_path),
                "--json",
            ]
        )
    assert rc == 2
    err = capsys.readouterr().err
    assert "serve_attach" in err or "refuse" in err


def test_combat_dry_run_without_session_ci_safe(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("AURA_BIN", raising=False)

    def _fake_status(**kw):
        return {
            "serve_attach_ok": False,
            "session_model": "shared",
            "serve_mode": "sync",
            "serve_cross_session_shared_ast": False,
            "serve_same_session_mutate_ok": False,
            "aura_bin": None,
            "pid": None,
        }

    out_dir = tmp_path / "combat_out"
    with patch("aura_build.serve_session.session_status", _fake_status):
        rc = main(
            [
                "self-evolve",
                "combat",
                "--dry-run",
                "--out-dir",
                str(out_dir),
                "--harness-root",
                str(tmp_path),
                "--json",
            ]
        )
    assert rc == 0
    out = capsys.readouterr().out
    assert "self_evolve_combat" in out
    assert "dry_run" in out
    # Artifacts written
    assert out_dir.is_dir()
    assert list(out_dir.glob("combat_*_stdout.json"))


def test_combat_dry_run_with_session_ok(tmp_path, monkeypatch, capsys):
    def _fake_status(**kw):
        return {
            "serve_attach_ok": True,
            "session_model": "serve",
            "serve_mode": "async",
            "serve_cross_session_shared_ast": True,
            "serve_same_session_mutate_ok": True,
            "serve_async_soft_ready": True,
            "aura_bin": "/workspace/aura-grok/build_soft4048/aura",
            "pid": 12345,
        }

    out_dir = tmp_path / "combat_out"
    with patch("aura_build.serve_session.session_status", _fake_status):
        rc = main(
            [
                "self-evolve",
                "combat",
                "--dry-run",
                "--out-dir",
                str(out_dir),
                "--harness-root",
                str(tmp_path),
                "--json",
                "--project",
                "examples/projects/mini-cache",
            ]
        )
    assert rc == 0
    out = capsys.readouterr().out
    assert "serve_attach_ok=True" in out or "serve_attach_ok=true" in out.lower() or "session_model=serve" in out
    payload = json.loads(out[out.index("{") :])
    assert payload["dry_run"] is True
    assert payload["ok"] is True
    assert payload["honesty"]["serve_attach_ok"] is True
    assert payload["honesty"]["session_model"] == "serve"
    assert payload.get("push") is False


def test_require_serve_attach_refuses_without_start(tmp_path):
    with patch(
        "aura_build.serve_session.session_status",
        return_value={"serve_attach_ok": False, "session_model": "shared"},
    ):
        st, meta = require_serve_attach(
            harness_root=tmp_path,
            aura_bin=None,
            start_session_if_needed=False,
        )
    assert st is None
    assert meta["refuse_reason"] == "serve_attach_required"


def test_honesty_stamps_measured_only():
    got = _stamp_honesty_from_summary(
        {
            "llm_via": "fiber",
            "llm_parallel": "fiber",
            "honesty": {"session_model": "serve", "fiber_live": True},
            "explore_parallel": "fiber_graph",
        }
    )
    assert got["llm_via"] == "fiber"
    assert got["llm_parallel"] == "fiber"
    assert got["session_model"] == "serve"
    assert "invented" not in got


def test_classify_findings_aura_stub_on_soft_signal():
    findings = classify_findings(
        {
            "ok": False,
            "reason": "soft_hang",
            "llm_via": "host",
            "honesty": {"session_model": "serve"},
        }
    )
    classes = {f["class"] for f in findings}
    assert "aura_kernel" in classes
    aura = next(f for f in findings if f["class"] == "aura_kernel")
    assert aura["action"] == "issue_draft"
    assert "cybrid-systems/aura" in aura["repo"]


def test_run_combat_no_push_default(tmp_path, monkeypatch):
    monkeypatch.delenv("AURA_BIN", raising=False)
    fake_summary = {
        "ok": True,
        "reason": "verify_green",
        "llm_via": "fiber",
        "llm_parallel": "fiber",
        "honesty": {
            "session_model": "serve",
            "serve_mode": "async",
            "serve_attach_ok": True,
            "fiber_live": True,
        },
        "worldline_backend": "fiber_graph",
        "explore_parallel": "fiber_graph",
        "fiber_explore_n": 3,
        "fiber_llm": True,
        "materialized": [],
    }

    def _fake_status(**kw):
        return {
            "serve_attach_ok": True,
            "session_model": "serve",
            "serve_mode": "async",
            "serve_cross_session_shared_ast": True,
            "serve_same_session_mutate_ok": True,
            "aura_bin": "/tmp/fake-aura",
            "pid": 1,
        }

    # Minimal project so resolve_task_spec inside run_closed_loop is never hit
    # (closed loop fully mocked).
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "GOAL.md").write_text("# goal\n", encoding="utf-8")
    (proj / "stub.aura").write_text("1\n", encoding="utf-8")
    (proj / "verify.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    with (
        patch("aura_build.serve_session.session_status", _fake_status),
        patch("aura_build.llm_dogfood.run_closed_loop", return_value=fake_summary),
        patch(
            "aura_build.minimax.load_minimax_config",
            side_effect=FileNotFoundError("no key in test"),
        ),
    ):
        result = run_combat(
            project=proj,
            harness_root=tmp_path,
            out_dir=tmp_path / "out",
            explore_tools="rule,intent",
            fiber_llm=False,
            push=False,
            max_rounds=1,
            worldlines=1,
        )
    assert result.get("ok") is True
    assert result.get("push") is False
    assert result.get("push_reason") == "no_push_default"
    assert (result.get("honesty") or {}).get("llm_via") == "fiber"
    line = format_combat_line(result)
    assert "self_evolve_combat" in line
    assert "llm_via=fiber" in line
