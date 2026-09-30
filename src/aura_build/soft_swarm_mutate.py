"""THIN harness adapter — Soft/Aura KERNEL owns swarm multi-mutate product brain.

Product path: ``aura/self_evolve_swarm.aura`` (Soft std/ant pheromone:rank +
mutate:rebind fanout). This module only starts Soft oneshot / reads harness
memory Soft wrote. Do NOT grow host string-mutator product logic here.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_SOFT = "/workspace/aura-grok/build/aura"
MUTATE_OPS: list[str] = [
    "edsl-lit-tweak",
    "edsl-op-swap",
    "edsl-body-wrap",
    "full-disp-bool",
    "full-disp-ref",
    "edsl-disp-ref",
    "full-hash-wrap",
    "edsl-cond-swap",
    "edsl-let-wrap",
    "full-tail-recur",
]


def resolve_aura_bin(aura_bin: str | None = None) -> str:
    return aura_bin or os.environ.get("AURA_BIN") or DEFAULT_SOFT


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _aura_path(repo: Path | None = None) -> str:
    r = repo or _repo_root()
    lib = os.environ.get("AURA_PATH")
    if lib:
        return lib
    # Soft stdlib + aura-build kernel
    soft_lib = Path("/workspace/aura-grok/lib")
    return f"{soft_lib}:{r / 'aura'}"


def run_kernel_swarm_mutate(
    *,
    slug: str,
    aura_bin: str | None = None,
    harness_root: Path | None = None,
    timeout_s: float = 60.0,
) -> dict[str, Any]:
    """Invoke Soft kernel ``run-swarm-mutate-round`` (product brain)."""
    bin_path = resolve_aura_bin(aura_bin)
    repo = _repo_root()
    hroot = Path(harness_root) if harness_root else repo / ".aura-build"
    env = {
        **os.environ,
        "AURA_BIN": bin_path,
        "AURA_PATH": _aura_path(repo),
        "AURA_BUILD_HARNESS_ROOT": str(hroot),
        "AURA_BUILD_SLUG": slug,
        "AURA_SANDBOX": os.environ.get("AURA_SANDBOX") or "off",
    }
    form = '(begin (require "self_evolve_swarm" all:) (run-swarm-mutate-round))'
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
        return {"ok": False, "reason": f"exc:{type(exc).__name__}", "path": "kernel_swarm_adapter"}
    out = (proc.stdout or "").strip()
    mem = hroot / "memory" / "leet_swarm.json"
    ranked = list(MUTATE_OPS)
    via = "host_fallback"
    if mem.is_file():
        try:
            data = json.loads(mem.read_text(encoding="utf-8"))
            ro = data.get("ranked_ops")
            if isinstance(ro, list) and ro:
                ranked = [str(x) for x in ro]
                via = "soft_ant_pheromone"
        except (OSError, json.JSONDecodeError):
            pass
    n_mut = 48
    diverge_sticky = True
    observe_gate = None
    if mem.is_file():
        try:
            data = json.loads(mem.read_text(encoding="utf-8"))
            observe_gate = data.get("observe_gate")
            if isinstance(data.get("n_mut"), (int, float)):
                # Soft observe-steer may shrink n_mut on red/amber gates — honor it.
                raw_n = int(data["n_mut"])
                if observe_gate in ("red", "amber") or data.get("observe_press_fanout") is False:
                    n_mut = max(8, min(64, raw_n))
                else:
                    n_mut = max(48, min(64, raw_n))
            diverge_sticky = bool(data.get("diverge_sticky", True))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    ok = proc.returncode == 0 and "swarm_mutate ok=true" in out
    return {
        "ok": ok,
        "via": via if ok else "soft_fail",
        "ranked_ops": ranked,
        "n_mut": n_mut,
        "diverge_sticky": diverge_sticky,
        "observe_gate": observe_gate,
        "stdout": out[:500],
        "stderr": (proc.stderr or "")[:300],
        "path": "kernel_swarm_mutate",
        "kernel": "aura",
        "returncode": proc.returncode,
    }


def soft_ant_rank_ops(
    ops: list[str] | None = None,
    *,
    aura_bin: str | None = None,
    timeout_s: float = 12.0,
) -> dict[str, Any]:
    """Thin: Soft pheromone:rank oneshot (kernel path preferred via run_kernel)."""
    types = list(ops or MUTATE_OPS)
    r = run_kernel_swarm_mutate(slug="rank-only", aura_bin=aura_bin, timeout_s=timeout_s)
    ranked = list(r.get("ranked_ops") or types)
    # keep only known
    soft_ord = [x for x in ranked if x in types]
    if soft_ord:
        rest = [x for x in types if x not in soft_ord]
        ranked = soft_ord + rest
    return {
        "ok": bool(r.get("ok")),
        "via": r.get("via") or "host_fallback",
        "ranked_ops": ranked or types,
        "kernel": "aura",
    }


def soft_swarm_probe(
    kind: str = "pso",
    *,
    aura_bin: str | None = None,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """Thin honesty probe — Soft kernel swarm-probe via oneshot."""
    bin_path = resolve_aura_bin(aura_bin)
    form = (
        f'(begin (require "self_evolve_swarm" all:) (swarm-probe "{kind}"))'
    )
    env = {
        **os.environ,
        "AURA_PATH": _aura_path(),
        "AURA_SANDBOX": os.environ.get("AURA_SANDBOX") or "off",
    }
    try:
        proc = subprocess.run(
            [bin_path, "-e", form],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            start_new_session=True,
            env=env,
        )
        ok = proc.returncode == 0
        return {
            "ok": ok,
            "via": f"soft_{kind}" if ok else "soft_fail",
            "kind": kind,
            "display": (proc.stdout or "")[:200],
            "kernel": "aura",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "via": "soft_fail", "kind": kind, "reason": str(exc)}


def local_multi_mutate(
    src: str,
    *,
    n: int = 16,
    ranked_ops: list[str] | None = None,
    seed: int = 424242,
    max_ops_per_variant: int = 3,
) -> list[dict[str, Any]]:
    """DEMOTION: host no longer owns mutate product.

    Returns schedule seeds (ops + prior src) for MiniMax / Soft mutate:rebind.
    Actual multi-mutate lives in ``aura/self_evolve_swarm.aura`` (mutate:rebind).
    Kept as thin seed list so Soft select pool still sees mutate explorers.
    """
    ops = list(ranked_ops or MUTATE_OPS)
    out: list[dict[str, Any]] = []
    # Seed variants: same src tagged with Soft-ranked op schedule — Soft kernel
    # (or MiniMax) applies; do not invent host sexpr rewrites as product.
    for i in range(max(1, min(int(n), 64))):
        op = ops[i % len(ops)]
        banner = f"; kernel-swarm-seed op={op} i={i} seed={seed}\n"
        out.append(
            {
                "name": f"mut-{i}",
                "src": banner + src if not src.lstrip().startswith("; kernel-swarm-seed") else src,
                "ops": [op],
                "via": "kernel_swarm_seed",
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
    slug: str = "unknown",
    harness_root: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Adapter: Soft kernel ranks → thin seeds. Brain = aura/self_evolve_swarm.aura."""
    kr = run_kernel_swarm_mutate(
        slug=slug, aura_bin=aura_bin, harness_root=harness_root
    )
    ranked = list(kr.get("ranked_ops") or MUTATE_OPS)
    probes: dict[str, Any] = {"ant": {"ok": kr.get("ok"), "via": kr.get("via")}}
    for k in prefer_kinds or ("pso", "abc"):
        if k == "ant":
            continue
        probes[k] = soft_swarm_probe(k, aura_bin=aura_bin)
    # Soft observe-steer may shrink n_mut when gates red/amber — honor Soft brain.
    soft_n = int(kr.get("n_mut") or 48)
    gate = kr.get("observe_gate")
    if gate in ("red", "amber") or kr.get("diverge_sticky") is False:
        n_eff = max(8, min(64, min(int(n), soft_n)))
    else:
        n_eff = max(int(n), soft_n, 48)
        n_eff = min(64, n_eff)
    cands = local_multi_mutate(src, n=n_eff, ranked_ops=ranked, seed=seed)
    meta = {
        "ok": bool(cands),
        "n_requested": int(n),
        "n": len(cands),
        "n_mut": n_eff,
        "diverge_sticky": bool(kr.get("diverge_sticky", True)),
        "observe_gate": kr.get("observe_gate"),
        "rank_via": kr.get("via") or "host_fallback",
        "ranked_ops": ranked,
        "probes": {
            k: {kk: vv for kk, vv in (v or {}).items() if kk in ("ok", "via", "kind")}
            for k, v in probes.items()
        },
        "path": "kernel_swarm_mutate",
        "kernel": "aura",
        "note": "host is thin adapter; Soft kernel owns rank+mutate:rebind",
    }
    return cands, meta
