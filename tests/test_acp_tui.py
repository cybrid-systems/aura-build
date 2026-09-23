"""M5 ACP hooks + TUI status stub."""

from __future__ import annotations

import json
from pathlib import Path

from aura_build.acp import (
    acp_discard_worldline,
    acp_list_worldlines,
    acp_start_session,
    acp_status,
    describe_hooks,
)
from aura_build.cli import main
from aura_build.orch import OrchConfig, run_episode
from aura_build.trajectory import TrajectoryWriter
from aura_build.tui import format_status
from aura_build.worldline import WorldlineWorkspace


def test_describe_hooks():
    hooks = describe_hooks()
    for name in ("start_session", "list_worldlines", "promote", "discard", "export"):
        assert name in hooks


def test_session_status_and_tui(tmp_path: Path, capsys):
    root = tmp_path / ".aura-build"
    traj = tmp_path / "traj.jsonl"
    result = run_episode("acp demo", OrchConfig(seed=1, n_worldlines=2))
    TrajectoryWriter(traj).append(result.episode)

    st = acp_start_session(
        prompt="acp demo",
        root=root,
        traj_path=traj,
        episode_id=result.episode["episode_id"],
    )
    assert st.session_id
    assert st.last_traj_path == str(traj)
    text = format_status(st)
    assert "aura-build tui" in text
    assert "incr_proven=False" in text
    assert "fiber_live=False" in text

    status = acp_status(root=root)
    assert status.last_episode_id == result.episode["episode_id"]


def test_list_worldlines_from_traj(tmp_path: Path):
    traj = tmp_path / "ep.jsonl"
    result = run_episode("wl list", OrchConfig(seed=2, n_worldlines=3))
    TrajectoryWriter(traj).append(result.episode)
    rows = acp_list_worldlines(traj_path=traj)
    assert len(rows) >= 3
    roles = {r["role"] for r in rows}
    assert "selected" in roles or "candidate" in roles


def test_discard_worldline_workspace(tmp_path: Path):
    ws_root = tmp_path / "ws"
    ws = WorldlineWorkspace.create(ws_root, n_candidates=2)
    payload = acp_discard_worldline("wl-1", workspace=ws_root, reason="test_discard")
    assert payload["discarded"] == "wl-1"
    assert payload["fiber_live"] is False
    assert (ws_root / "candidates" / "wl-1" / "DISCARDED").is_file()
    meta = json.loads((ws_root / "meta.json").read_text())
    assert any(d["id"] == "wl-1" for d in meta["discarded"])


def test_cli_tui_acp_l2(tmp_path: Path):
    root = tmp_path / ".aura-build"
    assert main(["acp", "hooks"]) == 0
    assert main(["acp", "start", "--prompt", "x", "--harness-root", str(root)]) == 0
    assert main(["tui", "--harness-root", str(root), "--json"]) == 0
    assert (
        main(
            [
                "l2",
                "promote",
                "--id",
                "specialist.cli.v0",
                "--notes",
                "cli",
                "--harness-root",
                str(root),
            ]
        )
        == 0
    )
    assert main(["l2", "show", "--id", "specialist.cli.v0", "--harness-root", str(root)]) == 0
    assert main(["l2", "list", "--harness-root", str(root), "--json"]) == 0
    # ACP promote alias (Aura-first when healthy; FORCE_PYTHON covered in kernel tests)
    assert main([
        "acp", "promote", "--id", "specialist.acp.cli.v0",
        "--notes", "cli", "--harness-root", str(root),
    ]) == 0
