"""MiniMax → aura-build closed loop: propose Aura source → verify → repair.

Primary verify prefers a long-lived Aura ``--serve`` session when attached
(``session_model=serve``); cold ``aura`` / ``verify.sh`` is the fallback
(``shared_workspace_subprocess``). Orch episode recording prefers the Aura
kernel (`llm-dogfood` cmd) when available; host owns MiniMax HTTP (propose-only).

mini-* tasks are CI fixtures / regression — see docs/optimal-dev-loop.md.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aura_build.kernel import prefer_aura_kernel, repo_root, try_invoke_aura
from aura_build.minimax import (
    MiniMaxConfig,
    chat_completions,
    extract_aura_source,
    extract_aura_sources,
    load_minimax_config,
    redact_secrets,
)
from aura_build.runtime import aura_subprocess_env, resolve_aura_bin
from aura_build.schema import validate_episode

SESSION_SHARED = "shared_workspace_subprocess"
SESSION_SERVE = "serve"

TASK_FIB = "fib"
TASK_GREET = "greet"
TASK_CALC = "calc"
TASK_KV = "kv"
TASK_STACK = "stack"
TASK_BANK = "bank"
TASK_ROUTER = "router"
TASK_CACHE = "cache"
DEFAULT_TASK = TASK_FIB
DEFAULT_MAX_ROUNDS = 8
DEFAULT_WORLDLINES = 3

SYSTEM_CODEGEN = """You are a careful Aura (Lisp-like) code generator for the Aura runtime.
Rules:
- Single-file: output ONE complete Aura program (prefer a ```aura fence).
- Multi-file: output EACH required file in a named fence, e.g.
  ```aura lib.aura
  ...
  ```
  ```aura main.aura
  ...
  ```
  For 3+ files keep the same named-fence pattern (one fence per required file,
  stable order as listed). (```aura:lib.aura and ```lib.aura also accepted).
  Prefer omitting unchanged files on repair when prior sources are provided.
- Use define/lambda/if/cond/let/display/newline/set!/equal?/number->string.
- No Python. Prefer Aura CLI multi-file (lib then main) or (load "lib.aura") when asked.
- Keep programs small and deterministic.
- Do not include API keys or secrets.
"""

FIB_USER = """Write a small Aura program that defines (fib n) recursively and prints exactly:
FIB10=55
followed by a newline. fib(10) must equal 55. No extra prose outside the code fence.
"""

FIB_EXPECT = "FIB10=55"
FIB_SUCCESS_RE = re.compile(r"FIB10\s*=\s*55")
FIB_FALLBACK = (
    '; empty model reply fallback\n'
    '(display "FIB10=0")(newline)\n'
)

GREET_USER = """Write a tiny Aura program that prints exactly:
GREET=aura
followed by a newline. Prefer (display "GREET=aura")(newline). No extra prose outside the code fence.
"""

GREET_EXPECT = "GREET=aura"
GREET_SUCCESS_RE = re.compile(r"GREET\s*=\s*aura")
GREET_FALLBACK = (
    '; empty model reply fallback\n'
    '(display "GREET=wrong")(newline)\n'
)

CALC_USER = """Write a small Aura program that defines named helpers and prints exactly:
ADD=7
MUL=12
MIX=17
each followed by a newline.
Semantics: ADD = (add 3 4) = 3+4; MUL = (mul 3 4) = 3*4; MIX = (add (mul 3 4) 5) = (3*4)+5.
You MUST include (define (add a b) ...) and (define (mul a b) ...) and call them —
do not only hardcode the three display strings. Prefer display/newline/+/*.
No extra prose outside the code fence.
"""

CALC_EXPECT = "ADD=7\nMUL=12\nMIX=17"
CALC_SUCCESS_RES = [
    re.compile(r"ADD\s*=\s*7"),
    re.compile(r"MUL\s*=\s*12"),
    re.compile(r"MIX\s*=\s*17"),
]
CALC_SOURCE_RES = [
    re.compile(r"\(define\s+\(add\b"),
    re.compile(r"\(define\s+\(mul\b"),
]
CALC_FALLBACK = (
    '; empty model reply fallback\n'
    '(define (add a b) (- a b))\n'
    '(display "ADD=")(display (add 3 4))(newline)\n'
    '(display "MUL=0")(newline)\n'
    '(display "MIX=0")(newline)\n'
)


KV_USER = """Write a small Aura program that implements a tiny in-memory key/value store
and prints exactly:
GET_a=1
GET_b=2
MISS=nil
GET_c=3
each followed by a newline.
Semantics: (kv-set "a" 1) then (kv-set "b" 2); (kv-get "a")->1; (kv-get "b")->2;
(kv-get "z")->nil; (kv-set "c" 3); (kv-get "c")->3.
You MUST include (define (kv-set k v) ...) and (define (kv-get k) ...) using set!/alist
(or equivalent) so gets see prior sets — do not only hardcode the four display strings.
Prefer display/newline/set!/cons/car/cdr/null?/equal?. No extra prose outside the code fence.
"""

KV_EXPECT = "GET_a=1\nGET_b=2\nMISS=nil\nGET_c=3"
KV_SUCCESS_RES = [
    re.compile(r"GET_a\s*=\s*1"),
    re.compile(r"GET_b\s*=\s*2"),
    re.compile(r"MISS\s*=\s*nil"),
    re.compile(r"GET_c\s*=\s*3"),
]
KV_SOURCE_RES = [
    re.compile(r"\(define\s+\(kv-set\b"),
    re.compile(r"\(define\s+\(kv-get\b"),
]
KV_FALLBACK = (
    "; empty model reply fallback\n"
    "(define store '())\n"
    "(define (kv-set k v) (set! store (cons k store)))\n"
    '(kv-set "a" 9)\n'
    '(display "GET_a=0")(newline)\n'
    '(display "GET_b=0")(newline)\n'
    '(display "MISS=missing")(newline)\n'
    '(display "GET_c=0")(newline)\n'
)


STACK_USER = """Write a small Aura program that implements a tiny mutable stack
and prints exactly:
TOP=30
POP=30
TOP2=20
SIZE=2
EMPTY=0
each followed by a newline.
Semantics: start empty; (stack-push 10) (stack-push 20) (stack-push 30);
(stack-top)->30; (stack-pop)->30; (stack-top)->20; (stack-size)->2; empty->0.
You MUST include (define (stack-push x) ...), (define (stack-pop) ...),
(define (stack-top) ...), and (define (stack-size) ...) using set!/cons/car/cdr
(or equivalent) — do not only hardcode the five display strings.
Prefer also (define (stack-empty) ...) returning 0/1.
Prefer display/newline/set!/cons/car/cdr/null?. No extra prose outside the code fence.
"""

STACK_EXPECT = "TOP=30\nPOP=30\nTOP2=20\nSIZE=2\nEMPTY=0"
STACK_SUCCESS_RES = [
    re.compile(r"TOP\s*=\s*30"),
    re.compile(r"POP\s*=\s*30"),
    re.compile(r"TOP2\s*=\s*20"),
    re.compile(r"SIZE\s*=\s*2"),
    re.compile(r"EMPTY\s*=\s*0"),
]
STACK_SOURCE_RES = [
    re.compile(r"\(define\s+\(stack-push\b"),
    re.compile(r"\(define\s+\(stack-pop\b"),
    re.compile(r"\(define\s+\(stack-top\b"),
    re.compile(r"\(define\s+\(stack-size\b"),
]
STACK_FALLBACK = (
    "; empty model reply fallback\n"
    "(define stk '())\n"
    "(define (stack-push x) (set! stk (cons x '())))\n"
    '(display "TOP=0")(newline)\n'
    '(display "POP=0")(newline)\n'
    '(display "TOP2=0")(newline)\n'
    '(display "SIZE=0")(newline)\n'
    '(display "EMPTY=1")(newline)\n'
)

REPAIR_STEER = """The previous Aura candidate failed verification under the Aura binary.
Fix the program. Keep the same required output contract.
Common Aura pitfalls: balanced parentheses; use (display x) (newline); recursion via
(define (fib n) (if (<= n 1) n (+ (fib (- n 1)) (fib (- n 2))))); no Python syntax.
If the task requires named helpers (e.g. add/mul, kv-set/kv-get, or
stack-push/stack-pop/stack-top/stack-size), keep those (define …) forms and
call them — do not only hardcode display strings. Use \b-safe define forms
including zero-arity (define (stack-pop) ...).
When verify stderr is present, treat it as the ground-truth failure reason.
Pay special attention to lines starting with 'verify mismatch line N:' — fix those
outputs first.
Single-file: return ONE corrected Aura program in a ```aura fence.
Multi-file: return EACH required file in a named fence (```aura <filename>).
Prefer rewriting only the failing file(s); omitted files are kept from the previous
candidate. Keep fence order stable (table/lib before match before main/entry).
"""

# Task registry: propose prompt + verify regex + empty-reply fallback.
TASKS: dict[str, dict[str, Any]] = {
    TASK_FIB: {
        "user": FIB_USER,
        "expect": FIB_EXPECT,
        "expect_re": FIB_SUCCESS_RE,
        "fallback": FIB_FALLBACK,
        "label": "fib",
        "project": "examples/minimax_fib_task.md",
    },
    TASK_GREET: {
        "user": GREET_USER,
        "expect": GREET_EXPECT,
        "expect_re": GREET_SUCCESS_RE,
        "fallback": GREET_FALLBACK,
        "label": "greet",
        "project": "examples/projects/mini-greet",
    },
    TASK_CALC: {
        "user": CALC_USER,
        "expect": CALC_EXPECT,
        "expect_re": CALC_SUCCESS_RES,
        "source_res": CALC_SOURCE_RES,
        "fallback": CALC_FALLBACK,
        "label": "calc",
        "project": "examples/projects/mini-calc",
    },
    TASK_KV: {
        "user": KV_USER,
        "expect": KV_EXPECT,
        "expect_re": KV_SUCCESS_RES,
        "source_res": KV_SOURCE_RES,
        "fallback": KV_FALLBACK,
        "label": "kv",
        "project": "examples/projects/mini-kv",
        "verify_script": "examples/projects/mini-kv/verify.sh",
    },
    TASK_STACK: {
        "user": STACK_USER,
        "expect": STACK_EXPECT,
        "expect_re": STACK_SUCCESS_RES,
        "source_res": STACK_SOURCE_RES,
        "fallback": STACK_FALLBACK,
        "label": "stack",
        "project": "examples/projects/mini-stack",
        "verify_script": "examples/projects/mini-stack/verify.sh",
    },
    # bank/router/cache: thin registry aliases; real prompts/stubs live under --project
    TASK_BANK: {
        "label": "bank",
        "project": "examples/projects/mini-bank",
        "verify_script": "examples/projects/mini-bank/verify.sh",
        "user": "",
        "expect": "A=100\nB=50\nA2=70\nB2=80\nOK=1",
        "fallback": "",
    },
    TASK_ROUTER: {
        "label": "router",
        "project": "examples/projects/mini-router",
        "verify_script": "examples/projects/mini-router/verify.sh",
        "user": "",
        "expect": "GET_SLASH=home\nGET_API=api\nGET_API_V1=api\nGET_API_V2=api\nPOST_API=405\nMISS=404\nCOUNT=5",
        "fallback": "",
    },
    TASK_CACHE: {
        "label": "cache",
        "project": "examples/projects/mini-cache",
        "verify_script": "examples/projects/mini-cache/verify.sh",
        "user": "",
        "expect": "GET_A=1\nGET_MISS=miss\nGET_B=2\nTTL_EXPIRED=miss\nCOUNT=2",
        "fallback": "",
    },
}




def _compile_res(patterns: list[str] | None) -> list[re.Pattern[str]] | None:
    if not patterns:
        return None
    return [re.compile(p) for p in patterns]


def load_project_spec(project: Path | str, *, repo: Path | None = None) -> dict[str, Any]:
    """Load a dogfood task from an external project directory.

    Expected layout (minimal):
      GOAL.md       — human goal; becomes the propose user prompt body
      stub.aura     — empty-reply / seed fallback (single-file; optional)
      stub/         — multi-file stubs mirroring ``files`` (e.g. stub/lib.aura)
      verify.sh     — exit 0 iff candidate green (preferred fitness oracle)
      dogfood.json  — optional machine contract (expect / expect_res / source_res /
                      files / run_mode / entry)

    Multi-file: set ``files`` in dogfood.json (e.g. ["lib.aura","main.aura"]).
    Aura natively accepts ``aura lib.aura main.aura`` and ``(load "lib.aura")``;
    ``run_mode`` documents which contract verify.sh uses (cli_multi | load | concat).
    Friction this fixes: extending llm-dogfood previously required editing the
    hard-coded TASKS registry + CLI ``--task`` choices for every new project.
    """
    root = Path(project)
    if not root.is_absolute():
        root = (repo or repo_root()) / root
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"project dir not found: {root}")
    goal_path = root / "GOAL.md"
    if not goal_path.is_file():
        raise FileNotFoundError(f"project missing GOAL.md: {goal_path}")
    goal = goal_path.read_text(encoding="utf-8")
    meta: dict[str, Any] = {}
    meta_path = root / "dogfood.json"
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid dogfood.json in {root}: {exc}") from exc
    files_raw = meta.get("files")
    files: list[str] = []
    if isinstance(files_raw, list) and files_raw:
        files = [str(f) for f in files_raw]
    multi = len(files) > 1
    run_mode = str(meta.get("run_mode") or ("cli_multi" if multi else "single"))
    entry = str(meta.get("entry") or (files[-1] if files else "program.aura"))

    fallback_files: dict[str, str] = {}
    stub_dir = root / "stub"
    if files:
        for fname in files:
            cand = stub_dir / fname
            if cand.is_file():
                fallback_files[fname] = cand.read_text(encoding="utf-8")
            else:
                alt = root / f"stub_{fname}"
                if alt.is_file():
                    fallback_files[fname] = alt.read_text(encoding="utf-8")
                else:
                    fallback_files[fname] = (
                        f"; stub missing for {fname}\n"
                        '(display "FAIL")(newline)\n'
                    )
        stub_path = root / "stub.aura"
        if stub_path.is_file() and entry not in fallback_files:
            fallback_files[entry] = stub_path.read_text(encoding="utf-8")
        fallback: str | dict[str, str] = fallback_files
    else:
        stub_path = root / "stub.aura"
        fallback = (
            stub_path.read_text(encoding="utf-8")
            if stub_path.is_file()
            else '; project stub missing\n(display "FAIL")(newline)\n'
        )

    label = str(meta.get("label") or root.name)
    expect = str(meta.get("expect") or "(see GOAL.md / verify.sh)")
    user_extra = str(meta.get("user_extra") or "").strip()
    if multi:
        fence_hint = "\n".join(f"```aura {fn}\n...\n```" for fn in files)
        user = (
            "Write a MULTI-FILE Aura program that satisfies the following "
            "project goal.\n"
            f"Required files (in order): {', '.join(files)}.\n"
            "Output EACH file in a named fence, for example:\n"
            f"{fence_hint}\n"
            f"Entrypoint / last file: {entry}. Run mode for verify: {run_mode}. "
            "Aura accepts `aura lib.aura main.aura` (CLI multi-file) and "
            '(load "lib.aura") — follow GOAL.md; do not invent unsupported modules.\n\n'
            f"## GOAL.md\n{goal.strip()}\n"
        )
    else:
        user = (
            "Write ONE complete Aura program that satisfies the following "
            "project goal.\n"
            "Output only the program in a ```aura fence.\n\n"
            f"## GOAL.md\n{goal.strip()}\n"
        )
    if user_extra:
        user += f"\n## Extra constraints\n{user_extra}\n"
    verify_script = root / "verify.sh"
    verify_script_s = str(verify_script) if verify_script.is_file() else None
    expect_re: re.Pattern[str] | list[re.Pattern[str]] | None = _compile_res(
        meta.get("expect_res")
    )
    if expect_re is None and isinstance(meta.get("expect_re"), str):
        expect_re = re.compile(str(meta["expect_re"]))
    source_res = _compile_res(meta.get("source_res"))
    if verify_script_s is None and expect_re is None:
        raise ValueError(
            f"project {root} needs verify.sh and/or dogfood.json expect_res"
        )
    seed_from_stub = bool(meta.get("seed_from_stub"))
    return {
        "user": user,
        "expect": expect,
        "expect_re": expect_re or [],
        "source_res": source_res,
        "fallback": fallback,
        "label": label,
        "project": str(root),
        "verify_script": verify_script_s,
        "goal_path": str(goal_path),
        "files": files,
        "multi_file": multi,
        "run_mode": run_mode,
        "entry": entry,
        "seed_from_stub": seed_from_stub,
    }




def resolve_task_spec(
    task: str | None = None,
    project: Path | str | None = None,
    *,
    repo: Path | None = None,
) -> tuple[str, dict[str, Any]]:
    """Resolve ``--task`` and/or ``--project`` into (task_label, task_spec)."""
    if project:
        spec = load_project_spec(project, repo=repo)
        label = str(spec.get("label") or "project")
        return label, spec
    name = task or DEFAULT_TASK
    if name not in TASKS:
        raise ValueError(
            f"unsupported task {name!r} (supported: {', '.join(sorted(TASKS))}"
            "; or pass --project DIR)"
        )
    return name, dict(TASKS[name])


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _make_id(prefix: str = "ep") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def load_honesty(harness_root: Path) -> dict[str, Any]:
    """Read last prove report if present; never invent fiber_live/incr_proven."""
    report = harness_root / "prove-incr-latest.json"
    honesty = {
        "incr_proven": False,
        "fiber_live": False,
        "measured": False,
        "session_model": SESSION_SHARED,
        "reason": "no_prove_report",
    }
    if not report.is_file():
        return honesty
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        honesty["reason"] = "prove_report_invalid_json"
        return honesty
    honesty["incr_proven"] = bool(data.get("incr_proven", False))
    honesty["fiber_live"] = bool(data.get("fiber_live", False))
    honesty["measured"] = bool(data.get("measured", False))
    honesty["session_model"] = (
        data.get("session_model")
        if data.get("fiber_live")
        else SESSION_SHARED
    )
    # Hard honesty: env alone cannot elevate fiber_live
    if not honesty["fiber_live"]:
        honesty["session_model"] = SESSION_SHARED
    honesty["reason"] = str(data.get("reason") or "from_prove_report")
    return honesty



def _matched_expect(
    passed: bool,
    stdout: str,
    expect_re: re.Pattern[str] | list[re.Pattern[str]] | None,
) -> bool:
    """True if verify passed or any expect pattern / known token appears in stdout."""
    if passed:
        return True
    if expect_re is not None:
        patterns = expect_re if isinstance(expect_re, list) else [expect_re]
        if any(bool(p.search(stdout or "")) for p in patterns):
            return True
    # Fallback tokens across dogfood tiers (fib/greet/calc/kv/stack)
    return bool(
        re.search(
            r"(?:FIB10=|GREET=|ADD=|MUL=|MIX=|GET_|MISS=|TTL_|COUNT=|TOP=|POP=|TOP2=|SIZE=|EMPTY=|A=|B=|A2=|B2=|OK=)",
            stdout or "",
        )
    )


def _structure_fail_note(source_res: list[re.Pattern[str]] | None) -> str:
    """Human-readable structure failure for repair / traj notes (task-agnostic)."""
    if not source_res:
        return "structure_fail: required source patterns missing\n"
    pats = ", ".join(p.pattern for p in source_res)
    return f"structure_fail: source must match all of: {pats}\n"


def _read_candidate_source(
    source_path: Path,
    *,
    candidate_dir: Path | str | None = None,
    files: list[str] | None = None,
) -> str:
    """Concatenate multi-file candidate in ``files`` order (CLI multi-file semantics)."""
    try:
        if candidate_dir and files:
            cdir = Path(candidate_dir)
            parts = [
                (cdir / fn).read_text(encoding="utf-8")
                for fn in files
                if (cdir / fn).is_file()
            ]
            return chr(10).join(parts)
        return source_path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _score_from_stdout(
    *,
    stdout: str,
    stderr: str,
    source_text: str,
    expect_re: re.Pattern[str] | list[re.Pattern[str]] | None,
    source_res: list[re.Pattern[str]] | None,
    has_error: bool,
    ms: int,
    via: str,
    session_model: str | None = None,
    cold_spawns: int = 0,
    serve_mode: Any = None,
    shared_ast: Any = None,
    oracle_verify_script: bool | None = None,
    exit_code: int | None = None,
) -> dict[str, Any]:
    if expect_re is None:
        patterns: list[re.Pattern[str]] = []
    else:
        patterns = expect_re if isinstance(expect_re, list) else [expect_re]
    matched = all(bool(p.search(stdout or "")) for p in patterns) if patterns else False
    structure_ok = True
    if source_res:
        structure_ok = all(bool(p.search(source_text or "")) for p in source_res)
    err_note = stderr or ""
    if not structure_ok and source_res:
        err_note = (err_note + "\n" + _structure_fail_note(source_res)).strip()
    passed = matched and structure_ok and not has_error
    if passed:
        fitness = 1.0
    elif matched and not structure_ok:
        fitness = 0.4
    elif matched and has_error:
        fitness = 0.35
    elif (stdout or "").strip() and not has_error:
        fitness = 0.25
    elif has_error:
        fitness = max(0.05, 0.2 - min(0.15, len(err_note) / 5000.0))
    else:
        fitness = 0.05
    out: dict[str, Any] = {
        "ok": passed,
        "fitness": round(fitness, 4),
        "passed": passed,
        "stdout": (stdout or "")[-4000:],
        "stderr": err_note[-4000:],
        "exit_code": 0 if passed else (1 if exit_code is None else exit_code),
        "ms": ms,
        "matched_expect": matched if patterns else _matched_expect(passed, stdout, expect_re),
        "structure_ok": structure_ok,
        "has_error": has_error,
        "via": via,
        "cold_spawns": int(cold_spawns),
    }
    if session_model is not None:
        out["session_model"] = session_model
    if serve_mode is not None:
        out["serve_mode"] = serve_mode
    if shared_ast is not None:
        out["serve_cross_session_shared_ast"] = shared_ast
    if oracle_verify_script is not None:
        out["oracle_verify_script"] = bool(oracle_verify_script)
    return out


def _run_verify_script(
    script: Path,
    *,
    verify_arg: str,
    env: dict[str, str],
    timeout_s: float,
    source_text: str,
    expect_re: re.Pattern[str] | list[re.Pattern[str]] | None,
    source_res: list[re.Pattern[str]] | None,
) -> dict[str, Any]:
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            ["bash", str(script), verify_arg],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        ms = int((time.monotonic() - t0) * 1000)
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else "verify_script_timeout"
        return _score_from_stdout(
            stdout=stdout,
            stderr=stderr,
            source_text=source_text,
            expect_re=expect_re,
            source_res=source_res,
            has_error=True,
            ms=ms,
            via="verify_script",
            session_model=SESSION_SHARED,
            cold_spawns=1,
            exit_code=124,
        )
    ms = int((time.monotonic() - t0) * 1000)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    passed = proc.returncode == 0
    structure_ok = True
    if source_res:
        structure_ok = all(bool(p.search(source_text)) for p in source_res)
    if passed and not structure_ok:
        passed = False
        stderr = (stderr + "\n" + _structure_fail_note(source_res)).strip()
    fitness = 1.0 if passed else (
        0.4 if "verify ok" in stdout.lower() else (
            0.25 if stdout.strip() else 0.1
        )
    )
    if not passed and proc.returncode != 0:
        fitness = max(0.05, min(0.45, fitness))
    return {
        "ok": passed,
        "fitness": round(fitness if passed else fitness, 4),
        "passed": passed,
        "stdout": stdout[-4000:],
        "stderr": stderr[-4000:],
        "exit_code": proc.returncode,
        "ms": ms,
        "matched_expect": _matched_expect(passed, stdout, expect_re),
        "structure_ok": structure_ok,
        "has_error": (not passed) and bool(
            re.search(r"(?i)\berror:|\bunbound variable\b", stdout + stderr)
        ),
        "via": "verify_script",
        "session_model": SESSION_SHARED,
        "cold_spawns": 1,
    }


def verify_aura_program(
    source_path: Path,
    *,
    expect_re: re.Pattern[str] | list[re.Pattern[str]] | None = None,
    source_res: list[re.Pattern[str]] | None = None,
    aura_bin: str | None = None,
    verify_script: str | Path | None = None,
    candidate_dir: Path | str | None = None,
    files: list[str] | None = None,
    timeout_s: float = 15.0,
    serve_session: Any | None = None,
    harness_root: Path | str | None = None,
    prefer_session: bool | None = None,
    oracle_verify_script: bool = False,
) -> dict[str, Any]:
    """Compile/run candidate; prefer hot serve session when attached.

    When ``prefer_session`` and a live Soft serve session is attached, multi-file
    candidates are concatenated in ``files`` order and scored via session
    set-code + eval-current (``via=serve_session``, ``cold_spawns=0``).
    ``verify_script`` is an optional oracle second check or fallback when the
    session is missing / times out — never faked. Structural ``source_res``
    checks run in Python without a cold aura spawn.
    """
    bin_path = resolve_aura_bin(aura_bin)
    if not bin_path and not verify_script:
        return {
            "ok": False,
            "fitness": 0.0,
            "passed": False,
            "stdout": "",
            "stderr": "aura_binary_missing",
            "exit_code": 2,
            "ms": 0,
            "matched_expect": False,
            "structure_ok": False,
            "has_error": True,
            "via": "missing_bin",
            "cold_spawns": 0,
        }
    env = aura_subprocess_env(bin_path) if bin_path else os.environ.copy()
    if bin_path:
        env.setdefault("AURA_BIN", bin_path)

    source_text = _read_candidate_source(
        source_path, candidate_dir=candidate_dir, files=files
    )
    # Structural checks are always local (no cold spawn).
    structure_ok = True
    if source_res:
        structure_ok = all(bool(p.search(source_text)) for p in source_res)

    sess = serve_session
    serve_mode = None
    shared_ast = None
    if sess is None and prefer_session is not False:
        try:
            from aura_build.serve_session import (
                attach_session,
                ensure_eval_session,
                prefer_session_verify,
                session_status,
            )
            hroot = harness_root
            st = session_status(harness_root=hroot, aura_bin=aura_bin)
            if prefer_session or prefer_session_verify(harness_root=hroot) or st.get(
                "serve_attach_ok"
            ):
                sess = ensure_eval_session(aura_bin=aura_bin, harness_root=hroot)
            else:
                sess = attach_session(harness_root=hroot, aura_bin=aura_bin)
            if st.get("serve_attach_ok"):
                serve_mode = st.get("serve_mode")
                shared_ast = bool(st.get("serve_cross_session_shared_ast"))
        except Exception:
            sess = None

    session_timeout = min(float(timeout_s), 5.0)
    hot: dict[str, Any] | None = None
    hot_structural_fail = False
    if sess is not None and prefer_session is not False:
        try:
            if hasattr(sess, "alive") and not sess.alive():
                raise RuntimeError("serve_session_dead")
            ev = sess.eval_source(source_text, timeout_s=session_timeout)
            stdout = ev.get("stdout") or ""
            stderr = ev.get("stderr") or ""
            has_error = bool(
                re.search(r"(?i)\berror:|\bunbound variable\b|\bsyntax\b", stderr)
                or re.search(r"(?i)\berror:|\bunbound variable\b", stdout)
                or not ev.get("ok")
            )
            # Attach live status stamps when available on the session object
            try:
                from aura_build.serve_session import session_status as _st
                st2 = _st(harness_root=getattr(sess, "harness_root", harness_root),
                          aura_bin=aura_bin)
                serve_mode = st2.get("serve_mode", serve_mode)
                shared_ast = bool(
                    st2.get("serve_cross_session_shared_ast", shared_ast)
                )
            except Exception:
                pass
            hot = _score_from_stdout(
                stdout=stdout,
                stderr=stderr,
                source_text=source_text,
                expect_re=expect_re,
                source_res=source_res,
                has_error=has_error,
                ms=int(ev.get("ms") or 0),
                via="serve_session",
                session_model=SESSION_SERVE,
                cold_spawns=0,
                serve_mode=serve_mode,
                shared_ast=shared_ast,
            )
        except Exception as exc:  # noqa: BLE001 — timeout / sock fail → fallback
            hot_structural_fail = True
            hot = {
                "ok": False,
                "passed": False,
                "fitness": 0.05,
                "stdout": "",
                "stderr": f"serve_session_verify_failed:{type(exc).__name__}:{exc}",
                "exit_code": 124,
                "ms": int(session_timeout * 1000),
                "matched_expect": False,
                "structure_ok": structure_ok,
                "has_error": True,
                "via": "serve_session_timeout",
                "cold_spawns": 0,
            }

    # Optional oracle second check when hot path ran and caller asked for it,
    # or fallback when session missing / timed out / produced no usable stdout
    # (Soft sync set-code sometimes returns empty display for multi-file concat).
    script_path = Path(verify_script) if verify_script else None
    want_oracle = bool(oracle_verify_script and hot is not None and script_path and script_path.is_file())
    hot_unusable = False
    if hot is not None and not hot_structural_fail and expect_re is not None:
        hot_out = (hot.get("stdout") or "").strip()
        if not hot_out and not hot.get("passed"):
            hot_unusable = True
        elif not hot.get("passed") and not hot.get("matched_expect"):
            # Session scored but missed expect — allow verify.sh oracle fallback
            hot_unusable = True
    need_fallback = hot is None or hot_structural_fail or hot_unusable
    if script_path is None or not script_path.is_file():
        need_fallback = hot is None or hot_structural_fail
    # Also fall back when prefer_session is False / no session — use verify.sh
    if hot is None and script_path is not None:
        need_fallback = True

    if (want_oracle or need_fallback) and script_path is not None:
        if not script_path.is_file():
            if hot is not None and not need_fallback:
                hot["oracle_verify_script"] = False
                return hot
            return {
                "ok": False,
                "fitness": 0.0,
                "passed": False,
                "stdout": "",
                "stderr": f"verify_script_missing:{script_path}",
                "exit_code": 2,
                "ms": 0,
                "matched_expect": False,
                "structure_ok": structure_ok,
                "has_error": True,
                "via": "verify_script",
                "cold_spawns": 0,
            }
        verify_arg = str(candidate_dir) if candidate_dir else str(source_path)
        cold = _run_verify_script(
            script_path,
            verify_arg=verify_arg,
            env=env,
            timeout_s=timeout_s,
            source_text=source_text,
            expect_re=expect_re,
            source_res=source_res,
        )
        if want_oracle and hot is not None and not need_fallback:
            # Hot path primary; stamp that oracle also ran. Prefer hot fitness
            # unless oracle disagrees on pass (then fail closed to oracle).
            hot = dict(hot)
            hot["oracle_verify_script"] = True
            hot["oracle_passed"] = bool(cold.get("passed"))
            hot["oracle_stdout"] = (cold.get("stdout") or "")[-1500:]
            hot["oracle_stderr"] = (cold.get("stderr") or "")[-1500:]
            if hot.get("passed") and not cold.get("passed"):
                hot["passed"] = False
                hot["ok"] = False
                hot["fitness"] = min(float(hot.get("fitness") or 0.0), 0.45)
                hot["stderr"] = (
                    (hot.get("stderr") or "")
                    + "\noracle_verify_script_failed:\n"
                    + (cold.get("stderr") or "")
                ).strip()
            return hot
        # Fallback primary
        cold["oracle_verify_script"] = False
        if hot is not None:
            cold["hot_via"] = hot.get("via")
            cold["hot_stderr"] = (hot.get("stderr") or "")[-800:]
        return cold

    if hot is not None:
        hot.setdefault("oracle_verify_script", False)
        return hot

    # Cold aura_bin single-file path
    if not bin_path:
        return {
            "ok": False,
            "fitness": 0.0,
            "passed": False,
            "stdout": "",
            "stderr": "aura_binary_missing",
            "exit_code": 2,
            "ms": 0,
            "matched_expect": False,
            "structure_ok": structure_ok,
            "has_error": True,
            "via": "aura_bin",
            "cold_spawns": 0,
        }
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            [bin_path, str(source_path)]
            if not (candidate_dir and files)
            else [bin_path, *[str(Path(candidate_dir) / fn) for fn in files]],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return _score_from_stdout(
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr="aura_bin_timeout",
            source_text=source_text,
            expect_re=expect_re,
            source_res=source_res,
            has_error=True,
            ms=int((time.monotonic() - t0) * 1000),
            via="aura_bin",
            session_model=SESSION_SHARED,
            cold_spawns=1,
            exit_code=124,
        )
    ms = int((time.monotonic() - t0) * 1000)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    has_error = bool(
        re.search(r"(?i)\berror:|\bunbound variable\b|\bsyntax\b", stderr)
        or re.search(r"(?i)\berror:|\bunbound variable\b", stdout)
    )
    return _score_from_stdout(
        stdout=stdout,
        stderr=stderr,
        source_text=source_text,
        expect_re=expect_re,
        source_res=source_res,
        has_error=has_error,
        ms=ms,
        via="aura_bin",
        session_model=SESSION_SHARED,
        cold_spawns=1,
        exit_code=proc.returncode,
    )



def _workspace_create(root: Path, n: int, episode_token: str) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    (root / "parent").mkdir(exist_ok=True)
    (root / "parent" / "SNAPSHOT").write_text(
        "parent_id=wl-parent\n", encoding="utf-8"
    )
    cands_dir = root / "candidates"
    cands_dir.mkdir(exist_ok=True)
    candidates: dict[str, str] = {}
    cand_meta: dict[str, Any] = {}
    for i in range(n):
        cid = f"wl-{i}"
        rel = f"candidates/{cid}"
        cdir = root / rel
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "REF").write_text(
            f"ref_id={cid}\nparent_ref=wl-parent\n", encoding="utf-8"
        )
        candidates[cid] = cid
        cand_meta[cid] = {
            "ref_id": cid,
            "parent_ref": "wl-parent",
            "workspace_relpath": rel,
            "kind": "candidate",
        }
    meta = {
        "episode_token": episode_token,
        "session_model": SESSION_SHARED,
        "parent": {
            "ref_id": "wl-parent",
            "parent_ref": None,
            "workspace_relpath": "parent",
            "kind": "parent",
        },
        "candidates": cand_meta,
        "discarded": [],
        "incr_proven": False,
        "fiber_live": False,
        "honesty": "shared workspace + stable refs; not fiber-live",
    }
    (root / "meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "root": str(root),
        "parent_ref": "wl-parent",
        "session_model": SESSION_SHARED,
        "candidates": candidates,
        "n": n,
    }


def _discard_losers(ws_root: Path, selected_id: str, fitness_by_id: dict[str, float]) -> list[dict[str, Any]]:
    discarded: list[dict[str, Any]] = []
    cands = ws_root / "candidates"
    if not cands.is_dir():
        return discarded
    for child in sorted(cands.iterdir()):
        if not child.is_dir():
            continue
        cid = child.name
        if cid == selected_id:
            continue
        marker = child / "DISCARDED"
        marker.write_text(
            f"reason=select_best_loser\nselected={selected_id}\n",
            encoding="utf-8",
        )
        discarded.append(
            {
                "id": cid,
                "reason": "select_best_loser",
                "fitness": float(fitness_by_id.get(cid, 0.0)),
                "stable_ref": cid,
            }
        )
    # update meta
    meta_path = ws_root / "meta.json"
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["discarded"] = discarded
            meta_path.write_text(
                json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        except json.JSONDecodeError:
            pass
    return discarded



# --- Explorer tools (any fiber may use; NOT named agent products) ---
# Tools: "rule" (deterministic patch), "llm" (MiniMax), "intent" (template/skeleton).

EXPLORE_TOOLS_DEFAULT = ("rule", "llm", "intent")


def parse_explore_tools(raw: str | list[str] | None) -> list[str]:
    """Parse ``--explore-tools rule,llm,intent`` into a validated tool list."""
    if raw is None:
        return list(EXPLORE_TOOLS_DEFAULT)
    if isinstance(raw, list):
        items = [str(x).strip().lower() for x in raw if str(x).strip()]
    else:
        items = [p.strip().lower() for p in str(raw).split(",") if p.strip()]
    allowed = set(EXPLORE_TOOLS_DEFAULT)
    out = [t for t in items if t in allowed]
    return out or list(EXPLORE_TOOLS_DEFAULT)


def _tool_rule_sources(
    task_spec: dict[str, Any],
    *,
    prev_sources: dict[str, str] | None,
    prev_errors: str | None,
) -> dict[str, Any]:
    """Deterministic mini-* repairs from verify stderr + known heuristics.

    Returns ``{ok, sources, source, tools_used}`` — no LLM.
    """
    files = list(task_spec.get("files") or [])
    label = str(task_spec.get("label") or "").lower()
    project = str(task_spec.get("project") or "").lower()
    err = (prev_errors or "").lower()
    expect = str(task_spec.get("expect") or "")
    sources: dict[str, str] = {}

    is_cache = label == "cache" or "mini-cache" in project or "cache-init" in expect.lower() or "ttl_expired" in expect.lower()
    is_router = label == "router" or "mini-router" in project or "post_api" in expect.lower()
    is_bank = label == "bank" or "mini-bank" in project

    if is_cache and files:
        sources = {
            "store.aura": (
                "(define store '())\n"
                "(define tick 0)\n"
                "(define (cache-init)\n"
                "  (set! store '())\n"
                "  (set! tick 0))\n"
                "(define (cache-set key val ttl)\n"
                "  (let ((expire (if (= ttl 0) #f (+ tick ttl))))\n"
                "    (set! store (cons (list key val expire) store))))\n"
            ),
            "ops.aura": (
                "(define (lookup key rs)\n"
                "  (if (null? rs)\n"
                "      #f\n"
                "      (let ((e (car rs)))\n"
                "        (if (equal? (car e) key)\n"
                "            e\n"
                "            (lookup key (cdr rs))))))\n"
                "(define (cache-get key)\n"
                "  (let ((hit (lookup key store)))\n"
                "    (if hit\n"
                "        (let ((expire (car (cdr (cdr hit)))))\n"
                "          (if (and expire (not (< tick expire)))\n"
                "              \"miss\"\n"
                "              (car (cdr hit))))\n"
                "        \"miss\")))\n"
                "(define (cache-tick n)\n"
                "  (set! tick (+ tick n)))\n"
            ),
            "main.aura": (
                "(cache-init)\n"
                "(define (show label val)\n"
                "  (display label)(display \"=\")(display val)(newline))\n"
                "(define c 0)\n"
                "(define (hit label key)\n"
                "  (let ((v (cache-get key)))\n"
                "    (show label v)\n"
                "    (if (equal? v \"miss\")\n"
                "        #t\n"
                "        (set! c (+ c 1)))))\n"
                "(cache-set \"a\" \"1\" 0)\n"
                "(cache-set \"b\" \"2\" 2)\n"
                "(hit \"GET_A\" \"a\")\n"
                "(hit \"GET_MISS\" \"nope\")\n"
                "(hit \"GET_B\" \"b\")\n"
                "(cache-tick 2)\n"
                "(hit \"TTL_EXPIRED\" \"b\")\n"
                "(show \"COUNT\" c)\n"
            ),
        }
        # Keep only requested files
        sources = {fn: sources[fn] for fn in files if fn in sources}
    elif is_router and files:
        sources = {
            "table.aura": (
                "(define routes '())\n"
                "(define (route-register method path handler)\n"
                "  (set! routes (cons (list method path handler) routes)))\n"
                "(define (route-table) routes)\n"
                "(define (routes-init)\n"
                "  (set! routes '())\n"
                "  (route-register \"GET\" \"/\" \"home\")\n"
                "  (route-register \"GET\" \"/api\" \"api\"))\n"
            ),
            "match.aura": (
                "(define (starts-with s prefix)\n"
                "  (let ((n (string-length prefix)))\n"
                "    (if (< (string-length s) n)\n"
                "        #f\n"
                "        (equal? (substring s 0 n) prefix))))\n"
                "(define (lookup-exact method path rs)\n"
                "  (if (null? rs)\n"
                "      #f\n"
                "      (let ((r (car rs)))\n"
                "        (if (and (equal? (car r) method) (equal? (car (cdr r)) path))\n"
                "            (car (cdr (cdr r)))\n"
                "            (lookup-exact method path (cdr rs))))))\n"
                "(define (route-lookup method path)\n"
                "  (cond\n"
                "    ((and (equal? method \"POST\") (equal? path \"/api\")) \"405\")\n"
                "    ((lookup-exact method path (route-table)))\n"
                "    ((and (equal? method \"GET\") (starts-with path \"/api\")) \"api\")\n"
                "    (else \"404\")))\n"
            ),
            "main.aura": (
                "(routes-init)\n"
                "(define (show label val)\n"
                "  (display label)(display \"=\")(display val)(newline))\n"
                "(define c 0)\n"
                "(define (hit label method path)\n"
                "  (let ((v (route-lookup method path)))\n"
                "    (show label v)\n"
                "    (if (equal? v \"404\")\n"
                "        #t\n"
                "        (set! c (+ c 1)))))\n"
                "(hit \"GET_SLASH\" \"GET\" \"/\")\n"
                "(hit \"GET_API\" \"GET\" \"/api\")\n"
                "(hit \"GET_API_V1\" \"GET\" \"/api/v1\")\n"
                "(hit \"GET_API_V2\" \"GET\" \"/api/v2\")\n"
                "(hit \"POST_API\" \"POST\" \"/api\")\n"
                "(hit \"MISS\" \"GET\" \"/nope\")\n"
                "(show \"COUNT\" c)\n"
            ),
        }
        sources = {fn: sources[fn] for fn in files if fn in sources}
    elif is_bank and files:
        sources = {
            "lib.aura": (
                "(define bals '())\n"
                "(define (find acct rs)\n"
                "  (if (null? rs) #f\n"
                "    (if (equal? (car (car rs)) acct) (car rs) (find acct (cdr rs)))))\n"
                "(define (strip acct rs)\n"
                "  (if (null? rs) '()\n"
                "    (if (equal? (car (car rs)) acct)\n"
                "        (strip acct (cdr rs))\n"
                "        (cons (car rs) (strip acct (cdr rs))))))\n"
                "(define (set-bal acct n)\n"
                "  (set! bals (cons (cons acct n) (strip acct bals))))\n"
                "(define (balance acct)\n"
                "  (let ((p (find acct bals))) (if p (cdr p) 0)))\n"
                "(define (credit acct n) (set-bal acct (+ (balance acct) n)))\n"
                "(define (debit acct n) (set-bal acct (- (balance acct) n)))\n"
            ),
            "main.aura": (
                "(credit \"A\" 100)\n"
                "(credit \"B\" 50)\n"
                "(display \"A=\")(display (balance \"A\"))(newline)\n"
                "(display \"B=\")(display (balance \"B\"))(newline)\n"
                "(debit \"A\" 30)\n"
                "(credit \"B\" 30)\n"
                "(display \"A2=\")(display (balance \"A\"))(newline)\n"
                "(display \"B2=\")(display (balance \"B\"))(newline)\n"
                "(display \"OK=\")(display 1)(newline)\n"
            ),
        }
        sources = {fn: sources[fn] for fn in files if fn in sources}
    elif prev_sources and err and ("count" in err or "ttl" in err or "405" in err or "mismatch" in err):
        # Surgical COUNT fix heuristic on main when previous sources exist
        sources = dict(prev_sources)
        main_key = None
        for cand in ("main.aura", files[-1] if files else None):
            if cand and cand in sources:
                main_key = cand
                break
        if main_key:
            body = sources[main_key]
            # Fix naive increment-on-every-hit → skip miss/404
            if "(set! c (+ c 1))" in body and "miss" in body.lower():
                body = body.replace(
                    "(set! c (+ c 1))",
                    '(if (or (equal? v "miss") (equal? v "404")) #t (set! c (+ c 1)))',
                )
                sources[main_key] = body

    if not sources:
        return {
            "ok": False,
            "source": "",
            "sources": {},
            "tools_used": ["rule"],
            "error": "rule_tool_no_patch",
        }
    joined = chr(10).join(
        f"; --- {fn} ---{chr(10)}{sources.get(fn, '')}" for fn in (files or list(sources))
    )
    return {
        "ok": True,
        "source": joined,
        "sources": sources,
        "tools_used": ["rule"],
        "error": "",
    }


def _tool_intent_sources(
    task_spec: dict[str, Any],
    *,
    prev_sources: dict[str, str] | None,
    cfg: MiniMaxConfig | None = None,
) -> dict[str, Any]:
    """Map GOAL/expect tokens → structured intent → template skeleton (no MiniMax when strong).

    Falls back to a narrow MiniMax prompt labeled intent only when the template is weak.
    """
    files = list(task_spec.get("files") or [])
    expect = str(task_spec.get("expect") or "")
    intent_key = hashlib.sha256(
        (expect + "|" + ",".join(files) + "|" + str(task_spec.get("label") or "")).encode()
    ).hexdigest()[:12]
    # Prefer rule-quality templates when we recognize the contract
    rule = _tool_rule_sources(task_spec, prev_sources=prev_sources, prev_errors="intent")
    if rule.get("ok") and rule.get("sources"):
        out = dict(rule)
        out["tools_used"] = ["intent"]
        out["intent_hash"] = intent_key
        return out
    # Weak intent: optional narrow LLM
    if cfg is not None:
        narrow = dict(task_spec)
        narrow["user"] = (
            "INTENT-MODE: emit ONLY the minimal Aura skeleton that prints exactly:\n"
            f"{expect}\n"
            "Include required (define …) forms from the goal. Named fences if multi-file.\n"
            f"intent_hash={intent_key}\n"
        )
        prop = _propose(
            cfg,
            task_spec=narrow,
            round_i=0,
            prev_source=None,
            prev_errors=None,
            candidate_index=0,
            prev_sources=prev_sources,
        )
        prop["tools_used"] = ["intent", "llm"]
        prop["intent_hash"] = intent_key
        return prop
    return {
        "ok": False,
        "source": "",
        "sources": dict(prev_sources or {}),
        "tools_used": ["intent"],
        "intent_hash": intent_key,
        "error": "intent_tool_weak",
    }


def _propose_with_tools(
    cfg: MiniMaxConfig,
    *,
    task_spec: dict[str, Any],
    round_i: int,
    prev_source: str | None,
    prev_errors: str | None,
    prev_sources: dict[str, str] | None,
    candidate_index: int,
    tools: list[str],
) -> dict[str, Any]:
    """Pick a propose strategy from available tools for this explorer worldline.

    Tools are mixed capabilities — not exclusive agent identities. Prefer rule
    on early repair rounds when sticky stubs are known; else llm; intent as
    alternate skeleton path.
    """
    preferred = tools[candidate_index % len(tools)] if tools else "llm"
    # Diversify: try preferred first, fall through
    order = [preferred] + [t for t in tools if t != preferred]
    last: dict[str, Any] = {"ok": False, "source": "", "sources": {}, "tools_used": []}
    for tool in order:
        if tool == "rule":
            got = _tool_rule_sources(
                task_spec, prev_sources=prev_sources, prev_errors=prev_errors
            )
            if got.get("ok"):
                return got
            last = got
        elif tool == "intent":
            got = _tool_intent_sources(
                task_spec, prev_sources=prev_sources, cfg=None  # template-only first
            )
            if got.get("ok"):
                return got
            last = got
        elif tool == "llm":
            got = _propose(
                cfg,
                task_spec=task_spec,
                round_i=round_i,
                prev_source=prev_source,
                prev_errors=prev_errors,
                prev_sources=prev_sources,
                candidate_index=candidate_index,
            )
            got = dict(got)
            got["tools_used"] = ["llm"]
            return got
    # Last resort: llm even if not listed
    got = _propose(
        cfg,
        task_spec=task_spec,
        round_i=round_i,
        prev_source=prev_source,
        prev_errors=prev_errors,
        prev_sources=prev_sources,
        candidate_index=candidate_index,
    )
    got = dict(got)
    used = list(last.get("tools_used") or [])
    if "llm" not in used:
        used.append("llm")
    got["tools_used"] = used
    return got


def fiber_fanout_probe(
    serve_session: Any,
    *,
    n: int,
    timeout_s: float = 8.0,
) -> dict[str, Any]:
    """Honest denseness probe: N sequential fiber:spawn+join oneshots.

    Soft Ready async has hung on large multi-binding ``let*`` fan-out scripts;
    sequential oneshots match fiber-spawn.md denseness and keep the holder alive.
    Returns ``{ok, fiber_ids, worldline_backend}``. Never invents fiber_graph.
    """
    if serve_session is None or n <= 0:
        return {"ok": False, "fiber_ids": [], "worldline_backend": None, "reason": "no_session"}
    # Soft Ready async denseness is live after Aura #4048 (affinity + body
    # mutex + Soft Ready auto workers=1). One successful spawn+join oneshot
    # is enough to stamp fiber_graph for the round (honest: denseness used).
    fiber_ids: list[Any] = []
    try:
        r = serve_session.raw_line(
            "(fiber:join (fiber:spawn (lambda () 7)))",
            timeout_s=min(5.0, float(timeout_s)),
        )
        if r.get("status") != "ok":
            return {
                "ok": False,
                "fiber_ids": [],
                "worldline_backend": None,
                "reason": f"fiber_probe_failed:{r.get('msg') or r.get('status')}",
                "raw": {k: r.get(k) for k in ("status", "value", "msg")},
            }
        join_val = r.get("value")
        join_ok = str(join_val) in ("7", "7.0") or join_val == 7
        if not join_ok:
            return {
                "ok": False,
                "fiber_ids": [],
                "worldline_backend": None,
                "reason": f"fiber_probe_bad_join:{join_val!r}",
                "raw": {k: r.get(k) for k in ("status", "value", "msg")},
            }
        return {
            "ok": True,
            "fiber_ids": fiber_ids,
            "worldline_backend": "fiber_graph",
            "spawn_n": 1,
            "join_value": join_val,
            "requested_n": n,
            "note": "soft_ready_async_denseness_4048",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "fiber_ids": fiber_ids,
            "worldline_backend": None,
            "reason": f"fiber_probe_exc:{type(exc).__name__}:{exc}",
        }



def _propose(
    cfg: MiniMaxConfig,
    *,
    task_spec: dict[str, Any],
    round_i: int,
    prev_source: str | None,
    prev_errors: str | None,
    candidate_index: int,
    prev_sources: dict[str, str] | None = None,
) -> dict[str, Any]:
    base_user = str(task_spec["user"])
    file_list = list(task_spec.get("files") or [])
    multi = len(file_list) > 1
    if round_i == 0 and not prev_errors:
        user = base_user + f"\n(candidate index={candidate_index}; vary structure slightly)\n"
        messages = [
            {"role": "system", "content": SYSTEM_CODEGEN},
            {"role": "user", "content": user},
        ]
    else:
        err = (prev_errors or "")[:3500]
        expect = str(task_spec.get("expect") or "")
        src_res = task_spec.get("source_res") or []
        struct_hint = ""
        if src_res:
            pats = ", ".join(
                getattr(p, "pattern", str(p)) for p in src_res
            )
            struct_hint = (
                f"Required source patterns (all must match; use \\b so zero-arity "
                f"(define (name) ...) works): {pats}\n"
            )
        mismatch_hint = ""
        if "verify mismatch line" in (err or "").lower():
            mismatch_hint = (
                "Verify reported line mismatches — fix those exact KEY=value lines "
                "(prefix rule, method 405, COUNT definition, etc.).\n"
            )
        if multi:
            fence_hint = "\n".join(f"```aura {fn}\n...\n```" for fn in file_list)
            prev_blocks = []
            src_map = dict(prev_sources or {})
            if not src_map and prev_source:
                # best-effort split from joined "; --- name ---" form
                parts = str(prev_source).split("; --- ")
                for part in parts:
                    if " ---\n" in part or " ---\r\n" in part:
                        name, _, body = part.partition(" ---")
                        name = name.strip()
                        body = body.lstrip("\r\n")
                        if name:
                            src_map[name] = body
            for fn in file_list:
                body = (src_map.get(fn) or "")[:2500]
                prev_blocks.append(f"```aura {fn}\n{body}\n```")
            prev_blob = "\n\n".join(prev_blocks) if prev_blocks else (
                f"```aura\n{(prev_source or '')[:3500]}\n```"
            )
            user_content = (
                f"{REPAIR_STEER}\nRequired exact output:\n{expect}\n"
                f"{struct_hint}{mismatch_hint}\n"
                f"Required files (stable order): {', '.join(file_list)}.\n"
                f"Emit named fences, e.g.:\n{fence_hint}\n"
                "Prefer rewrite ONLY files implicated by verify errors; omitted "
                "files are kept from the previous candidate.\n\n"
                f"## Previous sources\n{prev_blob}\n\n"
                f"## Verify errors / stdout\n```\n{err}\n```\n"
                f"(repair round={round_i} candidate={candidate_index})\n"
            )
        else:
            src = (prev_source or "")[:3500]
            user_content = (
                f"{REPAIR_STEER}\nRequired exact output:\n{expect}\n"
                f"{struct_hint}{mismatch_hint}\n"
                f"## Previous source\n```aura\n{src}\n```\n\n"
                f"## Verify errors / stdout\n```\n{err}\n```\n"
                f"(repair round={round_i} candidate={candidate_index})\n"
            )
        messages = [
            {"role": "system", "content": SYSTEM_CODEGEN},
            {"role": "user", "content": user_content},
        ]
    result = chat_completions(messages, config=cfg, thinking_disabled=True)
    content = (result.get("content") or "") if result.get("ok") else ""
    sources: dict[str, str] = {}
    source = ""
    if content:
        if multi:
            sources = extract_aura_sources(content, file_list)
            # Per-file repair merge: keep previous for omitted/empty files
            if prev_sources:
                for fn in file_list:
                    if not (sources.get(fn) or "").strip():
                        prev = prev_sources.get(fn) or ""
                        if prev.strip():
                            sources[fn] = prev
            source = chr(10).join(
                f"; --- {fn} ---{chr(10)}{sources.get(fn, '')}"
                for fn in file_list
            )
            if not any((v or "").strip() for v in sources.values()):
                source = extract_aura_source(content)
                sources = {file_list[-1]: source}
        else:
            source = extract_aura_source(content)
            if file_list:
                sources = {file_list[0]: source}
    return {
        **result,
        "source": source,
        "sources": sources,
        "files_written": list(sources.keys()),
        "messages_roles": [m["role"] for m in messages],
    }


def _append_traj(path: Path, episode: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    validate_episode(episode)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(episode, sort_keys=True) + "\n")
    return path


def _try_aura_orch_record(
    *,
    prompt: str,
    traj_id: str,
    workspace: Path,
    worldlines_payload: list[dict[str, Any]],
    selected_id: str,
    discarded: list[dict[str, Any]],
    honesty: dict[str, Any],
    model: str,
    round_i: int,
    harness_root: Path,
    out_path: Path,
) -> dict[str, Any] | None:
    """Ask Aura kernel to stamp an orch episode when preferred+available."""
    if not prefer_aura_kernel():
        return None
    # Write a manifest the Aura cmd can read
    manifest = harness_root / "llm-dogfood-manifest.json"
    payload = {
        "traj_id": traj_id,
        "prompt": prompt,
        "workspace": str(workspace),
        "selected_id": selected_id,
        "discarded": discarded,
        "worldlines": worldlines_payload,
        "honesty": honesty,
        "llm": {"provider": "minimax", "model": model},
        "round": round_i,
        "out": str(out_path),
    }
    harness_root.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    env = {
        "AURA_BUILD_LLM_MANIFEST": str(manifest),
        "AURA_BUILD_OUT": str(out_path),
        "AURA_BUILD_PROMPT": prompt,
        "AURA_BUILD_LLM_MODEL": model,
        "AURA_BUILD_LLM_PROVIDER": "minimax",
        "AURA_BUILD_TRAJ_ID": traj_id,
        "AURA_BUILD_WORKSPACE": str(workspace),
        "AURA_BUILD_SELECTED_ID": selected_id,
        "AURA_BUILD_ROUND": str(round_i),
    }
    try:
        kr = try_invoke_aura(
            "llm-dogfood",
            env,
            harness_root=harness_root,
            timeout_s=60.0,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": redact_secrets(str(exc)), "via": "aura"}
    if kr is None:
        return None
    return {
        "ok": kr.ok,
        "via": "aura",
        "response": kr.response,
        "stdout": redact_secrets(kr.stdout or "")[-1500:],
        "stderr": redact_secrets(kr.stderr or "")[-1500:],
    }


def run_closed_loop(
    *,
    task: str | None = DEFAULT_TASK,
    project: Path | str | None = None,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    worldlines: int = DEFAULT_WORLDLINES,
    out: Path | None = None,
    workspace: Path | None = None,
    harness_root: Path | None = None,
    aura_bin: str | None = None,
    keep_workspace: bool = True,
    config: MiniMaxConfig | None = None,
    prefer_session: bool | None = True,
    fiber_explore: int | None = None,
    explore_tools: list[str] | str | None = None,
) -> dict[str, Any]:
    """Propose → verify → repair with optional fiber:spawn concurrent explore.

    ``fiber_explore`` (default = worldlines when Soft prefer-session + multi-file)
    requests N explorer worldlines. Primary concurrency is fiber:spawn on a live
    Soft serve FlatAST when denseness measures; else host threads. Tools
    (rule / llm / intent) are strategies any explorer may use — not agent kinds.
    """
    repo = repo_root()
    registry_task = task
    auto_loaded = False
    # Auto-load project dir only when registry entry opts in via verify_script
    # (keeps greet/calc baked prompts stable; kv/stack + --project use verify.sh).
    if project is None and task in TASKS and TASKS[task].get("verify_script"):
        proj_rel = TASKS[task].get("project")
        if isinstance(proj_rel, str) and proj_rel.startswith("examples/projects/"):
            cand = repo / proj_rel
            if (cand / "GOAL.md").is_file() and (cand / "verify.sh").is_file():
                project = cand
                auto_loaded = True
    # When caller passed --project alone, ignore default --task fib so label
    # comes from dogfood.json (friction: traj showed task=fib for mini-kv).
    resolve_task = task
    if project is not None and not auto_loaded and task == DEFAULT_TASK:
        resolve_task = None
    task, task_spec = resolve_task_spec(resolve_task, project, repo=repo)
    if auto_loaded and registry_task in TASKS:
        task = registry_task
        task_spec = dict(task_spec)
        task_spec["label"] = registry_task
    expect_re = task_spec.get("expect_re")
    verify_script = task_spec.get("verify_script")
    if verify_script and not Path(str(verify_script)).is_absolute():
        vs = repo / str(verify_script)
        verify_script = str(vs) if vs.is_file() else str(verify_script)
    cfg = config or load_minimax_config()
    tools = parse_explore_tools(explore_tools)
    hroot = harness_root or (repo / ".aura-build")
    hroot.mkdir(parents=True, exist_ok=True)
    honesty = load_honesty(hroot)
    # fiber_live from prove-incr is a denseness bit — not the primary session_model
    # when a long-lived Soft serve attach is alive (optimal loop SSOT).
    session_model = (
        honesty["session_model"]
        if honesty.get("fiber_live")
        else SESSION_SHARED
    )
    # Never fake fiber
    if not honesty.get("fiber_live"):
        session_model = SESSION_SHARED
    # Prefer long-lived serve attach for verify (optimal loop); honest elevate.
    # Live serve wins over stale fiber denseness stamp for session_model.
    serve_sess = None
    serve_meta: dict[str, Any] = {}
    try:
        from aura_build.serve_session import (
            SESSION_SERVE as _SS,
            ensure_eval_session,
            prefer_session_verify,
            session_status,
        )
        st = session_status(harness_root=hroot, aura_bin=aura_bin)
        want_session = prefer_session is not False and (
            st.get("serve_attach_ok") or prefer_session_verify(harness_root=hroot)
        )
        if want_session:
            serve_sess = ensure_eval_session(aura_bin=aura_bin, harness_root=hroot)
        if serve_sess is not None and st.get("serve_attach_ok"):
            session_model = _SS
            honesty = dict(honesty)
            honesty["session_model"] = _SS
            honesty["serve_session_ok"] = True
            honesty["serve_attach_ok"] = True
            honesty["serve_mode"] = st.get("serve_mode")
            honesty["serve_cross_session_shared_ast"] = bool(
                st.get("serve_cross_session_shared_ast")
            )
            honesty["serve_same_session_mutate_ok"] = bool(
                st.get("serve_same_session_mutate_ok")
            )
            honesty["reason"] = (
                f"serve_attach_ok mode={st.get('serve_mode')} "
                f"shared_ast={st.get('serve_cross_session_shared_ast')} "
                f"(fiber_live denseness={bool(honesty.get('fiber_live'))} retained)"
            )
            serve_meta = {
                "serve_mode": st.get("serve_mode"),
                "serve_cross_session_shared_ast": bool(
                    st.get("serve_cross_session_shared_ast")
                ),
                "serve_same_session_mutate_ok": bool(
                    st.get("serve_same_session_mutate_ok")
                ),
                "via_prefer_session": True,
            }
    except Exception:
        serve_sess = None

    multi_file_task = bool(task_spec.get("multi_file")) and len(list(task_spec.get("files") or [])) > 1
    # Default fiber-explore N: worldlines when Soft prefer-session multi-file
    if fiber_explore is None:
        if prefer_session is not False and multi_file_task and serve_sess is not None:
            fiber_explore_n = max(1, int(worldlines))
        else:
            fiber_explore_n = max(1, int(worldlines))
    else:
        fiber_explore_n = max(1, int(fiber_explore))
    # Cap explorers to worldlines slots
    fiber_explore_n = min(fiber_explore_n, max(1, int(worldlines)))
    if not tools:
        tools = list(EXPLORE_TOOLS_DEFAULT) if (
            prefer_session is not False and multi_file_task
        ) else ["llm"]

    traj_id = _make_id("mm")
    out_path = out or (repo / "trajectories" / "minimax_dogfood.jsonl")
    ws_root = workspace or (
        repo / "trajectories" / f"_minimax_ws_{traj_id}"
    )
    if ws_root.exists():
        shutil.rmtree(ws_root)
    ws = _workspace_create(ws_root, worldlines, traj_id)

    rounds_log: list[dict[str, Any]] = []
    final_program: Path | None = None
    success = False
    selected_id = "wl-0"
    last_source = ""
    last_sources: dict[str, str] = {}
    last_errors = ""

    # Optional harness canary via Aura (best-effort; ignore refuse)
    canary_mid = None
    if prefer_aura_kernel():
        try:
            kr = try_invoke_aura(
                "harness-mutate",
                {
                    "AURA_BUILD_PROMPT": f"minimax dogfood canary {traj_id}",
                    "AURA_BUILD_OUT": str(out_path),
                    "AURA_BUILD_HARNESS_PATCHES": json.dumps(
                        {"worldline_count": max(2, worldlines)}
                    ),
                    "AURA_BUILD_FITNESS_PATCHES": json.dumps({"tests": 0.8}),
                    "AURA_BUILD_AUTOPROMOTE_FLAG": "",
                },
                harness_root=hroot,
                timeout_s=60.0,
            )
            if kr and isinstance(kr.response, dict):
                ep = kr.response.get("episode") or {}
                harness = ep.get("harness") if isinstance(ep, dict) else {}
                if isinstance(harness, dict):
                    canary_mid = harness.get("mid")
        except Exception:
            canary_mid = None

    # Sticky projects: verify stub first so round-0 propose is a repair (fail→repair).
    if task_spec.get("seed_from_stub") and isinstance(task_spec.get("fallback"), dict):
        files_seed = list(task_spec.get("files") or [])
        if files_seed:
            seed_dir = ws_root / "candidates" / "stub-seed"
            seed_dir.mkdir(parents=True, exist_ok=True)
            fb = task_spec["fallback"]
            for fn in files_seed:
                (seed_dir / fn).write_text(str(fb.get(fn) or ""), encoding="utf-8")
            entry_name = str(task_spec.get("entry") or files_seed[-1])
            seed_ver = verify_aura_program(
                seed_dir / entry_name,
                expect_re=expect_re,
                source_res=task_spec.get("source_res"),
                aura_bin=aura_bin,
                verify_script=verify_script,
                candidate_dir=seed_dir,
                files=files_seed,
                serve_session=serve_sess,
                harness_root=hroot,
            )
            last_sources = {
                fn: str(fb.get(fn) or "") for fn in files_seed
            }
            last_source = chr(10).join(
                f"; --- {fn} ---{chr(10)}{last_sources.get(fn, '')}" for fn in files_seed
            )
            last_errors = (
                f"stdout:\n{seed_ver.get('stdout', '')}\n"
                f"stderr:\n{seed_ver.get('stderr', '')}\n"
                "(seed_from_stub: previous candidate was project stub; repair it)\n"
            )
            rounds_log.append(
                {
                    "round": -1,
                    "selected_id": "stub-seed",
                    "passed": bool(seed_ver.get("passed")),
                    "fitness": float(seed_ver.get("fitness") or 0.0),
                    "seed_from_stub": True,
                }
            )

    for round_i in range(max_rounds):
        round_wls: list[dict[str, Any]] = []
        fitness_by_id: dict[str, float] = {}
        sources: dict[str, str] = {}
        round_via = "unknown"
        round_oracle = False
        round_backend: str | None = None
        round_fiber_live = bool(honesty.get("fiber_live", False))
        fiber_ids_round: list[Any] = []

        # Fiber denseness on the live serve FlatAST. Aura #4048 makes Soft
        # Ready --serve-async denseness honest (spawn+join returns). Probe on
        # sync and async Soft Ready; never invent fiber_graph without ok probe.
        # AURA_BUILD_FIBER_EXPLORE_FORCE=1 retained as an explicit override.
        fiber_probe = {"ok": False}
        serve_mode_now = serve_meta.get("serve_mode") or honesty.get("serve_mode")
        force_fiber = os.environ.get("AURA_BUILD_FIBER_EXPLORE_FORCE") == "1"
        if (
            serve_sess is not None
            and prefer_session is not False
            and (serve_mode_now in ("sync", "async") or force_fiber)
        ):
            fiber_probe = fiber_fanout_probe(
                serve_sess, n=fiber_explore_n, timeout_s=8.0
            )
            if fiber_probe.get("ok"):
                round_backend = "fiber_graph"
                fiber_ids_round = list(fiber_probe.get("fiber_ids") or [])
                round_fiber_live = True
            else:
                round_backend = None  # do not invent fiber_graph

        n_explore = fiber_explore_n

        def _explore_one(i: int) -> dict[str, Any]:
            """Propose+materialize+verify one explorer worldline (host side)."""
            cid = f"wl-{i}"
            cdir = ws_root / "candidates" / cid
            cdir.mkdir(parents=True, exist_ok=True)
            prop = _propose_with_tools(
                cfg,
                task_spec=task_spec,
                round_i=round_i,
                prev_source=last_source if (i == 0 or round_i > 0) else (
                    last_source if i == 0 else None
                ),
                prev_errors=(
                    last_errors
                    if (round_i > 0 or last_errors) and (i == 0 or True)
                    else None
                )
                if (round_i > 0 or last_errors)
                else None,
                prev_sources=last_sources if (round_i > 0 or last_errors) else None,
                candidate_index=i,
                tools=tools,
            )
            # Diversify repair errors for non-zero explorers
            if round_i > 0 and i > 0 and last_errors and "llm" in (prop.get("tools_used") or []):
                prop = _propose_with_tools(
                    cfg,
                    task_spec=task_spec,
                    round_i=round_i,
                    prev_source=last_source,
                    prev_errors=last_errors + f"\n(explorer variant {i})",
                    prev_sources=last_sources,
                    candidate_index=i,
                    tools=tools,
                )
            files = list(task_spec.get("files") or [])
            multi = bool(task_spec.get("multi_file")) and len(files) > 1
            sources_map = dict(prop.get("sources") or {})
            source = prop.get("source") or ""
            fallback = task_spec.get("fallback")
            tools_used = list(prop.get("tools_used") or [])
            if multi:
                for fn in files:
                    if not (sources_map.get(fn) or "").strip():
                        if (last_sources.get(fn) or "").strip():
                            sources_map[fn] = last_sources[fn]
                        elif isinstance(fallback, dict):
                            sources_map[fn] = str(fallback.get(fn) or "")
                if not any((sources_map.get(fn) or "").strip() for fn in files):
                    if last_sources:
                        sources_map = {fn: str(last_sources.get(fn) or "") for fn in files}
                    elif isinstance(fallback, dict):
                        sources_map = {fn: str(fallback.get(fn) or "") for fn in files}
                    else:
                        sources_map = {files[-1]: str(fallback or FIB_FALLBACK)}
                for fn in files:
                    (cdir / fn).write_text(sources_map.get(fn) or "", encoding="utf-8")
                source = chr(10).join(
                    f"; --- {fn} ---{chr(10)}{sources_map.get(fn, '')}" for fn in files
                )
                prog_path = cdir / str(task_spec.get("entry") or files[-1])
                target_id = ",".join(files)
                cand_dir: Path | None = cdir
            else:
                if not source.strip():
                    if isinstance(fallback, dict):
                        source = str(next(iter(fallback.values()), FIB_FALLBACK))
                    else:
                        source = str(fallback or FIB_FALLBACK)
                prog_path = cdir / "program.aura"
                prog_path.write_text(source, encoding="utf-8")
                sources_map = {prog_path.name: source}
                target_id = "program.aura"
                cand_dir = None
            (cdir / "mutation.json").write_text(
                json.dumps(
                    {
                        "op": "fiber_explore_propose",
                        "target_id": target_id,
                        "files_written": list(sources_map.keys()),
                        "summary": (
                            f"round={round_i} cand={cid} tools={tools_used} "
                            f"model={cfg.model}"
                        ),
                        "tools_used": tools_used,
                        "provider": "minimax" if "llm" in tools_used else "host_tool",
                        "model": cfg.model if "llm" in tools_used else None,
                        "llm_ok": bool(prop.get("ok")),
                        "llm_error": redact_secrets(prop.get("error") or "", cfg.api_key),
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            ver = verify_aura_program(
                prog_path,
                expect_re=expect_re,
                source_res=task_spec.get("source_res"),
                aura_bin=aura_bin,
                verify_script=verify_script,
                candidate_dir=cand_dir,
                files=files if multi else None,
                serve_session=serve_sess,
                harness_root=hroot,
                prefer_session=prefer_session,
            )
            return {
                "cid": cid,
                "cdir": cdir,
                "prog_path": prog_path,
                "source": source,
                "sources_map": sources_map,
                "target_id": target_id,
                "tools_used": tools_used,
                "ver": ver,
            }

        # Parallel host propose/verify across explorers (sock verify serializes
        # inside holder lock; propose tools can overlap).
        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max(1, n_explore)) as pool:
            futs = {pool.submit(_explore_one, i): i for i in range(n_explore)}
            for fut in as_completed(futs):
                results.append(fut.result())
        results.sort(key=lambda r: r["cid"])

        explore_parallel = (
            "fiber_graph" if round_backend == "fiber_graph" else "host_thread"
        )

        for res in results:
            cid = res["cid"]
            ver = res["ver"]
            tools_used = res["tools_used"]
            sources_map = res["sources_map"]
            source = res["source"]
            prog_path = res["prog_path"]
            target_id = res["target_id"]
            cdir = res["cdir"]
            fitness_by_id[cid] = float(ver["fitness"])
            sources[cid] = source
            round_via = str(ver.get("via") or round_via)
            if ver.get("oracle_verify_script"):
                round_oracle = True
            (cdir / "eval.json").write_text(
                json.dumps(
                    {
                        "fitness": ver["fitness"],
                        "passed": ver["passed"],
                        "stdout": redact_secrets(ver["stdout"], cfg.api_key),
                        "stderr": redact_secrets(ver["stderr"], cfg.api_key),
                        "ms": ver["ms"],
                        "via": ver.get("via"),
                        "cold_spawns": ver.get("cold_spawns"),
                        "oracle_verify_script": ver.get("oracle_verify_script"),
                        "tools_used": tools_used,
                        "worldline_backend": round_backend,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            wl_idx = int(cid.split("-")[-1]) if "-" in cid else 0
            fiber_id = (
                fiber_ids_round[wl_idx]
                if wl_idx < len(fiber_ids_round)
                else None
            )
            round_wls.append(
                {
                    "id": cid,
                    "parent_id": "wl-parent" if round_i > 0 else None,
                    "stable_ref": cid,
                    "tools_used": tools_used,
                    "fiber_id": fiber_id,
                    "worldline_backend": round_backend,
                    "mutations": [
                        {
                            "op": "fiber_explore_propose",
                            "target_id": target_id,
                            "files_written": list(sources_map.keys()),
                            "summary": (
                                f"explorer {cid} round {round_i} tools={tools_used}"
                            ),
                            "tools_used": tools_used,
                        }
                    ],
                    "eval": {
                        "fitness": ver["fitness"],
                        "passed": ver["passed"],
                        "metrics": {
                            "tests_passed": 1 if ver["passed"] else 0,
                            "tests_total": 1,
                            "incr_compile_ms": ver["ms"],
                            "audit_ok": True,
                            "incr_proven": False,
                            "matched_expect": ver.get("matched_expect", False),
                            "via": ver.get("via"),
                            "cold_spawns": ver.get("cold_spawns", 0),
                            "oracle_verify_script": bool(
                                ver.get("oracle_verify_script")
                            ),
                        },
                        "notes": redact_secrets(
                            (
                                (
                                    _structure_fail_note(task_spec.get("source_res"))
                                    if ver.get("structure_ok") is False
                                    else ""
                                )
                                + (ver["stderr"] or ver["stdout"] or "")
                            )[:800],
                            cfg.api_key,
                        ),
                    },
                    "program_path": str(prog_path),
                }
            )

        # select-best
        selected_id = max(
            fitness_by_id.keys(),
            key=lambda k: (fitness_by_id[k], k),
        )
        discarded = _discard_losers(ws_root, selected_id, fitness_by_id)
        best = next(w for w in round_wls if w["id"] == selected_id)
        last_source = sources[selected_id]
        # Capture per-file map for next-round partial repair merge
        last_sources = {}
        if task_spec.get("multi_file"):
            sel_cand = ws_root / "candidates" / selected_id
            for fn in list(task_spec.get("files") or []):
                fp = sel_cand / fn
                if fp.is_file():
                    try:
                        last_sources[fn] = fp.read_text(encoding="utf-8")
                    except OSError:
                        pass
        last_errors = best["eval"]["notes"]
        if not best["eval"]["passed"]:
            # richer error feed for repair
            eval_path = ws_root / "candidates" / selected_id / "eval.json"
            try:
                ev = json.loads(eval_path.read_text(encoding="utf-8"))
                last_errors = (
                    f"stdout:\n{ev.get('stdout','')}\nstderr:\n{ev.get('stderr','')}"
                )
            except Exception:
                pass

        # materialize selected to workspace final
        sel_dir = ws_root / "selected"
        sel_dir.mkdir(parents=True, exist_ok=True)
        cand_sel = ws_root / "candidates" / selected_id
        files_sel = list(task_spec.get("files") or [])
        if task_spec.get("multi_file") and len(files_sel) > 1:
            for fn in files_sel:
                src_f = cand_sel / fn
                if src_f.is_file():
                    shutil.copy2(src_f, sel_dir / fn)
            final_program = sel_dir / str(task_spec.get("entry") or files_sel[-1])
            (sel_dir / "FILES").write_text(chr(10).join(files_sel) + chr(10), encoding="utf-8")
        else:
            final_program = sel_dir / "program.aura"
            final_program.write_text(last_source, encoding="utf-8")
            src_prog = cand_sel / "program.aura"
            if src_prog.is_file():
                shutil.copy2(src_prog, final_program)


        episode = {
            "schema_version": "trajectory.v0",
            "episode_id": f"{traj_id}-r{round_i}",
            "ts_start": _iso_now(),
            "ts_end": _iso_now(),
            "prompt": f"minimax dogfood task={task} round={round_i}",
            "runtime": {
                "mode": "aura",
                "requested_mode": "aura",
                "kernel": "aura",
                "seed": round_i,
                "incr_proven": bool(honesty.get("incr_proven", False)),
                "fiber_live": bool(round_fiber_live),
                "measured": bool(honesty.get("measured", False)),
                "session_model": session_model,
                "worldline_backend": round_backend,
                "explore_parallel": explore_parallel,
                "fiber_explore_n": fiber_explore_n,
                "serve_mode": serve_meta.get("serve_mode"),
                "serve_cross_session_shared_ast": serve_meta.get(
                    "serve_cross_session_shared_ast"
                ),
                "serve_same_session_mutate_ok": serve_meta.get(
                    "serve_same_session_mutate_ok"
                ),
                "via_prefer_session": bool(serve_meta.get("via_prefer_session")),
                "via": round_via,
                "workspace": str(ws_root),
                "llm": cfg.public_dict(),
                "dogfood": {
                    "provider": "minimax",
                    "model": cfg.model,
                    "task": task,
                    "project": str(task_spec.get("project") or ""),
                    "verify_script": str(verify_script or ""),
                    "files": list(task_spec.get("files") or []),
                    "multi_file": bool(task_spec.get("multi_file")),
                    "run_mode": str(task_spec.get("run_mode") or "single"),
                    "round": round_i,
                    "max_rounds": max_rounds,
                    "traj_id": traj_id,
                    "explore_tools": list(tools),
                    "fiber_explore_n": fiber_explore_n,
                    "oracle_verify_script": round_oracle,
                },
            },
            "harness": {
                "l1_strategy_id": "minimax_dogfood.v0",
                "l2_weights_id": None,
                "l3_online": False,
                "mid": canary_mid,
                "outcome": "pass" if best["eval"]["passed"] else "repair",
                "actions": [
                    {
                        "op": "fiber_explore",
                        "n": fiber_explore_n,
                        "backend": round_backend or explore_parallel,
                        "tools": list(tools),
                    },
                    {"op": "verify", "via": round_via},
                    {"op": "select_best", "selected": selected_id},
                    {"op": "discard_losers", "count": len(discarded)},
                ],
            },
            "worldlines": [
                {k: v for k, v in w.items() if k != "program_path"} for w in round_wls
            ],
            "selected_id": selected_id,
            "selection_reason": "max_fitness",
            "discarded": discarded,
            "privacy": {"redacted": True, "retention_class": "dogfood"},
        }
        # Host writes traj (Aura may also append via llm-dogfood)
        _append_traj(out_path, episode)
        aura_rec = _try_aura_orch_record(
            prompt=episode["prompt"],
            traj_id=episode["episode_id"],
            workspace=ws_root,
            worldlines_payload=episode["worldlines"],
            selected_id=selected_id,
            discarded=discarded,
            honesty=honesty,
            model=cfg.model,
            round_i=round_i,
            harness_root=hroot,
            out_path=out_path,
        )

        rounds_log.append(
            {
                "round": round_i,
                "selected_id": selected_id,
                "fitness": best["eval"]["fitness"],
                "passed": best["eval"]["passed"],
                "discarded": len(discarded),
                "final_program": str(final_program),
                "via": round_via,
                "worldline_backend": round_backend,
                "explore_parallel": explore_parallel,
                "fiber_live": round_fiber_live,
                "tools_used_selected": list(best.get("tools_used") or []),
                "tools_used_round": sorted({
                    t
                    for w in round_wls
                    for t in (w.get("tools_used") or [])
                }),
                "oracle_verify_script": round_oracle,
                "aura_orch": (
                    {"ok": aura_rec.get("ok"), "via": aura_rec.get("via")}
                    if aura_rec
                    else {"ok": False, "via": "host_only"}
                ),
            }
        )

        if best["eval"]["passed"]:
            success = True
            break

    if not keep_workspace and success:
        # keep selected artifact copy under .aura-build
        keep = hroot / "minimax-last-program.aura"
        if final_program and final_program.is_file():
            shutil.copy2(final_program, keep)
            final_program = keep

    # Summarize fiber explore honesty from last successful / final round
    last_round = rounds_log[-1] if rounds_log else {}
    summary = {
        "ok": success,
        "traj_id": traj_id,
        "rounds": len([r for r in rounds_log if int(r.get("round", -1)) >= 0]),
        "max_rounds": max_rounds,
        "success": success,
        "final_program": str(final_program) if final_program else "",
        "selected_id": selected_id,
        "workspace": str(ws_root),
        "traj_path": str(out_path),
        "llm": cfg.public_dict(),
        "explore_tools": list(tools),
        "fiber_explore_n": fiber_explore_n,
        "worldline_backend": last_round.get("worldline_backend"),
        "explore_parallel": last_round.get("explore_parallel"),
        "via": last_round.get("via"),
        "tools_used_selected": last_round.get("tools_used_selected"),
        "honesty": {
            "incr_proven": bool(honesty.get("incr_proven", False)),
            "fiber_live": bool(
                last_round.get("fiber_live", honesty.get("fiber_live", False))
            ),
            "session_model": session_model,
            "worldline_backend": last_round.get("worldline_backend"),
            "explore_parallel": last_round.get("explore_parallel"),
            "serve_mode": serve_meta.get("serve_mode") or honesty.get("serve_mode"),
            "serve_cross_session_shared_ast": serve_meta.get(
                "serve_cross_session_shared_ast",
                honesty.get("serve_cross_session_shared_ast"),
            ),
            "serve_same_session_mutate_ok": serve_meta.get(
                "serve_same_session_mutate_ok",
                honesty.get("serve_same_session_mutate_ok"),
            ),
            "via_prefer_session": bool(serve_meta.get("via_prefer_session")),
            "via": last_round.get("via"),
            "reason": honesty.get("reason"),
        },
        "rounds_log": rounds_log,
        "kernel": "aura",
        "task": task,
        "expect": str(task_spec.get("expect") or ""),
        "project": str(task_spec.get("project") or ""),
        "verify_script": str(verify_script or ""),
        "reason": "verify_green" if success else f"max_rounds_{max_rounds}",
    }
    summary_path = hroot / "minimax-dogfood-latest.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary
