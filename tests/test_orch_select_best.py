"""Tests for simulated worldline select-best."""

from __future__ import annotations

import pytest

from aura_build.orch import OrchConfig, run_episode, select_best, Worldline
from aura_build.schema import validate_episode


def test_select_best_max_fitness():
    wls = [
        Worldline("wl-0", None, [], {"fitness": 0.2, "passed": False}),
        Worldline("wl-1", None, [], {"fitness": 0.9, "passed": True}),
        Worldline("wl-2", None, [], {"fitness": 0.5, "passed": True}),
    ]
    best, reason = select_best(wls)
    assert best.id == "wl-1"
    assert reason == "max_fitness"


def test_run_episode_writes_valid_schema():
    result = run_episode("demo select-best", OrchConfig(seed=7, n_worldlines=3))
    validate_episode(result.episode)
    assert result.episode["runtime"]["mode"] == "simulated"
    assert result.episode["selected_id"] == result.selected.id
    assert len(result.episode["worldlines"]) == 3
    assert result.episode["harness"]["l3_online"] is False


def test_deterministic_with_seed():
    a = run_episode("same", OrchConfig(seed=99, n_worldlines=3))
    b = run_episode("same", OrchConfig(seed=99, n_worldlines=3))
    fits_a = [w["eval"]["fitness"] for w in a.episode["worldlines"]]
    fits_b = [w["eval"]["fitness"] for w in b.episode["worldlines"]]
    assert fits_a == fits_b
    assert a.selected.id == b.selected.id


def test_l3_online_refused():
    with pytest.raises(ValueError, match="L3"):
        run_episode("x", OrchConfig(l3_online=True))


def test_custom_fitness_picks_last():
    def fit(prompt: str, seed: int, index: int) -> float:
        return float(index)

    result = run_episode("x", OrchConfig(n_worldlines=3, fitness_fn=fit, seed=1))
    assert result.selected.id == "wl-2"
