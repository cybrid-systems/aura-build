"""Stamp banner vs hash-literal agreement. Does not run MiniMax."""

from __future__ import annotations

from pathlib import Path

from aura_build.self_evolve_host import run_host_verify
from aura_build.stamp_banner import stamp_banner_agrees

_BOTH_FALSE = """
; incr_proven=false
; fiber_live=false
"incr_proven" #f
"fiber_live" #f
"""

_BOTH_TRUE = """
; incr_proven=true
; fiber_live=true
"incr_proven" #t
"fiber_live" #t
"""

_INCR_SPLIT = """
; incr_proven=true
; fiber_live=false
"incr_proven" #f
"fiber_live" #f
"""

_INCR_OTHER = """
; incr_proven=false
; fiber_live=false
"incr_proven" #t
"fiber_live" #f
"""

_FIBER_SPLIT = """
; incr_proven=false
; fiber_live=true
"incr_proven" #f
"fiber_live" #f
"""

_BANNER_ONLY = """
; incr_proven=false
; fiber_live=false
"""


def test_pairs_agree_or_disagree():
    assert stamp_banner_agrees(_BOTH_FALSE) is True
    assert stamp_banner_agrees(_BOTH_TRUE) is True
    assert stamp_banner_agrees(_INCR_SPLIT) is False
    assert stamp_banner_agrees(_INCR_OTHER) is False
    assert stamp_banner_agrees(_FIBER_SPLIT) is False
    assert stamp_banner_agrees(_BANNER_ONLY) is False


def _write_stamp(tmp_path: Path, text: str) -> None:
    path = tmp_path / "aura" / "self_evolve_stamp.aura"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_host_verify_stamp_on_tmp(tmp_path: Path):
    _write_stamp(tmp_path, _INCR_SPLIT)
    bad = run_host_verify(tmp_path, "stamp")
    assert bad["ok"] is False and bad["reason"] == "stamp_banner_mismatch"
    _write_stamp(tmp_path, _BOTH_FALSE)
    good = run_host_verify(tmp_path, "stamp")
    assert good["ok"] is True and good["reason"] == "stamp_ok"
    (tmp_path / "aura" / "self_evolve_stamp.aura").unlink()
    missing = run_host_verify(tmp_path, "stamp")
    assert missing["ok"] is False and missing["reason"] == "stamp_banner_mismatch"


def test_checked_in_stamp_agrees():
    root = Path(__file__).resolve().parents[1]
    text = (root / "aura" / "self_evolve_stamp.aura").read_text(encoding="utf-8")
    assert stamp_banner_agrees(text) is True
    result = run_host_verify(root, "stamp")
    assert result["ok"] is True and result["reason"] == "stamp_ok"
