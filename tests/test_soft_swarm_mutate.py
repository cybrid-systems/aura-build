"""Soft kernel swarm + feedback thin-adapter tests (brain in aura/*.aura)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from aura_build.prompt_feedback import (
    build_prompt_variation,
    classify_no_gain_cause,
    load_feedback,
)
from aura_build.soft_swarm_mutate import (
    local_multi_mutate,
    soft_ant_rank_ops,
    swarm_mutate_candidates,
)

SAMPLE = """(define (solve xs)
  (if (null? xs) 0 (+ 1 (solve (cdr xs)))))
(display "CASE0=")(display (solve (list 1 2)))(newline)
"""


def test_local_multi_mutate_is_kernel_seed_only():
    cands = local_multi_mutate(SAMPLE, n=8, seed=7)
    assert len(cands) >= 4
    assert all(c.get("via") == "kernel_swarm_seed" for c in cands)
    assert all(c.get("ops") for c in cands)


def test_classify_sock_vs_quality():
    explorers = [
        {"name": f"llm-{i}", "hits": 0, "reason": "set_code_failed", "transient": True}
        for i in range(10)
    ]
    assert classify_no_gain_cause(
        explorers=explorers, baseline_hits=4, selected_hits=0
    ) == "sock_transient"
    explorers2 = [
        {"name": "baseline", "hits": 4},
        {"name": "llm-0", "hits": 4},
        {"name": "llm-1", "hits": 3},
    ]
    assert classify_no_gain_cause(
        explorers=explorers2, baseline_hits=4, selected_hits=4
    ) == "quality_plateau"


def test_soft_ant_rank_uses_kernel_adapter():
    with patch(
        "aura_build.soft_swarm_mutate.run_kernel_swarm_mutate",
        return_value={
            "ok": True,
            "via": "soft_ant_pheromone",
            "ranked_ops": ["edsl-op-swap", "edsl-lit-tweak"],
            "kernel": "aura",
        },
    ):
        r = soft_ant_rank_ops(aura_bin="/no/such/aura")
    assert r["via"] == "soft_ant_pheromone"
    assert r["ranked_ops"][0] == "edsl-op-swap"
    assert r.get("kernel") == "aura"


def test_swarm_mutate_candidates_kernel_path():
    with patch(
        "aura_build.soft_swarm_mutate.run_kernel_swarm_mutate",
        return_value={
            "ok": True,
            "via": "soft_ant_pheromone",
            "ranked_ops": ["edsl-lit-tweak", "edsl-op-swap"],
            "kernel": "aura",
        },
    ), patch(
        "aura_build.soft_swarm_mutate.soft_swarm_probe",
        return_value={"ok": False, "via": "soft_fail", "kind": "pso"},
    ):
        cands, meta = swarm_mutate_candidates(SAMPLE, n=8, aura_bin="/no/aura", slug="t")
    assert meta["path"] == "kernel_swarm_mutate"
    assert meta["kernel"] == "aura"
    assert len(cands) >= 3


def test_feedback_load_missing(tmp_path: Path):
    (tmp_path / ".aura-build" / "memory").mkdir(parents=True)
    loaded = load_feedback(tmp_path, tmp_path / ".aura-build")
    assert loaded.get("kernel") == "aura"
    suffix = build_prompt_variation(
        slug="flood-fill",
        fail_details=[{"id": 1}],
        feedback=loaded,
        variant_i=0,
        mutate_seed_ops=["edsl-lit-tweak"],
        harness_root=tmp_path / ".aura-build",
        aura_bin="/no/aura",
    )
    assert "Soft" in suffix or "Kernel" in suffix or "failing" in suffix.lower()
