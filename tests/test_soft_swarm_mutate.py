"""Soft swarm local multi-mutation + prompt feedback product tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from aura_build.prompt_feedback import (
    build_prompt_variation,
    classify_no_gain_cause,
    load_feedback,
    observe_transform_feedback,
    save_feedback,
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


def test_local_multi_mutate_produces_distinct():
    cands = local_multi_mutate(SAMPLE, n=12, seed=7)
    assert len(cands) >= 4
    srcs = {c["src"] for c in cands}
    assert len(srcs) >= 4
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


def test_feedback_roundtrip(tmp_path: Path):
    repo = tmp_path
    (repo / ".aura-build").mkdir()
    st = load_feedback(repo)
    st = observe_transform_feedback(
        st,
        slug="flood-fill",
        ok=False,
        reason="no_gain_vs_baseline",
        selected_hits=0,
        baseline_hits=4,
        total=8,
        no_gain_cause="sock_score_collapse",
        llm_via="host_parallel",
        mutate_ops=["edsl-lit-tweak"],
    )
    save_feedback(repo, st)
    loaded = load_feedback(repo)
    assert loaded["last"]["cause"] == "sock_score_collapse"
    suffix = build_prompt_variation(
        slug="flood-fill",
        fail_details=[{"id": 1}],
        feedback=loaded,
        variant_i=3,
        mutate_seed_ops=["edsl-lit-tweak"],
    )
    assert "Feedback-accumulated" in suffix
    assert "edsl-lit-tweak" in suffix


def test_soft_ant_rank_fallback_without_soft(tmp_path: Path):
    with patch("aura_build.soft_swarm_mutate._soft_oneshot", return_value={"ok": False, "display": ""}):
        r = soft_ant_rank_ops(aura_bin="/no/such/aura")
    assert r["via"] == "host_fallback"
    assert "edsl-lit-tweak" in r["ranked_ops"]


def test_swarm_mutate_candidates_host_path():
    with patch(
        "aura_build.soft_swarm_mutate.soft_ant_rank_ops",
        return_value={"ok": False, "via": "host_fallback", "ranked_ops": ["edsl-lit-tweak", "edsl-op-swap"]},
    ), patch(
        "aura_build.soft_swarm_mutate.soft_swarm_probe",
        return_value={"ok": False, "via": "soft_fail", "kind": "pso"},
    ):
        cands, meta = swarm_mutate_candidates(SAMPLE, n=8, aura_bin="/no/aura")
    assert meta["path"] == "soft_swarm_local_multi_mutate"
    assert len(cands) >= 3
