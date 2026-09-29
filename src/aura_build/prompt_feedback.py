"""Feedback-accumulated prompts for MiniMax LeetCode/combat (product path).

Persists fail/hit/no_gain notes across rounds under harness_root so subsequent
proposes get richer, varied context — not denseness-only, not one-off scratch.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

FEEDBACK_NAME = "self_evolve_prompt_feedback.json"
MAX_NOTES = 48
MAX_SLUG_NOTES = 12


def feedback_path(repo: Path, harness_root: Path | None = None) -> Path:
    root = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or (repo / ".aura-build")
    )
    root.mkdir(parents=True, exist_ok=True)
    return root / FEEDBACK_NAME


def load_feedback(repo: Path, harness_root: Path | None = None) -> dict[str, Any]:
    path = feedback_path(repo, harness_root)
    if not path.is_file():
        return {"version": 1, "notes": [], "by_slug": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "notes": [], "by_slug": {}}
    if not isinstance(data, dict):
        return {"version": 1, "notes": [], "by_slug": {}}
    data.setdefault("version", 1)
    data.setdefault("notes", [])
    data.setdefault("by_slug", {})
    return data


def save_feedback(
    repo: Path,
    state: dict[str, Any],
    harness_root: Path | None = None,
) -> Path:
    path = feedback_path(repo, harness_root)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def observe_transform_feedback(
    state: dict[str, Any],
    *,
    slug: str,
    ok: bool,
    reason: str | None,
    fail_details: list[dict[str, Any]] | None = None,
    selected_hits: int | None = None,
    baseline_hits: int | None = None,
    total: int | None = None,
    no_gain_cause: str | None = None,
    llm_via: str | None = None,
    mutate_ops: list[str] | None = None,
) -> dict[str, Any]:
    """Append a durable note from a Soft+LLM transform round."""
    notes = list(state.get("notes") or [])
    by_slug: dict[str, Any] = dict(state.get("by_slug") or {})
    cause = no_gain_cause or ("gain" if ok else (reason or "unknown"))
    snippet_fails = []
    for d in (fail_details or [])[:6]:
        snippet_fails.append(
            {
                "id": d.get("id"),
                "expected": str(d.get("expected"))[:80],
                "got": str(d.get("got"))[:80],
            }
        )
    note = {
        "slug": slug,
        "ok": bool(ok),
        "reason": reason,
        "cause": cause,
        "hits": selected_hits,
        "baseline_hits": baseline_hits,
        "total": total,
        "llm_via": llm_via,
        "mutate_ops": list(mutate_ops or [])[:8],
        "fails": snippet_fails,
    }
    notes.append(note)
    state["notes"] = notes[-MAX_NOTES:]
    slug_notes = list(by_slug.get(slug) or [])
    slug_notes.append(note)
    by_slug[slug] = slug_notes[-MAX_SLUG_NOTES:]
    state["by_slug"] = by_slug
    state["last"] = note
    return state


def classify_no_gain_cause(
    *,
    explorers: list[dict[str, Any]] | None,
    soft_select: dict[str, Any] | None = None,
    baseline_hits: int | None = None,
    selected_hits: int | None = None,
    pre_score_session: dict[str, Any] | None = None,
) -> str:
    """Distinguish Soft sock collapse vs proposal quality no_gain (honest)."""
    ex = list(explorers or [])
    if not ex:
        return "no_explorers"
    n = len(ex)
    transient_n = sum(1 for e in ex if e.get("transient") or e.get("reason") in (
        "set_code_failed", "eval_transient", "run_transient"
    ))
    zero_n = sum(1 for e in ex if int(e.get("hits") or 0) == 0)
    # Sock: majority transient/set_code_failed OR selected zeros while baseline held hits
    if transient_n >= max(2, n // 3):
        return "sock_transient"
    if (
        baseline_hits is not None
        and selected_hits is not None
        and int(baseline_hits) > 0
        and int(selected_hits) == 0
        and zero_n >= max(2, (n * 2) // 3)
    ):
        return "sock_score_collapse"
    sel_via = (soft_select or {}).get("via")
    if sel_via == "host_fallback" and (soft_select or {}).get("transient"):
        return "sock_select_transient"
    pre = pre_score_session or {}
    if pre.get("via") in ("restart", "cold_start") and zero_n >= (n * 2) // 3:
        return "sock_after_reattach_still_poor"
    # Quality: Soft scored, best ≤ baseline
    if selected_hits is not None and baseline_hits is not None:
        if int(selected_hits) <= int(baseline_hits):
            if int(selected_hits) == int(baseline_hits) and int(selected_hits) > 0:
                return "quality_plateau"
            return "quality_no_improvement"
    return "quality_unknown"


def build_prompt_variation(
    *,
    slug: str,
    fail_details: list[dict[str, Any]],
    feedback: dict[str, Any] | None,
    variant_i: int = 0,
    mutate_seed_ops: list[str] | None = None,
    mutate_seed_note: str | None = None,
) -> str:
    """Richer, varied user-prompt suffix from accumulated feedback + mutate seed."""
    lines: list[str] = []
    fb = feedback or {}
    slug_notes = list((fb.get("by_slug") or {}).get(slug) or [])
    global_notes = list(fb.get("notes") or [])[-8:]
    # Cause histogram
    causes: dict[str, int] = {}
    for n in slug_notes + global_notes:
        c = str(n.get("cause") or "")
        if c:
            causes[c] = causes.get(c, 0) + 1
    if causes:
        top = sorted(causes.items(), key=lambda kv: -kv[1])[:5]
        lines.append("Feedback-accumulated no_gain/gain causes (recent):")
        for c, k in top:
            lines.append(f"  - {c}: {k}")
    # Prior fail patterns for this slug
    if slug_notes:
        last = slug_notes[-1]
        lines.append(
            f"Prior round on {slug}: ok={last.get('ok')} reason={last.get('reason')} "
            f"cause={last.get('cause')} hits={last.get('hits')}/{last.get('total')}"
        )
        for f in (last.get("fails") or [])[:4]:
            lines.append(
                f"  prior fail CASE{f.get('id')}: got={f.get('got')!r} expected={f.get('expected')!r}"
            )
    # Prompt variation by variant index
    focus = [
        "Focus on edge cases (empty / singleton / duplicates).",
        "Prefer iterative Soft-friendly loops over deep recursion.",
        "Preserve CASE print harness; only fix solve algorithm.",
        "Do not hardcode expected outputs into display.",
        "Watch off-by-one and inclusive bounds.",
        "Prefer Soft-native list/string helpers when available.",
        "Keep solution under 200 lines; avoid inventing APIs.",
        "If prior plateaued, try a different algorithm family.",
    ]
    lines.append(f"Prompt variation[{variant_i % len(focus)}]: {focus[variant_i % len(focus)]}")
    if mutate_seed_ops:
        lines.append(f"Local swarm-mutate seed ops: {', '.join(mutate_seed_ops[:6])}")
    if mutate_seed_note:
        lines.append(f"Mutate seed note: {mutate_seed_note[:240]}")
    # Current fail details already in main prompt — add emphasis
    if fail_details:
        lines.append(f"Still failing {len(fail_details)} cases — repair those first.")
    return "\n".join(lines)
