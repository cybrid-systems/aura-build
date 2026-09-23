"""Orchestrator: scout → mutate → eval → select-best (RuntimeBackend + M2 profiles)."""

from __future__ import annotations

import hashlib
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from aura_build.profile_aura_repo import (
    PROFILE_ID as AURA_REPO_PROFILE,
    AuraRepoProfile,
    evaluate_candidate,
    resolve_profile,
)
from aura_build.runtime import (
    AuraUnavailable,
    RuntimeBackend,
    SimulatedBackend,
    resolve_backend,
)
from aura_build.schema import SCHEMA_VERSION
from aura_build.worldline import (
    SESSION_SHARED_SUBPROCESS,
    WorldlineWorkspace,
)

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
    stable_ref: str | None = None


@dataclass
class EpisodeResult:
    episode: dict[str, Any]
    selected: Worldline


@dataclass
class OrchConfig:
    """Episode config.

    M1: backend from mode (simulated|aura|auto).
    M2: optional ``profile=aura-repo`` enables shared FlatAST-*workspace*
    fan-out with stable refs + discard losers (still not fiber-live).
    """

    n_worldlines: int = 3
    seed: int | None = None
    l1_strategy_id: str = "m2.worldline.select_best"
    l2_weights_id: str | None = None
    l3_online: bool = False
    mode: str = "simulated"  # simulated | aura | auto
    aura_bin: str | None = None
    aura_ref: str | None = None
    fitness_fn: Callable[[str, int, int], float] | None = None
    backend: RuntimeBackend | None = None
    profile: str | None = None  # None | "aura-repo"
    workspace_dir: Path | str | None = None
    try_live_build: bool = True
    keep_workspace: bool = False


def scout(prompt: str, cfg: OrchConfig) -> dict[str, Any]:
    """Scout phase — record task + harness hints."""
    return {
        "prompt": prompt,
        "l1_strategy_id": cfg.l1_strategy_id,
        "hints": ["anti-postman", "multi-candidate", "select-best", "stable-ref"],
        "mode": cfg.mode,
        "profile": cfg.profile,
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
        stable_ref=raw.get("stable_ref"),
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
        raise ValueError("L3 online weights are experimental-only; refuse in M0–M2")

    profile_name = (cfg.profile or "").strip().lower() or None
    if profile_name and profile_name != AURA_REPO_PROFILE:
        raise ValueError(
            f"unknown profile: {cfg.profile!r} (supported: {AURA_REPO_PROFILE!r})"
        )

    if profile_name == AURA_REPO_PROFILE:
        return _run_aura_repo_episode(prompt, cfg)

    return _run_backend_episode(prompt, cfg)


def _run_backend_episode(prompt: str, cfg: OrchConfig) -> EpisodeResult:
    """M0/M1 path: RuntimeBackend mutate/eval without shared workspace profile."""
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
                stable_ref=got.get("stable_ref"),
            )
        )
    selected, reason = select_best(evaluated)
    ts_end = _utc_now()

    resolved_mode = backend.mode
    resolved_ref = backend.aura_ref if resolved_mode == "aura" else cfg.aura_ref

    episode = _build_episode(
        prompt=prompt,
        cfg=cfg,
        seed=seed,
        ts_start=ts_start,
        ts_end=ts_end,
        evaluated=evaluated,
        selected=selected,
        reason=reason,
        resolved_mode=resolved_mode,
        resolved_ref=resolved_ref,
        runtime_extra={"incr_proven": False},
        discarded=[],
        profile_runtime=None,
    )
    return EpisodeResult(episode=episode, selected=selected)


def _run_aura_repo_episode(prompt: str, cfg: OrchConfig) -> EpisodeResult:
    """M2 aura-repo profile: shared workspace + parent→N stable refs + discard."""
    seed = _seed_from_prompt(prompt, cfg.seed)
    profile = resolve_profile(cfg.aura_ref, prefer_live_build=cfg.try_live_build)
    if profile is None:
        # Still runnable in CI: synthesize a stub profile root under workspace.
        profile = _stub_profile(cfg)

    # Backend for mode honesty (aura/simulated/auto). Profile fitness is separate.
    backend = resolve_backend(
        cfg.mode,
        aura_bin=cfg.aura_bin,
        aura_ref=cfg.aura_ref or str(profile.root),
        fitness_fn=cfg.fitness_fn,
        backend=cfg.backend,
    )

    ts_start = _utc_now()
    scout(prompt, cfg)

    tmp_ctx = None
    if cfg.workspace_dir is not None:
        ws_root = Path(cfg.workspace_dir)
        ws_root.mkdir(parents=True, exist_ok=True)
    else:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="aura-build-wl-")
        ws_root = Path(tmp_ctx.name)

    try:
        ws = WorldlineWorkspace.create(
            ws_root,
            n_candidates=cfg.n_worldlines,
            session_model=SESSION_SHARED_SUBPROCESS,
        )
        evaluated = _eval_on_workspace(
            ws, profile, prompt=prompt, seed=seed, cfg=cfg, backend=backend
        )
        selected, reason = select_best(evaluated)
        fitness_by_id = {w.id: float(w.eval["fitness"]) for w in evaluated}
        discard_recs = ws.discard_losers(selected.id, fitness_by_id)
        ts_end = _utc_now()

        resolved_mode = backend.mode
        resolved_ref = (
            backend.aura_ref
            if resolved_mode == "aura"
            else (cfg.aura_ref or str(profile.root))
        )
        runtime_extra = ws.to_runtime_fields()
        # Prefer profile's explicit incr_proven (always false in M2).
        runtime_extra["incr_proven"] = False
        runtime_extra["incr_claimed"] = profile.incr_claimed

        episode = _build_episode(
            prompt=prompt,
            cfg=cfg,
            seed=seed,
            ts_start=ts_start,
            ts_end=ts_end,
            evaluated=evaluated,
            selected=selected,
            reason=reason,
            resolved_mode=resolved_mode,
            resolved_ref=resolved_ref,
            runtime_extra=runtime_extra,
            discarded=[d.to_dict() for d in discard_recs],
            profile_runtime=profile.to_runtime_dict(),
        )
        if cfg.keep_workspace:
            episode["runtime"]["workspace_kept"] = True
        return EpisodeResult(episode=episode, selected=selected)
    finally:
        if tmp_ctx is not None and not cfg.keep_workspace:
            tmp_ctx.cleanup()


def _eval_on_workspace(
    ws: WorldlineWorkspace,
    profile: AuraRepoProfile,
    *,
    prompt: str,
    seed: int,
    cfg: OrchConfig,
    backend: RuntimeBackend,
) -> list[Worldline]:
    """Mutate notes on shared workspace; score via aura-repo fitness hooks.

    When ``backend.mode == aura``, we still prefer profile fitness for
    compile_ms fields, but may optionally also run the Aura mutate/eval
    bridge for the first candidate only (not claimed as multi-worldline).
    Default M2 path: profile fitness on shared workspace (subprocess or sim).
    """
    evaluated: list[Worldline] = []
    for i, (cid, ref) in enumerate(ws.candidates.items()):
        mutation = ws.fork_note(
            cid,
            summary=(
                f"aura-repo candidate {i} from parent={ws.parent.ref_id} "
                f"for: {prompt[:80]}"
            ),
        )
        fit = evaluate_candidate(
            profile,
            prompt=prompt,
            seed=seed,
            index=i,
            try_live=cfg.try_live_build,
            simulated_fn=cfg.fitness_fn,
        )
        # If user forced mode=aura, attempt one backend eval to keep the
        # bridge exercised — do not pretend N fiber worldlines.
        notes = fit.notes
        if backend.mode == "aura" and i == 0:
            try:
                raw_mut = backend.mutate_worldlines(prompt, seed, 1)[0]
                aura_got = backend.eval_worldline(raw_mut, prompt, seed, 0)
                notes = f"{fit.notes}; aura_bridge={aura_got['eval'].get('notes')}"
            except AuraUnavailable:
                raise
            except Exception as exc:  # noqa: BLE001 — record, keep profile fitness
                notes = f"{fit.notes}; aura_bridge_error={exc}"

        evaluated.append(
            Worldline(
                id=cid,
                parent_id=ws.parent.ref_id,
                mutations=[mutation],
                eval={
                    "fitness": fit.fitness,
                    "passed": fit.passed,
                    "metrics": fit.to_eval_metrics(),
                    "notes": notes,
                },
                stable_ref=ref.ref_id,
            )
        )
    return evaluated


def _stub_profile(cfg: OrchConfig) -> AuraRepoProfile:
    """CI-safe stub when no aura checkout is present."""
    root = Path(cfg.aura_ref) if cfg.aura_ref else Path("/tmp/aura-build-missing-ref")
    return AuraRepoProfile(
        root=root,
        build_py=None,
        has_tests=False,
        fitness_source="simulated",
        incr_claimed=True,
        incr_proven=False,
    )


def _build_episode(
    *,
    prompt: str,
    cfg: OrchConfig,
    seed: int,
    ts_start: str,
    ts_end: str,
    evaluated: list[Worldline],
    selected: Worldline,
    reason: str,
    resolved_mode: str,
    resolved_ref: str | None,
    runtime_extra: dict[str, Any],
    discarded: list[dict[str, Any]],
    profile_runtime: dict[str, Any] | None,
) -> dict[str, Any]:
    runtime: dict[str, Any] = {
        "mode": resolved_mode,
        "aura_ref": resolved_ref,
        "seed": seed,
        "requested_mode": cfg.mode,
        "incr_proven": False,
    }
    runtime.update(runtime_extra)
    if profile_runtime is not None:
        runtime["profile"] = profile_runtime

    worldlines: list[dict[str, Any]] = []
    for w in evaluated:
        entry: dict[str, Any] = {
            "id": w.id,
            "parent_id": w.parent_id,
            "mutations": w.mutations,
            "eval": w.eval,
        }
        if w.stable_ref is not None:
            entry["stable_ref"] = w.stable_ref
        worldlines.append(entry)

    episode: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "episode_id": str(uuid.uuid4()),
        "ts_start": ts_start,
        "ts_end": ts_end,
        "prompt": prompt,
        "runtime": runtime,
        "harness": {
            "l1_strategy_id": cfg.l1_strategy_id,
            "l2_weights_id": cfg.l2_weights_id,
            "l3_online": False,
        },
        "worldlines": worldlines,
        "selected_id": selected.id,
        "selection_reason": reason,
        "discarded": discarded,
        "privacy": {
            "redacted": False,
            "retention_class": "dogfood",
        },
    }
    return episode
