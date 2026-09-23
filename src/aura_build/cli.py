"""Headless CLI — thin host over the Aura kernel (`aura/*.aura`).

Argparse + env wiring + Parquet adapter. Product orch/worldline/prove/harness/
acp/tui live in Aura. Without a healthy AURA_BIN the host refuses (exit 2)
instead of silently running deleted Python orch.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aura_build import __version__
from aura_build.deprecated import KERNEL_TAG, refuse
from aura_build.export import export_trajectories, write_parquet
from aura_build.harness import AUTOPROMOTE_ENV, default_root
from aura_build.kernel import (
    invoke_aura_kernel,
    kernel_available,
    prefer_aura_kernel,
)
from aura_build.l2_weights import (
    L2PromoteError,
    list_l2_artifacts,
    promote_l2_offline,
    resolve_l2_weights,
)
from aura_build.memory import MemoryStore
from aura_build.prove_incr import doctor_snapshot, write_refuse_report
from aura_build.runtime import AuraUnavailable


def _clean_kernel_text(s: str) -> str:
    out = []
    for ln in (s or "").splitlines():
        if not ln.strip() or ln.strip() == "#t":
            continue
        ln = (
            ln.replace("=#t", "=True")
            .replace("=#f", "=False")
            .replace("= #t", "= True")
            .replace("= #f", "= False")
        )
        out.append(ln)
    return "\n".join(out)


def _try_aura_kernel(
    cmd: str,
    env_vars: dict[str, str],
    *,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
    harness_root: Path | None = None,
    timeout_s: float = 120.0,
) -> int | None:
    """Run Aura kernel when preferred+available; return exit code.

    None ⇒ caller should refuse (Python orch removed) or use a host-only path.
    """
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
    out = _clean_kernel_text(result.stdout)
    if out:
        print(out)
    err = _clean_kernel_text(result.stderr)
    if err:
        print(err, file=sys.stderr)
    return result.exit_code


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aura-build",
        description=(
            "Dev-time room on the Aura FlatAST floor — kernel is Aura. "
            "Thin Python host (argparse + Parquet adapter)."
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
    hm.add_argument("--prompt", required=True)
    hm.add_argument("--set", dest="sets", action="append", default=[], metavar="KEY=VAL")
    hm.add_argument(
        "--fitness-weight",
        dest="fitness_weights",
        action="append",
        default=[],
        metavar="KEY=VAL",
    )
    hm.add_argument("--autopropote", action="store_true")
    hm.add_argument("--harness-root", type=Path, default=None)
    hm.add_argument("--seed", type=int, default=None)
    hm.add_argument("--profile", choices=("aura-repo",), default=None)
    hm.add_argument("--out", type=Path, default=None)
    hm.add_argument("--json", action="store_true")
    hm.add_argument("--aura-bin", default=None)
    hm.add_argument("--aura-ref", default=None)

    mem = sub.add_parser("memory", help="get/set per-profile notes under .aura-build/")
    mem_sub = mem.add_subparsers(dest="mem_cmd", required=True)
    mg = mem_sub.add_parser("get")
    mg.add_argument("--profile", default="default")
    mg.add_argument("--key", required=True)
    mg.add_argument("--harness-root", type=Path, default=None)
    ms = mem_sub.add_parser("set")
    ms.add_argument("--profile", default="default")
    ms.add_argument("--key", required=True)
    ms.add_argument("--value", required=True)
    ms.add_argument("--harness-root", type=Path, default=None)
    ms.add_argument("--json-value", action="store_true")
    ml = mem_sub.add_parser("list")
    ml.add_argument("--profile", default="default")
    ml.add_argument("--harness-root", type=Path, default=None)

    exp = sub.add_parser(
        "export",
        help="batch-export trajectory JSONL → JSON (+ Parquet adapter); Aura-first",
    )
    exp.add_argument("inputs", nargs="*", type=Path)
    exp.add_argument("--out", type=Path, default=Path("trajectories/export.json"))
    exp.add_argument("--parquet", type=Path, default=None)
    exp.add_argument("--no-parquet", action="store_true")
    exp.add_argument("--include-raw", action="store_true")
    exp.add_argument("--no-redact", action="store_true")
    exp.add_argument("--strict", action="store_true")
    exp.add_argument("--json", action="store_true")

    show = sub.add_parser("harness-show", help="print live harness config")
    show.add_argument("--harness-root", type=Path, default=None)
    show.add_argument("--json", action="store_true")

    tui = sub.add_parser("tui", help="session status stub (Aura kernel)")
    tui.add_argument("--harness-root", type=Path, default=None)
    tui.add_argument("--json", action="store_true")

    acp = sub.add_parser("acp", help="agent control plane hooks (Aura kernel)")
    acp_sub = acp.add_subparsers(dest="acp_cmd", required=True)
    acp_hooks = acp_sub.add_parser("hooks")
    acp_hooks.add_argument("--json", action="store_true")
    acp_st = acp_sub.add_parser("status")
    acp_st.add_argument("--harness-root", type=Path, default=None)
    acp_st.add_argument("--json", action="store_true")
    acp_start = acp_sub.add_parser("start")
    acp_start.add_argument("--prompt", default=None)
    acp_start.add_argument("--workspace", type=Path, default=None)
    acp_start.add_argument("--harness-root", type=Path, default=None)
    acp_start.add_argument("--json", action="store_true")
    acp_wl = acp_sub.add_parser("worldlines")
    acp_wl.add_argument("--workspace", type=Path, default=None)
    acp_wl.add_argument("--traj", type=Path, default=None)
    acp_wl.add_argument("--harness-root", type=Path, default=None)
    acp_wl.add_argument("--json", action="store_true")
    acp_disc = acp_sub.add_parser("discard")
    acp_disc.add_argument("--workspace", type=Path, required=True)
    acp_disc.add_argument("--ref", required=True)
    acp_disc.add_argument("--reason", default="acp_discard")
    acp_disc.add_argument("--json", action="store_true")
    acp_prom = acp_sub.add_parser("promote")
    acp_prom.add_argument("--id", required=True)
    acp_prom.add_argument("--notes", default="")
    acp_prom.add_argument("--harness-root", type=Path, default=None)
    acp_prom.add_argument("--json", action="store_true")
    acp_exp = acp_sub.add_parser("export")
    acp_exp.add_argument("--out", type=Path, default=Path("trajectories/export.json"))
    acp_exp.add_argument("--include-raw", action="store_true")
    acp_exp.add_argument("--no-parquet", action="store_true")
    acp_exp.add_argument("--json", action="store_true")

    l2 = sub.add_parser("l2", help="L2 offline metadata weights")
    l2_sub = l2.add_subparsers(dest="l2_cmd", required=True)
    l2_show = l2_sub.add_parser("show")
    l2_show.add_argument("--id", required=True)
    l2_show.add_argument("--harness-root", type=Path, default=None)
    l2_show.add_argument("--json", action="store_true")
    l2_list = l2_sub.add_parser("list")
    l2_list.add_argument("--harness-root", type=Path, default=None)
    l2_list.add_argument("--json", action="store_true")
    l2_prom = l2_sub.add_parser("promote")
    l2_prom.add_argument("--id", required=True)
    l2_prom.add_argument("--notes", default="")
    l2_prom.add_argument("--from-export", type=Path, default=None)
    l2_prom.add_argument("--harness-root", type=Path, default=None)
    l2_prom.add_argument("--overwrite", action="store_true")
    l2_prom.add_argument("--json", action="store_true")

    prove = sub.add_parser("prove-incr", help="storm-still-incr prove-or-refuse (Aura)")
    prove.add_argument("--cycles", type=int, default=8)
    prove.add_argument("--worldlines", type=int, default=3)
    prove.add_argument("--aura-bin", default=None)
    prove.add_argument("--aura-ref", default=None)
    prove.add_argument("--timeout", type=float, default=30.0)
    prove.add_argument("--no-fiber-probe", action="store_true")
    prove.add_argument("--out", type=Path, default=None)
    prove.add_argument("--harness-root", type=Path, default=None)
    prove.add_argument("--json", action="store_true")

    doc = sub.add_parser("doctor", help="Aura probe + last prove-incr report")
    doc.add_argument("--aura-bin", default=None)
    doc.add_argument("--aura-ref", default=None)
    doc.add_argument("--harness-root", type=Path, default=None)
    doc.add_argument("--skip-probe", action="store_true")
    doc.add_argument("--json", action="store_true")

    return p


def _add_run_args(run_p: argparse.ArgumentParser) -> None:
    run_p.add_argument("--prompt", required=True)
    run_p.add_argument("--out", type=Path, default=None)
    run_p.add_argument("--seed", type=int, default=None)
    run_p.add_argument("--worldlines", type=int, default=3)
    run_p.add_argument(
        "--mode",
        choices=("simulated", "aura", "auto"),
        default="simulated",
        help="runtime backend recorded in traj (Aura kernel interprets)",
    )
    run_p.add_argument("--aura-bin", default=None)
    run_p.add_argument("--aura-ref", default=None)
    run_p.add_argument("--profile", choices=("aura-repo",), default=None)
    run_p.add_argument("--workspace", type=Path, default=None)
    run_p.add_argument("--keep-workspace", action="store_true")
    run_p.add_argument("--no-live-build", action="store_true")
    run_p.add_argument("--memory-profile", default=None)
    run_p.add_argument("--l2-weights-id", default=None)
    run_p.add_argument("--harness-root", type=Path, default=None)
    run_p.add_argument("--json", action="store_true")
    run_p.add_argument(
        "--attach-prove",
        action=argparse.BooleanOptionalAction,
        default=True,
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
        "AURA_BUILD_KEEP_WORKSPACE": "1" if args.keep_workspace else "0",
        "AURA_BUILD_NO_LIVE_BUILD": "1" if args.no_live_build else "0",
        "AURA_BUILD_JSON": "1" if args.json else "0",
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
    kc = _try_aura_kernel(
        "run",
        env,
        aura_bin=args.aura_bin,
        aura_ref=args.aura_ref,
        harness_root=root,
    )
    if kc is not None:
        return kc
    return refuse("run", reason="aura_kernel_unavailable")


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
        "AURA_BUILD_AUTOPROMOTE_FLAG": "1" if args.autopropote else "",
        "AURA_BUILD_JSON": "1" if args.json else "0",
    }
    if args.seed is not None:
        env["AURA_BUILD_SEED"] = str(args.seed)
    if args.profile:
        env["AURA_BUILD_PROFILE"] = args.profile
    kc = _try_aura_kernel(
        "harness-mutate",
        env,
        aura_bin=args.aura_bin,
        aura_ref=args.aura_ref,
        harness_root=root,
    )
    if kc is not None:
        return kc
    return refuse("harness-mutate", reason="aura_kernel_unavailable")


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
    # Thin host JSON I/O (not product orch)
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
    env = {"AURA_BUILD_JSON": "1" if args.json else "0"}
    kc = _try_aura_kernel("harness-show", env, harness_root=root)
    if kc is not None:
        return kc
    return refuse("harness-show", reason="aura_kernel_unavailable")


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
                    cleaned = _clean_kernel_text(kr.stdout)
                    if cleaned:
                        print(cleaned)
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

    # Host-side batch I/O adapter (not product orch) when Aura unavailable
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
        "kernel": "python_host",
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"exported={s.episodes_exported} files={s.files_read} "
            f"skipped_invalid={s.episodes_skipped_invalid} "
            f"redacted={s.redacted} kernel=python_host json={result.json_path}"
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
    harness = root or default_root()
    env = {"AURA_BUILD_TUI_JSON": "1" if args.json else "0"}
    if not prefer_aura_kernel():
        return refuse("tui", reason="force_python_deprecated")
    ok, _bin, _err = kernel_available(None, None)
    if not ok:
        return refuse("tui", reason="aura_kernel_unavailable")
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
        cleaned = _clean_kernel_text(kr.stdout)
        if cleaned:
            print(cleaned)
    return kr.exit_code if kr.exit_code is not None else (0 if kr.ok else 2)


def _cmd_acp(args: argparse.Namespace) -> int:
    root = _harness_root_arg(args)
    harness = root or default_root()
    op = args.acp_cmd
    if op == "export":
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
    env: dict[str, str] = {
        "AURA_BUILD_ACP_OP": op,
        "AURA_BUILD_ACP_JSON": "1" if getattr(args, "json", False) else "0",
        "AURA_BUILD_ACP_PROMPT": getattr(args, "prompt", "") or "",
        "AURA_BUILD_ACP_WORKSPACE": str(getattr(args, "workspace", "") or ""),
        "AURA_BUILD_ACP_TRAJ": str(getattr(args, "traj", "") or ""),
        "AURA_BUILD_ACP_REF": getattr(args, "ref", "") or "",
        "AURA_BUILD_ACP_REASON": getattr(args, "reason", "") or "acp_discard",
        "AURA_BUILD_ACP_L2_ID": getattr(args, "id", "") or "",
        "AURA_BUILD_ACP_L2_NOTES": getattr(args, "notes", "") or "",
    }
    if not prefer_aura_kernel():
        return refuse(f"acp {op}", reason="force_python_deprecated")
    ok, _bin, _err = kernel_available(None, None)
    if not ok:
        return refuse(f"acp {op}", reason="aura_kernel_unavailable")
    try:
        kr = invoke_aura_kernel("acp", env, harness_root=harness)
    except AuraUnavailable as exc:
        print(f"error: aura kernel: {exc}", file=sys.stderr)
        return 2
    if getattr(args, "json", False):
        payload = kr.response or {}
        if op == "hooks":
            print(json.dumps(payload.get("hooks") or {}, indent=2, sort_keys=True))
        elif op in ("status", "start"):
            print(json.dumps(payload.get("status") or {}, indent=2, sort_keys=True))
        elif op == "worldlines":
            print(json.dumps(payload.get("worldlines") or [], indent=2, sort_keys=True))
        elif op == "discard":
            print(json.dumps(payload.get("result") or payload, indent=2, sort_keys=True))
        elif op == "promote":
            print(json.dumps(payload.get("ref") or payload, indent=2, sort_keys=True))
        else:
            print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        cleaned = _clean_kernel_text(kr.stdout)
        if cleaned:
            print(cleaned)
    return kr.exit_code if kr.exit_code is not None else (0 if kr.ok else 2)


def _cmd_l2(args: argparse.Namespace) -> int:
    root = _harness_root_arg(args) or default_root()
    # promote --from-export stays host (corpus gate)
    if args.l2_cmd == "promote" and getattr(args, "from_export", None) is not None:
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
                f"artifact_present={ref.artifact_present} path={ref.artifact_path} "
                f"kernel=python_host"
            )
        return 0

    env = {
        "AURA_BUILD_L2_OP": args.l2_cmd,
        "AURA_BUILD_L2_ID": getattr(args, "id", "") or "",
        "AURA_BUILD_L2_NOTES": getattr(args, "notes", "") or "",
        "AURA_BUILD_JSON": "1" if args.json else "0",
    }
    if args.l2_cmd == "promote":
        env["AURA_BUILD_L2_OVERWRITE"] = "1" if args.overwrite else "0"
    kc = _try_aura_kernel("l2", env, harness_root=root)
    if kc is not None:
        return kc

    # Thin host metadata I/O when Aura unavailable
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
                export_path=None,
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
    if args.cycles < 1 or args.worldlines < 1:
        print("error: --cycles and --worldlines must be >= 1", file=sys.stderr)
        return 2
    root = Path(args.harness_root) if args.harness_root else default_root()
    env = {
        "AURA_BUILD_CYCLES": str(args.cycles),
        "AURA_BUILD_WORLDLINES": str(args.worldlines),
        "AURA_BUILD_JSON": "1" if args.json else "0",
        "AURA_BUILD_NO_FIBER_PROBE": "1" if args.no_fiber_probe else "0",
    }
    if args.out:
        env["AURA_BUILD_PROVE_OUT"] = str(args.out)
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

    # Honest refuse only — no Python storm orch
    reason = "aura_binary_missing"
    ok, _bin, err = kernel_available(args.aura_bin, args.aura_ref)
    if err:
        reason = err if "missing" in (err or "") else (err or reason)
        if not ok and err and "GLIBCXX" in err:
            reason = "aura_glibcxx_mismatch"
        elif not ok and err:
            reason = "aura_unhealthy"
    report, path = write_refuse_report(
        reason=reason,
        path=args.out,
        root=root,
        cycles=args.cycles,
        worldlines=args.worldlines,
    )
    payload = report.to_dict()
    payload["report_path"] = str(path)
    payload["kernel"] = KERNEL_TAG
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"incr_proven={report.incr_proven} measured={report.measured} "
            f"aura_healthy={report.aura_healthy} reason={report.reason} "
            f"session_model={report.session_model} fiber_live={report.fiber_live} "
            f"kernel={KERNEL_TAG} report={path}"
        )
    # Refuse is honest; exit 0 so CI can assert flags without Python orch green-path
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    root = Path(args.harness_root) if args.harness_root else default_root()
    if not args.skip_probe:
        kc = _try_aura_kernel(
            "doctor",
            {"AURA_BUILD_JSON": "1" if args.json else "0"},
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
        print("aura-build doctor")
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
            f"l3_online={h.get('l3_online')} kernel={snap.get('kernel')}"
        )
        print("  tips: " + " | ".join(snap.get("tips") or []))
    return 0


def console_main() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    console_main()
