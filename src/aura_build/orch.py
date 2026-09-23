"""Orchestrator: scout → mutate → eval → select-best (M0 simulated worldlines)."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from aura_build.schema import SCHEMA_VERSION


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_from_prompt(prompt: str, seed: int | None) -> int:
    if seed is not None:
        return seed
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


@dataclass
class Worldline:
    id: str
    parent_id: str | None
    mutations: list[dict[str, Any]]
    eval: dict[str, Any]


@dataclass
class EpisodeResult:
    episode: dict[str, Any]
    selected: Worldline


@dataclass
class OrchConfig:
    """M0 config — Aura client hooked in M1 behind the same surface."""

    n_worldlines: int = 3
    seed: int | None = None
    l1_strategy_id: str = "m0.simulated.select_best"
    l2_weights_id: str | None = None
    l3_online: bool = False
    mode: str = "simulated"  # simulated | aura
    aura_ref: str | None = None
    fitness_fn: Callable[[str, int, int], float] | None = None


def _default_fitness(prompt: str, seed: int, index: int) -> float:
    """Deterministic fake fitness for M0 demos."""
    h = hashlib.sha256(f"{seed}:{index}:{prompt}".encode()).hexdigest()
    # Mix in index so worldlines differ; prefer mid candidates slightly for demos.
    base = int(h[:6], 16) / float(0xFFFFFF)
    bump = 0.15 if index == 1 else 0.0
    return round(min(1.0, base * 0.85 + bump), 4)


def scout(prompt: str, cfg: OrchConfig) -> dict[str, Any]:
    """Scout phase — record task + harness hints."""
    return {
        "prompt": prompt,
        "l1_strategy_id": cfg.l1_strategy_id,
        "hints": ["anti-postman", "multi-candidate", "select-best"],
    }


def mutate_worldlines(prompt: str, seed: int, n: int) -> list[dict[str, Any]]:
    """Propose N simulated mutations (M0). M1 replaces with Aura mutate."""
    out: list[dict[str, Any]] = []
    for i in range(n):
        out.append(
            {
                "id": f"wl-{i}",
                "parent_id": None,
                "mutations": [
                    {
                        "op": "simulated_edit",
                        "target_id": f"node:demo:{i}",
                        "summary": f"candidate {i} for: {prompt[:80]}",
                    }
                ],
            }
        )
    return out


def eval_worldline(
    wl: dict[str, Any],
    prompt: str,
    seed: int,
    index: int,
    fitness_fn: Callable[[str, int, int], float],
) -> Worldline:
    fitness = fitness_fn(prompt, seed, index)
    passed = fitness >= 0.3
    metrics = {
        "tests_passed": 1 if passed else 0,
        "tests_total": 1,
        "incr_compile_ms": 5 + index * 3,
        "audit_ok": True,
    }
    return Worldline(
        id=wl["id"],
        parent_id=wl.get("parent_id"),
        mutations=list(wl.get("mutations") or []),
        eval={
            "fitness": fitness,
            "passed": passed,
            "metrics": metrics,
            "notes": "m0 simulated eval",
        },
    )


def select_best(worldlines: list[Worldline]) -> tuple[Worldline, str]:
    """Select highest fitness; tie-break by id for stability."""
    if not worldlines:
        raise ValueError("no worldlines to select")
    best = max(worldlines, key=lambda w: (w.eval["fitness"], w.id))
    return best, "max_fitness"


def run_episode(prompt: str, cfg: OrchConfig | None = None) -> EpisodeResult:
    """Full scout→mutate→eval→select-best; returns episode dict + selected."""
    cfg = cfg or OrchConfig()
    if cfg.l3_online:
        # M0 forbids promoting experimental online path silently.
        raise ValueError("L3 online weights are experimental-only; refuse in M0")

    seed = _seed_from_prompt(prompt, cfg.seed)
    fitness_fn = cfg.fitness_fn or _default_fitness
    ts_start = _utc_now()

    scout(prompt, cfg)
    raw = mutate_worldlines(prompt, seed, cfg.n_worldlines)
    evaluated = [
        eval_worldline(wl, prompt, seed, i, fitness_fn) for i, wl in enumerate(raw)
    ]
    selected, reason = select_best(evaluated)
    ts_end = _utc_now()

    episode: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "episode_id": str(uuid.uuid4()),
        "ts_start": ts_start,
        "ts_end": ts_end,
        "prompt": prompt,
        "runtime": {
            "mode": cfg.mode,
            "aura_ref": cfg.aura_ref,
            "seed": seed,
        },
        "harness": {
            "l1_strategy_id": cfg.l1_strategy_id,
            "l2_weights_id": cfg.l2_weights_id,
            "l3_online": False,
        },
        "worldlines": [
            {
                "id": w.id,
                "parent_id": w.parent_id,
                "mutations": w.mutations,
                "eval": w.eval,
            }
            for w in evaluated
        ],
        "selected_id": selected.id,
        "selection_reason": reason,
        "privacy": {
            "redacted": False,
            "retention_class": "dogfood",
        },
    }
    return EpisodeResult(episode=episode, selected=selected)
