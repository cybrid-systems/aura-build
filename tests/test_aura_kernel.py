"""Aura kernel integration — skip cleanly when aura binary unavailable."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from aura_build.kernel import invoke_aura_kernel, kernel_available
from aura_build.schema import SCHEMA_VERSION, validate_episode

from aura_build.schema import SCHEMA_VERSION
from aura_build.trajectory import TrajectoryWriter


def _fixture_episode(**overrides):
    ep = {
        "schema_version": SCHEMA_VERSION,
        "episode_id": "ep-kernel-fixture",
        "ts_start": "2026-01-01T00:00:00+00:00",
        "ts_end": "2026-01-01T00:00:01+00:00",
        "prompt": "fixture",
        "runtime": {
            "mode": "simulated",
            "kernel": "aura",
            "incr_proven": False,
            "fiber_live": False,
        },
        "harness": {"l3_online": False, "actions": []},
        "worldlines": [
            {"id": "wl-0", "eval": {"fitness": 0.9}, "mutations": [{"summary": "a"}]},
            {"id": "wl-1", "eval": {"fitness": 0.4}, "mutations": [{"summary": "b"}]},
        ],
        "selected_id": "wl-0",
    }
    ep.update(overrides)
    return ep


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
    assert ep["harness"]["l1_backend"] == "hot-strategy"


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
    assert ep["harness"]["l1_backend"] == "hot-strategy"
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
    assert ep["harness"]["l1_backend"] == "hot-strategy"


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
    assert honesty.get("l1_backend") in ("hot-strategy", "file")
    l1 = snap.get("l1") or {}
    assert l1.get("available") is True
    assert l1.get("preferred") == "hot-strategy"


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
    jsonl = tmp_path / "ep.jsonl"
    ep = _fixture_episode()
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


def test_cli_export_refuses_when_force_python(tmp_path: Path, monkeypatch) -> None:
    """FORCE_PYTHON: export refuses — JSON+redaction is Aura-only; Parquet is adapter."""
    from aura_build.cli import main

    monkeypatch.setenv("AURA_BUILD_FORCE_PYTHON", "1")
    rc = main(
        [
            "export",
            "--out",
            str(tmp_path / "batch.json"),
            "--no-parquet",
        ]
    )
    assert rc == 2



def test_kernel_acp_hooks_status_start(tmp_path: Path) -> None:
    hooks = invoke_aura_kernel(
        "acp",
        {"AURA_BUILD_ACP_OP": "hooks", "AURA_BUILD_ACP_JSON": "1"},
        harness_root=tmp_path,
    )
    assert hooks.via == "aura"
    assert hooks.ok
    assert (hooks.response or {}).get("kernel") == "aura"
    for name in ("start_session", "list_worldlines", "promote", "discard", "export"):
        assert name in ((hooks.response or {}).get("hooks") or {})

    start = invoke_aura_kernel(
        "acp",
        {
            "AURA_BUILD_ACP_OP": "start",
            "AURA_BUILD_ACP_PROMPT": "pytest acp",
        },
        harness_root=tmp_path,
    )
    assert start.via == "aura" and start.ok
    assert (tmp_path / "session.json").is_file()
    st = (start.response or {}).get("status") or {}
    assert st.get("kernel") == "aura"
    honesty = st.get("honesty") or {}
    assert honesty.get("incr_proven") is False
    assert honesty.get("fiber_live") is False

    status = invoke_aura_kernel(
        "acp",
        {"AURA_BUILD_ACP_OP": "status"},
        harness_root=tmp_path,
    )
    assert status.via == "aura" and status.ok
    st2 = (status.response or {}).get("status") or {}
    assert st2.get("session_id")
    assert (st2.get("honesty") or {}).get("incr_proven") is False
    assert (st2.get("honesty") or {}).get("fiber_live") is False


def test_kernel_acp_worldlines_discard_promote(tmp_path: Path) -> None:
    # Seed workspace layout expected by aura/acp.aura (no Python WorldlineWorkspace)
    ws = tmp_path / "ws"
    cand = ws / "candidates"
    for name in ("wl-0", "wl-1"):
        d = cand / name
        d.mkdir(parents=True)
        (d / "REF").write_text(name + "\n", encoding="utf-8")
    (ws / "PARENT").write_text("parent\n", encoding="utf-8")
    rows = invoke_aura_kernel(
        "acp",
        {
            "AURA_BUILD_ACP_OP": "worldlines",
            "AURA_BUILD_ACP_WORKSPACE": str(ws),
            "AURA_BUILD_ACP_JSON": "1",
        },
        harness_root=tmp_path,
    )
    assert rows.via == "aura" and rows.ok
    wls = (rows.response or {}).get("worldlines") or []
    assert len(wls) >= 2

    disc = invoke_aura_kernel(
        "acp",
        {
            "AURA_BUILD_ACP_OP": "discard",
            "AURA_BUILD_ACP_WORKSPACE": str(ws),
            "AURA_BUILD_ACP_REF": "wl-1",
            "AURA_BUILD_ACP_REASON": "pytest_discard",
        },
        harness_root=tmp_path,
    )
    assert disc.via == "aura" and disc.ok
    result = (disc.response or {}).get("result") or {}
    assert result.get("discarded") == "wl-1"
    assert result.get("fiber_live") is False
    assert result.get("kernel") == "aura"
    assert (ws / "candidates" / "wl-1" / "DISCARDED").is_file()

    prom = invoke_aura_kernel(
        "acp",
        {
            "AURA_BUILD_ACP_OP": "promote",
            "AURA_BUILD_ACP_L2_ID": "specialist.acp.pytest.v0",
            "AURA_BUILD_ACP_L2_NOTES": "pytest",
        },
        harness_root=tmp_path,
    )
    assert prom.via == "aura" and prom.ok
    ref = (prom.response or {}).get("ref") or {}
    assert ref.get("stub") is True
    assert ref.get("kernel") == "aura"
    assert (tmp_path / "weights" / "specialist.acp.pytest.v0.json").is_file()


def test_cli_acp_prefer_aura_and_force_python(tmp_path: Path, monkeypatch) -> None:
    from aura_build.cli import main

    monkeypatch.delenv("AURA_BUILD_FORCE_PYTHON", raising=False)
    rc = main(["acp", "start", "--prompt", "cli aura", "--harness-root", str(tmp_path)])
    assert rc == 0
    # status should mention kernel=aura when binary healthy
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["acp", "status", "--harness-root", str(tmp_path)])
    assert rc == 0
    out = buf.getvalue()
    assert "incr_proven=False" in out or "incr_proven=#f" in out
    assert "kernel=aura" in out
    assert "fiber_live=False" in out or "fiber_live=false" in out or "fiber_live=#f" in out

    monkeypatch.setenv("AURA_BUILD_FORCE_PYTHON", "1")
    import io as _io
    from contextlib import redirect_stderr
    err = _io.StringIO()
    with redirect_stderr(err):
        rc = main(["acp", "status", "--harness-root", str(tmp_path)])
    assert rc == 2
    assert "python_deprecated" in err.getvalue()


def test_kernel_tui_status(tmp_path: Path) -> None:
    # seed session via acp start
    start = invoke_aura_kernel(
        "acp",
        {"AURA_BUILD_ACP_OP": "start", "AURA_BUILD_ACP_PROMPT": "tui pytest"},
        harness_root=tmp_path,
    )
    assert start.via == "aura" and start.ok

    kr = invoke_aura_kernel(
        "tui",
        {"AURA_BUILD_TUI_JSON": "0"},
        harness_root=tmp_path,
    )
    assert kr.via == "aura" and kr.ok
    assert (kr.response or {}).get("kernel") == "aura"
    st = (kr.response or {}).get("status") or {}
    assert st.get("kernel") == "aura"
    honesty = st.get("honesty") or {}
    assert honesty.get("incr_proven") is False
    assert honesty.get("fiber_live") is False
    out = kr.stdout or ""
    assert "aura-build tui" in out
    assert "kernel=aura" in out
    assert "incr_proven=True" not in out.replace("incr_proven=False", "")
    assert "incr_proven=False" in out
    assert "fiber_live=False" in out


def test_cli_tui_prefer_aura_and_force_python(tmp_path: Path, monkeypatch) -> None:
    from aura_build.cli import main
    import io
    from contextlib import redirect_stdout

    monkeypatch.delenv("AURA_BUILD_FORCE_PYTHON", raising=False)
    assert main(["acp", "start", "--prompt", "tui cli", "--harness-root", str(tmp_path)]) == 0

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(["tui", "--harness-root", str(tmp_path)])
    assert rc == 0
    out = buf.getvalue()
    assert "aura-build tui" in out
    assert "kernel=aura" in out
    assert "incr_proven=False" in out
    assert "fiber_live=False" in out or "fiber_live=false" in out

    bufj = io.StringIO()
    with redirect_stdout(bufj):
        rc = main(["tui", "--harness-root", str(tmp_path), "--json"])
    assert rc == 0
    data = json.loads(bufj.getvalue())
    assert data.get("kernel") == "aura"
    assert (data.get("honesty") or {}).get("incr_proven") is False
    assert (data.get("honesty") or {}).get("fiber_live") is False

    monkeypatch.setenv("AURA_BUILD_FORCE_PYTHON", "1")
    import io as _io
    from contextlib import redirect_stderr
    err = _io.StringIO()
    with redirect_stderr(err):
        rc = main(["tui", "--harness-root", str(tmp_path)])
    assert rc == 2
    assert "python_deprecated" in err.getvalue()


def test_kernel_harness_mutate_file_backend(tmp_path: Path, monkeypatch) -> None:
    """AURA_BUILD_L1_BACKEND=file keeps honest file mirror path."""
    monkeypatch.setenv("AURA_BUILD_L1_BACKEND", "file")
    out = tmp_path / "ep.jsonl"
    result = invoke_aura_kernel(
        "harness-mutate",
        {
            "AURA_BUILD_PROMPT": "file backend canary",
            "AURA_BUILD_SEED": "1",
            "AURA_BUILD_OUT": str(out),
            "AURA_BUILD_HARNESS_PATCHES": '{"worldline_count": 4}',
            "AURA_BUILD_FITNESS_PATCHES": "{}",
        },
        harness_root=tmp_path,
    )
    assert result.via == "aura"
    assert result.exit_code == 0
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["harness"]["l1_backend"] == "file"
    assert ep["harness"]["outcome"] == "discard"
    assert ep["runtime"]["fiber_live"] is False
    assert ep["runtime"]["incr_proven"] is False
