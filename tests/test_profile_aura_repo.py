"""M2 aura-repo profile: detection, fitness hooks, incr_proven=false."""

from __future__ import annotations

from pathlib import Path

import pytest

from aura_build.orch import OrchConfig, run_episode
from aura_build.profile_aura_repo import (
    AuraRepoProfile,
    detect_aura_repo,
    evaluate_candidate,
    resolve_profile,
    run_build_hook,
)
from aura_build.schema import validate_episode


def test_detect_aura_grok_when_present():
    found = detect_aura_repo("/workspace/aura-grok")
    # Box may or may not have it; if present must have build.py.
    if Path("/workspace/aura-grok/build.py").is_file():
        assert found is not None
        assert (found / "build.py").is_file()
    else:
        assert found is None or (found / "build.py").is_file()


def test_resolve_profile_explicit_missing(tmp_path: Path, monkeypatch):
    # Empty explicit dir: fall through to defaults; with defaults cleared → None
    monkeypatch.delenv("AURA_REF", raising=False)
    monkeypatch.setattr(
        "aura_build.profile_aura_repo._DEFAULT_REFS",
        (),
    )
    assert resolve_profile(str(tmp_path / "nope")) is None


def test_resolve_profile_with_build_py(tmp_path: Path):
    root = tmp_path / "aura"
    root.mkdir()
    (root / "build.py").write_text("print('ok')\n", encoding="utf-8")
    (root / "tests").mkdir()
    prof = resolve_profile(str(root))
    assert prof is not None
    assert prof.fitness_source == "build.py"
    assert prof.incr_proven is False
    assert prof.incr_claimed is True
    d = prof.to_runtime_dict()
    assert d["id"] == "aura-repo"
    assert d["incr_proven"] is False


def test_evaluate_simulated_fallback(tmp_path: Path):
    root = tmp_path / "aura"
    root.mkdir()
    (root / "build.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
    prof = AuraRepoProfile(
        root=root,
        build_py=root / "build.py",
        has_tests=False,
        fitness_source="build.py",
        incr_claimed=True,
        incr_proven=False,
    )
    # Force live command that fails → simulated notes
    fit = evaluate_candidate(
        prof,
        prompt="p",
        seed=1,
        index=0,
        try_live=True,
        live_command=["python3", "-c", "raise SystemExit(2)"],
    )
    assert fit.incr_proven is False
    assert fit.incr_claimed is True
    assert fit.fitness_source == "simulated"
    assert "simulated after live miss" in fit.notes
    metrics = fit.to_eval_metrics()
    assert "compile_ms" in metrics
    assert metrics["incr_proven"] is False


def test_run_build_hook_ok(tmp_path: Path):
    root = tmp_path / "aura"
    root.mkdir()
    build = root / "build.py"
    build.write_text("print('list')\n", encoding="utf-8")
    prof = AuraRepoProfile(
        root=root,
        build_py=build,
        has_tests=False,
        fitness_source="build.py",
    )
    ok, ms, notes = run_build_hook(
        prof, command=["python3", str(build)], timeout_s=10
    )
    assert ok is True
    assert ms >= 0
    assert "ok" in notes


def test_aura_repo_episode_shared_workspace(tmp_path: Path):
    root = tmp_path / "aura"
    root.mkdir()
    (root / "build.py").write_text("print('suites')\n", encoding="utf-8")
    ws = tmp_path / "wl"
    result = run_episode(
        "aura-repo dogfood",
        OrchConfig(
            seed=11,
            n_worldlines=3,
            mode="simulated",
            profile="aura-repo",
            aura_ref=str(root),
            workspace_dir=ws,
            keep_workspace=True,
            try_live_build=True,
            harness_root=tmp_path / ".aura-build",
        ),
    )
    validate_episode(result.episode)
    ep = result.episode
    assert ep["runtime"]["mode"] == "simulated"
    assert ep["runtime"]["profile"]["id"] == "aura-repo"
    assert ep["runtime"]["incr_proven"] is False
    assert ep["runtime"]["session_model"] == "shared_workspace_subprocess"
    assert ep["runtime"]["parent_ref"] == "wl-parent"
    assert len(ep["worldlines"]) == 3
    assert all(w.get("parent_id") == "wl-parent" for w in ep["worldlines"])
    assert all(w.get("stable_ref") for w in ep["worldlines"])
    assert len(ep["discarded"]) == 2
    assert result.selected.id not in {d["id"] for d in ep["discarded"]}
    # Metrics honesty
    for w in ep["worldlines"]:
        m = w["eval"]["metrics"]
        assert "compile_ms" in m
        assert m["incr_proven"] is False
        assert "incr_claimed" in m
    assert (ws / "meta.json").is_file()
    assert (ws / "candidates" / result.selected.id / "REF").is_file()


def test_aura_repo_no_live_build(tmp_path: Path):
    result = run_episode(
        "sim only",
        OrchConfig(
            seed=2,
            n_worldlines=2,
            profile="aura-repo",
            aura_ref=str(tmp_path),  # no build.py → stub profile
            try_live_build=False,
            workspace_dir=tmp_path / "ws",
            keep_workspace=True,
            harness_root=tmp_path / ".aura-build",
        ),
    )
    validate_episode(result.episode)
    assert result.episode["runtime"]["incr_proven"] is False
    sources = {
        w["eval"]["metrics"]["fitness_source"]
        for w in result.episode["worldlines"]
    }
    assert sources == {"simulated"}


def test_unknown_profile_rejected():
    with pytest.raises(ValueError, match="unknown profile"):
        run_episode("x", OrchConfig(profile="nope"))
