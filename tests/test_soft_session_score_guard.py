"""Issue #4333 — _session_score_src must not credit a held workspace's display.

A reused Soft serve session can keep the PREVIOUS candidate's workspace
while set-code still reports ok (adopt-if-held); the transaction display
then scores the held program's CASE output on this candidate
(soft_score_inflate family: 28/64 explorers claiming 8/8 while oneshot of
their own bytes got 0/8 with got={}). Two guards:
1. set-code + eval-current run as ONE atomic begin transaction (a split
   across serve round-trips lets a parallel propose fiber re-set-code the
   shared workspace in between).
2. the session must have actually adopted the candidate source
   (current-source vs candidate, whitespace-insensitive) before the
   transaction display is credited — otherwise the explorer fails honestly
   (source_not_adopted, hits=0).

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
        adopt_after_retry: bool = False,
    ) -> None:
        self.adopted = adopted
        self.adopt_after_retry = adopt_after_retry
        self.set_code_calls = 0
        self.eval_calls = 0

    def _effective_adopted(self) -> bool:
        return self.adopted or (self.adopt_after_retry and self.set_code_calls >= 2)

    def raw_line(self, line: str, *, timeout_s: float = 30.0) -> dict:
        if "(set-code " in line and "(eval-current)" in line:
            # atomic #4333 transaction: set-code + eval-current in one eval.
            # The display is the candidate's own CASE output when adopted;
            # the held program's CASE output when not (the contamination
            # face — both print the same line here, the owner differs).
            self.set_code_calls += 1
            self.eval_calls += 1
            return {"status": "ok", "display": "CASE1=true"}
        if "current-source" in line:
            src = CAND if self._effective_adopted() else HELD
            return {"status": "ok", "display": src}
        if line == "(run-cases)":
            return {"status": "ok", "display": "CASE1=true"}
        return {"status": "ok", "display": ""}


def test_adopted_credits_hits() -> None:
    sess = FakeSession(adopted=True)
    sc = _session_score_src(sess, CAND, TESTS)
    assert sc["ok"] is True
    assert sc["hits"] == 1
    assert sc["total"] == 1
    assert sc.get("reason") is None
    assert sess.eval_calls == 1


def test_not_adopted_fails_honestly() -> None:
    sess = FakeSession(adopted=False)
    sc = _session_score_src(sess, CAND, TESTS)
    # regression: pre-#4333 this returned the held program's hits=1
    assert sc["ok"] is False
    assert sc["hits"] == 0
    assert sc["reason"] == "source_not_adopted"
    # two attempts (original + one re-arm) before the honest fail
    assert sess.set_code_calls == 2


def test_rearm_retry_adopts() -> None:
    sess = FakeSession(adopted=False, adopt_after_retry=True)
    sc = _session_score_src(sess, CAND, TESTS)
    assert sc["ok"] is True
    assert sc["hits"] == 1
    assert sess.eval_calls == 2


def test_atomic_transaction_single_round_trip() -> None:
    # set-code + eval-current must be one raw_line (begin) — a split lets a
    # parallel propose fiber re-set-code the shared workspace in between.
    seen: list[str] = []

    class Spy(FakeSession):
        def raw_line(self, line: str, *, timeout_s: float = 30.0) -> dict:
            seen.append(line)
            return super().raw_line(line, timeout_s=timeout_s)

    sess = Spy(adopted=True)
    _session_score_src(sess, CAND, TESTS)
    assert any(
        "(begin (set-code " in line and "(eval-current))" in line for line in seen
    ), "set-code + eval-current must share one atomic begin"
    assert not any(line.startswith("(set-code ") for line in seen), (
        "no split set-code round-trip before the adopted transaction"
    )
