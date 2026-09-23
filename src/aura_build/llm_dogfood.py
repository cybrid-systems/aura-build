"""MiniMax → aura-build closed loop: propose Aura source → verify → repair.

Uses shared_workspace_subprocess worldline layout (honest when fiber_live=false).
Orch episode recording prefers the Aura kernel (`llm-dogfood` cmd) when available;
host always owns MiniMax HTTP + repair steering.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import uuid
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

TASK_FIB = "fib"
TASK_GREET = "greet"
TASK_CALC = "calc"
TASK_KV = "kv"
TASK_STACK = "stack"
TASK_BANK = "bank"
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
  (```aura:lib.aura and ```lib.aura also accepted).
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
Return ONE corrected Aura program in a ```aura fence.
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
            r"(?:FIB10=|GREET=|ADD=|MUL=|MIX=|GET_|MISS=|TOP=|POP=|TOP2=|SIZE=|EMPTY=|A=|B=|A2=|B2=|OK=)",
            stdout or "",
        )
    )


def _structure_fail_note(source_res: list[re.Pattern[str]] | None) -> str:
    """Human-readable structure failure for repair / traj notes (task-agnostic)."""
    if not source_res:
        return "structure_fail: required source patterns missing\n"
    pats = ", ".join(p.pattern for p in source_res)
    return f"structure_fail: source must match all of: {pats}\n"


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
) -> dict[str, Any]:
    """Compile/run candidate with Aura binary; fitness from pass + error signal.

    ``expect_re`` may be one pattern or a list (all must match stdout).
    Optional ``source_res`` patterns must all match the candidate source
    (structural checks, e.g. require ``(define (add`` / ``(define (mul``).
    Optional ``verify_script`` (project ``verify.sh``) is the preferred oracle:
    exit 0 → pass; stdout/stderr are fed back into repair prompts.
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
        }
    env = aura_subprocess_env(bin_path) if bin_path else os.environ.copy()
    if bin_path:
        env.setdefault("AURA_BIN", bin_path)

    # Project-owned verify.sh oracle (preferred when present)
    if verify_script:
        script = Path(verify_script)
        if not script.is_file():
            return {
                "ok": False,
                "fitness": 0.0,
                "passed": False,
                "stdout": "",
                "stderr": f"verify_script_missing:{script}",
                "exit_code": 2,
                "ms": 0,
                "matched_expect": False,
                "structure_ok": False,
                "has_error": True,
                "via": "verify_script",
            }
        verify_arg = str(candidate_dir) if candidate_dir else str(source_path)
        t0 = time.monotonic()
        proc = subprocess.run(
            ["bash", str(script), verify_arg],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            check=False,
        )
        ms = int((time.monotonic() - t0) * 1000)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        passed = proc.returncode == 0
        # Optional extra structure check even when script is oracle
        source_text = ""
        try:
            if candidate_dir and files:
                cdir = Path(candidate_dir)
                parts = [
                    (cdir / fn).read_text(encoding="utf-8")
                    for fn in files
                    if (cdir / fn).is_file()
                ]
                source_text = chr(10).join(parts)
            else:
                source_text = source_path.read_text(encoding="utf-8")
        except OSError:
            source_text = ""
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
        }

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
            "structure_ok": False,
            "has_error": True,
            "via": "aura_bin",
        }
    t0 = time.monotonic()
    proc = subprocess.run(
        [bin_path, str(source_path)],
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env=env,
        check=False,
    )
    ms = int((time.monotonic() - t0) * 1000)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    has_error = bool(
        re.search(r"(?i)\berror:|\bunbound variable\b|\bsyntax\b", stderr)
        or re.search(r"(?i)\berror:|\bunbound variable\b", stdout)
    )
    if expect_re is None:
        patterns: list[re.Pattern[str]] = []
    else:
        patterns = expect_re if isinstance(expect_re, list) else [expect_re]
    matched = all(bool(p.search(stdout)) for p in patterns) if patterns else False
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except OSError:
        source_text = ""
    structure_ok = True
    if source_res:
        structure_ok = all(bool(p.search(source_text)) for p in source_res)
    passed = matched and structure_ok and not has_error
    if passed:
        fitness = 1.0
    elif matched and not structure_ok:
        fitness = 0.4
    elif matched and has_error:
        fitness = 0.35
    elif stdout.strip() and not has_error:
        fitness = 0.25
    elif has_error:
        fitness = max(0.05, 0.2 - min(0.15, len(stderr) / 5000.0))
    else:
        fitness = 0.05
    if not structure_ok and source_res:
        stderr = (stderr + "\n" + _structure_fail_note(source_res)).strip()
    return {
        "ok": passed,
        "fitness": round(fitness, 4),
        "passed": passed,
        "stdout": stdout[-4000:],
        "stderr": stderr[-4000:],
        "exit_code": proc.returncode,
        "ms": ms,
        "matched_expect": matched,
        "structure_ok": structure_ok,
        "has_error": has_error,
        "via": "aura_bin",
    }


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


def _propose(
    cfg: MiniMaxConfig,
    *,
    task_spec: dict[str, Any],
    round_i: int,
    prev_source: str | None,
    prev_errors: str | None,
    candidate_index: int,
) -> dict[str, Any]:
    base_user = str(task_spec["user"])
    if round_i == 0 and not prev_errors:
        user = base_user + f"\n(candidate index={candidate_index}; vary structure slightly)\n"
        messages = [
            {"role": "system", "content": SYSTEM_CODEGEN},
            {"role": "user", "content": user},
        ]
    else:
        err = (prev_errors or "")[:3500]
        src = (prev_source or "")[:3500]
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
        messages = [
            {"role": "system", "content": SYSTEM_CODEGEN},
            {
                "role": "user",
                "content": (
                    f"{REPAIR_STEER}\nRequired exact output:\n{expect}\n"
                    f"{struct_hint}\n"
                    f"## Previous source\n```aura\n{src}\n```\n\n"
                    f"## Verify errors / stdout\n```\n{err}\n```\n"
                    f"(repair round={round_i} candidate={candidate_index})\n"
                ),
            },
        ]
    result = chat_completions(messages, config=cfg, thinking_disabled=True)
    content = (result.get("content") or "") if result.get("ok") else ""
    file_list = list(task_spec.get("files") or [])
    sources: dict[str, str] = {}
    source = ""
    if content:
        if len(file_list) > 1:
            sources = extract_aura_sources(content, file_list)
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
) -> dict[str, Any]:
    """Run MiniMax propose → Aura verify → repair until success or max_rounds.

    Pass ``project`` (path to GOAL.md/stub/verify.sh) to dogfood an external
    mini project without extending the hard-coded TASKS registry.
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
    hroot = harness_root or (repo / ".aura-build")
    hroot.mkdir(parents=True, exist_ok=True)
    honesty = load_honesty(hroot)
    session_model = (
        honesty["session_model"]
        if honesty.get("fiber_live")
        else SESSION_SHARED
    )
    # Never fake fiber
    if not honesty.get("fiber_live"):
        session_model = SESSION_SHARED

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

    for round_i in range(max_rounds):
        round_wls: list[dict[str, Any]] = []
        fitness_by_id: dict[str, float] = {}
        sources: dict[str, str] = {}

        for i in range(worldlines):
            cid = f"wl-{i}"
            cdir = ws_root / "candidates" / cid
            cdir.mkdir(parents=True, exist_ok=True)
            # First worldline repairs from last errors; others diversify from base prompt
            if i == 0 and round_i > 0:
                prop = _propose(
                    cfg,
                    task_spec=task_spec,
                    round_i=round_i,
                    prev_source=last_source,
                    prev_errors=last_errors,
                    candidate_index=i,
                )
            else:
                prop = _propose(
                    cfg,
                    task_spec=task_spec,
                    round_i=0 if round_i == 0 else round_i,
                    prev_source=last_source if i == 0 else None,
                    prev_errors=last_errors if i == 0 and round_i > 0 else (
                        last_errors if round_i > 0 else None
                    ),
                    candidate_index=i,
                )
                if round_i > 0 and i > 0 and last_errors:
                    # diversify repair
                    prop = _propose(
                        cfg,
                        task_spec=task_spec,
                        round_i=round_i,
                        prev_source=last_source,
                        prev_errors=last_errors + f"\n(variant {i})",
                        candidate_index=i,
                    )

            files = list(task_spec.get("files") or [])
            multi = bool(task_spec.get("multi_file")) and len(files) > 1
            sources_map = dict(prop.get("sources") or {})
            source = prop.get("source") or ""
            fallback = task_spec.get("fallback")
            if multi:
                if isinstance(fallback, dict):
                    for fn in files:
                        if not (sources_map.get(fn) or "").strip():
                            sources_map[fn] = str(fallback.get(fn) or "")
                if not any((sources_map.get(fn) or "").strip() for fn in files):
                    if isinstance(fallback, dict):
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
                        "op": "minimax_codegen",
                        "target_id": target_id,
                        "files_written": list(sources_map.keys()),
                        "summary": f"round={round_i} cand={cid} model={cfg.model}",
                        "provider": "minimax",
                        "model": cfg.model,
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
            )
            fitness_by_id[cid] = float(ver["fitness"])
            sources[cid] = source
            (cdir / "eval.json").write_text(
                json.dumps(
                    {
                        "fitness": ver["fitness"],
                        "passed": ver["passed"],
                        "stdout": redact_secrets(ver["stdout"], cfg.api_key),
                        "stderr": redact_secrets(ver["stderr"], cfg.api_key),
                        "ms": ver["ms"],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            round_wls.append(
                {
                    "id": cid,
                    "parent_id": "wl-parent" if round_i > 0 else None,
                    "stable_ref": cid,
                    "mutations": [
                        {
                            "op": "minimax_codegen",
                            "target_id": target_id,
                            "files_written": list(sources_map.keys()),
                            "summary": f"MiniMax-M3 {task} candidate {cid} round {round_i}",
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
                "fiber_live": bool(honesty.get("fiber_live", False)),
                "measured": bool(honesty.get("measured", False)),
                "session_model": session_model,
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
                },
            },
            "harness": {
                "l1_strategy_id": "minimax_dogfood.v0",
                "l2_weights_id": None,
                "l3_online": False,
                "mid": canary_mid,
                "outcome": "pass" if best["eval"]["passed"] else "repair",
                "actions": [
                    {"op": "propose", "provider": "minimax"},
                    {"op": "verify", "via": "aura_bin"},
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

    summary = {
        "ok": success,
        "traj_id": traj_id,
        "rounds": len(rounds_log),
        "max_rounds": max_rounds,
        "success": success,
        "final_program": str(final_program) if final_program else "",
        "selected_id": selected_id,
        "workspace": str(ws_root),
        "traj_path": str(out_path),
        "llm": cfg.public_dict(),
        "honesty": {
            "incr_proven": bool(honesty.get("incr_proven", False)),
            "fiber_live": bool(honesty.get("fiber_live", False)),
            "session_model": session_model,
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
