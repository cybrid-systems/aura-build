"""Soft-materialized pick-best select helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from aura_build.soft_select import (
    HELPER_PATH,
    extract_pick_best_lambda,
    read_helper_src,
    select_explorer_soft,
    soft_pick_best_score,
)


def test_extract_lambda_from_shipped_helper():
    src = read_helper_src(Path("."))
    assert src is not None
    lam = extract_pick_best_lambda(src)
    assert lam is not None
    assert lam.startswith("(lambda (xs)")
    assert "letrec" in lam or "loop" in lam


def test_host_fallback_no_session():
    got = soft_pick_best_score([2, 9, 4, 7, 1], sess=None)
    assert got["ok"] is True
    assert got["value"] == 9
    assert got["via"] == "host_fallback"
    assert got["reason"] == "no_session"
    assert got["helper"] == HELPER_PATH


def test_host_fallback_helper_missing(tmp_path: Path):
    got = soft_pick_best_score([1, 3, 2], sess=MagicMock(), repo=tmp_path)
    assert got["via"] == "host_fallback"
    assert got["reason"] == "helper_missing"
    assert got["value"] == 3


def test_soft_ok_when_session_returns_host_max():
    sess = MagicMock()
    sess.raw_line.return_value = {"status": "ok", "value": "9"}
    got = soft_pick_best_score([2, 9, 4], sess=sess, repo=Path("."))
    assert got["via"] == "soft_pick_best"
    assert got["value"] == 9
    assert sess.raw_line.called
    form = sess.raw_line.call_args[0][0]
    assert "pick-best" in form and "(list 2 9 4)" in form


def test_soft_mismatch_falls_back_to_host():
    sess = MagicMock()
    sess.raw_line.return_value = {"status": "ok", "value": "2"}  # wrong
    got = soft_pick_best_score([2, 9, 4], sess=sess, repo=Path("."))
    assert got["via"] == "host_fallback"
    assert got["reason"] == "soft_mismatch:2"
    assert got["value"] == 9


def test_soft_eval_fail_falls_back():
    sess = MagicMock()
    sess.raw_line.return_value = {"status": "error", "msg": "boom"}
    got = soft_pick_best_score([5, 1], sess=sess, repo=Path("."))
    assert got["via"] == "host_fallback"
    assert got["value"] == 5


def test_select_explorer_tie_break():
    sess = MagicMock()
    sess.raw_line.return_value = {"status": "ok", "value": "5"}
    explorers = [
        {"name": "a", "hits": 5, "ok": True},
        {"name": "baseline", "hits": 5, "ok": True},
        {"name": "b", "hits": 3, "ok": True},
    ]
    best, pick = select_explorer_soft(
        explorers,
        score_key="hits",
        sess=sess,
        repo=Path("."),
        tie_key=lambda e: (int(e["hits"]), 0 if e["name"] != "baseline" else -1, e["name"]),
    )
    assert pick["via"] == "soft_pick_best"
    assert best is not None
    assert best["name"] == "a"  # non-baseline wins tie at hits=5
