"""THIN harness adapter — Soft/Aura KERNEL owns feedback-accumulated prompts.

Product path: ``aura/self_evolve_feedback.aura`` + memory profile leet_feedback.
Host only reads Soft-written JSON / invokes Soft ``run-feedback-round``.
Do NOT grow Python prompt product logic here.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_SOFT = "/workspace/aura-grok/build/aura"
FEEDBACK_NAME = "leet_feedback.json"  # Soft memory profile file
MAX_NOTES = 48
MAX_SLUG_NOTES = 12


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def feedback_path(repo: Path, harness_root: Path | None = None) -> Path:
    root = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or (repo / ".aura-build")
    )
    return root / "memory" / FEEDBACK_NAME


def load_feedback(repo: Path, harness_root: Path | None = None) -> dict[str, Any]:
    path = feedback_path(repo, harness_root)
    if not path.is_file():
        return {"version": 1, "notes": [], "by_slug": {}, "kernel": "aura"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "notes": [], "by_slug": {}, "kernel": "aura"}
    if not isinstance(data, dict):
        return {"version": 1, "notes": [], "by_slug": {}, "kernel": "aura"}
    data.setdefault("version", 1)
    data.setdefault("notes", [])
    data.setdefault("by_slug", {})
    data["kernel"] = "aura"
    # Soft memory stores slug:X keys; normalize by_slug for readers
    by = dict(data.get("by_slug") or {})
    for k, v in list(data.items()):
        if isinstance(k, str) and k.startswith("slug:") and isinstance(v, dict):
            slug = k[5:]
            by.setdefault(slug, [])
            if v not in by[slug]:
                by[slug] = (by.get(slug) or []) + [v]
                by[slug] = by[slug][-MAX_SLUG_NOTES:]
    data["by_slug"] = by
    return data


def save_feedback(
    repo: Path,
    state: dict[str, Any],
    harness_root: Path | None = None,
) -> Path:
    """Prefer Soft kernel write; host save is demoted fallback only."""
    path = feedback_path(repo, harness_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = dict(state)
    state["kernel"] = "aura"
    state["note"] = "prefer aura/self_evolve_feedback.aura memory-set"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def run_kernel_feedback(
    *,
    slug: str,
    ok: bool,
    cause: str,
    hits: int = 0,
    baseline: int = 0,
    total: int = 8,
    aura_bin: str | None = None,
    harness_root: Path | None = None,
    timeout_s: float = 30.0,
) -> dict[str, Any]:
    bin_path = aura_bin or os.environ.get("AURA_BIN") or DEFAULT_SOFT
    repo = _repo_root()
    hroot = Path(harness_root) if harness_root else repo / ".aura-build"
    soft_lib = Path("/workspace/aura-grok/lib")
    env = {
        **os.environ,
        "AURA_BIN": bin_path,
        "AURA_PATH": os.environ.get("AURA_PATH") or f"{soft_lib}:{repo / 'aura'}",
        "AURA_BUILD_HARNESS_ROOT": str(hroot),
        "AURA_BUILD_SLUG": slug,
        "AURA_BUILD_FB_OK": "true" if ok else "false",
        "AURA_BUILD_FB_CAUSE": cause,
        "AURA_BUILD_FB_HITS": str(int(hits)),
        "AURA_BUILD_FB_BASELINE": str(int(baseline)),
        "AURA_BUILD_FB_TOTAL": str(int(total)),
        "AURA_SANDBOX": os.environ.get("AURA_SANDBOX") or "off",
    }
    form = '(begin (require "self_evolve_feedback" all:) (run-feedback-round))'
    try:
        proc = subprocess.run(
            [bin_path, "-e", form],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            start_new_session=True,
            env=env,
            cwd=str(repo),
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": str(exc), "kernel": "aura"}
    return {
        "ok": proc.returncode == 0,
        "stdout": (proc.stdout or "")[:400],
        "kernel": "aura",
        "path": "kernel_feedback",
    }


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
    harness_root: Path | None = None,
    aura_bin: str | None = None,
) -> dict[str, Any]:
    """Write via Soft kernel; merge into returned state from Soft memory."""
    cause = no_gain_cause or ("gain" if ok else (reason or "unknown"))
    run_kernel_feedback(
        slug=slug,
        ok=ok,
        cause=str(cause),
        hits=int(selected_hits or 0),
        baseline=int(baseline_hits or 0),
        total=int(total or 8),
        aura_bin=aura_bin,
        harness_root=harness_root,
    )
    repo = _repo_root()
    loaded = load_feedback(repo, harness_root)
    # keep caller-compatible shape
    state["notes"] = list(loaded.get("notes") or [])[-MAX_NOTES:]
    state["by_slug"] = loaded.get("by_slug") or {}
    state["last"] = loaded.get("last") or {
        "slug": slug,
        "ok": ok,
        "cause": cause,
        "hits": selected_hits,
        "baseline_hits": baseline_hits,
        "total": total,
        "llm_via": llm_via,
        "mutate_ops": list(mutate_ops or [])[:8],
        "kernel": "aura",
    }
    state["kernel"] = "aura"
    return state


def classify_no_gain_cause(
    *,
    explorers: list[dict[str, Any]] | None,
    soft_select: dict[str, Any] | None = None,
    baseline_hits: int | None = None,
    selected_hits: int | None = None,
    pre_score_session: dict[str, Any] | None = None,
) -> str:
    """Honest sock-vs-quality classify (thin; mirrors Soft feedback-classify)."""
    ex = list(explorers or [])
    if not ex:
        return "no_explorers"
    n = len(ex)
    transient_n = sum(
        1
        for e in ex
        if e.get("transient")
        or e.get("reason") in ("set_code_failed", "eval_transient", "run_transient")
    )
    zero_n = sum(1 for e in ex if int(e.get("hits") or 0) == 0)
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
    harness_root: Path | None = None,
    aura_bin: str | None = None,
) -> str:
    """Read Soft kernel feedback + family tips from Soft memory (not Python brain)."""
    bin_path = aura_bin or os.environ.get("AURA_BIN") or DEFAULT_SOFT
    repo = _repo_root()
    hroot = Path(harness_root) if harness_root else (
        Path(os.environ.get("AURA_BUILD_HARNESS_ROOT") or (repo / ".aura-build"))
    )
    soft_lib = Path("/workspace/aura-grok/lib")
    env = {
        **os.environ,
        "AURA_PATH": os.environ.get("AURA_PATH") or f"{soft_lib}:{repo / 'aura'}",
        "AURA_BUILD_HARNESS_ROOT": str(hroot),
        "AURA_BUILD_SLUG": slug,
        "AURA_SANDBOX": os.environ.get("AURA_SANDBOX") or "off",
    }
    form = (
        "(begin (require \"self_evolve_feedback\" all:) "
        f"(feedback-prompt-suffix \"{hroot}\" \"{slug}\" {int(variant_i)}))"
    )
    lines: list[str] = []
    try:
        proc = subprocess.run(
            [bin_path, "-e", form],
            capture_output=True,
            text=True,
            timeout=20.0,
            check=False,
            start_new_session=True,
            env=env,
            cwd=str(repo),
        )
        out = (proc.stdout or "").strip()
        if out and proc.returncode == 0:
            lines.append(f"Kernel prompt_suffix: {out[:800]}")
    except Exception:  # noqa: BLE001
        pass
    fb = feedback or load_feedback(repo, hroot)
    last = fb.get("last") or {}
    if last:
        lines.append(
            f"Prior Soft-memory note: ok={last.get('ok')} cause={last.get('cause')} "
            f"hits={last.get('hits')}/{last.get('total')}"
        )
    if mutate_seed_ops:
        lines.append(f"Soft-ranked swarm seed ops: {', '.join(mutate_seed_ops[:6])}")
    if mutate_seed_note:
        lines.append(f"Mutate seed note: {mutate_seed_note[:240]}")
    if fail_details:
        lines.append(f"Still failing {len(fail_details)} cases — repair those first.")
    if not lines:
        lines.append("Kernel feedback empty — Soft select-best owns scoring.")
    return "\n".join(lines)
