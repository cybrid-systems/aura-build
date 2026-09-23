"""Headless CLI — thin argparse → AURA_BUILD_* → Aura kernel.

Product orch lives in aura/*.aura. Host: dispatch, refuse, Parquet, JSON I/O edges.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

from aura_build.cli_parser import build_parser, coerce_harness_patches, parse_kv_list
from aura_build.deprecated import refuse
from aura_build.export import complete_export_cli
from aura_build.harness import default_root
from aura_build.kernel import (
    clean_kernel_text,
    emit_kernel_io,
    kernel_exit_code,
    prefer_aura_kernel,
    try_invoke_aura,
)
from aura_build.l2_weights import host_cli as l2_host_cli
from aura_build.memory import host_cli as memory_host_cli
from aura_build.prove_incr import cli_refuse_prove, doctor_snapshot, format_doctor_text
from aura_build.runtime import AuraUnavailable

# Re-export for tests/docs that import build_parser from cli
__all__ = ["build_parser", "console_main", "main"]


def _root(args: argparse.Namespace) -> Path:
    hr = getattr(args, "harness_root", None)
    return Path(hr) if hr else default_root()


def _b(v: object) -> str:
    return "1" if v else "0"


def _dispatch(
    cmd: str,
    env: dict[str, str],
    *,
    refuse_as: str | None = None,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
    harness_root: Path | None = None,
    timeout_s: float = 120.0,
    print_io: bool = True,
) -> int | None:
    """Prefer Aura; return exit code. None ⇒ host fallback. refuse_as ⇒ refuse int."""
    if refuse_as is not None and not prefer_aura_kernel():
        return refuse(refuse_as, reason="force_python_deprecated")
    try:
        kr = try_invoke_aura(
            cmd, env, aura_bin=aura_bin, aura_ref=aura_ref,
            harness_root=harness_root, timeout_s=timeout_s,
        )
    except AuraUnavailable as exc:
        print(f"error: aura kernel: {exc}", file=sys.stderr)
        return 2
    if kr is None:
        return refuse(refuse_as, reason="aura_kernel_unavailable") if refuse_as else None
    if print_io:
        emit_kernel_io(kr)
    return kernel_exit_code(kr)


def _invoke_kr(cmd: str, env: dict[str, str], *, refuse_as: str, harness_root: Path | None = None):
    """KernelResult or refuse exit code (int). No auto-print."""
    if not prefer_aura_kernel():
        return refuse(refuse_as, reason="force_python_deprecated")
    try:
        kr = try_invoke_aura(cmd, env, harness_root=harness_root)
    except AuraUnavailable as exc:
        print(f"error: aura kernel: {exc}", file=sys.stderr)
        return 2
    return kr if kr is not None else refuse(refuse_as, reason="aura_kernel_unavailable")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers: dict[str, Callable[[argparse.Namespace], int]] = {
        "run": _cmd_run,
        "harness-mutate": _cmd_harness_mutate,
        "memory": _cmd_memory,
        "harness-show": _cmd_harness_show,
        "export": _cmd_export,
        "tui": _cmd_tui,
        "acp": _cmd_acp,
        "l2": _cmd_l2,
        "prove-incr": _cmd_prove_incr,
        "doctor": _cmd_doctor,
    }
    fn = handlers.get(args.cmd)
    return fn(args) if fn else 2


def _cmd_run(args: argparse.Namespace) -> int:
    env = {
        "AURA_BUILD_PROMPT": args.prompt,
        "AURA_BUILD_MODE": args.mode,
        "AURA_BUILD_REQUESTED_MODE": args.mode,
        "AURA_BUILD_WORLDLINES": str(args.worldlines),
        "AURA_BUILD_OUT": str(args.out or Path("trajectories/episodes.jsonl")),
        "AURA_BUILD_ATTACH_PROVE": _b(args.attach_prove),
        "AURA_BUILD_KEEP_WORKSPACE": _b(args.keep_workspace),
        "AURA_BUILD_NO_LIVE_BUILD": _b(args.no_live_build),
        "AURA_BUILD_JSON": _b(args.json),
    }
    for attr, key in (
        ("seed", "AURA_BUILD_SEED"),
        ("profile", "AURA_BUILD_PROFILE"),
        ("workspace", "AURA_BUILD_WORKSPACE"),
        ("l2_weights_id", "AURA_BUILD_L2"),
        ("memory_profile", "AURA_BUILD_MEMORY_PROFILE"),
        ("aura_ref", "AURA_BUILD_AURA_REF"),
    ):
        val = getattr(args, attr, None)
        if val is not None and val != "":
            env[key] = str(val)
    code = _dispatch(
        "run", env, refuse_as="run",
        aura_bin=args.aura_bin, aura_ref=args.aura_ref, harness_root=_root(args),
    )
    return code if code is not None else 2


def _cmd_harness_mutate(args: argparse.Namespace) -> int:
    try:
        patches = coerce_harness_patches(parse_kv_list(args.sets))
        fw = {k: float(v) for k, v in parse_kv_list(args.fitness_weights).items()}
    except SystemExit:
        raise
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not patches and not fw:
        print(
            "error: provide at least one --set KEY=VAL or --fitness-weight KEY=VAL",
            file=sys.stderr,
        )
        return 2
    env = {
        "AURA_BUILD_PROMPT": args.prompt,
        "AURA_BUILD_OUT": str(args.out or Path("trajectories/episodes.jsonl")),
        "AURA_BUILD_HARNESS_PATCHES": json.dumps(patches or {}),
        "AURA_BUILD_FITNESS_PATCHES": json.dumps(fw or {}),
        "AURA_BUILD_AUTOPROMOTE_FLAG": "1" if args.autopropote else "",
        "AURA_BUILD_JSON": _b(args.json),
    }
    if args.seed is not None:
        env["AURA_BUILD_SEED"] = str(args.seed)
    if args.profile:
        env["AURA_BUILD_PROFILE"] = args.profile
    code = _dispatch(
        "harness-mutate", env, refuse_as="harness-mutate",
        aura_bin=args.aura_bin, aura_ref=args.aura_ref, harness_root=_root(args),
    )
    return code if code is not None else 2


def _cmd_memory(args: argparse.Namespace) -> int:
    root = _root(args)
    env = {
        "AURA_BUILD_MEM_OP": args.mem_cmd,
        "AURA_BUILD_MEM_PROFILE": getattr(args, "profile", "default") or "default",
        "AURA_BUILD_MEM_KEY": getattr(args, "key", "") or "",
        "AURA_BUILD_MEM_VALUE": getattr(args, "value", "") or "",
    }
    code = _dispatch("memory", env, harness_root=root)
    if code is not None:
        return code
    return memory_host_cli(
        args.mem_cmd, root=root,
        profile=getattr(args, "profile", "default") or "default",
        key=getattr(args, "key", "") or "",
        value=getattr(args, "value", "") or "",
        json_value=bool(getattr(args, "json_value", False)),
    )


def _cmd_harness_show(args: argparse.Namespace) -> int:
    code = _dispatch(
        "harness-show", {"AURA_BUILD_JSON": _b(args.json)},
        refuse_as="harness-show", harness_root=_root(args),
    )
    return code if code is not None else 2


def _cmd_export(args: argparse.Namespace) -> int:
    include_raw = bool(args.include_raw or args.no_redact)
    cwd = Path.cwd()
    out_json = Path(args.out)
    if not out_json.is_absolute():
        out_json = cwd / out_json
    inputs = [
        str(p if (p := Path(raw)).is_absolute() else cwd / p) for raw in (args.inputs or [])
    ]
    env = {
        "AURA_BUILD_EXPORT_CWD": str(cwd),
        "AURA_BUILD_EXPORT_INPUTS": "\n".join(inputs),
        "AURA_BUILD_EXPORT_OUT": str(out_json),
        "AURA_BUILD_EXPORT_INCLUDE_RAW": _b(include_raw),
        "AURA_BUILD_EXPORT_STRICT": _b(args.strict),
        "AURA_BUILD_EXPORT_WANT_PARQUET": "0" if args.no_parquet else "1",
    }
    got = _invoke_kr("export", env, refuse_as="export", harness_root=default_root())
    if isinstance(got, int):
        return got
    meta = (got.response or {}).get("result") or {}
    if got.exit_code not in (0, None) and not meta.get("ok", True):
        if not args.json:
            cleaned = clean_kernel_text(got.stdout)
            if cleaned:
                print(cleaned)
        return got.exit_code if got.exit_code is not None else 2
    return complete_export_cli(
        out_json=out_json, cwd=cwd, include_raw=include_raw,
        no_parquet=args.no_parquet, parquet_arg=args.parquet, as_json=args.json,
        result_meta=meta, print_kernel_stdout=clean_kernel_text(got.stdout) or None,
    )


def _cmd_tui(args: argparse.Namespace) -> int:
    got = _invoke_kr(
        "tui", {"AURA_BUILD_TUI_JSON": _b(args.json)},
        refuse_as="tui", harness_root=_root(args),
    )
    if isinstance(got, int):
        return got
    if args.json:
        st = dict((got.response or {}).get("status") or {})
        st.setdefault("kernel", "aura")
        print(json.dumps(st, indent=2, sort_keys=True))
    else:
        cleaned = clean_kernel_text(got.stdout)
        if cleaned:
            print(cleaned)
    return kernel_exit_code(got)


_ACP_JSON_KEY = {
    "hooks": "hooks", "status": "status", "start": "status",
    "worldlines": "worldlines", "discard": "result", "promote": "ref",
}


def _cmd_acp(args: argparse.Namespace) -> int:
    op = args.acp_cmd
    if op == "export":
        return _cmd_export(argparse.Namespace(
            inputs=[], out=args.out, parquet=None, no_parquet=args.no_parquet,
            include_raw=args.include_raw, no_redact=False, strict=False, json=args.json,
        ))
    env = {
        "AURA_BUILD_ACP_OP": op,
        "AURA_BUILD_ACP_JSON": _b(getattr(args, "json", False)),
        "AURA_BUILD_ACP_PROMPT": getattr(args, "prompt", "") or "",
        "AURA_BUILD_ACP_WORKSPACE": str(getattr(args, "workspace", "") or ""),
        "AURA_BUILD_ACP_TRAJ": str(getattr(args, "traj", "") or ""),
        "AURA_BUILD_ACP_REF": getattr(args, "ref", "") or "",
        "AURA_BUILD_ACP_REASON": getattr(args, "reason", "") or "acp_discard",
        "AURA_BUILD_ACP_L2_ID": getattr(args, "id", "") or "",
        "AURA_BUILD_ACP_L2_NOTES": getattr(args, "notes", "") or "",
    }
    got = _invoke_kr("acp", env, refuse_as=f"acp {op}", harness_root=_root(args))
    if isinstance(got, int):
        return got
    if getattr(args, "json", False):
        payload = got.response or {}
        key = _ACP_JSON_KEY.get(op)
        body = payload.get(key) if key else payload
        if key in ("discard", "promote") and not body:
            body = payload
        if body is None:
            body = [] if key == "worldlines" else ({} if key else payload)
        print(json.dumps(body, indent=2, sort_keys=True))
    else:
        cleaned = clean_kernel_text(got.stdout)
        if cleaned:
            print(cleaned)
    return kernel_exit_code(got)


def _cmd_l2(args: argparse.Namespace) -> int:
    root = _root(args)
    if args.l2_cmd == "promote" and getattr(args, "from_export", None) is not None:
        return l2_host_cli(
            "promote", root=root, weights_id=args.id, notes=args.notes,
            from_export=args.from_export, overwrite=args.overwrite, as_json=args.json,
        )
    env = {
        "AURA_BUILD_L2_OP": args.l2_cmd,
        "AURA_BUILD_L2_ID": getattr(args, "id", "") or "",
        "AURA_BUILD_L2_NOTES": getattr(args, "notes", "") or "",
        "AURA_BUILD_JSON": _b(args.json),
    }
    if args.l2_cmd == "promote":
        env["AURA_BUILD_L2_OVERWRITE"] = _b(args.overwrite)
    code = _dispatch("l2", env, harness_root=root)
    if code is not None:
        return code
    return l2_host_cli(
        args.l2_cmd, root=root, weights_id=getattr(args, "id", "") or "",
        notes=getattr(args, "notes", "") or "", from_export=None,
        overwrite=bool(getattr(args, "overwrite", False)), as_json=args.json,
    )


def _cmd_prove_incr(args: argparse.Namespace) -> int:
    if args.cycles < 1 or args.worldlines < 1:
        print("error: --cycles and --worldlines must be >= 1", file=sys.stderr)
        return 2
    root = _root(args)
    env = {
        "AURA_BUILD_CYCLES": str(args.cycles),
        "AURA_BUILD_WORLDLINES": str(args.worldlines),
        "AURA_BUILD_JSON": _b(args.json),
        "AURA_BUILD_NO_FIBER_PROBE": _b(args.no_fiber_probe),
    }
    if args.out:
        env["AURA_BUILD_PROVE_OUT"] = str(args.out)
    code = _dispatch(
        "prove-incr", env, aura_bin=args.aura_bin, aura_ref=args.aura_ref,
        harness_root=root,
        timeout_s=max(60.0, float(args.timeout) * max(1, args.cycles)),
    )
    if code is not None:
        return code
    return cli_refuse_prove(
        aura_bin=args.aura_bin, aura_ref=args.aura_ref, out=args.out, root=root,
        cycles=args.cycles, worldlines=args.worldlines, as_json=args.json,
    )


def _cmd_doctor(args: argparse.Namespace) -> int:
    root = _root(args)
    if not args.skip_probe:
        code = _dispatch(
            "doctor", {"AURA_BUILD_JSON": _b(args.json)},
            aura_bin=args.aura_bin, aura_ref=args.aura_ref, harness_root=root,
        )
        if code is not None:
            return code
    snap = doctor_snapshot(
        root=args.harness_root, aura_bin=args.aura_bin, aura_ref=args.aura_ref,
        run_probe=not args.skip_probe,
    )
    print(json.dumps(snap, indent=2, sort_keys=True) if args.json else format_doctor_text(snap))
    return 0


def console_main() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    console_main()
