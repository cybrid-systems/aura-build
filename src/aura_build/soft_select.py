"""Soft-materialized select-best via ``aura/soft_worldline_pick.aura``.

Uses Soft ``pick-best`` when a live Soft session can eval the Soft-materialized
helper (inline ``let``, no FlatAST wipe). Honest host ``max`` fallback when
helper missing, Soft eval fails, or Soft value disagrees with host max.
Never invents fiber_live / Soft Ready.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Sequence

HELPER_PATH = "aura/soft_worldline_pick.aura"

_LAMBDA_RE = re.compile(
    r"\(define\s+pick-best\s+(\(lambda\s*\(xs\).*)$",
    re.DOTALL,
)


def helper_path(repo: Path | None = None) -> Path:
    root = repo if repo is not None else Path.cwd()
    return Path(root) / HELPER_PATH


def read_helper_src(repo: Path | None = None) -> str | None:
    path = helper_path(repo)
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return text if "pick-best" in text else None


def extract_pick_best_lambda(src: str) -> str | None:
    """Extract Soft-unparsed ``(lambda (xs) …)`` from materialized helper."""
    m = _LAMBDA_RE.search(src)
    if not m:
        # Soft sometimes keeps (define (pick-best xs) …)
        m2 = re.search(
            r"\(define\s*\(\s*pick-best\s+xs\s*\)\s*(.*)\)\s*$",
            src,
            re.DOTALL,
        )
        if not m2:
            return None
        body = m2.group(1).strip()
        return f"(lambda (xs) {body})"
    lam = m.group(1).strip()
    # Drop trailing parens that closed outer (begin …) / file noise
    # Balance from first '(' of lambda
    if not lam.startswith("(lambda"):
        return None
    depth = 0
    end = None
    for i, ch in enumerate(lam):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        return None
    return lam[:end]


def soft_pick_best_score(
    scores: Sequence[int | float],
    *,
    sess: Any | None = None,
    repo: Path | None = None,
    helper_src: str | None = None,
    timeout_s: float = 8.0,
) -> dict[str, Any]:
    """Return max score via Soft ``pick-best`` when measured; else host max.

    ``via`` is ``soft_pick_best`` only when Soft eval returns ok and the value
    matches host ``max(scores)``. Otherwise ``host_fallback`` with reason.
    """
    nums = [int(s) for s in scores]
    if not nums:
        return {
            "ok": False,
            "value": None,
            "via": "empty",
            "reason": "no_scores",
            "helper": HELPER_PATH,
        }
    host_max = max(nums)
    base = {
        "ok": True,
        "value": host_max,
        "helper": HELPER_PATH,
        "host_max": host_max,
        "n_scores": len(nums),
    }
    if sess is None:
        return {**base, "via": "host_fallback", "reason": "no_session"}

    src = helper_src if helper_src is not None else read_helper_src(repo)
    if not src:
        return {**base, "via": "host_fallback", "reason": "helper_missing"}

    lam = extract_pick_best_lambda(src)
    if not lam:
        return {**base, "via": "host_fallback", "reason": "lambda_extract_failed"}

    lst = " ".join(str(n) for n in nums)
    form = f"(let ((pick-best {lam})) (pick-best (list {lst})))".replace("\n", " ")
    try:
        r = sess.raw_line(form, timeout_s=timeout_s)
    except Exception as exc:  # noqa: BLE001
        return {
            **base,
            "via": "host_fallback",
            "reason": f"soft_exc:{type(exc).__name__}:{exc}",
        }

    from aura_build.serve_session import is_session_transient

    msg = r.get("msg") or r.get("status")
    if is_session_transient(msg):
        return {**base, "via": "host_fallback", "reason": f"transient:{msg}", "transient": True}
    if r.get("status") != "ok":
        return {**base, "via": "host_fallback", "reason": str(msg)}

    try:
        soft_val = int(float(str(r.get("value"))))
    except (TypeError, ValueError):
        return {
            **base,
            "via": "host_fallback",
            "reason": f"soft_bad_value:{r.get('value')!r}",
        }

    if soft_val != host_max:
        # Soft disagree — do not invent Soft select success
        return {
            **base,
            "via": "host_fallback",
            "reason": f"soft_mismatch:{soft_val}",
            "soft_value": soft_val,
        }

    return {
        **base,
        "via": "soft_pick_best",
        "value": soft_val,
        "soft_value": soft_val,
        "reason": "soft_ok",
    }


def select_explorer_soft(
    explorers: Sequence[dict[str, Any]],
    *,
    score_key: str,
    sess: Any | None = None,
    repo: Path | None = None,
    tie_key: Callable[[dict[str, Any]], Any] | None = None,
    require_ok: bool = False,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Pick explorer whose score equals Soft (or host) pick-best max.

    ``tie_key`` breaks ties among explorers sharing the max score (host-side).
    """
    pool = [
        e
        for e in explorers
        if (not require_ok or e.get("ok")) and e.get(score_key) is not None
    ]
    if not pool:
        return None, {
            "ok": False,
            "via": "empty",
            "reason": "no_scored_explorers",
            "helper": HELPER_PATH,
        }

    scores = [int(e[score_key]) for e in pool]
    pick = soft_pick_best_score(scores, sess=sess, repo=repo)
    best_score = int(pick["value"])
    cands = [e for e in pool if int(e[score_key]) == best_score]
    if not cands:
        # Should not happen when soft matches host max
        cands = pool
    if tie_key is None:
        best = max(cands, key=lambda e: int(e[score_key]))
    else:
        best = max(cands, key=tie_key)
    return best, pick
