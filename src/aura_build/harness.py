"""M3 harness: mutable L1 strategy config + canary propose→eval→commit/heal.

Honesty
-------
- Default AUTOPROMOTE is **OFF**. Env ``AURA_BUILD_AUTOPROMOTE=1`` or
  ``--autopropote`` enables commit after a passing canary (demo only).
- Canary runs on a **shadow** harness snapshot; live ``.aura-build/harness.json``
  is untouched until an explicit commit.
- Every propose / canary / commit / heal / discard writes a ``mid`` and
  trajectory ``harness.actions[]`` entries. Not fiber-live FlatAST.
"""

from __future__ import annotations

import copy
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "AUTOPROMOTE_ENV",
    "DEFAULT_HARNESS_ID",
    "HarnessConfig",
    "HarnessDecision",
    "HarnessProposal",
    "CanaryResult",
    "autopropote_enabled",
    "default_root",
    "decide",
    "load_harness",
    "propose_mutate",
    "save_harness",
    "validate_harness",
]

AUTOPROMOTE_ENV = "AURA_BUILD_AUTOPROMOTE"
DEFAULT_HARNESS_ID = "default"
DEFAULT_STRATEGY = "m3.harness.select_best"

_ALLOWED_ROUTING = frozenset({"simulated", "aura", "auto"})
_WEIGHT_KEYS = ("tests", "compile_ms", "audit")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_root(cwd: Path | str | None = None) -> Path:
    """``.aura-build`` under cwd (or process cwd)."""
    base = Path(cwd) if cwd is not None else Path.cwd()
    return base / ".aura-build"


def autopropote_enabled(flag: bool | None = None) -> bool:
    """AUTOPROMOTE default OFF; explicit True or env=1 enables."""
    if flag is True:
        return True
    if flag is False:
        return False
    raw = os.environ.get(AUTOPROMOTE_ENV, "").strip().lower()
    return raw in ("1", "true", "yes", "on")


@dataclass
class HarnessConfig:
    """Mutable L1 harness object (strategy code knobs).

    Fields
    ------
    worldline_count:
        Candidate fan-out for select-best.
    fitness_weights:
        Relative weights for tests / compile_ms / audit (recorded + used when
        combining metrics; simulated path still produces a scalar fitness).
    routing:
        When to use aura vs simulated: ``simulated`` | ``aura`` | ``auto``.
    l1_strategy_id / l2_weights_id:
        Harness identity fields written into every episode.
    """

    worldline_count: int = 3
    fitness_weights: dict[str, float] = field(
        default_factory=lambda: {"tests": 0.7, "compile_ms": 0.2, "audit": 0.1}
    )
    routing: str = "simulated"
    l1_strategy_id: str = DEFAULT_STRATEGY
    l2_weights_id: str | None = None
    version: int = 1
    harness_id: str = DEFAULT_HARNESS_ID

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HarnessConfig:
        fw = data.get("fitness_weights") or {}
        weights = {
            k: float(fw.get(k, dflt))
            for k, dflt in (("tests", 0.7), ("compile_ms", 0.2), ("audit", 0.1))
        }
        return cls(
            worldline_count=int(data.get("worldline_count", 3)),
            fitness_weights=weights,
            routing=str(data.get("routing", "simulated")),
            l1_strategy_id=str(data.get("l1_strategy_id", DEFAULT_STRATEGY)),
            l2_weights_id=data.get("l2_weights_id"),
            version=int(data.get("version", 1)),
            harness_id=str(data.get("harness_id", DEFAULT_HARNESS_ID)),
        )

    def apply_to_orch_kwargs(self) -> dict[str, Any]:
        """Map harness knobs onto OrchConfig fields."""
        return {
            "n_worldlines": self.worldline_count,
            "mode": self.routing,
            "l1_strategy_id": self.l1_strategy_id,
            "l2_weights_id": self.l2_weights_id,
        }


def validate_harness(cfg: HarnessConfig) -> list[str]:
    """Return list of rejection reasons (empty = ok)."""
    reasons: list[str] = []
    if cfg.worldline_count < 1:
        reasons.append(f"worldline_count must be >= 1, got {cfg.worldline_count}")
    if cfg.worldline_count > 32:
        reasons.append(f"worldline_count too large: {cfg.worldline_count}")
    if cfg.routing not in _ALLOWED_ROUTING:
        reasons.append(
            f"routing must be one of {sorted(_ALLOWED_ROUTING)}, got {cfg.routing!r}"
        )
    for k, v in cfg.fitness_weights.items():
        if not isinstance(v, (int, float)) or v < 0:
            reasons.append(f"fitness_weights[{k}] must be >= 0, got {v!r}")
    total = sum(float(cfg.fitness_weights.get(k, 0.0)) for k in _WEIGHT_KEYS)
    if total <= 0:
        reasons.append("fitness_weights must sum to > 0")
    if not cfg.l1_strategy_id or not str(cfg.l1_strategy_id).strip():
        reasons.append("l1_strategy_id must be non-empty")
    return reasons


def harness_path(root: Path | None = None) -> Path:
    return (root or default_root()) / "harness.json"


def load_harness(root: Path | None = None) -> HarnessConfig:
    path = harness_path(root)
    if not path.is_file():
        return HarnessConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    cfg = HarnessConfig.from_dict(data)
    bad = validate_harness(cfg)
    if bad:
        raise ValueError("stored harness invalid: " + "; ".join(bad))
    return cfg


def save_harness(cfg: HarnessConfig, root: Path | None = None) -> Path:
    bad = validate_harness(cfg)
    if bad:
        raise ValueError("refusing to save invalid harness: " + "; ".join(bad))
    root = root or default_root()
    root.mkdir(parents=True, exist_ok=True)
    path = harness_path(root)
    payload = cfg.to_dict()
    payload["saved_at"] = _utc_now()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


@dataclass
class HarnessProposal:
    mid: str
    base: HarnessConfig
    proposed: HarnessConfig
    changes: list[dict[str, Any]]
    ts: str
    shadow_profile: str

    def action_propose(self) -> dict[str, Any]:
        return {
            "op": "propose",
            "mid": self.mid,
            "ts": self.ts,
            "changes": self.changes,
            "shadow_profile": self.shadow_profile,
        }


@dataclass
class CanaryResult:
    mid: str
    accepted: bool
    reasons: list[str]
    episode: dict[str, Any] | None
    baseline_fitness: float | None
    canary_fitness: float | None
    actions: list[dict[str, Any]]


@dataclass
class HarnessDecision:
    mid: str
    outcome: str  # commit | heal | discard
    autopropote: bool
    committed: bool
    harness: HarnessConfig
    actions: list[dict[str, Any]]
    path: Path | None = None


def propose_mutate(
    base: HarnessConfig | None = None,
    *,
    patches: dict[str, Any] | None = None,
    fitness_weight_patches: dict[str, float] | None = None,
    root: Path | None = None,
    mid: str | None = None,
) -> HarnessProposal:
    """Propose a harness mutation (does not touch live store)."""
    base = base or load_harness(root)
    proposed = copy.deepcopy(base)
    changes: list[dict[str, Any]] = []
    patches = dict(patches or {})

    if "worldline_count" in patches:
        old = proposed.worldline_count
        proposed.worldline_count = int(patches["worldline_count"])
        changes.append(
            {"field": "worldline_count", "from": old, "to": proposed.worldline_count}
        )
    if "routing" in patches:
        old = proposed.routing
        proposed.routing = str(patches["routing"])
        changes.append({"field": "routing", "from": old, "to": proposed.routing})
    if "l1_strategy_id" in patches:
        old = proposed.l1_strategy_id
        proposed.l1_strategy_id = str(patches["l1_strategy_id"])
        changes.append(
            {"field": "l1_strategy_id", "from": old, "to": proposed.l1_strategy_id}
        )
    if "l2_weights_id" in patches:
        old = proposed.l2_weights_id
        val = patches["l2_weights_id"]
        proposed.l2_weights_id = None if val in (None, "", "null") else str(val)
        changes.append(
            {"field": "l2_weights_id", "from": old, "to": proposed.l2_weights_id}
        )

    if fitness_weight_patches:
        for k, v in fitness_weight_patches.items():
            old = proposed.fitness_weights.get(k)
            proposed.fitness_weights[k] = float(v)
            changes.append(
                {
                    "field": f"fitness_weights.{k}",
                    "from": old,
                    "to": proposed.fitness_weights[k],
                }
            )

    if not changes:
        raise ValueError("propose_mutate requires at least one patch")

    proposed.version = int(base.version) + 1
    mut_id = mid or f"mid-{uuid.uuid4().hex[:12]}"
    return HarnessProposal(
        mid=mut_id,
        base=base,
        proposed=proposed,
        changes=changes,
        ts=_utc_now(),
        shadow_profile=f"shadow:{mut_id}",
    )


def decide(
    proposal: HarnessProposal,
    canary: CanaryResult,
    *,
    autopropote: bool | None = None,
    root: Path | None = None,
) -> HarnessDecision:
    """Commit proposed harness, or heal/discard. Default is discard unless promote."""
    promote = autopropote_enabled(autopropote)
    actions: list[dict[str, Any]] = list(canary.actions)

    if not canary.accepted:
        actions.append(
            {
                "op": "heal",
                "mid": proposal.mid,
                "ts": _utc_now(),
                "reasons": canary.reasons,
                "note": "canary rejected; live harness unchanged",
            }
        )
        return HarnessDecision(
            mid=proposal.mid,
            outcome="heal",
            autopropote=promote,
            committed=False,
            harness=proposal.base,
            actions=actions,
        )

    if not promote:
        actions.append(
            {
                "op": "discard",
                "mid": proposal.mid,
                "ts": _utc_now(),
                "reasons": ["autopropote_off"],
                "note": "canary passed but AUTOPROMOTE off; live harness unchanged",
            }
        )
        return HarnessDecision(
            mid=proposal.mid,
            outcome="discard",
            autopropote=False,
            committed=False,
            harness=proposal.base,
            actions=actions,
        )

    path = save_harness(proposal.proposed, root=root)
    actions.append(
        {
            "op": "commit",
            "mid": proposal.mid,
            "ts": _utc_now(),
            "harness_version": proposal.proposed.version,
            "path": str(path),
        }
    )
    return HarnessDecision(
        mid=proposal.mid,
        outcome="commit",
        autopropote=True,
        committed=True,
        harness=proposal.proposed,
        actions=actions,
        path=path,
    )


def score_with_weights(
    metrics: dict[str, Any],
    weights: dict[str, float],
    *,
    fallback_fitness: float,
) -> float:
    """Combine metrics with harness fitness_weights; fall back to scalar."""
    tests_passed = float(metrics.get("tests_passed", 0) or 0)
    tests_total = float(metrics.get("tests_total", 1) or 1)
    test_score = tests_passed / tests_total if tests_total else 0.0
    compile_ms = float(metrics.get("compile_ms") or metrics.get("incr_compile_ms") or 0)
    # Lower compile time is better; map loosely into [0,1].
    compile_score = 1.0 / (1.0 + max(compile_ms, 0.0) / 100.0)
    audit_ok = metrics.get("audit_ok", True)
    audit_score = 1.0 if audit_ok else 0.0

    parts = {
        "tests": test_score,
        "compile_ms": compile_score,
        "audit": audit_score,
    }
    total_w = sum(float(weights.get(k, 0.0)) for k in parts) or 1.0
    weighted = sum(float(weights.get(k, 0.0)) * parts[k] for k in parts) / total_w
    # Blend with backend scalar so simulated episodes stay informative.
    return 0.5 * float(fallback_fitness) + 0.5 * weighted
