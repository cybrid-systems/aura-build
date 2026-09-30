"""THIN harness adapter — Soft/Aura KERNEL owns observe-steer product brain.

Product path: ``aura/self_evolve_observe.aura`` samples existing Aura
``query:*`` faces (incremental-relower / dirty-cascade / soa-dirty / type-linear
/ mutation-hold / steal residual) and adapts worldlines / explorer / MiniMax
mix. Soft observe ≠ Hard proof.

Soft storm (force-full / cold-miss / parity / soa-desync / …) → shrink.
Transform ``accuracy_ok=False`` / accuracy_red is NOT Soft storm — Soft keeps
press or amber-mid with llm; host only mirrors Soft knobs (no accuracy→shrink).

This module only starts Soft oneshot (or optional serve raw_line) and reads
harness memory Soft wrote. Do NOT grow a Python evolution brain here.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_SOFT = "/workspace/aura-grok/build/aura"


def resolve_aura_bin(aura_bin: str | None = None) -> str:
    return aura_bin or os.environ.get("AURA_BIN") or DEFAULT_SOFT


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _aura_path(repo: Path | None = None) -> str:
    r = repo or _repo_root()
    lib = os.environ.get("AURA_PATH")
    if lib:
        return lib
    soft_lib = Path("/workspace/aura-grok/lib")
    return f"{soft_lib}:{r / 'aura'}"


def _read_observe_memory(hroot: Path) -> dict[str, Any]:
    mem = hroot / "memory" / "leet_observe.json"
    if not mem.is_file():
        return {}
    try:
        data = json.loads(mem.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def run_kernel_observe_steer(
    *,
    slug: str = "observe",
    aura_bin: str | None = None,
    harness_root: Path | None = None,
    accuracy_ok: bool = True,
    timeout_s: float = 45.0,
    serve_session: Any | None = None,
) -> dict[str, Any]:
    """Invoke Soft ``run-observe-steer-round`` (product brain).

    Prefer live ``serve_session.raw_line`` when provided (same Soft process as
    scoring → counters reflect session work). Else Soft oneshot.
    """
    bin_path = resolve_aura_bin(aura_bin)
    repo = _repo_root()
    hroot = Path(harness_root) if harness_root else repo / ".aura-build"
    form = '(begin (require "self_evolve_observe" all:) (run-observe-steer-round))'
    env = {
        **os.environ,
        "AURA_BIN": bin_path,
        "AURA_PATH": _aura_path(repo),
        "AURA_BUILD_HARNESS_ROOT": str(hroot),
        "AURA_BUILD_SLUG": slug,
        "AURA_BUILD_ACC_OK": "true" if accuracy_ok else "false",
        "AURA_SANDBOX": os.environ.get("AURA_SANDBOX") or "off",
    }
    via = "oneshot"
    stdout = ""
    stderr = ""
    rc = -1
    need_oneshot = True
    if serve_session is not None and hasattr(serve_session, "raw_line"):
        try:
            r = serve_session.raw_line(form, timeout_s=min(30.0, float(timeout_s)))
            ok_sess = r.get("status") == "ok"
            stdout = str(r.get("value") or r.get("msg") or r.get("display") or "")[:500]
            if ok_sess:
                via = "serve_session"
                need_oneshot = False
                rc = 0
            else:
                via = "serve_session_fail→oneshot"
        except Exception as exc:  # noqa: BLE001
            via = f"serve_exc→oneshot:{type(exc).__name__}"
    if need_oneshot:
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
            rc = int(proc.returncode)
            stdout = (proc.stdout or "").strip()
            stderr = (proc.stderr or "")[:300]
            via = "oneshot" if "oneshot" in via else via
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "reason": f"exc:{type(exc).__name__}:{exc}",
                "path": "kernel_observe_steer_adapter",
                "soft_observe_ne_hard": True,
            }
    mem = _read_observe_memory(hroot)
    steer = mem.get("steer") if isinstance(mem.get("steer"), dict) else {}
    gate = mem.get("last_gate") if isinstance(mem.get("last_gate"), dict) else {}
    if not gate and isinstance(mem.get("gate"), str):
        gate = {"gate": mem.get("gate")}
    ok = ("observe_steer ok=true" in stdout) or bool(steer.get("gate") or mem.get("gate"))
    gate_color = (
        (gate.get("gate") if isinstance(gate, dict) else None)
        or mem.get("gate")
        or steer.get("gate")
    )
    storm_red = False
    accuracy_signal = False
    if isinstance(gate, dict):
        storm_red = bool(gate.get("storm_red"))
        accuracy_signal = bool(gate.get("accuracy_signal")) or (
            "accuracy_red" in (gate.get("reasons") or [])
        )
    if not accuracy_signal and isinstance(steer, dict):
        accuracy_signal = bool(steer.get("accuracy_signal"))
    return {
        "ok": ok,
        "via": via,
        "gate": gate_color,
        "storm_red": storm_red,
        "accuracy_signal": accuracy_signal,
        "reasons": (gate.get("reasons") if isinstance(gate, dict) else None) or [],
        "worldlines_prefer": steer.get("worldlines_prefer")
        or mem.get("worldlines_prefer"),
        "explorer_cap_prefer": steer.get("explorer_cap_prefer")
        or mem.get("explorer_cap_prefer"),
        "minimax_cap_prefer": steer.get("minimax_cap_prefer")
        or mem.get("minimax_cap_prefer"),
        "n_mut": steer.get("n_mut") or mem.get("n_mut"),
        "mix": steer.get("mix") or mem.get("mix") or ["rule", "mutate", "llm"],
        "press_fanout": bool(
            steer.get("press_fanout")
            if "press_fanout" in steer
            else mem.get("press_fanout")
        ),
        "soft_observe_ne_hard": True,
        "stdout": stdout[:600],
        "stderr": stderr,
        "returncode": rc,
        "path": "kernel_observe_steer",
        "kernel": "aura",
        "query_keys": [
            "query:incremental-relower-stats",
            "query:dirty-cascade-stats",
            "query:soa-dirty-stats",
            "query:type-linear-commit-health",
            "query:mutation-hold-estimate",
            "query:mutation-hold-live",
            "query:work-steal-stats",
            "query:post-steal-closed-loop-stats",
        ],
        "sample_present": isinstance(mem.get("last_sample"), dict),
    }


def apply_observe_to_strategy(state: dict[str, Any], observe: dict[str, Any]) -> dict[str, Any]:
    """Thin merge: Soft observe knobs → host strategy mirror (no Python brain)."""
    if not observe or not observe.get("ok"):
        return state
    notes = list(state.get("notes") or [])
    gate = observe.get("gate")
    wl = observe.get("worldlines_prefer")
    ex = observe.get("explorer_cap_prefer")
    mix = observe.get("mix")
    press = observe.get("press_fanout")
    if gate:
        state["observe_gate"] = gate
    if isinstance(wl, (int, float)):
        state["worldlines"] = int(wl)
        # keep idx coherent with ramp
        if int(wl) >= 256:
            state["worldlines_idx"] = 2
        elif int(wl) >= 128:
            state["worldlines_idx"] = 1
        else:
            state["worldlines_idx"] = 0
    if isinstance(ex, (int, float)):
        state["explorer_cap"] = max(8, min(64, int(ex)))
    if isinstance(mix, list) and mix:
        state["mix_explorers"] = [str(x) for x in mix]
    state["observe_press_fanout"] = bool(press)
    state["soft_observe_ne_hard"] = True
    state["observe_storm_red"] = bool(observe.get("storm_red"))
    state["observe_accuracy_signal"] = bool(observe.get("accuracy_signal"))
    state["diverge_sticky"] = bool(observe.get("press_fanout")) and gate == "green"
    notes.append(
        f"observe_steer gate={gate} storm={observe.get('storm_red')} "
        f"acc_sig={observe.get('accuracy_signal')} wl={wl} explorer={ex} "
        f"press={press} reasons={observe.get('reasons')}"
    )
    state["notes"] = notes[-24:]
    return state
