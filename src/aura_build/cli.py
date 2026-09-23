"""Headless CLI — thin argparse → AURA_BUILD_* → Aura kernel.

Product orch lives in aura/*.aura. Host: dispatch, refuse, Parquet, JSON I/O edges.
"""

from __future__ import annotations

import argparse
import json
import os
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
from aura_build.self_evolve_host import git_commit_and_maybe_push, run_host_verify
from aura_build.kernel import repo_root as _kernel_repo_root

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
        "self-evolve": _cmd_self_evolve,
        "llm": _cmd_llm,
        "llm-dogfood": _cmd_llm_dogfood,
        "session": _cmd_session,
        "pursue": _cmd_pursue,
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



def _cmd_self_evolve(args: argparse.Namespace) -> int:
    """Aura self-evolve → host verify → optional commit/push."""
    root = _root(args)
    try:
        raw_sets = getattr(args, "sets", []) or []
        raw_fw = getattr(args, "fitness_weights", []) or []
        patches = coerce_harness_patches(parse_kv_list(raw_sets)) if raw_sets else {}
        fw = {k: float(v) for k, v in parse_kv_list(raw_fw).items()} if raw_fw else {}
    except SystemExit:
        raise
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    repo = _kernel_repo_root()
    env = {
        "AURA_BUILD_PROMPT": args.prompt,
        "AURA_BUILD_WORLDLINES": str(args.worldlines),
        "AURA_BUILD_OUT": str(args.out or Path("trajectories/self_evolve.jsonl")),
        "AURA_BUILD_REPO_ROOT": str(repo),
        "AURA_BUILD_HARNESS_PATCHES": json.dumps(patches or {}),
        "AURA_BUILD_FITNESS_PATCHES": json.dumps(fw or {}),
        "AURA_BUILD_JSON": _b(args.json),
    }
    if args.seed is not None:
        env["AURA_BUILD_SEED"] = str(args.seed)

    got = _invoke_kr(
        "self-evolve",
        env,
        refuse_as="self-evolve",
        harness_root=root,
    )
    if isinstance(got, int):
        return got

    emit_kernel_io(got)
    resp = dict(got.response or {})
    if not resp.get("ok", False):
        reason = resp.get("reason") or "self_evolve_failed"
        print(f"self-evolve: fail reason={reason} (no commit/push)", file=sys.stderr)
        code = kernel_exit_code(got)
        return code if code != 0 else 1

    verify = run_host_verify(
        repo,
        getattr(args, "verify", "smoke") or "smoke",
        aura_bin=getattr(args, "aura_bin", None),
        harness_root=root,
    )
    if not verify.get("ok"):
        print(
            f"self-evolve: verify failed mode={verify.get('mode')} "
            f"reason={verify.get('reason')} (no commit/push)",
            file=sys.stderr,
        )
        if verify.get("stdout"):
            print(str(verify["stdout"])[-1000:], file=sys.stderr)
        if verify.get("stderr"):
            print(str(verify["stderr"])[-1000:], file=sys.stderr)
        return int(verify.get("exit_code") or 1)

    honesty = resp.get("honesty") or {}
    print(
        "self-evolve host_verify=ok"
        f" incr_proven={bool(honesty.get('incr_proven', False))}"
        f" fiber_live={bool(honesty.get('fiber_live', False))}"
        f" kernel=aura"
        f" traj={resp.get('traj_id', '')}"
        f" mid={resp.get('harness_mid', '')}"
    )

    if getattr(args, "no_commit", False):
        print("self-evolve: --no-commit set; skip git")
        if args.json:
            print(
                json.dumps(
                    {"response": resp, "verify": verify, "git": {"skipped": True}},
                    indent=2,
                    sort_keys=True,
                )
            )
        return 0

    paths = [str(p) for p in (resp.get("materialized") or [])]
    for extra in (
        "aura/self_evolve_stamp.aura",
        "aura/self_evolve.aura",
        "aura/main.aura",
        "src/aura_build/cli.py",
        "src/aura_build/cli_parser.py",
        "src/aura_build/self_evolve_host.py",
        "tests/test_self_evolve.py",
        "docs/iteration-plan.md",
        "README.md",
    ):
        if (repo / extra).exists() and extra not in paths:
            paths.append(extra)

    msg = resp.get("commit_message") or (
        f"self-evolve: traj={resp.get('traj_id', '?')} mid={resp.get('harness_mid', '?')} "
        "kernel=aura incr_proven=false fiber_live=false"
    )
    git_res = git_commit_and_maybe_push(
        repo,
        message=msg,
        paths=paths,
        no_push=bool(getattr(args, "no_push", False)),
    )
    print(
        f"self-evolve git reason={git_res.get('reason')} tip={git_res.get('tip', '')} "
        f"pushed={git_res.get('pushed', False)}"
    )
    if args.json:
        print(
            json.dumps(
                {"response": resp, "verify": verify, "git": git_res},
                indent=2,
                sort_keys=True,
            )
        )
    return 0 if git_res.get("ok", False) else 1




def _cmd_llm(args: argparse.Namespace) -> int:
    """Thin MiniMax chat completions (host HTTP; CN endpoint locked)."""
    from aura_build.minimax import chat_completions, load_minimax_config, redact_secrets

    try:
        cfg = load_minimax_config(env_file=getattr(args, "env_file", None))
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: minimax config: {exc}", file=sys.stderr)
        return 2
    thinking_disabled = (getattr(args, "thinking", "disabled") or "disabled") == "disabled"
    result = chat_completions(
        [
            {"role": "system", "content": args.system},
            {"role": "user", "content": args.prompt},
        ],
        config=cfg,
        temperature=float(args.temperature),
        max_tokens=int(args.max_tokens),
        thinking_disabled=thinking_disabled,
    )
    if args.json:
        safe = {
            "ok": result.get("ok"),
            "model": result.get("model"),
            "provider": result.get("provider"),
            "content": result.get("content"),
            "error": redact_secrets(result.get("error") or "", cfg.api_key),
            "llm": cfg.public_dict(),
        }
        print(json.dumps(safe, indent=2, sort_keys=True))
    else:
        if not result.get("ok"):
            print(
                f"error: llm failed model={result.get('model')} "
                f"err={redact_secrets(result.get('error') or '', cfg.api_key)}",
                file=sys.stderr,
            )
            return 1
        print(result.get("content") or "")
    return 0 if result.get("ok") else 1



def _cmd_session(args: argparse.Namespace) -> int:
    """Long-lived Aura --serve attach + optional in-session dogfood."""
    from aura_build.serve_session import (
        run_session_dogfood,
        session_status,
        start_session,
        stop_session,
    )

    op = getattr(args, "session_cmd", None) or "status"
    hroot = _root(args)
    aura_bin = getattr(args, "aura_bin", None)
    want_json = bool(getattr(args, "json", False))

    if op == "start":
        try:
            sess = start_session(
                aura_bin=aura_bin,
                harness_root=hroot,
                force=bool(getattr(args, "force", False)),
            )
        except RuntimeError as exc:
            print(f"session start failed: {exc}", file=sys.stderr)
            return 2
        st = session_status(harness_root=hroot, aura_bin=aura_bin)
        payload = {
            "ok": True,
            "cmd": "session.start",
            "pid": sess.pid,
            "session_model": "serve",
            "serve_attach_ok": True,
            "serve_mode": st.get("serve_mode"),
            "serve_cross_session_shared_ast": st.get("serve_cross_session_shared_ast"),
            "serve_same_session_mutate_ok": st.get("serve_same_session_mutate_ok"),
            "aura_bin": sess.aura_bin,
            "marker": str(hroot / "serve-session.json"),
        }
        if want_json:
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        else:
            print(
                f"session start ok pid={sess.pid} session_model=serve "
                f"serve_mode={st.get('serve_mode')} "
                f"serve_attach_ok=true "
                f"shared_ast={st.get('serve_cross_session_shared_ast')} "
                f"same_session_mutate={st.get('serve_same_session_mutate_ok')} "
                f"marker={hroot / 'serve-session.json'}"
            )
        return 0

    if op == "status":
        st = session_status(harness_root=hroot, aura_bin=aura_bin)
        payload = {"ok": True, "cmd": "session.status", **st}
        if want_json:
            print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        else:
            print(
                f"session status serve_attach_ok={st.get('serve_attach_ok')} "
                f"eval_available={st.get('eval_available')} "
                f"session_model={st.get('session_model')} "
                f"serve_mode={st.get('serve_mode')} "
                f"pid={st.get('pid')} "
                f"serve_cross_session_shared_ast={st.get('serve_cross_session_shared_ast')} "
                f"same_session_mutate={st.get('serve_same_session_mutate_ok')}"
            )
        return 0 if st.get("serve_attach_ok") or st.get("marker") is None else 0

    if op == "stop":
        res = stop_session(harness_root=hroot)
        payload = {"ok": True, "cmd": "session.stop", **res}
        if want_json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"session stop stopped={res.get('stopped')} serve_attach_ok=false")
        return 0

    if op == "dogfood":
        try:
            summary = run_session_dogfood(
                rounds=int(getattr(args, "rounds", 3) or 3),
                aura_bin=aura_bin,
                harness_root=hroot,
                out=getattr(args, "out", None),
                compare_cold=bool(getattr(args, "compare_cold", True)),
            )
        except RuntimeError as exc:
            print(f"session dogfood failed: {exc}", file=sys.stderr)
            return 2
        timing = summary.get("timing") or {}
        if want_json:
            print(json.dumps(summary, indent=2, sort_keys=True, default=str))
        else:
            print(
                f"session dogfood ok traj={summary.get('traj_id')} "
                f"session_model={summary.get('session_model')} "
                f"serve_mode={summary.get('serve_mode')} "
                f"path_kind={timing.get('path_kind')} "
                f"session_ms_mean={timing.get('session_ms_mean')} "
                f"cold_ms_mean={timing.get('cold_ms_mean')} "
                f"cold_spawns={timing.get('cold_spawns')} "
                f"cold_compare_spawns={timing.get('cold_compare_spawns')} "
                f"session_evals={timing.get('session_evals')} "
                f"shared_ast={summary.get('serve_cross_session_shared_ast')} "
                f"path={summary.get('path')}"
            )
        return 0 if summary.get("ok") else 1

    print(f"session: unknown op {op}", file=sys.stderr)
    return 2


def _cmd_llm_dogfood(args: argparse.Namespace) -> int:
    """Closed-loop MiniMax codegen → Aura verify → repair (worldlines)."""
    from aura_build.llm_dogfood import run_closed_loop
    from aura_build.minimax import load_minimax_config

    try:
        cfg = load_minimax_config(env_file=getattr(args, "env_file", None))
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"error: minimax config: {exc}", file=sys.stderr)
        return 2
    # Optimal loop: prefer long-lived serve verify unless --no-prefer-session
    prefer = getattr(args, "prefer_session", True)
    if prefer:
        os.environ["AURA_BUILD_SESSION"] = os.environ.get("AURA_BUILD_SESSION") or "1"
    else:
        os.environ["AURA_BUILD_SESSION"] = "cold"
    # Ensure session started when preferred so verify hits serve path
    if prefer:
        try:
            from aura_build.serve_session import ensure_eval_session, start_session
            h = _root(args)
            sess = ensure_eval_session(
                aura_bin=getattr(args, "aura_bin", None), harness_root=h
            )
            if sess is None:
                start_session(
                    aura_bin=getattr(args, "aura_bin", None), harness_root=h
                )
        except Exception as exc:
            print(f"llm-dogfood: session attach skipped ({exc}); cold verify", file=sys.stderr)
    summary = run_closed_loop(
        task=getattr(args, "task", "fib") or "fib",
        project=getattr(args, "project", None),
        max_rounds=int(getattr(args, "max_rounds", 8) or 8),
        worldlines=int(getattr(args, "worldlines", 3) or 3),
        out=getattr(args, "out", None),
        workspace=getattr(args, "workspace", None),
        harness_root=_root(args),
        aura_bin=getattr(args, "aura_bin", None),
        keep_workspace=bool(getattr(args, "keep_workspace", True)),
        config=cfg,
        prefer_session=prefer,
    )
    hon = summary.get("honesty") or {}
    print(
        "llm_dogfood"
        f" ok={summary.get('ok')}"
        f" success={summary.get('success')}"
        f" task={summary.get('task')}"
        f" project={summary.get('project')}"
        f" expect={summary.get('expect')}"
        f" rounds={summary.get('rounds')}"
        f" traj={summary.get('traj_id')}"
        f" program={summary.get('final_program')}"
        f" session_model={hon.get('session_model')}"
        f" serve_mode={hon.get('serve_mode')}"
        f" shared_ast={hon.get('serve_cross_session_shared_ast')}"
        f" via_prefer_session={hon.get('via_prefer_session')}"
        f" fiber_live={hon.get('fiber_live')}"
        f" incr_proven={hon.get('incr_proven')}"
        f" kernel=aura"
        f" model={summary.get('llm', {}).get('model')}"
        f" reason={summary.get('reason')}"
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("ok") else 1





def _cmd_pursue(args: argparse.Namespace) -> int:
    """Continuous goal loop — prefer in-session mutate:rebind; else Aura kernel.

    MiniMax never controls. Soft Ready --serve-async may refuse (#3098); session
    path still uses Soft --serve same-session mutate when measured.
    """
    root = _root(args)
    min_fit = args.min_fitness
    predicate = args.predicate
    if min_fit is not None and predicate:
        print("error: use either --min-fitness or --predicate, not both", file=sys.stderr)
        return 2
    if min_fit is not None:
        predicate = f"fitness_ge:{min_fit}"
        min_fit_s = str(min_fit)
        min_fit_f = float(min_fit)
    elif predicate:
        min_fit_s = ""
        min_fit_f = 0.8
        if predicate.startswith("fitness_ge:"):
            min_fit_s = predicate.split(":", 1)[1]
            try:
                min_fit_f = float(min_fit_s)
            except ValueError:
                min_fit_f = 0.8
    else:
        predicate = "fitness_ge:0.8"
        min_fit_s = "0.8"
        min_fit_f = 0.8

    llm_assist = "off"
    llm_hint = ""
    if getattr(args, "with_llm", False):
        try:
            from aura_build.minimax import chat_completions, load_minimax_config, redact_secrets

            cfg = load_minimax_config(env_file=getattr(args, "env_file", None))
            hint_prompt = (
                "In one short paragraph, refine this coding/optimization goal into a concrete "
                "success-oriented hint. Do not take control of any loop; hint only.\n\n"
                f"Goal: {args.goal}"
            )
            result = chat_completions(
                [
                    {"role": "system", "content": "You assist aura-build pursue with brief hints only."},
                    {"role": "user", "content": hint_prompt},
                ],
                config=cfg,
                temperature=0.2,
                max_tokens=256,
                thinking_disabled=True,
            )
            if result.get("ok") and (result.get("content") or "").strip():
                llm_hint = (result.get("content") or "").strip()[:800]
                llm_assist = "hint"
            else:
                err = redact_secrets(result.get("error") or "llm_failed", cfg.api_key)
                print(f"pursue: --with-llm unavailable ({err}); continuing without hint", file=sys.stderr)
                llm_assist = "unavailable"
        except Exception as exc:  # noqa: BLE001 — honest degrade
            print(f"pursue: --with-llm unavailable ({exc}); continuing without hint", file=sys.stderr)
            llm_assist = "unavailable"

    force_kernel = bool(
        getattr(args, "force_kernel", False)
        or getattr(args, "no_prefer_session", False)
        or getattr(args, "harness_mutate", False)
        or str(getattr(args, "mode", "aura")) == "simulated"
    )
    prefer_session = bool(getattr(args, "prefer_session", True)) and not force_kernel

    if prefer_session:
        try:
            from aura_build.serve_session import run_pursue_session

            summary = run_pursue_session(
                goal=args.goal,
                min_fitness=min_fit_f,
                max_rounds=int(args.max_rounds),
                worldlines=int(args.worldlines),
                aura_bin=args.aura_bin,
                harness_root=root,
                out=args.out or Path("trajectories/pursue.jsonl"),
                seed=args.seed,
                llm_assist=llm_assist,
                llm_hint=llm_hint,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"pursue: session path failed ({exc}); falling back to kernel", file=sys.stderr)
            summary = {"ok": False, "fallback": "aura_kernel_dispatch", "error": str(exc)}
        if summary.get("ok") and summary.get("path_kind") in ("mutate_rebind", "set_code_eval"):
            line = (
                f"pursue ok={summary.get('ok')} goal_met={summary.get('goal_met')} "
                f"stop_reason={summary.get('stop_reason')} "
                f"best_fitness={summary.get('best_fitness')} "
                f"worldline_backend={summary.get('worldline_backend')} "
                f"session_model={summary.get('session_model')} "
                f"path_kind={summary.get('path_kind')} "
                f"serve_mode={summary.get('serve_mode')} "
                f"cold_spawns={summary.get('cold_spawns')} "
                f"soft_ready={summary.get('serve_async_soft_ready_ok')} "
                f"fail_bits={summary.get('serve_async_soft_ready_fail_bits')} "
                f"kernel=aura"
            )
            print(line)
            if args.json:
                print(json.dumps(summary, indent=2, sort_keys=True))
            return 0 if summary.get("ok") else 1
        if summary.get("fallback") == "aura_kernel_dispatch" or not summary.get("ok"):
            print(
                f"pursue: session mutate unavailable "
                f"({summary.get('stop_reason') or summary.get('error')}); "
                f"dispatching Aura kernel",
                file=sys.stderr,
            )

    # Mild L1 patch so harness-mutate canary has something to propose (AUTOPROMOTE off).
    patches = {}
    if getattr(args, "harness_mutate", False):
        patches = {"worldline_count": int(args.worldlines)}

    env = {
        "AURA_BUILD_GOAL": args.goal,
        "AURA_BUILD_PROMPT": args.goal,
        "AURA_BUILD_PREDICATE": predicate or "fitness_ge:0.8",
        "AURA_BUILD_MIN_FITNESS": min_fit_s,
        "AURA_BUILD_MAX_ROUNDS": str(args.max_rounds),
        "AURA_BUILD_WORLDLINES": str(args.worldlines),
        "AURA_BUILD_MODE": args.mode,
        "AURA_BUILD_REQUESTED_MODE": args.mode,
        "AURA_BUILD_OUT": str(args.out or Path("trajectories/pursue.jsonl")),
        "AURA_BUILD_JSON": _b(args.json),
        "AURA_BUILD_LLM_ASSIST": llm_assist,
        "AURA_BUILD_LLM_HINT": llm_hint,
        "AURA_BUILD_PURSUE_HARNESS_MUTATE": _b(getattr(args, "harness_mutate", False)),
        "AURA_BUILD_HARNESS_PATCHES": __import__("json").dumps(patches),
        "AURA_BUILD_FITNESS_PATCHES": "{}",
        "AURA_BUILD_AUTOPROMOTE_FLAG": "",  # never promote from pursue
        "AURA_BUILD_ATTACH_PROVE": "1",
    }
    if args.seed is not None:
        env["AURA_BUILD_SEED"] = str(args.seed)

    timeout = max(180.0, float(args.max_rounds) * 90.0)
    code = _dispatch(
        "pursue",
        env,
        refuse_as="pursue",
        aura_bin=args.aura_bin,
        aura_ref=args.aura_ref,
        harness_root=root,
        timeout_s=timeout,
    )
    return code if code is not None else 2



def console_main() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    console_main()
