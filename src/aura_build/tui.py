"""Minimal TUI / status surface (M5) — stdlib-first stub.

Inspired by grok-build's host layering (headless first, TUI later), **not** a
full-screen agent chrome and **not** postman physics. Prefer
``aura-build tui`` as a session status printer; a Textual/rich loop is deferred
until deps stay light.

Prints: session id, harness routing, L2 stub presence, last trajectory path,
worldline count, honesty flags. Headless ``run`` remains SSOT.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aura_build.acp import SessionStatus, acp_status, describe_hooks

__all__ = ["format_status", "run_tui_stub"]


def format_status(status: SessionStatus) -> str:
    """Human-readable status block for stdout."""
    h = status.honesty or {}
    lines = [
        "aura-build tui (M5 stub — stdlib status; not a full TUI)",
        f"  session_id     = {status.session_id or '-'}",
        f"  started        = {status.started or '-'}",
        f"  prompt         = {(status.prompt or '-')[:60]}",
        f"  harness_id     = {status.harness_id or '-'}",
        f"  routing        = {status.harness_routing or '-'}",
        f"  worldline_count= {status.worldline_count if status.worldline_count is not None else '-'}",
        f"  l2_weights_id  = {status.l2_weights_id or '-'}",
        f"  l2_artifact    = {status.l2_artifact_present}",
        f"  workspace      = {status.workspace or '-'}",
        f"  last_traj_path = {status.last_traj_path or '-'}",
        f"  last_episode   = {status.last_episode_id or '-'}",
        "  honesty:",
        f"    incr_proven={h.get('incr_proven', False)} "
        f"fiber_live={h.get('fiber_live', False)} "
        f"l3_online={h.get('l3_online', False)} "
        f"l2_stub_metadata_only={h.get('l2_stub_metadata_only', True)}",
        "  acp hooks: " + ", ".join(sorted(describe_hooks())),
        "  tip: aura-build acp hooks | aura-build run | aura-build l2 promote",
    ]
    return "\n".join(lines) + "\n"


def run_tui_stub(
    *,
    root: Path | str | None = None,
    traj_search: list[Path] | None = None,
    as_json: bool = False,
) -> dict[str, Any]:
    """Gather status and return dict (CLI prints text or JSON)."""
    status = acp_status(root=root, traj_search=traj_search)
    return status.to_dict()
