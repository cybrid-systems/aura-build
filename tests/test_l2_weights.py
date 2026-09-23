"""M3 L2 stub resolve-by-id."""

from __future__ import annotations

from aura_build.l2_weights import resolve_l2_weights
from aura_build.orch import OrchConfig, run_episode
from aura_build.schema import validate_episode


def test_resolve_none():
    assert resolve_l2_weights(None) is None
    assert resolve_l2_weights("") is None
    assert resolve_l2_weights("null") is None


def test_resolve_stub_by_id():
    ref = resolve_l2_weights("specialist.compile.v0")
    assert ref is not None
    assert ref.weights_id == "specialist.compile.v0"
    assert ref.loaded is True
    assert ref.stub is True


def test_episode_records_l2_ref():
    result = run_episode(
        "l2 stub",
        OrchConfig(seed=5, n_worldlines=2, l2_weights_id="specialist.demo.v0"),
    )
    validate_episode(result.episode)
    assert result.episode["harness"]["l2_weights_id"] == "specialist.demo.v0"
    assert result.episode["harness"]["l2_ref"]["stub"] is True
    assert result.episode["runtime"]["incr_proven"] is False
