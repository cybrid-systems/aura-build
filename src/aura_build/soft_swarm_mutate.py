"""Soft-std swarm local multi-mutation (product path).

Uses Soft ``std/ant`` (ACO pheromone rank), ``std/pso``, ``std/abc`` via
oneshot/serve when Soft is live; always applies host-local source mutators
ranked by Soft (or host fallback order). Opaque Aura bodies are mutated on
the **host**; Soft swarm ranks **operator types** / continuous knobs — Soft
docs: apply via mutate outside swarm search.

Pipeline for LeetCode/combat:
  1. Soft pheromone:rank (or host order) → mutate op schedule
  2. Local multi-mutation → many source variants from baseline
  3. Caller scores / seeds MiniMax concurrent propose with those variants

Never invents Soft Ready / fiber_live.
"""

from __future__ import annotations

import os
import random
import re
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_SOFT = "/workspace/aura-grok/build/aura"

# Host mutator ids aligned with Soft ant pheromone type names where possible.
MUTATE_OPS: list[str] = [
    "edsl-lit-tweak",
    "edsl-op-swap",
    "edsl-body-wrap",
    "full-disp-bool",
    "full-disp-ref",
    "edsl-disp-ref",
    "full-hash-wrap",
]

_NUM_LIT_RE = re.compile(r"(?<![A-Za-z_\-:])(-?\d+)(?![A-Za-z_\-:])")
_OP_SWAP_PAIRS = [
    ("+", "-"),
    ("-", "+"),
    ("*", "/"),
    ("/", "*"),
    ("<", ">"),
    (">", "<"),
    ("<=", ">="),
    (">=", "<="),
    ("car", "cdr"),
    ("cdr", "car"),
    ("null?", "pair?"),
    ("#t", "#f"),
    ("#f", "#t"),
]


def resolve_aura_bin(aura_bin: str | None = None) -> str:
    return (
        aura_bin
        or os.environ.get("AURA_BIN")
        or DEFAULT_SOFT
    )


def _soft_oneshot(
    form: str,
    *,
    aura_bin: str,
    timeout_s: float = 12.0,
) -> dict[str, Any]:
    """Run a Soft oneshot sexpr; return {ok, display, stderr}."""
    try:
        proc = subprocess.run(
            [aura_bin, "-e", form],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            start_new_session=True,
            env={
                **os.environ,
                "AURA_SANDBOX": os.environ.get("AURA_SANDBOX") or "off",
            },
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"exc:{type(exc).__name__}:{exc}", "display": ""}
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    ok = proc.returncode == 0 and "error" not in out.lower()[:80]
    return {
        "ok": ok,
        "display": out,
        "stderr": err[:400],
        "returncode": proc.returncode,
    }


def soft_ant_rank_ops(
    ops: list[str] | None = None,
    *,
    aura_bin: str | None = None,
    timeout_s: float = 12.0,
) -> dict[str, Any]:
    """Soft ``pheromone:rank`` over mutation-type names (ACO). Host fallback = ops order."""
    types = list(ops or MUTATE_OPS)
    bin_path = resolve_aura_bin(aura_bin)
    lst = " ".join(f'"{t}"' for t in types)
    form = (
        "(begin (require \"std/ant\" all:) (pheromone:init) "
        f"(pheromone:rank (list {lst})))"
    )
    r = _soft_oneshot(form, aura_bin=bin_path, timeout_s=timeout_s)
    ranked = types[:]
    via = "host_fallback"
    if r.get("ok") and r.get("display"):
        # Soft prints ("a" "b" ...) — extract quoted strings in order
        found = re.findall(r'"([^"]+)"', str(r["display"]))
        # keep only known ops, preserve Soft order
        soft_ord = [x for x in found if x in types]
        if soft_ord:
            rest = [x for x in types if x not in soft_ord]
            ranked = soft_ord + rest
            via = "soft_ant_pheromone"
    return {
        "ok": via == "soft_ant_pheromone",
        "via": via,
        "ranked_ops": ranked,
        "soft": {k: r.get(k) for k in ("ok", "display", "stderr", "reason") if r.get(k) is not None},
    }


def soft_swarm_probe(
    kind: str = "pso",
    *,
    aura_bin: str | None = None,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """Smoke Soft std/swarm backend (pso|abc|ant|grid). Honesty only — no invent Ready."""
    bin_path = resolve_aura_bin(aura_bin)
    k = kind if kind in ("pso", "abc", "ant", "grid") else "pso"
    if k == "ant":
        return soft_ant_rank_ops(aura_bin=bin_path, timeout_s=timeout_s)
    if k == "abc":
        form = (
            "(begin (require \"std/abc\" all:) "
            "(abc:init 1 8 (list (list -2.0 2.0))) "
            "(abc:step! (lambda (x) (- 0.0 (* (car x) (car x))))) "
            "(abc:best))"
        )
    elif k == "grid":
        form = (
            "(begin (require \"std/swarm\" all:) "
            "(swarm:init (hash \"kind\" \"grid\" \"dim\" 1 \"pop\" 8 "
            "\"bounds\" (list (list -1.0 1.0)) \"bins\" 8)) "
            "(swarm:step! (lambda (x) (- 0.0 (* (car x) (car x))))) "
            "(swarm:best))"
        )
    else:
        form = (
            "(begin (require \"std/pso\" all:) "
            "(pso:init 2 8 (list (list 0.0 1.0) (list 0.0 1.0))) "
            "(pso:step! (lambda (x) (- 0.0 (+ (* (car x) (car x)) "
            "(* (car (cdr x)) (car (cdr x))))))) "
            "(pso:best))"
        )
    r = _soft_oneshot(form, aura_bin=bin_path, timeout_s=timeout_s)
    return {
        "ok": bool(r.get("ok")),
        "via": f"soft_{k}" if r.get("ok") else "soft_fail",
        "kind": k,
        "display": (r.get("display") or "")[:200],
        "stderr": r.get("stderr") or r.get("reason"),
    }


def _apply_lit_tweak(src: str, rng: random.Random) -> str:
    nums = list(_NUM_LIT_RE.finditer(src))
    if not nums:
        return src
    m = rng.choice(nums)
    try:
        v = int(m.group(1))
    except ValueError:
        return src
    delta = rng.choice((-2, -1, 1, 2, v or 1))
    nv = v + delta if abs(delta) <= 2 else (v * 2 if delta == (v or 1) else max(0, v // 2))
    return src[: m.start()] + str(nv) + src[m.end() :]


def _apply_op_swap(src: str, rng: random.Random) -> str:
    pairs = [(a, b) for a, b in _OP_SWAP_PAIRS if a in src]
    if not pairs:
        return src
    a, b = rng.choice(pairs)
    # replace first occurrence only (local mutate)
    return src.replace(a, b, 1)


def _apply_body_wrap(src: str, rng: random.Random) -> str:
    # Wrap first (define (solve ...) ...) body hint via comment seed for LLM
    tag = rng.choice(("fail-focus", "edge-empty", "edge-singleton", "invariant"))
    banner = f"; swarm-mutate:{tag}\n"
    if banner.strip() in src:
        return src
    return banner + src


def _apply_bool_flip(src: str, rng: random.Random) -> str:
    if "#t" in src and rng.random() < 0.5:
        return src.replace("#t", "#f", 1)
    if "#f" in src:
        return src.replace("#f", "#t", 1)
    return _apply_op_swap(src, rng)


def _apply_disp_ref(src: str, rng: random.Random) -> str:
    # Nudge display/CASE harness lines — keep solve intact; seed LLM attention
    if "CASE" in src and "display" in src:
        return src.replace("(display ", "(begin (display ", 1) + ")" if False else src
    # Insert a note near solve
    if "(define (solve" in src:
        return src.replace("(define (solve", "; swarm-mutate:disp-ref\n(define (solve", 1)
    return _apply_body_wrap(src, rng)


_OP_IMPL: dict[str, Any] = {
    "edsl-lit-tweak": _apply_lit_tweak,
    "edsl-op-swap": _apply_op_swap,
    "edsl-body-wrap": _apply_body_wrap,
    "full-disp-bool": _apply_bool_flip,
    "full-disp-ref": _apply_disp_ref,
    "edsl-disp-ref": _apply_disp_ref,
    "full-hash-wrap": _apply_body_wrap,
}


def local_multi_mutate(
    src: str,
    *,
    n: int = 16,
    ranked_ops: list[str] | None = None,
    seed: int = 424242,
    max_ops_per_variant: int = 3,
) -> list[dict[str, Any]]:
    """Apply Soft-ranked (or default) host mutators → n distinct source variants."""
    ops = list(ranked_ops or MUTATE_OPS)
    rng = random.Random(seed)
    out: list[dict[str, Any]] = []
    seen = {src.strip()}
    for i in range(max(1, int(n))):
        cur = src
        used: list[str] = []
        # Prefer higher-ranked ops earlier; still mix
        schedule = ops[:] if i % 2 == 0 else list(reversed(ops))
        rng.shuffle(schedule)
        # Bias: first slots from Soft rank head
        schedule = ops[:3] + schedule
        for op in schedule:
            if len(used) >= max_ops_per_variant:
                break
            fn = _OP_IMPL.get(op)
            if not fn:
                continue
            nxt = fn(cur, rng)
            if nxt != cur:
                cur = nxt
                used.append(op)
        key = cur.strip()
        if key in seen or not used:
            # force lit tweak fallback
            cur = _apply_lit_tweak(src, rng)
            used = used or ["edsl-lit-tweak"]
            key = cur.strip()
        if key in seen:
            cur = _apply_body_wrap(cur, rng)
            key = cur.strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "name": f"mut-{i}",
                "src": cur,
                "ops": used,
                "via": "host_local_multi_mutate",
            }
        )
    return out


def swarm_mutate_candidates(
    src: str,
    *,
    n: int = 16,
    aura_bin: str | None = None,
    seed: int = 424242,
    prefer_kinds: list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Soft ant-rank (+ optional pso/abc probe) → local multi-mutation variants.

    Returns (candidates, meta). Soft Ready never invented — probe failures → host order.
    """
    bin_path = resolve_aura_bin(aura_bin)
    rank = soft_ant_rank_ops(aura_bin=bin_path)
    probes: dict[str, Any] = {"ant": rank}
    for k in prefer_kinds or ("pso", "abc"):
        if k == "ant":
            continue
        probes[k] = soft_swarm_probe(k, aura_bin=bin_path)
    cands = local_multi_mutate(
        src,
        n=n,
        ranked_ops=list(rank.get("ranked_ops") or MUTATE_OPS),
        seed=seed,
    )
    meta = {
        "ok": bool(cands),
        "n_requested": int(n),
        "n": len(cands),
        "rank_via": rank.get("via"),
        "ranked_ops": rank.get("ranked_ops"),
        "probes": {k: {kk: vv for kk, vv in (v or {}).items() if kk in ("ok", "via", "kind")} for k, v in probes.items()},
        "path": "soft_swarm_local_multi_mutate",
    }
    return cands, meta
