"""Orchestrator: scout → mutate → eval → select-best (RuntimeBackend)."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from aura_build.runtime import (
    AuraUnavailable,
    RuntimeBackend,
    SimulatedBackend,
    resolve_backend,
)
from aura_build.schema import SCHEMA_VERSION

__all__ = [
    "AuraUnavailable",
    "EpisodeResult",
    "OrchConfig",
    "Worldline",
    "eval_worldline",
    "mutate_worldlines",
    "run_episode",
    "scout",
    "select_best",
]


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
    """Episode config. M1: backend resolved from mode (simulated|aura|auto)."""

    n_worldlines: int = 3
    seed: int | None = None
    l1_strategy_id: str = "m1.runtime.select_best"
    l2_weights_id: str | None = None
    l3_online: bool = False
    mode: str = "simulated"  # simulated | aura | auto
    aura_bin: str | None = None
    aura_ref: str | None = None
    fitness_fn: Callable[[str, int, int], float] | None = None
    backend: RuntimeBackend | None = None


def scout(prompt: str, cfg: OrchConfig) -> dict[str, Any]:
    """Scout phase — record task + harness hints."""
    return {
        "prompt": prompt,
        "l1_strategy_id": cfg.l1_strategy_id,
        "hints": ["anti-postman", "multi-candidate", "select-best"],
        "mode": cfg.mode,
    }


def mutate_worldlines(prompt: str, seed: int, n: int) -> list[dict[str, Any]]:
    """Backward-compatible helper — simulated mutations only."""
    return SimulatedBackend().mutate_worldlines(prompt, seed, n)


def eval_worldline(
    wl: dict[str, Any],
    prompt: str,
    seed: int,
    index: int,
    fitness_fn: Callable[[str, int, int], float],
) -> Worldline:
    """Backward-compatible helper — simulated eval only."""
    raw = SimulatedBackend(fitness_fn=fitness_fn).eval_worldline(wl, prompt, seed, index)
    return Worldline(
        id=raw["id"],
        parent_id=raw.get("parent_id"),
        mutations=list(raw.get("mutations") or []),
        eval=raw["eval"],
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
        raise ValueError("L3 online weights are experimental-only; refuse in M0/M1")

    seed = _seed_from_prompt(prompt, cfg.seed)
    backend = resolve_backend(
        cfg.mode,
        aura_bin=cfg.aura_bin,
        aura_ref=cfg.aura_ref,
        fitness_fn=cfg.fitness_fn,
        backend=cfg.backend,
    )
    ts_start = _utc_now()

    scout(prompt, cfg)
    raw = backend.mutate_worldlines(prompt, seed, cfg.n_worldlines)
    evaluated: list[Worldline] = []
    for i, wl in enumerate(raw):
        got = backend.eval_worldline(wl, prompt, seed, i)
        evaluated.append(
            Worldline(
                id=got["id"],
                parent_id=got.get("parent_id"),
                mutations=list(got.get("mutations") or []),
                eval=got["eval"],
            )
        )
    selected, reason = select_best(evaluated)
    ts_end = _utc_now()

    # Honest mode: what backend actually ran, not the requested auto preference.
    resolved_mode = backend.mode
    resolved_ref = backend.aura_ref if resolved_mode == "aura" else cfg.aura_ref

    episode: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "episode_id": str(uuid.uuid4()),
        "ts_start": ts_start,
        "ts_end": ts_end,
        "prompt": prompt,
        "runtime": {
            "mode": resolved_mode,
            "aura_ref": resolved_ref,
            "seed": seed,
            "requested_mode": cfg.mode,
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
