"""Issue #4333 — _session_score_src must not credit a held workspace's display.

A reused Soft session can keep the PREVIOUS candidate's workspace while
set-code still reports ok (adopt-if-held); the eval-current display then
scores the held program's CASE output on this candidate (soft_score_inflate
family: 28/64 explorers claiming 8/8 while oneshot of their own bytes got
0/8 with got={}). The harness now verifies the session actually adopted the
candidate source (current-source vs candidate, whitespace-insensitive) and
fails the explorer honestly (source_not_adopted) otherwise.

Pure fakes — no Soft binary required.
"""

from __future__ import annotations

from aura_build.soft_leetcode_runtime import _session_score_src

CAND = "(define (solve x) x)"
HELD = "(define (solve-held x) 0)"

TESTS = [{"id": 1, "expected": "true"}]


class FakeSession:
    """raw_line responder scripted per call pattern."""

    def __init__(
        self,
        *,
        adopted: bool,
        held_case_display: str = "CASE1=true",
        adopt_after_retry: bool = False,
    ) -> None:
        self.adopted = adopted
        self.adopt_after_retry = adopt_after_retry
        self.held_case_display = held_case_display
        self.set_code_calls = 0
        self.eval_calls = 0

    def raw_line(self, line: str, *, timeout_s: float = 30.0) -> dict:
        if line.startswith("(set-code "):
            self.set_code_calls += 1
            if self.adopt_after_retry and self.set_code_calls == 1:
                # first write races the workspace: reported ok, not adopted
                return {"status": "ok"}
            return {"status": "ok"}
        if "current-source" in line:
            src = CAND if (self.adopted or (self.adopt_after_retry and self.set_code_calls >= 2)) else HELD
            return {"status": "ok", "display": src}
        if line == "(eval-current)":
            self.eval_calls += 1
            # the held workspace's display — must never be credited when
            # the candidate was not adopted
            return {"status": "ok", "display": self.held_case_display}
        if line == "(run-cases)":
            return {"status": "ok", "display": "CASE1=true"}
        return {"status": "ok", "display": ""}


def test_adopted_credits_hits() -> None:
    sess = FakeSession(adopted=True)
    sc = _session_score_src(sess, CAND, TESTS)
    assert sc["ok"] is True
    assert sc["hits"] == 1
    assert sc["total"] == 1
    assert sess.eval_calls == 1


def test_not_adopted_fails_honestly() -> None:
    sess = FakeSession(adopted=False)
    sc = _session_score_src(sess, CAND, TESTS)
    # regression: pre-#4333 this returned the held program's hits=1
    assert sc["ok"] is False
    assert sc["hits"] == 0
    assert sc["reason"] == "source_not_adopted"
    # never evaluated the held program for this candidate
    assert sess.eval_calls == 0
    # one re-arm retry happened before the honest fail
    assert sess.set_code_calls == 2


def test_rearm_retry_adopts() -> None:
    sess = FakeSession(adopted=False, adopt_after_retry=True)
    sc = _session_score_src(sess, CAND, TESTS)
    assert sc["ok"] is True
    assert sc["hits"] == 1
    assert sess.eval_calls == 1
