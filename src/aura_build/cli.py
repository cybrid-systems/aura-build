"""Headless CLI — thin host over the Aura kernel (`aura/*.aura`).

Primary run/prove/harness/memory/l2/acp/export/tui shells to Aura when healthy.
Python keeps schema validate, CI fallback, Parquet adapter for export, and TUI text fallback.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aura_build import __version__
from aura_build.harness import (
    AUTOPROMOTE_ENV,
    default_root,
    load_harness,
)
from aura_build.memory import MemoryStore
from aura_build.orch import AuraUnavailable, OrchConfig, run_episode, run_harness_canary
from aura_build.export import export_trajectories, write_parquet
from aura_build.trajectory import TrajectoryWriter
from aura_build.acp import (
    L2PromoteError,
    acp_discard_worldline,
    acp_list_worldlines,
    acp_promote_l2,
    acp_start_session,
    acp_status,
    describe_hooks,
)
from aura_build.l2_weights import (
    list_l2_artifacts,
    promote_l2_offline,
    resolve_l2_weights,
)
from aura_build.prove_incr import (
    doctor_snapshot,
    prove_or_refuse,
    write_report,
)
from aura_build.tui import format_status

from aura_build.kernel import (
    invoke_aura_kernel,
    kernel_available,
    prefer_aura_kernel,
)


def _try_aura_kernel(
    cmd: str,
    env_vars: dict[str, str],
    *,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
    harness_root: Path | None = None,
    timeout_s: float = 120.0,
) -> int | None:
    """Run Aura kernel when available; return exit code. None ⇒ caller fallback."""
    if not prefer_aura_kernel():
        return None
    ok, _bin, _err = kernel_available(aura_bin, aura_ref)
    if not ok:
        return None
    try:
        result = invoke_aura_kernel(
            cmd,
            env_vars,
            aura_bin=aura_bin,
            aura_ref=aura_ref,
            harness_root=harness_root,
            timeout_s=timeout_s,
        )
    except AuraUnavailable as exc:
        print(f"error: aura kernel: {exc}", file=sys.stderr)
        return 2
    # Replay kernel stdout; drop Aura trailing `#t`; coerce #t/#f for hosts
    def _clean(s: str) -> str:
        out = []
        for ln in (s or "").splitlines():
            if not ln.strip() or ln.strip() == "#t":
                continue
            # Aura prints #t/#f; normalize for host terminals (with/without spaces)
            ln = (
                ln.replace("=#t", "=True")
                .replace("=#f", "=False")
                .replace("= #t", "= True")
                .replace("= #f", "= False")
            )
            out.append(ln)
        return "\n".join(out)
    out = _clean(result.stdout)
    if out:
        print(out)
    err = _clean(result.stderr)
    if err:
        print(err, file=sys.stderr)
    return result.exit_code


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aura-build",
        description=(
            "Dev-time room on the Aura FlatAST floor — kernel is Aura. "
            "Thin Python host (Post-M5 prove-incr / M5 TUI/ACP / L2)."
        ),
    )
    p.add_argument("--version", action="version", version=f"aura-build {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="scout→mutate→eval→select-best episode")
    _add_run_args(run_p)

    hm = sub.add_parser(
        "harness-mutate",
        help=(
            "propose L1 harness mutate → canary on shadow → commit|heal|discard "
            f"(AUTOPROMOTE default OFF; set {AUTOPROMOTE_ENV}=1 or --autopropote)"
        ),
    )
    hm.add_argument("--prompt", required=True, help="canary episode prompt")
    hm.add_argument(
        "--set",
        dest="sets",
        action="append",
        default=[],
        metavar="KEY=VAL",
        help=(
            "harness patch (repeatable): worldline_count|routing|l1_strategy_id|"
            "l2_weights_id"
        ),
    )
    hm.add_argument(
        "--fitness-weight",
        dest="fitness_weights",
        action="append",
        default=[],
        metavar="KEY=VAL",
        help="fitness weight patch (repeatable): tests|compile_ms|audit",
    )
    hm.add_argument(
        "--autopropote",
        action="store_true",
        help=f"commit passing canary to live harness (or {AUTOPROMOTE_ENV}=1)",
    )
    hm.add_argument(
        "--harness-root",
        type=Path,
        default=None,
        help="`.aura-build` root (default: ./.aura-build)",
    )
    hm.add_argument("--seed", type=int, default=None)
    hm.add_argument(
        "--profile",
        choices=("aura-repo",),
        default=None,
        help="optional profile for canary episode",
    )
    hm.add_argument(
        "--out",
        type=Path,
        default=None,
        help="trajectory JSONL path (default: trajectories/episodes.jsonl)",
    )
    hm.add_argument("--json", action="store_true", help="print full episode JSON")
    hm.add_argument("--aura-bin", default=None)
    hm.add_argument("--aura-ref", default=None)

    mem = sub.add_parser("memory", help="get/set per-profile notes under .aura-build/")
    mem_sub = mem.add_subparsers(dest="mem_cmd", required=True)
    mg = mem_sub.add_parser("get", help="get one note")
    mg.add_argument("--profile", default="default")
    mg.add_argument("--key", required=True)
    mg.add_argument("--harness-root", type=Path, default=None)
    ms = mem_sub.add_parser("set", help="set one note")
    ms.add_argument("--profile", default="default")
    ms.add_argument("--key", required=True)
    ms.add_argument("--value", required=True)
    ms.add_argument("--harness-root", type=Path, default=None)
    ms.add_argument("--json-value", action="store_true", help="parse --value as JSON")
    ml = mem_sub.add_parser("list", help="list notes for profile")
    ml.add_argument("--profile", default="default")
    ml.add_argument("--harness-root", type=Path, default=None)

    exp = sub.add_parser(
        "export",
        help=(
            "batch-export trajectory JSONL → JSON array (+ Parquet if "
            "pandas/pyarrow installed); privacy redaction ON by default"
        ),
    )
    exp.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        help=(
            "JSONL files and/or dirs (default: trajectories/*.jsonl and "
            ".aura-build/**/*.jsonl)"
        ),
    )
    exp.add_argument(
        "--out",
        type=Path,
        default=Path("trajectories/export.json"),
        help="JSON array output path (default: trajectories/export.json)",
    )
    exp.add_argument(
        "--parquet",
        type=Path,
        default=None,
        help="optional Parquet path (default: same stem as --out)",
    )
    exp.add_argument(
        "--no-parquet",
        action="store_true",
        help="skip Parquet attempt entirely",
    )
    exp.add_argument(
        "--include-raw",
        action="store_true",
        help="disable privacy redaction (local dogfood only)",
    )
    exp.add_argument(
        "--no-redact",
        action="store_true",
        help="alias of --include-raw",
    )
    exp.add_argument(
        "--strict",
        action="store_true",
        help="fail on invalid JSONL lines instead of skipping",
    )
    exp.add_argument("--json", action="store_true", help="print export stats JSON")

    show = sub.add_parser("harness-show", help="print live harness config")
    show.add_argument("--harness-root", type=Path, default=None)
    show.add_argument("--json", action="store_true")

    tui = sub.add_parser(
        "tui",
        help="session status stub (Aura-first; stdlib printer, not full Textual)",
    )
    tui.add_argument("--harness-root", type=Path, default=None)
    tui.add_argument("--json", action="store_true")

    acp = sub.add_parser(
        "acp",
        help="agent control plane hooks (start/list/promote/discard/export)",
    )
    acp_sub = acp.add_subparsers(dest="acp_cmd", required=True)
    acp_hooks = acp_sub.add_parser("hooks", help="list ACP hook descriptions")
    acp_hooks.add_argument("--json", action="store_true")
    acp_st = acp_sub.add_parser("status", help="session + harness + last traj")
    acp_st.add_argument("--harness-root", type=Path, default=None)
    acp_st.add_argument("--json", action="store_true")
    acp_start = acp_sub.add_parser("start", help="start/refresh session marker")
    acp_start.add_argument("--prompt", default=None)
    acp_start.add_argument("--workspace", type=Path, default=None)
    acp_start.add_argument("--harness-root", type=Path, default=None)
    acp_start.add_argument("--json", action="store_true")
    acp_wl = acp_sub.add_parser("worldlines", help="list worldlines from traj/workspace")
    acp_wl.add_argument("--workspace", type=Path, default=None)
    acp_wl.add_argument("--traj", type=Path, default=None)
    acp_wl.add_argument("--harness-root", type=Path, default=None)
    acp_wl.add_argument("--json", action="store_true")
    acp_disc = acp_sub.add_parser(
        "discard", help="mark worldline discarded in shared workspace"
    )
    acp_disc.add_argument("--workspace", type=Path, required=True)
    acp_disc.add_argument("--ref", required=True, help="candidate ref id (e.g. wl-1)")
    acp_disc.add_argument("--reason", default="acp_discard")
    acp_disc.add_argument("--json", action="store_true")
    acp_prom = acp_sub.add_parser(
        "promote",
        help="offline L2 metadata promote (alias of `l2 promote`)",
    )
    acp_prom.add_argument("--id", required=True)
    acp_prom.add_argument("--notes", default="")
    acp_prom.add_argument("--harness-root", type=Path, default=None)
    acp_prom.add_argument("--json", action="store_true")
    acp_exp = acp_sub.add_parser(
        "export",
        help="hint / thin alias — prefer `aura-build export`",
    )
    acp_exp.add_argument(
        "--out",
        type=Path,
        default=Path("trajectories/export.json"),
    )
    acp_exp.add_argument("--include-raw", action="store_true")
    acp_exp.add_argument("--no-parquet", action="store_true")
    acp_exp.add_argument("--json", action="store_true")

    l2 = sub.add_parser("l2", help="L2 offline metadata weights (stub artifacts)")
    l2_sub = l2.add_subparsers(dest="l2_cmd", required=True)
    l2_show = l2_sub.add_parser("show", help="resolve / load weights id")
    l2_show.add_argument("--id", required=True)
    l2_show.add_argument("--harness-root", type=Path, default=None)
    l2_show.add_argument("--json", action="store_true")
    l2_list = l2_sub.add_parser("list", help="list .aura-build/weights/*.json")
    l2_list.add_argument("--harness-root", type=Path, default=None)
    l2_list.add_argument("--json", action="store_true")
    l2_prom = l2_sub.add_parser(
        "promote",
        help="write offline metadata stub (refuses l3_online=true corpora)",
    )
    l2_prom.add_argument("--id", required=True)
    l2_prom.add_argument("--notes", default="")
    l2_prom.add_argument(
        "--from-export",
        type=Path,
        default=None,
        help="optional export JSON/JSONL to gate (no l3_online=true)",
    )
    l2_prom.add_argument("--harness-root", type=Path, default=None)
    l2_prom.add_argument("--overwrite", action="store_true")
    l2_prom.add_argument("--json", action="store_true")

    prove = sub.add_parser(
        "prove-incr",
        help=(
            "storm-still-incr prove-or-refuse: fail-closed if Aura unhealthy; "
            "never sets incr_proven without measured incr-valid signal"
        ),
    )
    prove.add_argument("--cycles", type=int, default=8, help="rapid mutate+eval cycles")
    prove.add_argument(
        "--worldlines",
        type=int,
        default=3,
        help="concurrent worldline pressure per cycle",
    )
    prove.add_argument("--aura-bin", default=None)
    prove.add_argument("--aura-ref", default=None)
    prove.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="per-eval timeout seconds",
    )
    prove.add_argument(
        "--no-fiber-probe",
        action="store_true",
        help="skip optional fiber/long-lived session probe",
    )
    prove.add_argument(
        "--out",
        type=Path,
        default=None,
        help="report JSON path (default: .aura-build/prove-incr-latest.json)",
    )
    prove.add_argument("--harness-root", type=Path, default=None)
    prove.add_argument("--json", action="store_true")

    doc = sub.add_parser(
        "doctor",
        help="Aura probe + last prove-incr report + honesty flags",
    )
    doc.add_argument("--aura-bin", default=None)
    doc.add_argument("--aura-ref", default=None)
    doc.add_argument("--harness-root", type=Path, default=None)
    doc.add_argument(
        "--skip-probe",
        action="store_true",
        help="do not invoke aura binary (report + paths only)",
    )
    doc.add_argument("--json", action="store_true")

    return p


def _add_run_args(run_p: argparse.ArgumentParser) -> None:
    run_p.add_argument("--prompt", required=True, help="task prompt")
    run_p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="trajectory JSONL path (default: trajectories/episodes.jsonl)",
    )
    run_p.add_argument("--seed", type=int, default=None, help="deterministic seed")
    run_p.add_argument(
        "--worldlines",
        type=int,
        default=3,
        help="number of candidate worldlines (default 3)",
    )
    run_p.add_argument(
        "--mode",
        choices=("simulated", "aura", "auto"),
        default="simulated",
        help="runtime backend: simulated (default), aura (fail if missing), "
        "auto (aura if probe ok else simulated; trajectory records actual mode)",
    )
    run_p.add_argument(
        "--aura-bin",
        default=None,
        help="path to aura binary (else AURA_BIN / discovery)",
    )
    run_p.add_argument(
        "--aura-ref",
        default=None,
        help="aura checkout path (also used for aura-repo profile detection)",
    )
    run_p.add_argument(
        "--profile",
        choices=("aura-repo",),
        default=None,
        help="optional dogfood profile (aura-repo: shared workspace + build.py fitness)",
    )
    run_p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="shared worldline workspace dir (default: ephemeral temp)",
    )
    run_p.add_argument(
        "--keep-workspace",
        action="store_true",
        help="retain workspace dir after episode (implies useful with --workspace)",
    )
    run_p.add_argument(
        "--no-live-build",
        action="store_true",
        help="aura-repo: skip build.py hook; simulated fitness only",
    )
    run_p.add_argument(
        "--memory-profile",
        default=None,
        help="optional memory profile id to update after select-best",
    )
    run_p.add_argument(
        "--l2-weights-id",
        default=None,
        help="optional L2 offline weights id (stub resolve only)",
    )
    run_p.add_argument(
        "--harness-root",
        type=Path,
        default=None,
        help="`.aura-build` root for harness/memory (default: ./.aura-build)",
    )
    run_p.add_argument(
        "--json",
        action="store_true",
        help="print full episode JSON to stdout",
    )
    run_p.add_argument(
        "--attach-prove",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "attach latest prove-incr / doctor honesty into trajectory runtime "
            "(default ON; cheap JSON read; never invents incr_proven true). "
            "Use --no-attach-prove to skip."
        ),
    )


def _parse_kv_list(items: list[str]) -> dict[str, str]:
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


def _coerce_patches(raw: dict[str, str]) -> dict[str, object]:
    patches: dict[str, object] = {}
    for k, v in raw.items():
        if k == "worldline_count":
            patches[k] = int(v)
        elif k in ("routing", "l1_strategy_id", "l2_weights_id"):
            patches[k] = v
        else:
            raise SystemExit(
                f"unknown harness key {k!r} "
                "(allowed: worldline_count, routing, l1_strategy_id, l2_weights_id)"
            )
    return patches


def main(argv: list[str] | None = None) -> int:
    """CLI entry used by tests; returns process exit code."""
    args = build_parser().parse_args(argv)

    if args.cmd == "run":
        return _cmd_run(args)
    if args.cmd == "harness-mutate":
        return _cmd_harness_mutate(args)
    if args.cmd == "memory":
        return _cmd_memory(args)
    if args.cmd == "harness-show":
        return _cmd_harness_show(args)
    if args.cmd == "export":
        return _cmd_export(args)
    if args.cmd == "tui":
        return _cmd_tui(args)
    if args.cmd == "acp":
        return _cmd_acp(args)
    if args.cmd == "l2":
        return _cmd_l2(args)
    if args.cmd == "prove-incr":
        return _cmd_prove_incr(args)
    if args.cmd == "doctor":
        return _cmd_doctor(args)
    return 2


def _cmd_run(args: argparse.Namespace) -> int:
    root = Path(args.harness_root) if args.harness_root else default_root()
    out = args.out or Path("trajectories/episodes.jsonl")
    env = {
        "AURA_BUILD_PROMPT": args.prompt,
        "AURA_BUILD_MODE": args.mode,
        "AURA_BUILD_REQUESTED_MODE": args.mode,
        "AURA_BUILD_WORLDLINES": str(args.worldlines),
        "AURA_BUILD_OUT": str(out),
        "AURA_BUILD_ATTACH_PROVE": "1" if args.attach_prove else "0",
    }
    if args.seed is not None:
        env["AURA_BUILD_SEED"] = str(args.seed)
    if args.profile:
        env["AURA_BUILD_PROFILE"] = args.profile
    if args.workspace:
        env["AURA_BUILD_WORKSPACE"] = str(args.workspace)
    if args.l2_weights_id:
        env["AURA_BUILD_L2"] = args.l2_weights_id
    if args.memory_profile:
        env["AURA_BUILD_MEMORY_PROFILE"] = args.memory_profile
    if args.aura_ref:
        env["AURA_BUILD_AURA_REF"] = args.aura_ref
    # Prefer Aura kernel (product path). --json still falls back to Python
    # so the full episode is printed from the writer path.
    if not args.json:
        kc = _try_aura_kernel(
            "run",
            env,
            aura_bin=args.aura_bin,
            aura_ref=args.aura_ref,
            harness_root=root,
        )
        if kc is not None:
            return kc

    cfg = OrchConfig(
        n_worldlines=args.worldlines,
        seed=args.seed,
        mode=args.mode,
        aura_bin=args.aura_bin,
        aura_ref=args.aura_ref,
        profile=args.profile,
        workspace_dir=args.workspace,
        keep_workspace=args.keep_workspace,
        try_live_build=not args.no_live_build,
        memory_profile=args.memory_profile,
        l2_weights_id=args.l2_weights_id,
        harness_root=args.harness_root,
        attach_prove=bool(args.attach_prove),
    )
    try:
        result = run_episode(args.prompt, cfg)
    except AuraUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    writer = TrajectoryWriter(args.out)
    path = writer.append(result.episode)
    if args.json:
        print(json.dumps(result.episode, ensure_ascii=False, indent=2))
    else:
        sel = result.selected
        mode = result.episode["runtime"]["mode"]
        prof = result.episode["runtime"].get("profile")
        prof_s = prof.get("id") if isinstance(prof, dict) else (args.profile or "-")
        discarded_n = len(result.episode.get("discarded") or [])
        rt = result.episode["runtime"]
        print(
            f"selected={sel.id} fitness={sel.eval['fitness']} "
            f"mode={mode} profile={prof_s} discarded={discarded_n} "
            f"kernel={rt.get('kernel', 'python')} "
            f"incr_proven={rt.get('incr_proven', False)} "
            f"measured={rt.get('measured', False)} "
            f"fiber_live={rt.get('fiber_live', False)} "
            f"episode={result.episode['episode_id']} wrote={path}"
        )
    return 0


def _cmd_harness_mutate(args: argparse.Namespace) -> int:
    try:
        patches = _coerce_patches(_parse_kv_list(args.sets))
        fw_raw = _parse_kv_list(args.fitness_weights)
        fitness_weight_patches = {k: float(v) for k, v in fw_raw.items()}
    except SystemExit:
        raise
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not patches and not fitness_weight_patches:
        print(
            "error: provide at least one --set KEY=VAL or --fitness-weight KEY=VAL",
            file=sys.stderr,
        )
        return 2

    root = Path(args.harness_root) if args.harness_root else default_root()
    out = args.out or Path("trajectories/episodes.jsonl")
    env = {
        "AURA_BUILD_PROMPT": args.prompt,
        "AURA_BUILD_OUT": str(out),
        "AURA_BUILD_HARNESS_PATCHES": json.dumps(patches or {}),
        "AURA_BUILD_FITNESS_PATCHES": json.dumps(fitness_weight_patches or {}),
    }
    # FLAG=1 forces promote; empty clears a stale parent env so AURA_BUILD_AUTOPROMOTE works
    env["AURA_BUILD_AUTOPROMOTE_FLAG"] = "1" if args.autopropote else ""
    if args.seed is not None:
        env["AURA_BUILD_SEED"] = str(args.seed)
    if args.profile:
        env["AURA_BUILD_PROFILE"] = args.profile
    if not args.json:
        kc = _try_aura_kernel(
            "harness-mutate",
            env,
            aura_bin=args.aura_bin,
            aura_ref=args.aura_ref,
            harness_root=root,
        )
        if kc is not None:
            return kc

    try:
        result = run_harness_canary(
            args.prompt,
            patches=patches or None,
            fitness_weight_patches=fitness_weight_patches or None,
            autopropote=True if args.autopropote else None,
            seed=args.seed,
            harness_root=args.harness_root,
            profile=args.profile,
            try_live_build=False,
            aura_bin=args.aura_bin,
            aura_ref=args.aura_ref,
        )
    except AuraUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    writer = TrajectoryWriter(args.out)
    path = writer.append(result.episode)
    if args.json:
        print(json.dumps(result.episode, ensure_ascii=False, indent=2))
    else:
        h = result.episode["harness"]
        print(
            f"mid={h['mid']} outcome={h['outcome']} "
            f"accepted={result.canary.accepted} "
            f"autopropote={h['autopropote']} committed={h['committed']} "
            f"kernel={result.episode['runtime'].get('kernel', 'python')} "
            f"incr_proven={result.episode['runtime'].get('incr_proven', False)} "
            f"episode={result.episode['episode_id']} wrote={path}"
        )
    # Exit 1 when canary rejected (heal); 0 for discard/commit of accepted.
    if not result.canary.accepted:
        return 1
    return 0


def _cmd_memory(args: argparse.Namespace) -> int:
    root = Path(args.harness_root) if args.harness_root else default_root()
    env = {
        "AURA_BUILD_MEM_OP": args.mem_cmd,
        "AURA_BUILD_MEM_PROFILE": getattr(args, "profile", "default") or "default",
        "AURA_BUILD_MEM_KEY": getattr(args, "key", "") or "",
        "AURA_BUILD_MEM_VALUE": getattr(args, "value", "") or "",
    }
    kc = _try_aura_kernel("memory", env, harness_root=root)
    if kc is not None:
        return kc
    store = MemoryStore(root=root / "memory")
    if args.mem_cmd == "get":
        val = store.get(args.profile, args.key)
        if val is None:
            print("null")
            return 1
        print(json.dumps(val, ensure_ascii=False) if not isinstance(val, str) else val)
        return 0
    if args.mem_cmd == "set":
        value: object = args.value
        if args.json_value:
            value = json.loads(args.value)
        note = store.set(args.profile, args.key, value)
        print(json.dumps(note.to_dict(), ensure_ascii=False))
        return 0
    if args.mem_cmd == "list":
        notes = store.list_notes(args.profile)
        print(json.dumps(notes, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    return 2


def _cmd_harness_show(args: argparse.Namespace) -> int:
    root = Path(args.harness_root) if args.harness_root else default_root()
    if not args.json:
        kc = _try_aura_kernel("harness-show", {}, harness_root=root)
        if kc is not None:
            return kc
    cfg = load_harness(root)
    if args.json:
        print(json.dumps(cfg.to_dict(), indent=2, sort_keys=True))
    else:
        print(
            f"harness_id={cfg.harness_id} version={cfg.version} "
            f"worldline_count={cfg.worldline_count} routing={cfg.routing} "
            f"l1={cfg.l1_strategy_id} l2={cfg.l2_weights_id}"
        )
    return 0




def _cmd_export(args: argparse.Namespace) -> int:
    include_raw = bool(args.include_raw or args.no_redact)
    cwd = Path.cwd()
    out_json = Path(args.out)
    if not out_json.is_absolute():
        out_json = cwd / out_json
    input_paths: list[str] = []
    for raw in args.inputs or []:
        p = Path(raw)
        if not p.is_absolute():
            p = cwd / p
        input_paths.append(str(p))

    root = default_root()
    env = {
        "AURA_BUILD_EXPORT_CWD": str(cwd),
        "AURA_BUILD_EXPORT_INPUTS": "\n".join(input_paths),
        "AURA_BUILD_EXPORT_OUT": str(out_json),
        "AURA_BUILD_EXPORT_INCLUDE_RAW": "1" if include_raw else "0",
        "AURA_BUILD_EXPORT_STRICT": "1" if args.strict else "0",
        "AURA_BUILD_EXPORT_WANT_PARQUET": "0" if args.no_parquet else "1",
    }

    used_aura = False
    result_meta: dict = {}
    if prefer_aura_kernel():
        ok, _bin, _err = kernel_available(None, None)
        if ok:
            try:
                kr = invoke_aura_kernel("export", env, harness_root=root)
                used_aura = True
                result_meta = (kr.response or {}).get("result") or {}
                if not args.json:
                    # Replay human summary from kernel stdout (drop trailing #t)
                    for ln in (kr.stdout or "").splitlines():
                        if not ln.strip() or ln.strip() == "#t":
                            continue
                        ln = (
                            ln.replace("=#t", "=True")
                            .replace("=#f", "=False")
                            .replace("= #t", "= True")
                            .replace("= #f", "= False")
                        )
                        print(ln)
                if kr.exit_code not in (0, None) and not result_meta.get("ok", True):
                    return kr.exit_code
            except AuraUnavailable as exc:
                print(f"error: aura kernel: {exc}", file=sys.stderr)
                return 2

    if used_aura:
        parquet_path = None
        parquet_written = False
        parquet_skip_reason = result_meta.get("parquet_skip_reason")
        if not args.no_parquet:
            try:
                episodes = json.loads(out_json.read_text(encoding="utf-8"))
                if not isinstance(episodes, list):
                    episodes = []
            except (OSError, json.JSONDecodeError):
                episodes = []
            pq = (
                Path(args.parquet)
                if args.parquet is not None
                else out_json.with_suffix(".parquet")
            )
            if not pq.is_absolute():
                pq = cwd / pq
            parquet_path, parquet_skip_reason = write_parquet(episodes, pq)
            parquet_written = parquet_path is not None
            if parquet_written and not args.json:
                print(f"parquet={parquet_path}")
            elif parquet_skip_reason and not args.json:
                print(parquet_skip_reason, file=sys.stderr)

        if args.json:
            payload = {
                "json": str(out_json),
                "parquet": str(parquet_path) if parquet_path else None,
                "files_read": result_meta.get("files_read", 0),
                "episodes_exported": result_meta.get("episodes_exported", 0),
                "episodes_skipped_invalid": result_meta.get(
                    "episodes_skipped_invalid", 0
                ),
                "redacted": result_meta.get("redacted", not include_raw),
                "parquet_written": parquet_written,
                "parquet_skip_reason": parquet_skip_reason,
                "kernel": "aura",
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if result_meta.get("ok", True) else 2

    result = export_trajectories(
        inputs=args.inputs or None,
        out_json=args.out,
        out_parquet=args.parquet,
        redact=not include_raw,
        include_raw=include_raw,
        skip_invalid=not args.strict,
        want_parquet=not args.no_parquet,
    )
    s = result.stats
    payload = {
        "json": str(result.json_path),
        "parquet": str(result.parquet_path) if result.parquet_path else None,
        "files_read": s.files_read,
        "episodes_exported": s.episodes_exported,
        "episodes_skipped_invalid": s.episodes_skipped_invalid,
        "redacted": s.redacted,
        "parquet_written": s.parquet_written,
        "parquet_skip_reason": s.parquet_skip_reason,
        "kernel": "python",
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"exported={s.episodes_exported} files={s.files_read} "
            f"skipped_invalid={s.episodes_skipped_invalid} "
            f"redacted={s.redacted} kernel=python json={result.json_path}"
        )
        if s.parquet_written and result.parquet_path:
            print(f"parquet={result.parquet_path}")
        elif s.parquet_skip_reason:
            print(s.parquet_skip_reason, file=sys.stderr)
    return 0


def _harness_root_arg(args: argparse.Namespace) -> Path | None:
    return Path(args.harness_root) if getattr(args, "harness_root", None) else None


def _cmd_tui(args: argparse.Namespace) -> int:
    """TUI status stub — prefer Aura kernel; Python fallback when forced/unavailable."""
    root = _harness_root_arg(args)
    harness = root or default_root()
    env = {
        "AURA_BUILD_TUI_JSON": "1" if args.json else "0",
    }
    if prefer_aura_kernel():
        ok, _bin, _err = kernel_available(None, None)
        if ok:
            try:
                kr = invoke_aura_kernel("tui", env, harness_root=harness)
            except AuraUnavailable as exc:
                print(f"error: aura kernel: {exc}", file=sys.stderr)
                return 2
            if args.json:
                st = (kr.response or {}).get("status") or {}
                if "kernel" not in st:
                    st = dict(st)
                    st["kernel"] = "aura"
                print(json.dumps(st, indent=2, sort_keys=True))
            else:
                for ln in (kr.stdout or "").splitlines():
                    if not ln.strip() or ln.strip() == "#t":
                        continue
                    ln = (
                        ln.replace("=#t", "=True")
                        .replace("=#f", "=False")
                        .replace("= #t", "= True")
                        .replace("= #f", "= False")
                    )
                    print(ln)
            return kr.exit_code if kr.exit_code is not None else (0 if kr.ok else 2)

    # Python fallback
    st = acp_status(root=root)
    if args.json:
        d = st.to_dict()
        d["kernel"] = "python"
        print(json.dumps(d, indent=2, sort_keys=True))
    else:
        print(format_status(st, kernel="python"), end="")
    return 0


def _cmd_acp(args: argparse.Namespace) -> int:
    """ACP hooks — prefer Aura kernel; Python fallback when forced/unavailable."""
    root = _harness_root_arg(args)
    harness = root or default_root()
    op = args.acp_cmd
    # hooks are static — still prefer Aura so kernel=aura is visible when healthy
    env: dict[str, str] = {
        "AURA_BUILD_ACP_OP": {
            "hooks": "hooks",
            "status": "status",
            "start": "start",
            "worldlines": "worldlines",
            "discard": "discard",
            "promote": "promote",
            "export": "export",
        }.get(op, op),
        "AURA_BUILD_ACP_JSON": "1" if getattr(args, "json", False) else "0",
        "AURA_BUILD_ACP_PROMPT": getattr(args, "prompt", "") or "",
        "AURA_BUILD_ACP_WORKSPACE": str(getattr(args, "workspace", "") or ""),
        "AURA_BUILD_ACP_TRAJ": str(getattr(args, "traj", "") or ""),
        "AURA_BUILD_ACP_REF": getattr(args, "ref", "") or "",
        "AURA_BUILD_ACP_REASON": getattr(args, "reason", "") or "acp_discard",
        "AURA_BUILD_ACP_L2_ID": getattr(args, "id", "") or "",
        "AURA_BUILD_ACP_L2_NOTES": getattr(args, "notes", "") or "",
    }
    if op == "export":
        # Reuse export host wiring (Parquet adapter stays Python).
        return _cmd_export(
            argparse.Namespace(
                inputs=[],
                out=args.out,
                parquet=None,
                no_parquet=args.no_parquet,
                include_raw=args.include_raw,
                no_redact=False,
                strict=False,
                json=args.json,
            )
        )

    # Prefer Aura kernel (same host policy as run/prove/harness/export).
    if prefer_aura_kernel():
        ok, _bin, _err = kernel_available(None, None)
        if ok:
            try:
                kr = invoke_aura_kernel("acp", env, harness_root=harness)
            except AuraUnavailable as exc:
                print(f"error: aura kernel: {exc}", file=sys.stderr)
                return 2
            if args.json:
                # Prefer structured response payload over raw stdout.
                payload = kr.response or {}
                if op == "hooks":
                    print(json.dumps(payload.get("hooks") or {}, indent=2, sort_keys=True))
                elif op in ("status", "start"):
                    st = payload.get("status") or {}
                    print(json.dumps(st, indent=2, sort_keys=True))
                elif op == "worldlines":
                    print(json.dumps(payload.get("worldlines") or [], indent=2, sort_keys=True))
                elif op == "discard":
                    print(json.dumps(payload.get("result") or payload, indent=2, sort_keys=True))
                elif op == "promote":
                    print(json.dumps(payload.get("ref") or payload, indent=2, sort_keys=True))
                else:
                    print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                for ln in (kr.stdout or "").splitlines():
                    if not ln.strip() or ln.strip() == "#t":
                        continue
                    ln = (
                        ln.replace("=#t", "=True")
                        .replace("=#f", "=False")
                        .replace("= #t", "= True")
                        .replace("= #f", "= False")
                    )
                    print(ln)
            return kr.exit_code if kr.exit_code is not None else (0 if kr.ok else 2)

    # Python fallback
    if op == "hooks":
        hooks = describe_hooks()
        if args.json:
            print(json.dumps(hooks, indent=2, sort_keys=True))
        else:
            for name, desc in sorted(hooks.items()):
                print(f"{name}: {desc}")
        return 0
    if op == "status":
        st = acp_status(root=root)
        if args.json:
            print(json.dumps(st.to_dict(), indent=2, sort_keys=True))
        else:
            print(format_status(st), end="")
            print("kernel=python")
        return 0
    if op == "start":
        st = acp_start_session(
            prompt=args.prompt,
            root=root,
            workspace=args.workspace,
        )
        if args.json:
            d = st.to_dict()
            d["kernel"] = "python"
            print(json.dumps(d, indent=2, sort_keys=True))
        else:
            print(
                f"session_id={st.session_id} started={st.started} "
                f"last_traj={st.last_traj_path or '-'} kernel=python"
            )
        return 0
    if op == "worldlines":
        rows = acp_list_worldlines(
            root=root,
            workspace=args.workspace,
            traj_path=args.traj,
        )
        if args.json:
            print(json.dumps(rows, indent=2, sort_keys=True))
        else:
            if not rows:
                print("worldlines: (none)")
            for r in rows:
                print(
                    f"{r.get('role', '?'):10} id={r.get('id') or r.get('ref_id')} "
                    f"stable_ref={r.get('stable_ref') or r.get('ref_id')} "
                    f"fitness={r.get('fitness')}"
                )
        return 0
    if op == "discard":
        try:
            payload = acp_discard_worldline(
                args.ref,
                workspace=args.workspace,
                reason=args.reason,
            )
        except (KeyError, FileNotFoundError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        payload = dict(payload)
        payload["kernel"] = "python"
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(
                f"discarded={payload['discarded']} reason={payload['reason']} "
                f"workspace={payload['workspace']} fiber_live=false kernel=python"
            )
        return 0
    if op == "promote":
        try:
            ref = acp_promote_l2(args.id, notes=args.notes or "", root=harness)
        except Exception as exc:  # noqa: BLE001
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if isinstance(ref, dict):
            payload = dict(ref)
        else:
            payload = ref.to_dict() if hasattr(ref, "to_dict") else {"weights_id": args.id}
        payload["kernel"] = "python"
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(
                f"promoted id={payload.get('weights_id', args.id)} "
                f"stub={payload.get('stub', True)} "
                f"artifact_present={payload.get('artifact_present', False)} "
                f"kernel=python"
            )
        return 0
    return 2



def _cmd_l2(args: argparse.Namespace) -> int:
    root = _harness_root_arg(args) or default_root()
    if not args.json and args.l2_cmd in ("show", "list", "promote"):
        env = {
            "AURA_BUILD_L2_OP": args.l2_cmd,
            "AURA_BUILD_L2_ID": getattr(args, "id", "") or "",
            "AURA_BUILD_L2_NOTES": getattr(args, "notes", "") or "",
        }
        # promote --from-export stays Python (corpus gate)
        if args.l2_cmd != "promote" or getattr(args, "from_export", None) is None:
            kc = _try_aura_kernel("l2", env, harness_root=root)
            if kc is not None:
                return kc
    if args.l2_cmd == "show":
        ref = resolve_l2_weights(args.id, root=root)
        if ref is None:
            print("null")
            return 1
        if args.json:
            print(json.dumps(ref.to_dict(), indent=2, sort_keys=True))
        else:
            print(
                f"id={ref.weights_id} loaded={ref.loaded} stub={ref.stub} "
                f"artifact_present={ref.artifact_present} "
                f"created={ref.created or '-'} path={ref.artifact_path or '-'}"
            )
        return 0
    if args.l2_cmd == "list":
        refs = list_l2_artifacts(root=root)
        payload = [r.to_dict() for r in refs]
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            if not refs:
                print("l2 weights: (none)")
            for r in refs:
                print(
                    f"id={r.weights_id} stub={r.stub} "
                    f"created={r.created or '-'} path={r.artifact_path}"
                )
        return 0
    if args.l2_cmd == "promote":
        try:
            ref = promote_l2_offline(
                args.id,
                notes=args.notes,
                root=root,
                export_path=args.from_export,
                overwrite=args.overwrite,
            )
        except L2PromoteError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(ref.to_dict(), indent=2, sort_keys=True))
        else:
            print(
                f"promoted id={ref.weights_id} stub={ref.stub} "
                f"artifact_present={ref.artifact_present} path={ref.artifact_path}"
            )
        return 0
    return 2




def _cmd_prove_incr(args: argparse.Namespace) -> int:
    """Prove-or-refuse storm-still-incr; always writes a report.

    Exit 0 on refuse (unhealthy / unproven) and on proven — the report's
    ``incr_proven`` field is the honesty surface. Exit 2 only on bad args.
    Prefer Aura kernel when binary healthy; Python fail-closed otherwise.
    """
    if args.cycles < 1 or args.worldlines < 1:
        print("error: --cycles and --worldlines must be >= 1", file=sys.stderr)
        return 2
    root = Path(args.harness_root) if args.harness_root else default_root()
    env = {
        "AURA_BUILD_CYCLES": str(args.cycles),
        "AURA_BUILD_WORLDLINES": str(args.worldlines),
    }
    if not args.json:
        kc = _try_aura_kernel(
            "prove-incr",
            env,
            aura_bin=args.aura_bin,
            aura_ref=args.aura_ref,
            harness_root=root,
            timeout_s=max(60.0, float(args.timeout) * max(1, args.cycles)),
        )
        if kc is not None:
            return kc
    report = prove_or_refuse(
        cycles=args.cycles,
        worldline_pressure=args.worldlines,
        aura_bin=args.aura_bin,
        aura_ref=args.aura_ref,
        timeout_s=args.timeout,
        probe_fiber=not args.no_fiber_probe,
    )
    path = write_report(report, path=args.out, root=args.harness_root)
    payload = report.to_dict()
    payload["report_path"] = str(path)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"incr_proven={report.incr_proven} measured={report.measured} "
            f"aura_healthy={report.aura_healthy} reason={report.reason} "
            f"session_model={report.session_model} fiber_live={report.fiber_live} "
            f"cycles_ok={report.cycles_ok}/{report.cycles_completed} "
            f"incr_valid={report.cycles_incr_valid}/{report.cycles_completed} "
            f"report={path}"
        )
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    root = Path(args.harness_root) if args.harness_root else default_root()
    if not args.json and not args.skip_probe:
        kc = _try_aura_kernel(
            "doctor",
            {},
            aura_bin=args.aura_bin,
            aura_ref=args.aura_ref,
            harness_root=root,
        )
        if kc is not None:
            return kc
    snap = doctor_snapshot(
        root=args.harness_root,
        aura_bin=args.aura_bin,
        aura_ref=args.aura_ref,
        run_probe=not args.skip_probe,
    )
    if args.json:
        print(json.dumps(snap, indent=2, sort_keys=True))
    else:
        h = snap["honesty"]
        print("aura-build doctor (Post-M5)")
        print(f"  aura_bin        = {snap.get('aura_bin') or '-'}")
        print(f"  aura_probe_ok   = {snap.get('aura_probe_ok')}")
        err = snap.get("aura_probe_error")
        if err:
            print(f"  aura_probe_error= {str(err)[:200]}")
        print(f"  prove_report    = {snap.get('prove_incr_report_path')}")
        latest = snap.get("prove_incr_latest")
        if latest:
            print(
                f"  last_prove      = incr_proven={latest.get('incr_proven')} "
                f"reason={latest.get('reason')} measured={latest.get('measured')}"
            )
        else:
            print("  last_prove      = (none — run aura-build prove-incr)")
        print(
            f"  honesty         = incr_proven={h.get('incr_proven')} "
            f"fiber_live={h.get('fiber_live')} "
            f"session_model={h.get('session_model')} "
            f"l3_online={h.get('l3_online')}"
        )
        print("  tips: " + " | ".join(snap.get("tips") or []))
    return 0


def console_main() -> None:
    """setuptools console_scripts entry — propagates exit code."""
    raise SystemExit(main())


if __name__ == "__main__":
    console_main()
