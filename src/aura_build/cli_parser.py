"""Argparse surface for aura-build CLI (flags stay here; dispatch in cli.py)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from aura_build import __version__
from aura_build.harness import AUTOPROMOTE_ENV


def _opt(p: argparse.ArgumentParser, *names: str, **kw: Any) -> None:
    p.add_argument(*names, **kw)


def _common(
    p: argparse.ArgumentParser, *, aura: bool = False, harness: bool = True, json_flag: bool = True
) -> None:
    if harness:
        _opt(p, "--harness-root", type=Path, default=None)
    if json_flag:
        _opt(p, "--json", action="store_true")
    if aura:
        _opt(p, "--aura-bin", default=None)
        _opt(p, "--aura-ref", default=None)


def _add_run_args(p: argparse.ArgumentParser) -> None:
    _opt(p, "--prompt", required=True)
    _opt(p, "--out", type=Path, default=None)
    _opt(p, "--seed", type=int, default=None)
    _opt(p, "--worldlines", type=int, default=3)
    _opt(
        p,
        "--mode",
        choices=("simulated", "aura", "auto"),
        default="simulated",
        help="runtime backend recorded in traj (Aura kernel interprets)",
    )
    _common(p, aura=True)
    _opt(p, "--profile", choices=("aura-repo",), default=None)
    _opt(p, "--workspace", type=Path, default=None)
    _opt(p, "--keep-workspace", action="store_true")
    _opt(p, "--no-live-build", action="store_true")
    _opt(p, "--memory-profile", default=None)
    _opt(p, "--l2-weights-id", default=None)
    _opt(p, "--attach-prove", action=argparse.BooleanOptionalAction, default=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aura-build",
        description=(
            "Dev-time room on the Aura FlatAST floor — kernel is Aura. "
            "Thin Python host (argparse + Parquet adapter)."
        ),
    )
    _opt(p, "--version", action="version", version=f"aura-build {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    _add_run_args(sub.add_parser("run", help="scout→mutate→eval→select-best episode"))

    hm = sub.add_parser(
        "harness-mutate",
        help=(
            "propose L1 harness mutate → canary on shadow → commit|heal|discard "
            f"(AUTOPROMOTE default OFF; set {AUTOPROMOTE_ENV}=1 or --autopropote)"
        ),
    )
    _opt(hm, "--prompt", required=True)
    _opt(hm, "--set", dest="sets", action="append", default=[], metavar="KEY=VAL")
    _opt(
        hm,
        "--fitness-weight",
        dest="fitness_weights",
        action="append",
        default=[],
        metavar="KEY=VAL",
    )
    _opt(hm, "--autopropote", action="store_true")
    _common(hm, aura=True)
    _opt(hm, "--seed", type=int, default=None)
    _opt(hm, "--profile", choices=("aura-repo",), default=None)
    _opt(hm, "--out", type=Path, default=None)

    mem = sub.add_parser("memory", help="get/set per-profile notes under .aura-build/")
    msub = mem.add_subparsers(dest="mem_cmd", required=True)
    for name, key, val in (("get", True, False), ("set", True, True), ("list", False, False)):
        mp = msub.add_parser(name)
        _opt(mp, "--profile", default="default")
        _common(mp, harness=True, json_flag=False)
        if key:
            _opt(mp, "--key", required=True)
        if val:
            _opt(mp, "--value", required=True)
            _opt(mp, "--json-value", action="store_true")

    exp = sub.add_parser(
        "export",
        help="batch-export trajectory JSONL → JSON (+ Parquet adapter); Aura-first",
    )
    _opt(exp, "inputs", nargs="*", type=Path)
    _opt(exp, "--out", type=Path, default=Path("trajectories/export.json"))
    _opt(exp, "--parquet", type=Path, default=None)
    _opt(exp, "--no-parquet", action="store_true")
    _opt(exp, "--include-raw", action="store_true")
    _opt(exp, "--no-redact", action="store_true")
    _opt(exp, "--strict", action="store_true")
    _common(exp, harness=False)

    _common(sub.add_parser("harness-show", help="print live harness config"))
    _common(sub.add_parser("tui", help="session status stub (Aura kernel)"))

    acp = sub.add_parser("acp", help="agent control plane hooks (Aura kernel)")
    asub = acp.add_subparsers(dest="acp_cmd", required=True)
    _common(asub.add_parser("hooks"), harness=False)
    for name in ("status", "start", "worldlines", "discard", "promote", "export"):
        ap = asub.add_parser(name)
        if name == "start":
            _opt(ap, "--prompt", default=None)
            _opt(ap, "--workspace", type=Path, default=None)
            _common(ap)
        elif name == "status":
            _common(ap)
        elif name == "worldlines":
            _opt(ap, "--workspace", type=Path, default=None)
            _opt(ap, "--traj", type=Path, default=None)
            _common(ap)
        elif name == "discard":
            _opt(ap, "--workspace", type=Path, required=True)
            _opt(ap, "--ref", required=True)
            _opt(ap, "--reason", default="acp_discard")
            _common(ap, harness=False)
        elif name == "promote":
            _opt(ap, "--id", required=True)
            _opt(ap, "--notes", default="")
            _common(ap)
        else:
            _opt(ap, "--out", type=Path, default=Path("trajectories/export.json"))
            _opt(ap, "--include-raw", action="store_true")
            _opt(ap, "--no-parquet", action="store_true")
            _common(ap, harness=False)

    l2 = sub.add_parser("l2", help="L2 offline metadata weights")
    lsub = l2.add_subparsers(dest="l2_cmd", required=True)
    ls = lsub.add_parser("show")
    _opt(ls, "--id", required=True)
    _common(ls)
    _common(lsub.add_parser("list"))
    lp = lsub.add_parser("promote")
    _opt(lp, "--id", required=True)
    _opt(lp, "--notes", default="")
    _opt(lp, "--from-export", type=Path, default=None)
    _opt(lp, "--overwrite", action="store_true")
    _common(lp)


    llm = sub.add_parser(
        "llm",
        help="thin MiniMax (OpenAI-compatible) chat; key from file, never echoed",
    )
    _opt(llm, "--prompt", required=True, help="user prompt")
    _opt(llm, "--system", default="You are a helpful coding assistant.")
    _opt(llm, "--max-tokens", type=int, default=1024)
    _opt(llm, "--temperature", type=float, default=0.2)
    _opt(
        llm,
        "--thinking",
        choices=("disabled", "enabled"),
        default="disabled",
        help="MiniMax thinking mode (default disabled for speed)",
    )
    _opt(llm, "--env-file", type=Path, default=None)
    _common(llm, harness=False)

    dog = sub.add_parser(
        "llm-dogfood",
        help=(
            "MiniMax→Aura closed loop: propose Aura program → verify → repair "
            "(worldlines select-best; host HTTP + Aura orch stamp)"
        ),
    )
    _opt(
        dog,
        "--task",
        choices=("fib", "greet", "calc", "kv", "stack", "bank", "router", "cache", "queue", "pubsub", "2pc", "twopc", "saga", "exchange"),
        default="fib",
        help="Built-in dogfood task (or use --project for any GOAL.md dir)",
    )
    _opt(
        dog,
        "--project",
        type=Path,
        default=None,
        help=(
            "External project dir (GOAL.md + stub.aura + verify.sh / dogfood.json). "
            "Preferred over extending the hard-coded --task registry."
        ),
    )
    _opt(dog, "--max-rounds", type=int, default=8)
    _opt(dog, "--worldlines", type=int, default=3)
    _opt(dog, "--out", type=Path, default=None)
    _opt(dog, "--workspace", type=Path, default=None)
    _opt(dog, "--env-file", type=Path, default=None)
    _opt(dog, "--keep-workspace", action=argparse.BooleanOptionalAction, default=True)
    _opt(
        dog,
        "--prefer-session",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "prefer long-lived aura --serve verify when session available "
            "(default ON; cold subprocess fallback)"
        ),
    )
    _opt(
        dog,
        "--fiber-explore",
        type=int,
        default=None,
        help=(
            "spawn N explorer worldlines; Soft Ready prefers fiber:spawn denseness "
            "fan-out on shared FlatAST when measured (default: --worldlines)"
        ),
    )
    _opt(
        dog,
        "--explore-tools",
        default="rule,llm,intent",
        help=(
            "comma tools any explorer fiber may use: rule,llm,intent "
            "(strategies — not named agent products; default rule,llm,intent)"
        ),
    )
    _opt(
        dog,
        "--concurrent-llm",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "force every explorer to tools=['llm'] for parallel MiniMax proposes "
            "(also AURA_BUILD_CONCURRENT_LLM=1); stamps concurrent_llm + llm_parallel_ok"
        ),
    )
    _opt(
        dog,
        "--fiber-llm",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "route MiniMax propose through Soft fiber http-post when measured ok "
            "(also AURA_BUILD_LLM_VIA=fiber); stamps llm_via=fiber; denseness≠LLM"
        ),
    )
    _common(dog, aura=True)

    sess = sub.add_parser(
        "session",
        help=(
            "long-lived Aura --serve attach (optimal loop floor): "
            "start|status|stop|dogfood"
        ),
    )
    ssub = sess.add_subparsers(dest="session_cmd", required=True)
    sp_start = ssub.add_parser("start", help="start aura --serve + write marker")
    _opt(sp_start, "--force", action="store_true", help="restart even if alive")
    _common(sp_start, aura=True, harness=True)
    sp_st = ssub.add_parser("status", help="serve_attach_ok / session_model honesty")
    _common(sp_st, aura=True, harness=True)
    sp_stop = ssub.add_parser("stop", help="stop serve process + clear marker")
    _common(sp_stop, aura=False, harness=True, json_flag=True)
    sp_df = ssub.add_parser(
        "dogfood",
        help="closed-loop in-session verify (no MiniMax); compare cold spawns",
    )
    _opt(sp_df, "--rounds", type=int, default=3)
    _opt(sp_df, "--out", type=Path, default=None)
    _opt(
        sp_df,
        "--compare-cold",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="also time cold aura subprocess evals for comparison",
    )
    _common(sp_df, aura=True, harness=True)

    prove = sub.add_parser("prove-incr", help="storm-still-incr prove-or-refuse (Aura)")
    _opt(prove, "--cycles", type=int, default=8)
    _opt(prove, "--worldlines", type=int, default=3)
    _opt(prove, "--timeout", type=float, default=30.0)
    _opt(prove, "--no-fiber-probe", action="store_true")
    _opt(prove, "--out", type=Path, default=None)
    _common(prove, aura=True)

    se = sub.add_parser(
        "self-evolve",
        help=(
            "L1/stamp dogfood (default) or Soft+fiber combat "
            "(`self-evolve combat`); stamp path unchanged"
        ),
    )
    _opt(se, "--prompt", default="self-evolve dogfood aura-build")
    _opt(se, "--worldlines", type=int, default=3)
    _opt(se, "--seed", type=int, default=None)
    _opt(se, "--out", type=Path, default=None)
    _opt(
        se,
        "--verify",
        choices=("none", "smoke", "prove", "kernel"),
        default="smoke",
        help="host verify after Aura materialize (default smoke; stamp path)",
    )
    _opt(se, "--no-push", action="store_true", help="commit only / dry-run push skip (stamp path)")
    _opt(se, "--no-commit", action="store_true", help="skip git commit (materialize+verify only)")
    _opt(
        se,
        "--set",
        dest="sets",
        action="append",
        default=[],
        metavar="KEY=VAL",
        help="optional harness L1 patch (same keys as harness-mutate)",
    )
    _opt(
        se,
        "--fitness-weight",
        dest="fitness_weights",
        action="append",
        default=[],
        metavar="KEY=VAL",
    )
    _common(se, aura=True)
    se_sub = se.add_subparsers(dest="self_evolve_cmd", required=False)
    combat = se_sub.add_parser(
        "combat",
        help=(
            "Soft+fiber closed combat loop (SSOT docs/self-evolve-combat.md): "
            "requires live serve_attach_ok; traj+findings; --no-push default; "
            "dual-sink Aura issue stubs (no kernel edit)"
        ),
    )
    _opt(
        combat,
        "--project",
        type=Path,
        default=None,
        help="project dir (GOAL.md+verify); default examples/projects/mini-saga",
    )
    _opt(
        combat,
        "--task",
        default=None,
        help="optional built-in llm-dogfood task (ignored when --project set)",
    )
    _opt(combat, "--max-rounds", type=int, default=8)
    _opt(combat, "--worldlines", type=int, default=3)
    _opt(
        combat,
        "--fiber-explore",
        type=int,
        default=None,
        help="explorer N (default: --worldlines); Soft denseness when measured",
    )
    _opt(
        combat,
        "--explore-tools",
        default="rule,llm,intent",
        help="comma tools: rule,llm,intent (default rule,llm,intent)",
    )
    _opt(
        combat,
        "--concurrent-llm",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="force explorers to llm-only for parallel MiniMax proposes",
    )
    _opt(
        combat,
        "--fiber-llm",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Soft in-fiber MiniMax when measured (default: on if minimax env-file "
            "exists; --no-fiber-llm forces off)"
        ),
    )
    _opt(combat, "--env-file", type=Path, default=None)
    _opt(
        combat,
        "--out-dir",
        type=Path,
        default=None,
        help="combat artifacts dir (default scratch/self_evolve_combat/)",
    )
    _opt(combat, "--out", type=Path, default=None, help="trajectory JSONL path")
    _opt(
        combat,
        "--start-session",
        action="store_true",
        help="start Soft serve if not attached (needs AURA_BIN / --aura-bin)",
    )
    _opt(
        combat,
        "--stop-session",
        action="store_true",
        help="stop Soft session after combat (default: leave up)",
    )
    _opt(
        combat,
        "--push",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "push aura-build main only after verify green + product materialize "
            "(default --no-push; never pushes Aura kernel)"
        ),
    )
    _opt(
        combat,
        "--dry-run",
        action="store_true",
        help="CI-safe: check attach / plan only; no llm-dogfood (no live Soft required for refuse path)",
    )
    _common(combat, aura=True, harness=True)

    pursue = sub.add_parser(
        "pursue",
        help=(
            "continuous goal-driven loop: prefers in-session mutate:rebind when "
            "serve attach live; else Aura kernel worldlines → select-best; "
            "optional MiniMax hint; optional harness-mutate canary"
        ),
    )
    _opt(pursue, "--goal", required=True, help="goal text for the pursue loop")
    _opt(
        pursue,
        "--predicate",
        default=None,
        help="success predicate, e.g. fitness_ge:0.8 (default fitness_ge:0.8)",
    )
    _opt(pursue, "--min-fitness", type=float, default=None, help="alias for fitness_ge threshold")
    _opt(pursue, "--max-rounds", type=int, default=8)
    _opt(pursue, "--worldlines", type=int, default=3)
    _opt(
        pursue,
        "--mode",
        choices=("simulated", "aura", "auto"),
        default="aura",
        help="runtime backend per round (default aura)",
    )
    _opt(pursue, "--seed", type=int, default=None)
    _opt(pursue, "--out", type=Path, default=None, help="trajectory JSONL (default trajectories/pursue.jsonl)")
    _opt(
        pursue,
        "--with-llm",
        action="store_true",
        help="optional MiniMax one-shot hint (never controller); requires key",
    )
    _opt(
        pursue,
        "--harness-mutate",
        action="store_true",
        help="optional L1 harness-mutate canary once (AUTOPROMOTE off)",
    )
    _opt(pursue, "--env-file", type=Path, default=None, help="MiniMax env file when --with-llm")
    _opt(
        pursue,
        "--prefer-session",
        action="store_true",
        default=True,
        help=(
            "prefer in-session mutate:rebind pursue when serve_same_session_mutate_ok "
            "(default on; Soft Ready async may still be refused)"
        ),
    )
    _opt(
        pursue,
        "--force-kernel",
        action="store_true",
        help="skip serve session path; always dispatch Aura kernel pursue.aura",
    )
    _opt(
        pursue,
        "--no-prefer-session",
        action="store_true",
        help="alias of --force-kernel for pursue",
    )
    _common(pursue, aura=True)

    doc = sub.add_parser("doctor", help="Aura probe + last prove-incr report")
    _opt(doc, "--skip-probe", action="store_true")
    _common(doc, aura=True)
    return p


def parse_kv_list(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in items:
        if "=" not in raw:
            raise SystemExit(f"expected KEY=VAL, got {raw!r}")
        k, v = raw.split("=", 1)
        k = k.strip()
        if not k:
            raise SystemExit(f"empty key in {raw!r}")
        out[k] = v
    return out


def coerce_harness_patches(raw: dict[str, str]) -> dict[str, object]:
    allowed = {"worldline_count", "routing", "l1_strategy_id", "l2_weights_id"}
    patches: dict[str, object] = {}
    for k, v in raw.items():
        if k not in allowed:
            raise SystemExit(
                f"unknown harness key {k!r} "
                "(allowed: worldline_count, routing, l1_strategy_id, l2_weights_id)"
            )
        patches[k] = int(v) if k == "worldline_count" else v
    return patches
