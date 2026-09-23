"""Headless CLI — `aura-build run|harness-mutate|memory|export|tui|acp|l2`."""

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
from aura_build.export import export_trajectories
from aura_build.trajectory import TrajectoryWriter
from aura_build.acp import (
    L2PromoteError,
    acp_discard_worldline,
    acp_list_worldlines,
    acp_start_session,
    acp_status,
    describe_hooks,
)
from aura_build.l2_weights import (
    list_l2_artifacts,
    promote_l2_offline,
    resolve_l2_weights,
)
from aura_build.tui import format_status


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aura-build",
        description=(
            "Dev-time room on the Aura FlatAST floor "
            "(M5: TUI/ACP stub + L2 offline metadata + export + harness canary)."
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
        help="M5 status stub (stdlib): session + last traj path (not a full TUI)",
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
    return 2


def _cmd_run(args: argparse.Namespace) -> int:
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
        print(
            f"selected={sel.id} fitness={sel.eval['fitness']} "
            f"mode={mode} profile={prof_s} discarded={discarded_n} "
            f"incr_proven={result.episode['runtime'].get('incr_proven', False)} "
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
            f"incr_proven={result.episode['runtime'].get('incr_proven', False)} "
            f"episode={result.episode['episode_id']} wrote={path}"
        )
    # Exit 1 when canary rejected (heal); 0 for discard/commit of accepted.
    if not result.canary.accepted:
        return 1
    return 0


def _cmd_memory(args: argparse.Namespace) -> int:
    root = Path(args.harness_root) if args.harness_root else default_root()
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
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"exported={s.episodes_exported} files={s.files_read} "
            f"skipped_invalid={s.episodes_skipped_invalid} "
            f"redacted={s.redacted} json={result.json_path}"
        )
        if s.parquet_written and result.parquet_path:
            print(f"parquet={result.parquet_path}")
        elif s.parquet_skip_reason:
            print(s.parquet_skip_reason, file=sys.stderr)
    return 0



def _harness_root_arg(args: argparse.Namespace) -> Path | None:
    return Path(args.harness_root) if getattr(args, "harness_root", None) else None


def _cmd_tui(args: argparse.Namespace) -> int:
    root = _harness_root_arg(args)
    st = acp_status(root=root)
    if args.json:
        print(json.dumps(st.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_status(st), end="")
    return 0


def _cmd_acp(args: argparse.Namespace) -> int:
    root = _harness_root_arg(args)
    if args.acp_cmd == "hooks":
        hooks = describe_hooks()
        if args.json:
            print(json.dumps(hooks, indent=2, sort_keys=True))
        else:
            for name, desc in sorted(hooks.items()):
                print(f"{name}: {desc}")
        return 0
    if args.acp_cmd == "status":
        st = acp_status(root=root)
        if args.json:
            print(json.dumps(st.to_dict(), indent=2, sort_keys=True))
        else:
            print(format_status(st))
        return 0
    if args.acp_cmd == "start":
        st = acp_start_session(
            prompt=args.prompt,
            root=root,
            workspace=args.workspace,
        )
        if args.json:
            print(json.dumps(st.to_dict(), indent=2, sort_keys=True))
        else:
            print(
                f"session_id={st.session_id} started={st.started} "
                f"last_traj={st.last_traj_path or '-'}"
            )
        return 0
    if args.acp_cmd == "worldlines":
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
    if args.acp_cmd == "discard":
        try:
            payload = acp_discard_worldline(
                args.ref,
                workspace=args.workspace,
                reason=args.reason,
            )
        except (KeyError, FileNotFoundError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(
                f"discarded={payload['discarded']} reason={payload['reason']} "
                f"workspace={payload['workspace']} fiber_live=false"
            )
        return 0
    if args.acp_cmd == "export":
        # Thin wire to existing export command.
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
    return 2


def _cmd_l2(args: argparse.Namespace) -> int:
    root = _harness_root_arg(args)
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



def console_main() -> None:
    """setuptools console_scripts entry — propagates exit code."""
    raise SystemExit(main())


if __name__ == "__main__":
    console_main()
