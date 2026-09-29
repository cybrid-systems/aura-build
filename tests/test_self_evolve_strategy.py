"""Unit tests for adaptive self-evolve strategy + latency clock."""

from __future__ import annotations

import json
from pathlib import Path

from aura_build.self_evolve_strategy import EXPLORER_CAP_CEILING


def test_latency_clock_phases(tmp_path: Path):
    from aura_build.self_evolve_strategy import LatencyClock

    clock = LatencyClock(session="t")
    clock.start("session_start")
    clock.end("session_start", ok=True)
    clock.mark("explorer_loop", ok=True, fiber_live=True, n=8, ms=1200)
    clock.mark("stamp", ok=True, fiber_live=True, ms=50)
    clock.mark("oneshot_fallback", ok=True, fiber_live=False, ms=0)
    clock.mark("pursue_round", ok=True, ms=3000)
    clock.mark("materialize_commit", ok=True, ms=100)
    s = clock.summary(fiber_live=True)
    assert s["total_ms"] >= 0
    assert any(p["phase"] == "explorer_loop" for p in s["phases"])
    assert "fiber_live=true" in s["progress"]
    assert "explorer_loop=1200ms/ok/n=8" in s["progress"]


def test_effective_explorer_cap_never_raises():
    from aura_build.self_evolve_strategy import effective_explorer_cap

    assert effective_explorer_cap({"explorer_cap": 32}) == 32
    assert effective_explorer_cap({"explorer_cap": 64}) == EXPLORER_CAP_CEILING
    assert effective_explorer_cap({"explorer_cap": 4}) == 8  # floor
    assert effective_explorer_cap({"explorer_cap": 32}, requested=16) == 16


def test_soft_native_skip_and_already_green(tmp_path: Path):
    from aura_build.self_evolve_strategy import should_skip_helper_rematerialize

    helper = tmp_path / "aura" / "soft_find.aura"
    helper.parent.mkdir(parents=True)
    helper.write_text("; stub\n", encoding="utf-8")
    state = {
        "last_helpers_all_green": False,
        "last_nothing_to_commit": False,
        "soft_native_green": {"find": True},
    }
    skip, reason = should_skip_helper_rematerialize(
        state, helper_key="find_helper", helper_path=helper, soft_native_green={"find": True}
    )
    assert skip and reason.startswith("soft_native_skip")

    state2 = {
        "last_helpers_all_green": True,
        "last_nothing_to_commit": True,
        "soft_native_green": {},
    }
    skip2, reason2 = should_skip_helper_rematerialize(
        state2, helper_key="starts_helper", helper_path=helper, soft_native_green={}
    )
    assert skip2 and reason2 == "already_green_nothing_to_commit"

    missing = tmp_path / "missing.aura"
    skip3, reason3 = should_skip_helper_rematerialize(
        state2, helper_key="starts_helper", helper_path=missing
    )
    assert not skip3 and reason3 == "missing_file"


def test_observe_hang_lowers_cap_and_prefer_oneshot(tmp_path: Path):
    from aura_build.self_evolve_strategy import (
        load_strategy,
        observe_runtime_round,
        save_strategy,
        should_prefer_oneshot,
    )

    repo = tmp_path
    state = load_strategy(repo)
    assert state["explorer_cap"] == EXPLORER_CAP_CEILING
    state = observe_runtime_round(
        state,
        helpers={"helper": {"ok": True}, "find_helper": {"ok": True}},
        explorers=[{"ok": False, "status": "timeout", "ms": 15000}],
        fiber_live=False,
        fallback_oneshot=True,
        hang_or_timeout=True,
        nothing_to_commit=False,
        latency={"total_ms": 90000, "progress": "x"},
    )
    assert state["explorer_cap"] <= 32  # hang → ceil//2 with FIBER=64
    assert should_prefer_oneshot(state)
    save_strategy(repo, state)
    assert (repo / ".aura-build" / "self_evolve_strategy.json").is_file()


def test_observe_pursue_shrinks_then_ramps():
    from aura_build.self_evolve_strategy import (
        WORLDLINES_FAST,
        WORLDLINES_FULL,
        effective_worldlines,
        observe_pursue_round,
    )

    state = {
        "worldlines": WORLDLINES_FULL,
        "worldlines_idx": 2,
        "notes": [],
    }
    state = observe_pursue_round(
        state, soft_ready=True, goal_met=True, ms=90_000
    )
    assert state["worldlines"] == 128  # one step down from 256
    state = observe_pursue_round(
        state, soft_ready=True, goal_met=True, ms=80_000
    )
    assert state["worldlines"] == WORLDLINES_FAST
    # miss ramps up
    state = observe_pursue_round(
        state, soft_ready=False, goal_met=False, ms=60_000
    )
    assert state["worldlines"] == 128
    assert effective_worldlines(state, requested=256) == state["worldlines"]
    assert effective_worldlines(state, requested=32) == 32  # explicit low sticky


def test_fiber_explorer_cap_ceiling_matches_runtime():
    from aura_build import self_evolve_runtime as m

    assert m.FIBER_EXPLORER_CAP == 64
    assert m.FIBER_EXPLORER_CAP == EXPLORER_CAP_CEILING


def test_cmd_runtime_source_has_latency_and_strategy():
    import inspect
    from aura_build import self_evolve_runtime as m

    src = inspect.getsource(m.cmd_runtime)
    assert "LatencyClock" in src
    assert "self_evolve_latency" in src
    assert "denseness_per_helper" in src
    assert "soft_native_probe" in src
    assert 'result["list_take_helper"]' in src or "list_take_helper" in src
    assert m.DEFAULT_SOFT.endswith("build/aura")


def test_already_green_skip_without_nothing_to_commit(tmp_path: Path) -> None:
    from aura_build.self_evolve_strategy import should_skip_helper_rematerialize

    helper = tmp_path / "soft_worldline_pick.aura"
    helper.write_text("; stub\n", encoding="utf-8")
    st = {
        "last_helpers_all_green": True,
        "last_nothing_to_commit": False,
        "soft_native_green": {},
    }
    skip, reason = should_skip_helper_rematerialize(
        st, helper_key="helper", helper_path=helper
    )
    assert skip is True
    assert reason == "already_green_skip"
