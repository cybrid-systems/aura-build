"""Orchestrator: scout → mutate → eval → select-best (RuntimeBackend + M2/M3)."""

from __future__ import annotations

import hashlib
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from aura_build.harness import (
    CanaryResult,
    HarnessConfig,
    HarnessDecision,
    HarnessProposal,
    decide,
    default_root,
    load_harness,
    propose_mutate,
    score_with_weights,
    validate_harness,
)
from aura_build.l2_weights import resolve_l2_weights
from aura_build.memory import MemoryStore
from aura_build.profile_aura_repo import (
    PROFILE_ID as AURA_REPO_PROFILE,
    AuraRepoProfile,
    evaluate_candidate,
    resolve_profile,
)
from aura_build.prove_incr import attach_prove_metadata, merge_prove_into_runtime
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
    "HarnessCanaryEpisode",
    "OrchConfig",
    "Worldline",
    "eval_worldline",
    "memory_update",
    "mutate_worldlines",
    "run_episode",
    "run_harness_canary",
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
class HarnessCanaryEpisode:
    """Result of propose → canary → commit|heal|discard."""

    proposal: HarnessProposal
    canary: CanaryResult
    decision: HarnessDecision
    episode: dict[str, Any]


@dataclass
class OrchConfig:
    """Episode config.

    M1: backend from mode (simulated|aura|auto).
    M2: optional ``profile=aura-repo`` enables shared FlatAST-*workspace*
    fan-out with stable refs + discard losers (still not fiber-live).
    M3: optional harness / memory / L2 stub ids; canary path is separate.
    """

    n_worldlines: int = 3
    seed: int | None = None
    l1_strategy_id: str = "m3.harness.select_best"
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
    # M3
    harness: HarnessConfig | None = None
    harness_root: Path | str | None = None
    memory_profile: str | None = None
    apply_fitness_weights: bool = True
    harness_actions: list[dict[str, Any]] = field(default_factory=list)
    harness_mid: str | None = None
    shadow: bool = False
    # Post-M5: auto-attach latest prove-incr / doctor honesty into traj runtime
    # (cheap JSON read; never invents incr_proven/fiber_live true).
    attach_prove: bool = True


def scout(prompt: str, cfg: OrchConfig) -> dict[str, Any]:
    """Scout phase — record task + harness hints."""
    return {
        "prompt": prompt,
        "l1_strategy_id": cfg.l1_strategy_id,
        "hints": [
            "anti-postman",
            "multi-candidate",
            "select-best",
            "stable-ref",
            "harness-canary",
        ],
        "mode": cfg.mode,
        "profile": cfg.profile,
        "harness_mid": cfg.harness_mid,
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


def memory_update(
    profile_id: str,
    updates: dict[str, Any],
    *,
    root: Path | str | None = None,
    mid: str | None = None,
) -> list[dict[str, Any]]:
    """Update per-profile memory notes via orch (file-backed under .aura-build/)."""
    base = Path(root) if root is not None else default_root()
    store = MemoryStore(root=base / "memory")
    notes = store.update(profile_id, updates, mid=mid)
    return [n.to_dict() for n in notes]


def _resolve_harness(cfg: OrchConfig) -> HarnessConfig | None:
    if cfg.harness is not None:
        return cfg.harness
    root = Path(cfg.harness_root) if cfg.harness_root else None
    path = (root or default_root()) / "harness.json"
    if path.is_file():
        return load_harness(root)
    return None


def _apply_harness_defaults(cfg: OrchConfig) -> OrchConfig:
    """Fill orch knobs from harness when caller left defaults."""
    h = _resolve_harness(cfg)
    if h is None:
        return cfg
    # Only overlay when caller used stock defaults for these fields.
    # Explicit CLI values already sit on cfg; we treat harness as source of
    # truth when ``cfg.harness`` was provided (canary), else soft-fill.
    if cfg.harness is not None:
        cfg.n_worldlines = h.worldline_count
        cfg.mode = h.routing
        cfg.l1_strategy_id = h.l1_strategy_id
        cfg.l2_weights_id = h.l2_weights_id
    return cfg


def run_episode(prompt: str, cfg: OrchConfig | None = None) -> EpisodeResult:
    """Full scout→mutate→eval→select-best; returns episode dict + selected."""
    cfg = cfg or OrchConfig()
    if cfg.l3_online:
        raise ValueError("L3 online weights are experimental-only; refuse in M0–M5")

    cfg = _apply_harness_defaults(cfg)

    # Resolve L2 stub (by id only).
    l2 = resolve_l2_weights(cfg.l2_weights_id, root=cfg.harness_root)
    if l2 is not None and cfg.l2_weights_id is None:
        cfg.l2_weights_id = l2.weights_id

    profile_name = (cfg.profile or "").strip().lower() or None
    if profile_name and profile_name != AURA_REPO_PROFILE:
        raise ValueError(
            f"unknown profile: {cfg.profile!r} (supported: {AURA_REPO_PROFILE!r})"
        )

    if profile_name == AURA_REPO_PROFILE:
        result = _run_aura_repo_episode(prompt, cfg)
    else:
        result = _run_backend_episode(prompt, cfg)

    # Optional memory touch: record last selected id under memory_profile.
    if cfg.memory_profile:
        memory_update(
            cfg.memory_profile,
            {
                "last_selected_id": result.selected.id,
                "last_prompt": prompt[:200],
                "last_fitness": result.selected.eval.get("fitness"),
            },
            root=cfg.harness_root,
            mid=cfg.harness_mid,
        )
        result.episode.setdefault("memory", {})
        result.episode["memory"]["profile_id"] = cfg.memory_profile
        result.episode["memory"]["updated_keys"] = [
            "last_selected_id",
            "last_prompt",
            "last_fitness",
        ]

    if l2 is not None:
        result.episode["harness"]["l2_ref"] = l2.to_dict()

    if cfg.attach_prove:
        fields = attach_prove_metadata(root=cfg.harness_root)
        merge_prove_into_runtime(result.episode.setdefault("runtime", {}), fields)

    return result


def run_harness_canary(
    prompt: str,
    *,
    patches: dict[str, Any] | None = None,
    fitness_weight_patches: dict[str, float] | None = None,
    autopropote: bool | None = None,
    seed: int | None = None,
    harness_root: Path | str | None = None,
    profile: str | None = None,
    try_live_build: bool = False,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
) -> HarnessCanaryEpisode:
    """Propose harness mutate → canary episode on shadow → commit|heal|discard.

    Default AUTOPROMOTE off: a passing canary still **discards** unless
    ``autopropote=True`` or ``AURA_BUILD_AUTOPROMOTE=1``.
    """
    root = Path(harness_root) if harness_root is not None else default_root()
    base = load_harness(root)
    proposal = propose_mutate(
        base,
        patches=patches,
        fitness_weight_patches=fitness_weight_patches,
        root=root,
    )
    actions: list[dict[str, Any]] = [proposal.action_propose()]

    # Pre-validate proposed config — reject bad L1 before running episode.
    pre_bad = validate_harness(proposal.proposed)
    if pre_bad:
        canary = CanaryResult(
            mid=proposal.mid,
            accepted=False,
            reasons=pre_bad,
            episode=None,
            baseline_fitness=None,
            canary_fitness=None,
            actions=actions
            + [
                {
                    "op": "canary",
                    "mid": proposal.mid,
                    "ts": _utc_now(),
                    "accepted": False,
                    "reasons": pre_bad,
                    "shadow_profile": proposal.shadow_profile,
                }
            ],
        )
        decision = decide(proposal, canary, autopropote=autopropote, root=root)
        episode = _harness_change_episode(
            prompt=prompt,
            proposal=proposal,
            canary=canary,
            decision=decision,
            seed=_seed_from_prompt(prompt, seed),
        )
        return HarnessCanaryEpisode(
            proposal=proposal, canary=canary, decision=decision, episode=episode
        )

    # Baseline with live harness (shadow memory only).
    baseline_cfg = OrchConfig(
        seed=seed,
        harness=proposal.base,
        harness_root=root,
        memory_profile=proposal.shadow_profile,
        harness_mid=proposal.mid,
        harness_actions=list(actions),
        shadow=True,
        profile=profile,
        try_live_build=try_live_build,
        aura_bin=aura_bin,
        aura_ref=aura_ref,
        mode=proposal.base.routing,
        n_worldlines=proposal.base.worldline_count,
        l1_strategy_id=proposal.base.l1_strategy_id,
        l2_weights_id=proposal.base.l2_weights_id,
    )
    baseline = run_episode(prompt, baseline_cfg)
    baseline_fit = float(baseline.selected.eval["fitness"])

    canary_cfg = OrchConfig(
        seed=seed,
        harness=proposal.proposed,
        harness_root=root,
        memory_profile=proposal.shadow_profile,
        harness_mid=proposal.mid,
        harness_actions=list(actions),
        shadow=True,
        profile=profile,
        try_live_build=try_live_build,
        aura_bin=aura_bin,
        aura_ref=aura_ref,
        mode=proposal.proposed.routing,
        n_worldlines=proposal.proposed.worldline_count,
        l1_strategy_id=proposal.proposed.l1_strategy_id,
        l2_weights_id=proposal.proposed.l2_weights_id,
    )
    try:
        canary_ep = run_episode(prompt, canary_cfg)
        canary_fit = float(canary_ep.selected.eval["fitness"])
        passed = bool(canary_ep.selected.eval.get("passed", True))
        # Reject if canary fails tests or collapses fitness badly.
        reasons: list[str] = []
        if not passed:
            reasons.append("canary selected worldline passed=false")
        if canary_fit + 1e-9 < baseline_fit * 0.5:
            reasons.append(
                f"canary fitness {canary_fit:.4f} << baseline {baseline_fit:.4f}"
            )
        accepted = not reasons
        canary_action = {
            "op": "canary",
            "mid": proposal.mid,
            "ts": _utc_now(),
            "accepted": accepted,
            "reasons": reasons,
            "shadow_profile": proposal.shadow_profile,
            "baseline_fitness": baseline_fit,
            "canary_fitness": canary_fit,
            "canary_episode_id": canary_ep.episode["episode_id"],
        }
        actions.append(canary_action)
        canary = CanaryResult(
            mid=proposal.mid,
            accepted=accepted,
            reasons=reasons,
            episode=canary_ep.episode,
            baseline_fitness=baseline_fit,
            canary_fitness=canary_fit,
            actions=list(actions),
        )
    except (AuraUnavailable, ValueError) as exc:
        reasons = [str(exc)]
        actions.append(
            {
                "op": "canary",
                "mid": proposal.mid,
                "ts": _utc_now(),
                "accepted": False,
                "reasons": reasons,
                "shadow_profile": proposal.shadow_profile,
            }
        )
        canary = CanaryResult(
            mid=proposal.mid,
            accepted=False,
            reasons=reasons,
            episode=None,
            baseline_fitness=baseline_fit,
            canary_fitness=None,
            actions=list(actions),
        )

    decision = decide(proposal, canary, autopropote=autopropote, root=root)
    episode = _harness_change_episode(
        prompt=prompt,
        proposal=proposal,
        canary=canary,
        decision=decision,
        seed=_seed_from_prompt(prompt, seed),
        nested=canary.episode,
        harness_root=root,
    )
    # Tag shadow memory with decision.
    memory_update(
        proposal.shadow_profile,
        {
            "last_harness_mid": proposal.mid,
            "last_harness_outcome": decision.outcome,
            "autopropote": decision.autopropote,
        },
        root=root,
        mid=proposal.mid,
    )
    return HarnessCanaryEpisode(
        proposal=proposal, canary=canary, decision=decision, episode=episode
    )


def _harness_change_episode(
    *,
    prompt: str,
    proposal: HarnessProposal,
    canary: CanaryResult,
    decision: HarnessDecision,
    seed: int,
    nested: dict[str, Any] | None = None,
    harness_root: Path | str | None = None,
) -> dict[str, Any]:
    """Episode that records mid + harness actions (every harness change)."""
    ts = _utc_now()
    # Minimal valid worldline so schema accepts the harness-change tape.
    if nested and nested.get("worldlines"):
        worldlines = nested["worldlines"]
        selected_id = nested["selected_id"]
        selection_reason = nested.get("selection_reason", "max_fitness")
        discarded = nested.get("discarded") or []
        runtime_mode = nested.get("runtime", {}).get("mode", "simulated")
    else:
        worldlines = [
            {
                "id": "wl-harness-0",
                "parent_id": None,
                "mutations": [
                    {
                        "op": "harness_mutate",
                        "target_id": f"harness:{proposal.base.harness_id}",
                        "summary": f"canary mid={proposal.mid} outcome={decision.outcome}",
                        "mid": proposal.mid,
                        "changes": proposal.changes,
                    }
                ],
                "eval": {
                    "fitness": float(canary.canary_fitness or 0.0),
                    "passed": canary.accepted,
                    "metrics": {
                        "tests_passed": 1 if canary.accepted else 0,
                        "tests_total": 1,
                        "incr_compile_ms": 0,
                        "compile_ms": 0,
                        "audit_ok": True,
                        "incr_claimed": False,
                        "incr_proven": False,
                    },
                    "notes": f"harness canary {decision.outcome}",
                },
            }
        ]
        selected_id = "wl-harness-0"
        selection_reason = f"harness_{decision.outcome}"
        discarded = []
        runtime_mode = "simulated"

    episode: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "episode_id": str(uuid.uuid4()),
        "ts_start": ts,
        "ts_end": _utc_now(),
        "prompt": prompt,
        "runtime": {
            "mode": runtime_mode,
            "requested_mode": proposal.proposed.routing,
            "aura_ref": None,
            "seed": seed,
            "incr_proven": False,
            "shadow": True,
            "harness_canary": True,
        },
        "harness": {
            "l1_strategy_id": proposal.proposed.l1_strategy_id,
            "l2_weights_id": proposal.proposed.l2_weights_id,
            "l3_online": False,
            "mid": proposal.mid,
            "harness_id": proposal.proposed.harness_id,
            "version_base": proposal.base.version,
            "version_proposed": proposal.proposed.version,
            "config_proposed": proposal.proposed.to_dict(),
            "config_base": proposal.base.to_dict(),
            "actions": decision.actions,
            "outcome": decision.outcome,
            "autopropote": decision.autopropote,
            "committed": decision.committed,
            "shadow_profile": proposal.shadow_profile,
        },
        "worldlines": worldlines,
        "selected_id": selected_id,
        "selection_reason": selection_reason,
        "discarded": discarded,
        "privacy": {
            "redacted": False,
            "retention_class": "dogfood",
        },
    }
    l2 = resolve_l2_weights(proposal.proposed.l2_weights_id, root=harness_root)
    if l2 is not None:
        episode["harness"]["l2_ref"] = l2.to_dict()
    # Harness-change tapes also carry prove-incr honesty (default attach ON).
    fields = attach_prove_metadata(root=harness_root)
    merge_prove_into_runtime(episode.setdefault("runtime", {}), fields)
    return episode


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
    harness = cfg.harness
    for i, wl in enumerate(raw):
        got = backend.eval_worldline(wl, prompt, seed, i)
        ev = dict(got["eval"])
        if cfg.apply_fitness_weights and harness is not None:
            metrics = dict(ev.get("metrics") or {})
            ev["fitness"] = score_with_weights(
                metrics,
                harness.fitness_weights,
                fallback_fitness=float(ev["fitness"]),
            )
            metrics["fitness_weights_applied"] = True
            ev["metrics"] = metrics
        evaluated.append(
            Worldline(
                id=got["id"],
                parent_id=got.get("parent_id"),
                mutations=list(got.get("mutations") or []),
                eval=ev,
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
        profile = _stub_profile(cfg)

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
    """Mutate notes on shared workspace; score via aura-repo fitness hooks."""
    evaluated: list[Worldline] = []
    harness = cfg.harness
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

        metrics = fit.to_eval_metrics()
        fitness = float(fit.fitness)
        if cfg.apply_fitness_weights and harness is not None:
            fitness = score_with_weights(
                metrics, harness.fitness_weights, fallback_fitness=fitness
            )
            metrics["fitness_weights_applied"] = True

        evaluated.append(
            Worldline(
                id=cid,
                parent_id=ws.parent.ref_id,
                mutations=[mutation],
                eval={
                    "fitness": fitness,
                    "passed": fit.passed,
                    "metrics": metrics,
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
    if cfg.shadow:
        runtime["shadow"] = True

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

    harness_block: dict[str, Any] = {
        "l1_strategy_id": cfg.l1_strategy_id,
        "l2_weights_id": cfg.l2_weights_id,
        "l3_online": False,
    }
    if cfg.harness_mid:
        harness_block["mid"] = cfg.harness_mid
    if cfg.harness_actions:
        harness_block["actions"] = list(cfg.harness_actions)
    if cfg.harness is not None:
        harness_block["config"] = cfg.harness.to_dict()
        harness_block["harness_id"] = cfg.harness.harness_id

    episode: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "episode_id": str(uuid.uuid4()),
        "ts_start": ts_start,
        "ts_end": ts_end,
        "prompt": prompt,
        "runtime": runtime,
        "harness": harness_block,
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
