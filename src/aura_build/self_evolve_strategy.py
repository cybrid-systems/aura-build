"""Adaptive self-evolve strategy + latency breakdown (高速进化修复).

North-star: maximize throughput AND accuracy of LeetCode/combat code transforms
WHILE aura-build self-evolves. Latency breakdown shows where Soft serve serial
time goes; adaptive policy shortens closed loops without inventing Soft Ready.

Policy (documented; driven by recent observations in process or scratch state):

1. Explorers hang/timeout → keep/lower effective FIBER_EXPLORER_CAP (never raise
   above module ceiling) or prefer oneshot earlier (honest fiber_live=false).
2. Denseness helpers already green + prior nothing_to_commit → skip rematerialize
   / shorten runtime (keep soft_* files as defense-in-depth).
3. Pursue soft_ready + goal_met fast → optionally shrink worldlines next round
   (e.g. 256→64) until miss, then ramp back. Do not invent Soft Ready.
4. Soft-native gold symbols measured green → skip invent/rematerialize soft_*
   denseness for those symbols (prefer Soft-native; soft_* = temporary DI).
5. Combat/LeetCode inventory nonempty → first-class transform path; skip invent
   soft_extent etc. only when combat inventory empty.

Honesty: fiber_live / incr_proven / Soft Ready only when measured. Soft bugs →
file Aura issues only; do not implement Soft C++ here.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

# Ceiling matches self_evolve_runtime.FIBER_EXPLORER_CAP — adaptive may lower only.
EXPLORER_CAP_CEILING = 32
EXPLORER_CAP_FLOOR = 8
WORLDLINES_FULL = 256
WORLDLINES_FAST = 64
WORLDLINES_RAMP = (64, 128, 256)

# Soft-native gold probes (oneshot). Prefer Soft-native; skip soft_* denseness
# rematerialize when measured green. Not task-specific gold overrides of Soft LLM.
SOFT_NATIVE_GOLD: dict[str, tuple[str, str]] = {
    "find": ("(find even? (list 1 2 3))", "2"),
    "count": ("(count even? (list 1 2 3 4))", "2"),
    "filter": ("(filter even? (list 1 2 3 4))", "(2 4)"),
    "any": ("(any even? (list 1 3 4))", "#t"),
    "all": ("(all even? (list 2 4 6))", "#t"),
    "partition": ("(partition even? (list 1 2 3 4))", "((2 4) (1 3))"),
    "member": ("(member 2 (list 1 2 3))", "(2 3)"),
    "zip": ("(zip (list 1 2) (list 3 4))", "((1 3) (2 4))"),
    "remove": ("(remove even? (list 1 2 3 4))", "(1 3)"),
    "delete": ("(delete 2 (list 1 2 3 2))", "(1 3)"),
    "last": ("(last (list 1 2 3))", "3"),
    "string-take": ('(string-take "abcd" 2)', '"ab"'),
    "string-drop": ('(string-drop "abcd" 2)', '"cd"'),
    "list:take": ("(list:take (list 1 2 3 4) 2)", "(1 2)"),
}

# soft_* helper key → Soft-native gold key (None = no Soft-native skip).
HELPER_SOFT_NATIVE: dict[str, str | None] = {
    "helper": None,  # worldline_pick — host kernel helper, keep denseness
    "starts_helper": None,
    "ends_helper": None,
    "contains_helper": None,
    "split_helper": None,
    "replace_helper": None,
    "trim_helper": None,
    "downcase_helper": None,
    "upcase_helper": None,
    "pad_helper": None,
    "take_helper": "string-take",
    "drop_helper": "string-drop",
    "list_take_helper": "list:take",
    "list_drop_helper": None,  # Soft list:drop unbound — keep denseness DI
    "make_list_helper": None,
    "for_each_helper": None,
    "hash_for_each_helper": None,
    "hash_fold_helper": None,
    "foldr_helper": None,
    "hash_empty_helper": None,
    "hash_to_list_helper": None,
    "any_helper": "any",
    "all_helper": "all",
    "last_helper": "last",
    "find_helper": "find",
    "count_helper": "count",
    "remove_helper": "remove",
    "delete_helper": "delete",
}

STATE_NAME = "self_evolve_strategy.json"


def strategy_path(repo: Path, harness_root: Path | None = None) -> Path:
    root = Path(harness_root) if harness_root else (repo / ".aura-build")
    root.mkdir(parents=True, exist_ok=True)
    return root / STATE_NAME


def load_strategy(repo: Path, harness_root: Path | None = None) -> dict[str, Any]:
    path = strategy_path(repo, harness_root)
    if not path.is_file():
        return _default_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _default_state()
    if not isinstance(data, dict):
        return _default_state()
    base = _default_state()
    base.update(data)
    return base


def save_strategy(
    repo: Path, state: dict[str, Any], harness_root: Path | None = None
) -> str:
    path = strategy_path(repo, harness_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path)


def _default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "explorer_cap": EXPLORER_CAP_CEILING,
        "prefer_oneshot_early": False,
        "worldlines": WORLDLINES_FULL,
        "worldlines_idx": 2,  # index into WORLDLINES_RAMP → 256
        "last_helpers_all_green": False,
        "last_nothing_to_commit": False,
        "last_explorer_hang": False,
        "last_pursue_soft_ready": False,
        "last_pursue_goal_met": False,
        "last_pursue_ms": None,
        "soft_native_green": {},
        "recent_latency": [],
        "notes": [],
    }


class LatencyClock:
    """Wall-clock phase tracker for self-evolve JSON events + progress summary."""

    def __init__(self, *, session: str = "self_evolve") -> None:
        self.session = session
        self.t0 = time.monotonic()
        self.phases: list[dict[str, Any]] = []
        self._open: dict[str, float] = {}

    def start(self, name: str) -> None:
        self._open[name] = time.monotonic()

    def end(
        self,
        name: str,
        *,
        ok: bool | None = None,
        fiber_live: bool | None = None,
        n: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        t1 = time.monotonic()
        t_start = self._open.pop(name, t1)
        ms = max(0, int((t1 - t_start) * 1000))
        ev: dict[str, Any] = {"phase": name, "ms": ms}
        if ok is not None:
            ev["ok"] = bool(ok)
        if fiber_live is not None:
            ev["fiber_live"] = bool(fiber_live)
        if n is not None:
            ev["n"] = int(n)
        if extra:
            ev.update(extra)
        self.phases.append(ev)
        return ev

    def mark(
        self,
        name: str,
        *,
        ok: bool | None = None,
        fiber_live: bool | None = None,
        n: int | None = None,
        ms: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a completed phase (caller already timed, or zero-cost mark)."""
        ev: dict[str, Any] = {"phase": name, "ms": int(ms or 0)}
        if ok is not None:
            ev["ok"] = bool(ok)
        if fiber_live is not None:
            ev["fiber_live"] = bool(fiber_live)
        if n is not None:
            ev["n"] = int(n)
        if extra:
            ev.update(extra)
        self.phases.append(ev)
        return ev

    def total_ms(self) -> int:
        return max(0, int((time.monotonic() - self.t0) * 1000))

    def summary(self, *, fiber_live: bool | None = None) -> dict[str, Any]:
        by_phase = {p["phase"]: p for p in self.phases}
        return {
            "session": self.session,
            "total_ms": self.total_ms(),
            "phases": list(self.phases),
            "fiber_live": fiber_live,
            "progress": _progress_line(self.phases, self.total_ms(), fiber_live),
        }

    def emit_event(self, event: str = "self_evolve_latency") -> dict[str, Any]:
        payload = {"event": event, **self.summary()}
        print(json.dumps(payload, ensure_ascii=False))
        return payload


def _progress_line(
    phases: list[dict[str, Any]], total_ms: int, fiber_live: bool | None
) -> str:
    bits: list[str] = [f"total={total_ms}ms"]
    if fiber_live is not None:
        bits.append(f"fiber_live={'true' if fiber_live else 'false'}")
    for p in phases:
        name = p.get("phase")
        ms = p.get("ms")
        ok = p.get("ok")
        n = p.get("n")
        part = f"{name}={ms}ms"
        if ok is not None:
            part += f"/{'ok' if ok else 'fail'}"
        if n is not None:
            part += f"/n={n}"
        fl = p.get("fiber_live")
        if fl is not None:
            part += f"/fl={'t' if fl else 'f'}"
        bits.append(part)
    return " ".join(bits)


def probe_soft_native(
    aura_bin: str,
    *,
    symbols: dict[str, tuple[str, str]] | None = None,
    timeout_s: float = 8.0,
) -> dict[str, Any]:
    """Measure Soft-native gold binds via cold oneshot. Never invents green."""
    gold = symbols or SOFT_NATIVE_GOLD
    env = os.environ.copy()
    env["AURA_SANDBOX"] = env.get("AURA_SANDBOX") or "off"
    env["AURA_PIPELINE_STRICT"] = env.get("AURA_PIPELINE_STRICT") or "0"
    results: dict[str, Any] = {}
    t0 = time.monotonic()
    if not Path(aura_bin).is_file():
        return {
            "ok": False,
            "reason": "aura_bin_missing",
            "green": {},
            "ms": 0,
            "results": {},
        }
    for name, (expr, expect) in gold.items():
        try:
            proc = subprocess.run(
                [aura_bin, "-e", expr],
                capture_output=True,
                text=True,
                timeout=timeout_s,
                env=env,
                check=False,
            )
            out = (proc.stdout or "").strip()
            ok = proc.returncode == 0 and out == expect
            results[name] = {
                "ok": ok,
                "out": out[:120],
                "expect": expect,
                "rc": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            results[name] = {"ok": False, "reason": "timeout", "expect": expect}
        except OSError as exc:
            results[name] = {"ok": False, "reason": f"os:{exc}", "expect": expect}
    green = {k: bool(v.get("ok")) for k, v in results.items()}
    ms = max(0, int((time.monotonic() - t0) * 1000))
    return {
        "ok": True,
        "reason": "probed",
        "green": green,
        "ms": ms,
        "results": results,
        "n_green": sum(1 for v in green.values() if v),
        "n_total": len(green),
    }


def effective_explorer_cap(state: dict[str, Any], *, requested: int | None = None) -> int:
    """Adaptive explorer cap: never above ceiling; lower on hang observations."""
    cap = int(state.get("explorer_cap") or EXPLORER_CAP_CEILING)
    cap = max(EXPLORER_CAP_FLOOR, min(EXPLORER_CAP_CEILING, cap))
    if requested is not None:
        cap = max(1, min(cap, int(requested)))
    return cap


def effective_worldlines(state: dict[str, Any], *, requested: int | None = None) -> int:
    """Adaptive pursue/runtime worldlines from recent soft_ready+goal_met speed."""
    wl = int(state.get("worldlines") or WORLDLINES_FULL)
    wl = max(WORLDLINES_FAST, min(WORLDLINES_FULL, wl))
    if requested is not None and int(requested) > 0:
        # Honor explicit CLI when lower than adaptive; allow adaptive shrink of default 256.
        req = int(requested)
        if req < WORLDLINES_FULL:
            return req
        return min(req, wl)
    return wl


def should_prefer_oneshot(state: dict[str, Any]) -> bool:
    return bool(state.get("prefer_oneshot_early"))


def should_skip_helper_rematerialize(
    state: dict[str, Any],
    *,
    helper_key: str,
    helper_path: Path,
    soft_native_green: dict[str, bool] | None = None,
) -> tuple[bool, str]:
    """Return (skip, reason). Prefer Soft-native; skip redundant denseness."""
    if not helper_path.is_file():
        return False, "missing_file"
    native_key = HELPER_SOFT_NATIVE.get(helper_key)
    green = soft_native_green if soft_native_green is not None else state.get("soft_native_green") or {}
    if native_key and bool(green.get(native_key)):
        return True, f"soft_native_skip:{native_key}"
    if state.get("last_helpers_all_green") and state.get("last_nothing_to_commit"):
        return True, "already_green_nothing_to_commit"
    return False, "run"


def observe_runtime_round(
    state: dict[str, Any],
    *,
    helpers: dict[str, Any],
    explorers: list[dict[str, Any]] | None,
    fiber_live: bool,
    fallback_oneshot: bool,
    hang_or_timeout: bool,
    nothing_to_commit: bool,
    latency: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update strategy after a runtime round (same process or persisted)."""
    helper_oks = [
        bool(v.get("ok"))
        for k, v in helpers.items()
        if isinstance(v, dict) and (k == "helper" or str(k).endswith("_helper") or str(k).endswith("helper"))
    ]
    if not helper_oks:
        helper_oks = [bool(v.get("ok")) for v in helpers.values() if isinstance(v, dict)]
    all_green = bool(helper_oks) and all(helper_oks)
    state["last_helpers_all_green"] = all_green
    state["last_nothing_to_commit"] = bool(nothing_to_commit)

    hang = bool(hang_or_timeout)
    if explorers:
        for e in explorers:
            st = str(e.get("status") or "")
            if st in ("timeout", "hang") or e.get("hang") or (
                not e.get("ok") and int(e.get("ms") or 0) >= 14000
            ):
                hang = True
                break
    state["last_explorer_hang"] = hang

    cap = int(state.get("explorer_cap") or EXPLORER_CAP_CEILING)
    notes: list[str] = list(state.get("notes") or [])[-20:]
    if hang:
        new_cap = max(EXPLORER_CAP_FLOOR, min(cap, EXPLORER_CAP_CEILING // 2))
        state["explorer_cap"] = new_cap
        state["prefer_oneshot_early"] = True
        notes.append(f"hang→cap={new_cap},prefer_oneshot")
    elif fiber_live and not fallback_oneshot and all_green:
        # Recovery: slowly allow cap back toward ceiling; clear oneshot prefer.
        state["prefer_oneshot_early"] = False
        if cap < EXPLORER_CAP_CEILING:
            state["explorer_cap"] = min(EXPLORER_CAP_CEILING, cap + 8)
            notes.append(f"fiber_ok→cap={state['explorer_cap']}")
    elif fallback_oneshot and not hang:
        # Honest oneshot fallback without hang — keep cap, prefer oneshot next once.
        state["prefer_oneshot_early"] = True
        notes.append("oneshot_fallback→prefer_oneshot_next")

    if latency:
        recent = list(state.get("recent_latency") or [])
        recent.append(
            {
                "total_ms": latency.get("total_ms"),
                "progress": latency.get("progress"),
                "fiber_live": fiber_live,
            }
        )
        state["recent_latency"] = recent[-10:]
    state["notes"] = notes[-20:]
    return state


def observe_pursue_round(
    state: dict[str, Any],
    *,
    soft_ready: bool,
    goal_met: bool,
    ms: int | None,
    requested_worldlines: int | None = None,
) -> dict[str, Any]:
    """Adaptive worldlines: soft_ready+goal_met fast → shrink until miss, then ramp."""
    state["last_pursue_soft_ready"] = bool(soft_ready)
    state["last_pursue_goal_met"] = bool(goal_met)
    state["last_pursue_ms"] = ms
    notes: list[str] = list(state.get("notes") or [])[-20:]
    idx = int(state.get("worldlines_idx") if state.get("worldlines_idx") is not None else 2)
    idx = max(0, min(len(WORLDLINES_RAMP) - 1, idx))

    fast = ms is not None and int(ms) < 45_000
    if soft_ready and goal_met and fast:
        # Shrink toward WORLDLINES_FAST
        idx = max(0, idx - 1)
        notes.append(f"pursue_fast_ok→wl={WORLDLINES_RAMP[idx]}")
    elif not goal_met or not soft_ready:
        # Miss / not soft_ready → ramp up
        idx = min(len(WORLDLINES_RAMP) - 1, idx + 1)
        notes.append(f"pursue_miss_or_not_ready→wl={WORLDLINES_RAMP[idx]}")

    state["worldlines_idx"] = idx
    state["worldlines"] = WORLDLINES_RAMP[idx]
    if requested_worldlines is not None and int(requested_worldlines) < WORLDLINES_FULL:
        # Explicit low CLI stays sticky for this observe only via effective_worldlines
        pass
    state["notes"] = notes[-20:]
    return state


def leetcode_inventory_nonempty(repo: Path) -> bool:
    root = repo / "corpus" / "leetcode"
    if not root.is_dir():
        return False
    for p in root.iterdir():
        if p.is_dir() and (p / "tests.json").is_file() and (p / "problem.md").is_file():
            return True
    return False


def combat_inventory_nonempty(repo: Path) -> bool:
    """Combat first-class when docs/combat inventory or scratch combat targets exist."""
    docs = repo / "docs" / "self-evolve-combat"
    if docs.is_dir() and any(docs.glob("*.md")):
        # Docs alone are not inventory — check for concrete combat fixtures
        pass
    combat_scratch = repo / "scratch" / "self_evolve_combat"
    if combat_scratch.is_dir():
        for p in combat_scratch.iterdir():
            if p.suffix in (".json", ".jsonl") or p.name.startswith("combat_"):
                return True
    # LeetCode nonempty counts as transform inventory for dual goal
    return leetcode_inventory_nonempty(repo)


def skipped_helper_stub(
    *,
    path: str,
    reason: str,
    selected: str = "skip",
) -> dict[str, Any]:
    return {
        "ok": True,
        "reason": reason,
        "path": path,
        "selected": selected,
        "fiber_live": False,  # skip did not re-measure denseness this round
        "materialize": "skipped",
        "src_len": 0,
        "denseness_note": reason,
        "skipped": True,
        "incr_proven": False,
    }


def run_timed(
    clock: LatencyClock,
    phase: str,
    fn: Callable[[], dict[str, Any]],
    *,
    fiber_live_key: str = "fiber_live",
) -> dict[str, Any]:
    clock.start(phase)
    out = fn()
    clock.end(
        phase,
        ok=bool(out.get("ok")) if isinstance(out, dict) else None,
        fiber_live=bool(out.get(fiber_live_key)) if isinstance(out, dict) and fiber_live_key in out else None,
        extra={"skipped": bool(out.get("skipped"))} if isinstance(out, dict) and out.get("skipped") else None,
    )
    return out
