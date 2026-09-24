"""Parse-gate / elitist / fitness-gradient helpers for multi-file MiniMax repair."""

from __future__ import annotations

from aura_build.llm_dogfood import (
    _aggregate_llm_parallel,
    _aura_parse_gate,
    _fitness_partial,
    _merge_sources_parse_gate,
    _parens_balanced,
    _repair_focus_files,
)


def test_parens_balanced_basic():
    assert _parens_balanced("(define (f x) (+ x 1))")[0] is True
    assert _parens_balanced("(define (f x) (+ x 1")[0] is False


def test_parens_ignores_string_and_comment():
    src = '; (comment open\n(define (f) "q ( paren")\n'
    assert _parens_balanced(src)[0] is True


def test_merge_rejects_unbalanced_keeps_base(tmp_path):
    base = {
        "main.aura": "(define (main) 1)\n",
        "order.aura": '(define (order-place) "x")\n',
    }
    proposed = {
        "main.aura": "(define (main) (+ 1\n",  # unbalanced
        "order.aura": '(define (order-place) "partial")\n',
    }
    merged, notes = _merge_sources_parse_gate(
        base, proposed, files=["main.aura", "order.aura"], aura_bin=None
    )
    assert merged["main.aura"] == base["main.aura"]
    assert "partial" in merged["order.aura"]
    assert any(r.get("file") == "main.aura" for r in notes.get("rejected") or [])


def test_fitness_line_gradient_beats_flat_quarter():
    expect = "FILL1=partial\nLEFT1=3\nRISK=reject\nSTP=0\nCXL=cancelled\n"
    stdout = "FILL1=partial\nLEFT1=3\nRISK=reject\n"
    fit, meta = _fitness_partial(
        passed=False,
        structure_ok=True,
        has_error=False,
        stdout=stdout,
        stderr="",
        expect_text=expect,
    )
    assert fit > 0.25
    assert meta["expect_hits"] == 3
    assert meta["expect_total"] == 5


def test_aggregate_llm_parallel_prefers_fiber_over_final_serial():
    rounds = [
        {"round": 0, "llm_parallel": "fiber", "llm_parallel_ok": True},
        {"round": 1, "llm_parallel": "fiber", "llm_parallel_ok": True},
        {"round": 7, "llm_parallel": "fiber_serial", "llm_parallel_ok": True},
    ]
    val, ok, meta = _aggregate_llm_parallel(rounds)
    assert val == "fiber"
    assert meta["counts"]["fiber"] == 2
    assert meta["counts"]["fiber_serial"] == 1


def test_repair_focus_stages_bottom_up():
    files = [
        "idemp.aura",
        "match.aura",
        "order.aura",
        "main.aura",
        "ledger.aura",
        "fee.aura",
    ]
    early = _repair_focus_files(files, round_i=0, err="stub", prev_sources=None)
    assert "ledger.aura" in early or "idemp.aura" in early
    late = _repair_focus_files(
        files, round_i=5, err="FILL1=filled expected partial", prev_sources=None
    )
    assert "main.aura" in late or "order.aura" in late


def test_expect_literal_hardcode_hits_show_count():
    from aura_build.llm_dogfood import _expect_literal_hardcode_hits

    src = '(show "FILL1" (f))\n(show "STP" 0)\n(show "COUNT" 10)\n'
    hits = _expect_literal_hardcode_hits(src, "FILL1=partial\nSTP=0\nCOUNT=10\n")
    assert "STP=0" in hits and "COUNT=10" in hits
    assert "FILL1=partial" not in hits  # computed, not literal partial string as sole arg matching... 
    # (show "FILL1" (f)) should not hit FILL1=partial
    assert _expect_literal_hardcode_hits('(show "COUNT" c)', "COUNT=10") == []
