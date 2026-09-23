"""M3 harness config + canary propose→commit/heal/discard."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from aura_build.harness import (
    AUTOPROMOTE_ENV,
    HarnessConfig,
    autopropote_enabled,
    decide,
    load_harness,
    propose_mutate,
    save_harness,
    validate_harness,
)
from aura_build.orch import run_harness_canary
from aura_build.schema import validate_episode


def test_validate_rejects_zero_worldlines():
    cfg = HarnessConfig(worldline_count=0)
    assert any("worldline_count" in r for r in validate_harness(cfg))


def test_validate_rejects_bad_routing():
    cfg = HarnessConfig(routing="fiber-live")
    assert any("routing" in r for r in validate_harness(cfg))


def test_save_load_roundtrip(tmp_path: Path):
    root = tmp_path / ".aura-build"
    cfg = HarnessConfig(worldline_count=4, routing="auto")
    save_harness(cfg, root=root)
    got = load_harness(root)
    assert got.worldline_count == 4
    assert got.routing == "auto"


def test_propose_mutate_bumps_version(tmp_path: Path):
    root = tmp_path / ".aura-build"
    save_harness(HarnessConfig(version=2), root=root)
    prop = propose_mutate(patches={"worldline_count": 5}, root=root)
    assert prop.base.version == 2
    assert prop.proposed.version == 3
    assert prop.proposed.worldline_count == 5
    assert prop.mid.startswith("mid-")
    assert prop.shadow_profile.startswith("shadow:")


def test_autopropote_default_off(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(AUTOPROMOTE_ENV, raising=False)
    assert autopropote_enabled() is False
    assert autopropote_enabled(False) is False
    monkeypatch.setenv(AUTOPROMOTE_ENV, "1")
    assert autopropote_enabled() is True


def test_canary_rejects_bad_l1_before_default(tmp_path: Path):
    root = tmp_path / ".aura-build"
    save_harness(HarnessConfig(worldline_count=3), root=root)
    result = run_harness_canary(
        "canary bad L1",
        patches={"worldline_count": 0},
        harness_root=root,
        seed=1,
    )
    assert result.canary.accepted is False
    assert result.decision.outcome == "heal"
    assert result.decision.committed is False
    validate_episode(result.episode)
    assert result.episode["harness"]["mid"] == result.proposal.mid
    ops = [a["op"] for a in result.episode["harness"]["actions"]]
    assert "propose" in ops
    assert "canary" in ops
    assert "heal" in ops
    # Live harness unchanged.
    assert load_harness(root).worldline_count == 3
    assert result.episode["runtime"]["incr_proven"] is False


def test_canary_pass_discards_when_autopropote_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv(AUTOPROMOTE_ENV, raising=False)
    root = tmp_path / ".aura-build"
    save_harness(HarnessConfig(worldline_count=3), root=root)
    result = run_harness_canary(
        "canary ok discard",
        patches={"worldline_count": 4},
        harness_root=root,
        seed=7,
        autopropote=False,
    )
    assert result.canary.accepted is True
    assert result.decision.outcome == "discard"
    assert result.decision.committed is False
    assert load_harness(root).worldline_count == 3
    validate_episode(result.episode)
    ops = [a["op"] for a in result.episode["harness"]["actions"]]
    assert ops[-1] == "discard"


def test_canary_commit_when_autopropote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv(AUTOPROMOTE_ENV, raising=False)
    root = tmp_path / ".aura-build"
    save_harness(HarnessConfig(worldline_count=3, routing="simulated"), root=root)
    result = run_harness_canary(
        "canary ok commit",
        patches={"worldline_count": 4, "l2_weights_id": "specialist.stub.v0"},
        harness_root=root,
        seed=11,
        autopropote=True,
    )
    assert result.canary.accepted is True
    assert result.decision.outcome == "commit"
    assert result.decision.committed is True
    live = load_harness(root)
    assert live.worldline_count == 4
    assert live.l2_weights_id == "specialist.stub.v0"
    validate_episode(result.episode)
    assert result.episode["harness"]["l2_ref"]["stub"] is True
    assert result.episode["runtime"]["incr_proven"] is False


def test_decide_heal_on_reject(tmp_path: Path):
    root = tmp_path / ".aura-build"
    save_harness(HarnessConfig(), root=root)
    prop = propose_mutate(patches={"routing": "auto"}, root=root)
    from aura_build.harness import CanaryResult

    canary = CanaryResult(
        mid=prop.mid,
        accepted=False,
        reasons=["boom"],
        episode=None,
        baseline_fitness=0.5,
        canary_fitness=0.1,
        actions=[prop.action_propose()],
    )
    dec = decide(prop, canary, autopropote=True, root=root)
    assert dec.outcome == "heal"
    assert load_harness(root).routing == "simulated"
