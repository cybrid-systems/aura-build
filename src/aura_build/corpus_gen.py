"""LeetCode-style Aura corpus generator — MiniMax quota burn via aura-build.

Produces ``corpus/leetcode/<slug>/`` artifacts for future repair targets.
Correctness is NOT required; measured facts only in meta.json / run logs.

Harness convention (stdin-less)::

  - Aura program defines ``(solve ...)`` for the problem.
  - At file end, for each embedded test case i, print exactly one line:
      CASEi=<canonical>
    using ``(display "CASEi=")(display <value>)(newline)`` (or equivalent).
  - Expected values live ONLY in ``tests.json`` (from running ``ref.py``).
  - Canonical encoding matches ref.py: JSON via ``json.dumps(..., separators=(',',':'))``
    for structured values; bare number/bool/string otherwise as JSON literals.

Three-layer: product code only — never edits Aura runtime.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from aura_build.minimax import (
    chat_completions,
    extract_aura_source,
    load_minimax_config,
    redact_secrets,
    MiniMaxConfig,
)
from aura_build.runtime import resolve_aura_bin

# ---------------------------------------------------------------------------
# Defaults / paths
# ---------------------------------------------------------------------------

DEFAULT_CORPUS = Path("corpus/leetcode")
DEFAULT_CATALOG = DEFAULT_CORPUS / "catalog.jsonl"
DEFAULT_SCRATCH = Path("scratch/corpus_gen")
DEFAULT_PID = DEFAULT_SCRATCH / "burn.pid"
DEFAULT_RUN_LOG = DEFAULT_SCRATCH / "run_log.jsonl"
DEFAULT_BURN_LOG = DEFAULT_SCRATCH / "burn.log"

DEFAULT_AURA_BIN = "/workspace/aura-grok/build_soft4055/aura"
LLM_TIMEOUT_S = 120.0
AURA_TIMEOUT_S = 20.0
PY_TIMEOUT_S = 20.0
DEFAULT_WORKERS = 6
DEFAULT_VARIANTS = 2
DEFAULT_CATALOG_TARGET = 300

CATEGORIES = [
    "arrays",
    "strings",
    "hashing",
    "two_pointers",
    "sliding_window",
    "stack_queue",
    "linked_list",
    "trees",
    "binary_search",
    "dynamic_programming",
    "greedy",
    "graphs_bfs_dfs",
    "backtracking",
    "heaps",
    "bit_manipulation",
    "math",
    "intervals",
    "tries",
    "union_find",
]

AURA_PRIMER = """Aura language primer (Lisp-like; NOT Python):
- Forms: (define x 1) (define (f a b) ...) (lambda (x) ...) (if test then else)
  (cond (test expr) ... (else expr)) (let ((a 1) (b 2)) ...) (begin ...)
- Mutate: (set! x v). Lists: '(), (cons a b), (car xs), (cdr xs), (null? xs), (list a b)
- Predicates: equal? number? string? null?  Arithmetic: + - * / modulo quotient
- Compare: < > <= >= =   Booleans: #t #f   and/or/not
- I/O: (display x) (newline)  Convert: (number->string n) (string-append a b)
- Recursion OK. No Python syntax, no list comprehensions, no dict literals.
- Prefer pure recursive/list solutions; arrays as lists of numbers.
"""

SYSTEM_CATALOG = """You list well-known LeetCode (and LeetCode-like) algorithm problems.
Return ONLY a JSON array (no markdown fence unless needed). Each item:
{"slug":"two-sum","title":"Two Sum","category":"arrays","statement":"one-sentence problem summary"}
Rules: slug is kebab-case unique; category must be exactly one of the requested set;
statement is short (1-2 sentences), no full editorial. Prefer classic popular problems.
No API keys. No prose outside JSON."""

SYSTEM_REF = """You write a Python 3 reference solution for a coding problem.
Output a SINGLE ```python fence with a complete runnable script.
Requirements:
- Define solve(...) with a clear signature matching the problem.
- Define CASES: a list of dicts with the keyword args / inputs for each test (3-8 cases,
  including edge cases). Do NOT put expected outputs in CASES.
- When __name__ == '__main__': run solve on each case, encode expected with
  json.dumps(result, separators=(',', ':'), ensure_ascii=False) for all values
  (including ints/bools/lists), and print ONE JSON array to stdout:
  [{"id":0,"input":{...},"expected":"<canonical>"}, ...]
- No network, no files except stdout. Keep runtime tiny (<1s). Use tiny inputs only.
- Do NOT use assert/unittest in __main__ — only compute and print JSON.
- Do not include expected answers inside comments that match the printed expected
  strings as the only logic — actually compute via solve.
"""

SYSTEM_AURA = f"""You are an Aura (Lisp-like) code generator for algorithm problems.
{AURA_PRIMER}
Rules:
- Output ONE complete Aura program in a ```aura fence.
- Define (solve ...) implementing the algorithm (may be wrong; try honestly).
- Do NOT hardcode expected CASE outputs as bare display strings without calling solve.
- At the end, for each provided test input i=0..n-1, call solve and print:
  (display "CASEi=") (display <result-as-aura-value>) (newline)
  For lists print them in a readable form (e.g. via recursive display helper) OR
  print a simple number/bool/string result. Prefer printing numbers and #t/#f directly.
- stdin-less: all test inputs are embedded literals in the program.
- Keep programs small. No secrets.
"""


SYSTEM_AURA_REPAIR = f"""You repair a failing Aura (Lisp-like) program for an algorithm problem.
{AURA_PRIMER}
Rules:
- Output ONE complete Aura program in a ```aura fence (full file, not a patch).
- Keep (solve ...) as the algorithm entry; fix unbound names, parse errors, and wrong logic.
- You may `(require "compat" all:)` at the top for helpers: make-list, assoc, assq, list-tail,
  expt, make-string, string, even?, odd?, caddr, cadddr, bitwise-xor, bitwise-and, ash,
  arithmetic-shift, atom?, make-hash, exact->inexact.
- Use failing CASE diffs and stderr as clues. Do NOT hardcode expected CASE outputs as bare
  display strings without calling solve — still compute via solve for each embedded input.
- At the end, for each test input i, call solve and print:
  (display "CASEi=") (display <result>) (newline)
- Prefer #t/#f for booleans. Keep programs small. No secrets.
"""

SYSTEM_PROBLEM_MD = """You write a concise problem statement markdown for an algorithm puzzle
adapted to a stdin-less Aura harness.
Include: title, short statement, function signature hint for (solve ...),
I/O convention (CASE0=... lines), and 1-2 notes. No solution code. No secrets."""

_SLUG_RE = re.compile(r"^[a-z][a-z0-9\-]{1,80}$")
_CASE_RE = re.compile(r"^CASE(\d+)=(.*)$", re.MULTILINE)
_FENCE_PY = re.compile(r"```(?:python|py)\s*\n([\s\S]*?)```", re.IGNORECASE)
_FENCE_JSON = re.compile(r"```(?:json)?\s*\n([\s\S]*?)```", re.IGNORECASE)

_log_lock = threading.Lock()
_rate_lock = threading.Lock()
_rate_errors = 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _shanghai_now() -> str:
    # box clock is Asia/Shanghai
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S CST")


def ensure_dirs(corpus: Path, scratch: Path) -> None:
    corpus.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    with _log_lock:
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def load_catalog(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        slug = str(row.get("slug") or "").strip()
        if not slug or slug in seen or not _SLUG_RE.match(slug):
            continue
        seen.add(slug)
        out.append(row)
    return out


def save_catalog(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    lines: list[str] = []
    for row in rows:
        slug = str(row.get("slug") or "").strip()
        if not slug or slug in seen or not _SLUG_RE.match(slug):
            continue
        seen.add(slug)
        lines.append(
            json.dumps(
                {
                    "slug": slug,
                    "title": str(row.get("title") or slug),
                    "category": str(row.get("category") or "arrays"),
                    "statement": str(row.get("statement") or ""),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _extract_json_array(text: str) -> list[Any]:
    if not text:
        return []
    m = _FENCE_JSON.search(text)
    body = m.group(1).strip() if m else text.strip()
    # find first [ ... ] span
    start = body.find("[")
    end = body.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        obj = json.loads(body[start : end + 1])
    except json.JSONDecodeError:
        return []
    return obj if isinstance(obj, list) else []


def _extract_python(text: str) -> str:
    if not text:
        return ""
    m = _FENCE_PY.search(text)
    if m:
        return m.group(1).strip() + "\n"
    stripped = text.strip()
    if stripped.startswith("def ") or stripped.startswith("import "):
        return stripped + ("\n" if not stripped.endswith("\n") else "")
    return stripped + "\n"


def _llm(
    messages: list[dict[str, str]],
    *,
    cfg: MiniMaxConfig,
    temperature: float,
    max_tokens: int,
    timeout_s: float,
    run_log: Path | None,
    tag: str,
    slug: str = "",
) -> dict[str, Any]:
    global _rate_errors
    t0 = time.monotonic()
    attempt = 0
    last: dict[str, Any] = {"ok": False, "content": "", "error": "no_attempt", "usage": {}}
    while attempt < 5:
        attempt += 1
        last = chat_completions(
            messages,
            config=cfg,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_disabled=True,
            timeout_s=timeout_s,
        )
        err = str(last.get("error") or "")
        is_rate = "429" in err or "rate" in err.lower() or "limit" in err.lower()
        usage = last.get("usage") if isinstance(last.get("usage"), dict) else {}
        rec = {
            "ts": _utc_now(),
            "ts_local": _shanghai_now(),
            "tag": tag,
            "slug": slug,
            "ok": bool(last.get("ok")),
            "attempt": attempt,
            "temperature": temperature,
            "model": last.get("model") or cfg.model,
            "duration_s": round(time.monotonic() - t0, 3),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "error": redact_secrets(err, cfg.api_key)[:300] if err else "",
        }
        if run_log is not None:
            append_jsonl(run_log, rec)
        if last.get("ok"):
            with _rate_lock:
                _rate_errors = max(0, _rate_errors - 1)
            return last
        if is_rate:
            with _rate_lock:
                _rate_errors += 1
                backoff = min(60.0, 2.0 ** attempt + _rate_errors)
            time.sleep(backoff)
            continue
        break
    return last


# ---------------------------------------------------------------------------
# Catalog generation
# ---------------------------------------------------------------------------

def generate_catalog_batch(
    *,
    category: str,
    existing_slugs: set[str],
    cfg: MiniMaxConfig,
    batch_size: int = 20,
    run_log: Path | None = None,
) -> list[dict[str, Any]]:
    avoid = ", ".join(sorted(existing_slugs)[:80])
    user = (
        f"Category: {category}\n"
        f"Return about {batch_size} distinct well-known problems in this category.\n"
        f"Do NOT repeat these existing slugs: {avoid or '(none)'}\n"
        f"Allowed categories (use exactly '{category}'): {', '.join(CATEGORIES)}\n"
    )
    resp = _llm(
        [
            {"role": "system", "content": SYSTEM_CATALOG},
            {"role": "user", "content": user},
        ],
        cfg=cfg,
        temperature=0.7,
        max_tokens=4096,
        timeout_s=LLM_TIMEOUT_S,
        run_log=run_log,
        tag="catalog",
        slug=category,
    )
    if not resp.get("ok"):
        return []
    rows: list[dict[str, Any]] = []
    for item in _extract_json_array(str(resp.get("content") or "")):
        if not isinstance(item, dict):
            continue
        slug = str(item.get("slug") or "").strip().lower().replace("_", "-").replace(" ", "-")
        slug = re.sub(r"[^a-z0-9\-]", "", slug)
        if not _SLUG_RE.match(slug) or slug in existing_slugs:
            continue
        rows.append(
            {
                "slug": slug,
                "title": str(item.get("title") or slug),
                "category": category,
                "statement": str(item.get("statement") or "")[:500],
            }
        )
        existing_slugs.add(slug)
    return rows


def cmd_catalog(
    *,
    corpus_dir: Path,
    target: int,
    env_file: Path | None,
    run_log: Path,
    scratch: Path,
) -> int:
    ensure_dirs(corpus_dir, scratch)
    catalog_path = corpus_dir / "catalog.jsonl"
    cfg = load_minimax_config(env_file=env_file)
    rows = load_catalog(catalog_path)
    existing = {str(r["slug"]) for r in rows}
    print(json.dumps({"event": "catalog_start", "have": len(rows), "target": target}))
    cats = list(CATEGORIES)
    idx = 0
    while len(rows) < target:
        cat = cats[idx % len(cats)]
        idx += 1
        need = min(25, target - len(rows))
        batch = generate_catalog_batch(
            category=cat,
            existing_slugs=existing,
            cfg=cfg,
            batch_size=need,
            run_log=run_log,
        )
        if not batch:
            # try next category; if we spin without progress, stop
            if idx > len(cats) * 3 and len(rows) == len(existing):
                break
            continue
        rows.extend(batch)
        save_catalog(catalog_path, rows)
        print(
            json.dumps(
                {
                    "event": "catalog_batch",
                    "category": cat,
                    "added": len(batch),
                    "total": len(rows),
                }
            )
        )
    save_catalog(catalog_path, rows)
    # harness doc
    readme = corpus_dir / "HARNESS.md"
    if not readme.is_file():
        readme.write_text(_HARNESS_MD, encoding="utf-8")
    print(json.dumps({"event": "catalog_done", "total": len(rows), "path": str(catalog_path)}))
    return 0


_HARNESS_MD = """# LeetCode Aura corpus harness

## Layout

- `catalog.jsonl` — problem index (`slug`, `title`, `category`, `statement`)
- `<slug>/problem.md` — statement adapted to this harness
- `<slug>/ref.py` — Python reference; run → stdout JSON → `tests.json`
- `<slug>/tests.json` — `[{id, input, expected}, ...]` measured from ref.py
- `<slug>/solution.aura` / `solution_N.aura` — MiniMax Aura candidates
- `<slug>/meta.json` — measured parse/run/pass + token usage (facts only)

## Stdin-less Aura convention

1. Define `(solve ...)` for the problem.
2. Embed test inputs as literals; for each case `i` print one line:
   `CASEi=<value>` via `(display "CASEi=")(display ...)(newline)`.
3. Expected values live **only** in `tests.json` — do not treat hardcoded
   `display` of expected answers as a correct solution (anti-hardcode).

## Comparison

Host parses `CASEi=` lines from Aura stdout and compares string equality to
`tests.json[].expected` (canonical JSON literals from ref.py).
"""


# ---------------------------------------------------------------------------
# Per-problem generation
# ---------------------------------------------------------------------------

@dataclass
class BurnConfig:
    corpus_dir: Path
    scratch: Path
    run_log: Path
    aura_bin: str
    env_file: Path | None
    workers: int = DEFAULT_WORKERS
    variants: int = DEFAULT_VARIANTS
    llm_timeout_s: float = LLM_TIMEOUT_S
    aura_timeout_s: float = AURA_TIMEOUT_S
    py_timeout_s: float = PY_TIMEOUT_S
    temperatures: list[float] = field(default_factory=lambda: [0.3, 0.7, 0.95])
    continuous: bool = False
    limit: int | None = None
    catalog_extend_batch: int = 40
    stop_flag: Path | None = None
    auto_commit: bool = False
    commit_every: int = 20


def problem_dir(corpus: Path, slug: str) -> Path:
    return corpus / slug


def _run_subprocess(
    cmd: list[str],
    *,
    timeout_s: float,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    t0 = time.monotonic()
    try:
        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=str(cwd) if cwd else None,
            env=env,
        )
        return {
            "ok": cp.returncode == 0,
            "exit_code": cp.returncode,
            "stdout": cp.stdout or "",
            "stderr": (cp.stderr or "")[:2000],
            "duration_s": round(time.monotonic() - t0, 3),
            "timeout": False,
        }
    except subprocess.TimeoutExpired as exc:
        out = ""
        err = "timeout"
        if exc.stdout:
            out = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else str(exc.stdout)
        if exc.stderr:
            err = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else str(exc.stderr)
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": out,
            "stderr": (err or "timeout")[:2000],
            "duration_s": round(time.monotonic() - t0, 3),
            "timeout": True,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "exit_code": -2,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}"[:2000],
            "duration_s": round(time.monotonic() - t0, 3),
            "timeout": False,
        }


def generate_problem_md(
    entry: dict[str, Any],
    *,
    cfg: MiniMaxConfig,
    bc: BurnConfig,
) -> str:
    user = (
        f"Title: {entry.get('title')}\n"
        f"Slug: {entry.get('slug')}\n"
        f"Category: {entry.get('category')}\n"
        f"Summary: {entry.get('statement')}\n"
        "Write problem.md content now."
    )
    resp = _llm(
        [
            {"role": "system", "content": SYSTEM_PROBLEM_MD},
            {"role": "user", "content": user},
        ],
        cfg=cfg,
        temperature=0.3,
        max_tokens=1200,
        timeout_s=bc.llm_timeout_s,
        run_log=bc.run_log,
        tag="problem_md",
        slug=str(entry.get("slug")),
    )
    if not resp.get("ok"):
        return (
            f"# {entry.get('title')}\n\n"
            f"{entry.get('statement')}\n\n"
            f"## Harness\nDefine `(solve ...)` and print `CASEi=` lines for embedded tests.\n"
        )
    return str(resp.get("content") or "").strip() + "\n"


def generate_ref_py(
    entry: dict[str, Any],
    problem_md: str,
    *,
    cfg: MiniMaxConfig,
    bc: BurnConfig,
) -> tuple[str, dict[str, Any]]:
    user = (
        f"Problem slug: {entry.get('slug')}\n"
        f"Title: {entry.get('title')}\n"
        f"Category: {entry.get('category')}\n"
        f"Statement:\n{problem_md[:3000]}\n"
        "Write ref.py now."
    )
    resp = _llm(
        [
            {"role": "system", "content": SYSTEM_REF},
            {"role": "user", "content": user},
        ],
        cfg=cfg,
        temperature=0.2,
        max_tokens=3500,
        timeout_s=bc.llm_timeout_s,
        run_log=bc.run_log,
        tag="ref_py",
        slug=str(entry.get("slug")),
    )
    meta = {
        "ok": bool(resp.get("ok")),
        "error": resp.get("error") or "",
        "usage": resp.get("usage") or {},
        "model": resp.get("model") or cfg.model,
    }
    if not resp.get("ok"):
        return "", meta
    return _extract_python(str(resp.get("content") or "")), meta


def run_ref_py(ref_path: Path, tests_path: Path, *, timeout_s: float) -> dict[str, Any]:
    ref_abs = ref_path.resolve()
    r = _run_subprocess(
        ["python3", str(ref_abs)],
        timeout_s=timeout_s,
        cwd=str(ref_abs.parent),
    )
    result: dict[str, Any] = {
        "ref_ok": False,
        "exit_code": r["exit_code"],
        "stderr": r["stderr"][:500],
        "duration_s": r["duration_s"],
        "timeout": r["timeout"],
        "n_tests": 0,
    }
    if not r["ok"]:
        return result
    text = (r["stdout"] or "").strip()
    # find JSON array
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        result["stderr"] = (result["stderr"] + " | no_json_array").strip(" |")
        return result
    try:
        tests = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        result["stderr"] = f"json_decode: {exc}"
        return result
    if not isinstance(tests, list) or not tests:
        result["stderr"] = "empty_tests"
        return result
    # normalize
    norm: list[dict[str, Any]] = []
    for i, t in enumerate(tests):
        if not isinstance(t, dict):
            continue
        exp = t.get("expected")
        if not isinstance(exp, str):
            exp = json.dumps(exp, separators=(",", ":"), ensure_ascii=False)
        norm.append(
            {
                "id": int(t.get("id", i)),
                "input": t.get("input"),
                "expected": exp,
            }
        )
    if not norm:
        result["stderr"] = "no_normalized_tests"
        return result
    tests_path.write_text(json.dumps(norm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["ref_ok"] = True
    result["n_tests"] = len(norm)
    return result


def generate_aura_solution(
    entry: dict[str, Any],
    problem_md: str,
    tests: list[dict[str, Any]],
    *,
    cfg: MiniMaxConfig,
    bc: BurnConfig,
    temperature: float,
    variant: int,
) -> tuple[str, dict[str, Any]]:
    cases_desc = []
    for t in tests:
        cases_desc.append(
            f"- CASE{t.get('id', 0)} input={json.dumps(t.get('input'), ensure_ascii=False)}"
        )
    user = (
        f"Slug: {entry.get('slug')}\nTitle: {entry.get('title')}\n"
        f"Category: {entry.get('category')}\n\n"
        f"Problem:\n{problem_md[:2500]}\n\n"
        f"Embedded test INPUTS (print CASEi= after calling solve; do not hardcode expected):\n"
        + "\n".join(cases_desc)
        + "\n\nWrite solution.aura now."
    )
    resp = _llm(
        [
            {"role": "system", "content": SYSTEM_AURA},
            {"role": "user", "content": user},
        ],
        cfg=cfg,
        temperature=temperature,
        max_tokens=4000,
        timeout_s=bc.llm_timeout_s,
        run_log=bc.run_log,
        tag=f"aura_v{variant}",
        slug=str(entry.get("slug")),
    )
    meta = {
        "ok": bool(resp.get("ok")),
        "error": resp.get("error") or "",
        "usage": resp.get("usage") or {},
        "model": resp.get("model") or cfg.model,
        "temperature": temperature,
        "variant": variant,
    }
    if not resp.get("ok"):
        return "", meta
    src = extract_aura_source(str(resp.get("content") or ""))
    return src, meta


def run_aura_solution(
    aura_path: Path,
    tests: list[dict[str, Any]],
    *,
    aura_bin: str,
    timeout_s: float,
) -> dict[str, Any]:
    r = _run_subprocess([aura_bin, str(aura_path.resolve())], timeout_s=timeout_s)
    stderr = r["stderr"]
    stdout = r["stdout"]
    parse_ok = (not r["timeout"]) and (
        r["exit_code"] == 0
        or not re.search(r"(?i)syntax|parse error|unbound variable", stderr)
    )
    # stricter parse: exit 0 and no error markers
    has_err = bool(re.search(r"(?i)\berror:|\bsyntax\b|\bunbound variable\b", stderr))
    run_ok = r["exit_code"] == 0 and not r["timeout"] and not has_err
    parse_ok = run_ok or (r["exit_code"] == 0 and not has_err)

    got: dict[int, str] = {}
    for m in _CASE_RE.finditer(stdout):
        got[int(m.group(1))] = m.group(2).strip()

    passed = 0
    total = len(tests)
    details = []
    for t in tests:
        tid = int(t.get("id", 0))
        exp = str(t.get("expected", ""))
        actual = got.get(tid)
        ok = actual is not None and _values_match(actual, exp)
        if ok:
            passed += 1
        details.append({"id": tid, "ok": ok, "expected": exp, "got": actual})

    return {
        "parse_ok": bool(parse_ok and not has_err),
        "run_ok": bool(run_ok),
        "exit_code": r["exit_code"],
        "timeout": r["timeout"],
        "duration_s": r["duration_s"],
        "stdout_snippet": stdout[:800],
        "stderr_snippet": stderr[:500],
        "tests_passed": passed,
        "tests_total": total,
        "case_details": details,
    }


def _values_match(got: str, expected: str) -> bool:
    g = got.strip()
    e = expected.strip()
    if g == e:
        return True
    # Aura may print True/#t vs JSON true
    aliases = {
        "#t": "true",
        "#f": "false",
        "True": "true",
        "False": "false",
        "nil": "null",
        "()": "[]",
    }
    g2 = aliases.get(g, g)
    e2 = aliases.get(e, e)
    if g2 == e2:
        return True
    # try json parse both
    try:
        return json.loads(g) == json.loads(e)
    except Exception:
        pass
    # strip quotes
    if len(e) >= 2 and e[0] == '"' and e[-1] == '"' and g == json.loads(e):
        return True
    return False


def _solution_name(variant: int) -> str:
    if variant <= 1:
        return "solution.aura"
    return f"solution_{variant}.aura"


def _load_meta(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"variants": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"variants": []}


def _should_stop(bc: BurnConfig) -> bool:
    if bc.stop_flag and bc.stop_flag.is_file():
        return True
    return False


def process_problem(entry: dict[str, Any], bc: BurnConfig, cfg: MiniMaxConfig) -> dict[str, Any]:
    slug = str(entry["slug"])
    pdir = problem_dir(bc.corpus_dir, slug)
    pdir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {"slug": slug, "actions": []}

    if _should_stop(bc):
        summary["stopped"] = True
        return summary

    problem_path = pdir / "problem.md"
    if not problem_path.is_file():
        md = generate_problem_md(entry, cfg=cfg, bc=bc)
        problem_path.write_text(md, encoding="utf-8")
        summary["actions"].append("problem_md")
    problem_md = problem_path.read_text(encoding="utf-8")

    ref_path = pdir / "ref.py"
    tests_path = pdir / "tests.json"
    ref_meta: dict[str, Any] = {}
    if not tests_path.is_file():
        if not ref_path.is_file():
            src, ref_meta = generate_ref_py(entry, problem_md, cfg=cfg, bc=bc)
            if src.strip():
                ref_path.write_text(src, encoding="utf-8")
                summary["actions"].append("ref_py")
            else:
                summary["ref_failed"] = ref_meta.get("error") or "empty"
                _write_meta_partial(pdir, entry, ref_meta, None)
                return summary
        run_info = run_ref_py(ref_path, tests_path, timeout_s=bc.py_timeout_s)
        summary["actions"].append("run_ref")
        summary["ref_run"] = {k: run_info[k] for k in ("ref_ok", "exit_code", "n_tests", "stderr") if k in run_info}
        if not run_info.get("ref_ok"):
            # quarantine bad ref so a later pass regenerates
            bad = pdir / "ref.py.bad"
            try:
                if ref_path.is_file():
                    ref_path.replace(bad)
            except OSError:
                pass
            _write_meta_partial(pdir, entry, ref_meta, run_info)
            return summary

    if not tests_path.is_file():
        summary["ref_failed"] = "no_tests"
        return summary

    try:
        tests = json.loads(tests_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        summary["ref_failed"] = "bad_tests_json"
        return summary
    if not isinstance(tests, list):
        summary["ref_failed"] = "tests_not_list"
        return summary

    meta = _load_meta(pdir / "meta.json")
    meta.setdefault("slug", slug)
    meta.setdefault("title", entry.get("title"))
    meta.setdefault("category", entry.get("category"))
    meta.setdefault("variants", [])
    existing_vars = {
        int(v.get("variant", 0))
        for v in meta["variants"]
        if isinstance(v, dict) and v.get("aura_file")
    }

    temps = bc.temperatures
    for v_i in range(1, bc.variants + 1):
        if _should_stop(bc):
            summary["stopped"] = True
            break
        sname = _solution_name(v_i)
        spath = pdir / sname
        if spath.is_file() and v_i in existing_vars:
            continue
        if spath.is_file() and any(
            isinstance(v, dict) and v.get("aura_file") == sname for v in meta["variants"]
        ):
            continue
        temp = temps[(v_i - 1) % len(temps)]
        src, gen_meta = generate_aura_solution(
            entry,
            problem_md,
            tests,
            cfg=cfg,
            bc=bc,
            temperature=temp,
            variant=v_i,
        )
        summary["actions"].append(f"aura_v{v_i}")
        if not src.strip():
            meta["variants"] = [v for v in meta["variants"] if v.get("variant") != v_i]
            meta["variants"].append(
                {
                    "variant": v_i,
                    "aura_file": sname,
                    "temperature": temp,
                    "model": gen_meta.get("model"),
                    "ts": _utc_now(),
                    "ts_local": _shanghai_now(),
                    "llm_ok": False,
                    "error": gen_meta.get("error"),
                    "usage": gen_meta.get("usage") or {},
                    "parse_ok": False,
                    "run_ok": False,
                    "tests_passed": 0,
                    "tests_total": len(tests),
                }
            )
            continue
        spath.write_text(src, encoding="utf-8")
        run = run_aura_solution(
            spath, tests, aura_bin=bc.aura_bin, timeout_s=bc.aura_timeout_s
        )
        meta["variants"] = [v for v in meta["variants"] if v.get("variant") != v_i]
        meta["variants"].append(
            {
                "variant": v_i,
                "aura_file": sname,
                "temperature": temp,
                "model": gen_meta.get("model"),
                "ts": _utc_now(),
                "ts_local": _shanghai_now(),
                "llm_ok": True,
                "usage": gen_meta.get("usage") or {},
                "parse_ok": run["parse_ok"],
                "run_ok": run["run_ok"],
                "exit_code": run["exit_code"],
                "timeout": run["timeout"],
                "duration_s": run["duration_s"],
                "tests_passed": run["tests_passed"],
                "tests_total": run["tests_total"],
                "stderr_snippet": run["stderr_snippet"],
                "stdout_snippet": run["stdout_snippet"][:400],
            }
        )
        summary.setdefault("variants_done", []).append(
            {
                "variant": v_i,
                "parse_ok": run["parse_ok"],
                "run_ok": run["run_ok"],
                "passed": run["tests_passed"],
                "total": run["tests_total"],
            }
        )

    meta["updated_at"] = _utc_now()
    meta["updated_at_local"] = _shanghai_now()
    (pdir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def _write_meta_partial(
    pdir: Path,
    entry: dict[str, Any],
    ref_meta: dict[str, Any] | None,
    run_info: dict[str, Any] | None,
) -> None:
    meta = _load_meta(pdir / "meta.json")
    meta["slug"] = entry.get("slug")
    meta["title"] = entry.get("title")
    meta["category"] = entry.get("category")
    meta["ref"] = {
        "llm": ref_meta or {},
        "run": run_info or {},
        "ts": _utc_now(),
    }
    meta["updated_at"] = _utc_now()
    (pdir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def problem_needs_work(entry: dict[str, Any], bc: BurnConfig) -> bool:
    pdir = problem_dir(bc.corpus_dir, str(entry["slug"]))
    if not (pdir / "tests.json").is_file():
        return True
    meta = _load_meta(pdir / "meta.json")
    done = {
        int(v.get("variant", 0))
        for v in meta.get("variants", [])
        if isinstance(v, dict) and v.get("aura_file") and (pdir / str(v["aura_file"])).is_file()
    }
    for v_i in range(1, bc.variants + 1):
        if v_i not in done:
            # also check file existence without meta
            if not (pdir / _solution_name(v_i)).is_file():
                return True
            if v_i not in done:
                return True
    return False


def extend_catalog(bc: BurnConfig, cfg: MiniMaxConfig, target_extra: int) -> int:
    catalog_path = bc.corpus_dir / "catalog.jsonl"
    rows = load_catalog(catalog_path)
    existing = {str(r["slug"]) for r in rows}
    before = len(rows)
    for cat in CATEGORIES:
        if len(rows) - before >= target_extra:
            break
        batch = generate_catalog_batch(
            category=cat,
            existing_slugs=existing,
            cfg=cfg,
            batch_size=min(15, target_extra - (len(rows) - before)),
            run_log=bc.run_log,
        )
        rows.extend(batch)
        save_catalog(catalog_path, rows)
    return len(rows) - before


def bump_variants_for_done(bc: BurnConfig) -> None:
    """When catalog exhausted, raise variants so we keep generating new .aura files."""
    # handled by increasing bc.variants in continuous loop
    pass



def maybe_auto_commit(bc: BurnConfig, *, note: str) -> None:
    """Commit+push corpus/leetcode only (product layer). Best-effort; log failures."""
    if not bc.auto_commit:
        return
    repo = Path.cwd()
    try:
        subprocess.run(
            ["git", "add", "corpus/leetcode", "src/aura_build/corpus_gen.py"],
            cwd=repo,
            check=False,
            capture_output=True,
            timeout=60,
        )
        st = subprocess.run(
            ["git", "status", "--porcelain", "corpus/leetcode"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if not (st.stdout or "").strip():
            return
        msg = f"chore(corpus): leetcode burn chunk — {note}"
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=repo,
            check=False,
            capture_output=True,
            timeout=120,
        )
        subprocess.run(
            ["git", "push", "origin", "HEAD"],
            cwd=repo,
            check=False,
            capture_output=True,
            timeout=180,
        )
        print(json.dumps({"event": "auto_commit", "note": note, "ts_local": _shanghai_now()}))
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"event": "auto_commit_error", "error": str(exc)[:200]}))


def cmd_burn(bc: BurnConfig) -> int:
    ensure_dirs(bc.corpus_dir, bc.scratch)
    readme = bc.corpus_dir / "HARNESS.md"
    if not readme.is_file():
        readme.write_text(_HARNESS_MD, encoding="utf-8")

    cfg = load_minimax_config(env_file=bc.env_file)
    aura = resolve_aura_bin(bc.aura_bin) or bc.aura_bin
    if not Path(aura).is_file():
        print(json.dumps({"error": "aura_bin_missing", "path": aura}))
        return 2
    bc.aura_bin = aura

    stop_flag = bc.stop_flag or (bc.scratch / "STOP")
    bc.stop_flag = stop_flag
    if stop_flag.is_file():
        stop_flag.unlink()

    pid_path = bc.scratch / "burn.pid"
    pid_path.write_text(str(os.getpid()) + "\n", encoding="utf-8")

    processed = 0
    round_id = 0
    try:
        while True:
            if _should_stop(bc):
                print(json.dumps({"event": "stop_flag", "processed": processed}))
                break
            catalog_path = bc.corpus_dir / "catalog.jsonl"
            rows = load_catalog(catalog_path)
            if not rows:
                print(json.dumps({"event": "catalog_empty_generating"}))
                cmd_catalog(
                    corpus_dir=bc.corpus_dir,
                    target=min(60, DEFAULT_CATALOG_TARGET),
                    env_file=bc.env_file,
                    run_log=bc.run_log,
                    scratch=bc.scratch,
                )
                rows = load_catalog(catalog_path)

            todo = [r for r in rows if problem_needs_work(r, bc)]
            if not todo:
                if not bc.continuous:
                    print(json.dumps({"event": "done_no_work", "processed": processed}))
                    break
                # extend catalog then bump variants
                added = extend_catalog(bc, cfg, bc.catalog_extend_batch)
                if added == 0:
                    bc.variants += 1
                    print(
                        json.dumps(
                            {
                                "event": "bump_variants",
                                "variants": bc.variants,
                                "round": round_id,
                            }
                        )
                    )
                else:
                    print(json.dumps({"event": "catalog_extended", "added": added}))
                round_id += 1
                continue

            if bc.limit is not None:
                remain = bc.limit - processed
                if remain <= 0:
                    break
                todo = todo[:remain]

            print(
                json.dumps(
                    {
                        "event": "burn_batch",
                        "todo": len(todo),
                        "workers": bc.workers,
                        "variants": bc.variants,
                        "ts_local": _shanghai_now(),
                    }
                )
            )

            with ThreadPoolExecutor(max_workers=max(1, bc.workers)) as pool:
                futs = {
                    pool.submit(process_problem, entry, bc, cfg): entry.get("slug")
                    for entry in todo
                }
                for fut in as_completed(futs):
                    slug = futs[fut]
                    try:
                        result = fut.result()
                    except Exception as exc:  # noqa: BLE001
                        result = {
                            "slug": slug,
                            "error": f"{type(exc).__name__}: {exc}",
                            "trace": traceback.format_exc()[-500:],
                        }
                    processed += 1
                    print(json.dumps({"event": "problem_done", **result}, ensure_ascii=False))
                    if bc.auto_commit:
                        every = max(1, bc.commit_every)
                        bucket = processed // every
                        if bucket > getattr(bc, "_last_commit_bucket", 0):
                            bc._last_commit_bucket = bucket  # type: ignore[attr-defined]
                            maybe_auto_commit(bc, note=f"processed={processed}")
                    if bc.limit is not None and processed >= bc.limit:
                        # cancel remaining roughly by setting stop flag
                        stop_flag.write_text("limit\n", encoding="utf-8")

            if bc.limit is not None and processed >= bc.limit:
                print(json.dumps({"event": "limit_reached", "processed": processed}))
                break
            if not bc.continuous:
                # one pass over current todo
                still = [r for r in load_catalog(catalog_path) if problem_needs_work(r, bc)]
                if not still:
                    print(json.dumps({"event": "pass_complete", "processed": processed}))
                    break
            round_id += 1
    finally:
        if pid_path.is_file():
            try:
                cur = pid_path.read_text(encoding="utf-8").strip()
                if cur == str(os.getpid()):
                    pid_path.unlink()
            except OSError:
                pass

    return 0




# ---------------------------------------------------------------------------
# MiniMax repair (stderr + failing CASE diffs → solution_repair.aura)
# ---------------------------------------------------------------------------

REPAIR_VARIANT = 90  # meta variant id for solution_repair.aura
REPAIR_AURA_FILE = "solution_repair.aura"


def _best_variant_row(meta: dict[str, Any]) -> dict[str, Any] | None:
    best = None
    best_key = (-1.0, -1)
    for v in meta.get("variants") or []:
        if not isinstance(v, dict) or not v.get("aura_file"):
            continue
        tp = int(v.get("tests_passed") or 0)
        tt = int(v.get("tests_total") or 0)
        ratio = (tp / tt) if tt else -1.0
        key = (ratio, tp)
        if key > best_key:
            best_key = key
            best = v
    return best


def problem_needs_repair(entry: dict[str, Any], corpus_dir: Path) -> bool:
    """True when tests exist and best variant is not full pass."""
    pdir = problem_dir(corpus_dir, str(entry["slug"]))
    tests_path = pdir / "tests.json"
    if not tests_path.is_file():
        return False
    meta = _load_meta(pdir / "meta.json")
    best = _best_variant_row(meta)
    if best is None:
        # no scored variant yet — still repairable if a solution file exists
        return any((pdir / n).is_file() for n in ("solution.aura", "solution_2.aura", REPAIR_AURA_FILE))
    tp = int(best.get("tests_passed") or 0)
    tt = int(best.get("tests_total") or 0)
    return tt > 0 and tp < tt


def generate_aura_repair(
    entry: dict[str, Any],
    problem_md: str,
    tests: list[dict[str, Any]],
    *,
    prior_src: str,
    stderr_snippet: str,
    case_details: list[dict[str, Any]],
    cfg: MiniMaxConfig,
    bc: BurnConfig,
    temperature: float,
) -> tuple[str, dict[str, Any]]:
    fail_lines = []
    for d in case_details:
        if d.get("ok"):
            continue
        tid = d.get("id")
        # Include got vs expected for the repair prompt only — solution must still call solve.
        fail_lines.append(
            f"- CASE{tid} input={json.dumps(next((t.get('input') for t in tests if int(t.get('id', -1)) == int(tid)), None), ensure_ascii=False)}"
            f" got={d.get('got')!r} expected={d.get('expected')!r}"
        )
    if not fail_lines:
        fail_lines = ["(no CASE diffs; rely on stderr)"]
    user = (
        f"Slug: {entry.get('slug')}\nTitle: {entry.get('title')}\n"
        f"Category: {entry.get('category')}\n\n"
        f"Problem:\n{problem_md[:2000]}\n\n"
        f"Prior Aura source (fix):\n```aura\n{prior_src[:6000]}\n```\n\n"
        f"stderr (truncated):\n{stderr_snippet[:1200]}\n\n"
        f"Failing CASE diffs (fix; do not hardcode expected into display):\n"
        + "\n".join(fail_lines[:16])
        + "\n\nWrite a repaired complete solution.aura now."
    )
    resp = _llm(
        [
            {"role": "system", "content": SYSTEM_AURA_REPAIR},
            {"role": "user", "content": user},
        ],
        cfg=cfg,
        temperature=temperature,
        max_tokens=4000,
        timeout_s=bc.llm_timeout_s,
        run_log=bc.run_log,
        tag="aura_repair",
        slug=str(entry.get("slug")),
    )
    meta = {
        "ok": bool(resp.get("ok")),
        "error": resp.get("error") or "",
        "usage": resp.get("usage") or {},
        "model": resp.get("model") or cfg.model,
        "temperature": temperature,
        "variant": REPAIR_VARIANT,
    }
    if not resp.get("ok"):
        return "", meta
    src = extract_aura_source(str(resp.get("content") or ""))
    return src, meta


def repair_problem(entry: dict[str, Any], bc: BurnConfig, cfg: MiniMaxConfig) -> dict[str, Any]:
    slug = str(entry["slug"])
    pdir = problem_dir(bc.corpus_dir, slug)
    summary: dict[str, Any] = {"slug": slug, "actions": []}
    if _should_stop(bc):
        summary["stopped"] = True
        return summary
    tests_path = pdir / "tests.json"
    problem_path = pdir / "problem.md"
    if not tests_path.is_file() or not problem_path.is_file():
        summary["skipped"] = "missing_tests_or_problem"
        return summary
    try:
        tests = json.loads(tests_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        summary["skipped"] = "bad_tests_json"
        return summary
    if not isinstance(tests, list) or not tests:
        summary["skipped"] = "empty_tests"
        return summary

    meta = _load_meta(pdir / "meta.json")
    best = _best_variant_row(meta)
    prior_name = str(best.get("aura_file")) if best else "solution.aura"
    prior_path = pdir / prior_name
    if not prior_path.is_file():
        for cand in ("solution.aura", "solution_2.aura", REPAIR_AURA_FILE):
            if (pdir / cand).is_file():
                prior_path = pdir / cand
                prior_name = cand
                break
    if not prior_path.is_file():
        summary["skipped"] = "no_prior_solution"
        return summary

    prior_src = prior_path.read_text(encoding="utf-8")
    # Score prior (fresh) to get case_details + stderr for the prompt.
    prior_run = run_aura_solution(prior_path, tests, aura_bin=bc.aura_bin, timeout_s=bc.aura_timeout_s)
    summary["prior"] = {
        "aura_file": prior_name,
        "tests_passed": prior_run.get("tests_passed"),
        "tests_total": prior_run.get("tests_total"),
    }
    if int(prior_run.get("tests_passed") or 0) >= len(tests) and prior_run.get("run_ok"):
        summary["skipped"] = "already_full"
        return summary

    temp = (bc.temperatures or [0.4])[0]
    problem_md = problem_path.read_text(encoding="utf-8")
    src, gen_meta = generate_aura_repair(
        entry,
        problem_md,
        tests,
        prior_src=prior_src,
        stderr_snippet=str(prior_run.get("stderr_snippet") or ""),
        case_details=list(prior_run.get("case_details") or []),
        cfg=cfg,
        bc=bc,
        temperature=temp,
    )
    summary["actions"].append("aura_repair")
    if not src.strip():
        summary["llm_ok"] = False
        summary["error"] = gen_meta.get("error") or "empty"
        return summary

    # Ensure compat require if unbound names look like compat exports and missing.
    if '(require "compat"' not in src and "unbound variable" in str(prior_run.get("stderr_snippet") or ""):
        src = '(require "compat" all:)\n' + src

    out_path = pdir / REPAIR_AURA_FILE
    # Stage to scratch then promote so a crash mid-write does not clobber a prior repair.
    staged = bc.scratch / f"repair_stage_{slug}.aura"
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(src, encoding="utf-8")
    run = run_aura_solution(staged, tests, aura_bin=bc.aura_bin, timeout_s=bc.aura_timeout_s)
    prior_passed = int(prior_run.get("tests_passed") or 0)
    new_passed = int(run.get("tests_passed") or 0)
    # Keep prior solution_repair if it was strictly better than this attempt.
    existing_repair_passed = -1
    if out_path.is_file():
        try:
            existing_repair_passed = int(
                run_aura_solution(out_path, tests, aura_bin=bc.aura_bin, timeout_s=bc.aura_timeout_s).get("tests_passed") or 0
            )
        except Exception:
            existing_repair_passed = -1
    if new_passed >= existing_repair_passed:
        out_path.write_text(src, encoding="utf-8")
    else:
        # re-score the kept file for meta honesty
        run = run_aura_solution(out_path, tests, aura_bin=bc.aura_bin, timeout_s=bc.aura_timeout_s)
        new_passed = int(run.get("tests_passed") or 0)
    try:
        staged.unlink()
    except OSError:
        pass
    summary["actions"].append("run_repair")
    summary["repair"] = {
        "tests_passed": run.get("tests_passed"),
        "tests_total": run.get("tests_total"),
        "parse_ok": run.get("parse_ok"),
        "run_ok": run.get("run_ok"),
        "delta": int(run.get("tests_passed") or 0) - int(prior_run.get("tests_passed") or 0),
    }

    row = {
        "variant": REPAIR_VARIANT,
        "aura_file": REPAIR_AURA_FILE,
        "temperature": temp,
        "model": gen_meta.get("model"),
        "ts": _utc_now(),
        "ts_local": _shanghai_now(),
        "llm_ok": True,
        "usage": gen_meta.get("usage") or {},
        "parse_ok": run.get("parse_ok"),
        "run_ok": run.get("run_ok"),
        "exit_code": run.get("exit_code"),
        "timeout": run.get("timeout"),
        "duration_s": run.get("duration_s"),
        "tests_passed": run.get("tests_passed"),
        "tests_total": run.get("tests_total"),
        "stderr_snippet": run.get("stderr_snippet"),
        "stdout_snippet": run.get("stdout_snippet"),
        "repair_of": prior_name,
        "prior_passed": prior_run.get("tests_passed"),
    }
    meta.setdefault("variants", [])
    meta["variants"] = [v for v in meta["variants"] if not (isinstance(v, dict) and v.get("aura_file") == REPAIR_AURA_FILE)]
    meta["variants"].append(row)
    meta["slug"] = slug
    meta["title"] = entry.get("title")
    meta["category"] = entry.get("category")
    meta["updated_at"] = _utc_now()
    meta["updated_at_local"] = _shanghai_now()
    (pdir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary["llm_ok"] = True
    summary["improved"] = bool(summary["repair"]["delta"] > 0)
    return summary


def cmd_repair(bc: BurnConfig) -> int:
    """Repair non-full corpus problems via MiniMax using stderr + failing CASE diffs."""
    ensure_dirs(bc.corpus_dir, bc.scratch)
    stop_flag = bc.stop_flag or (bc.scratch / "STOP")
    bc.stop_flag = stop_flag
    if stop_flag.is_file():
        try:
            stop_flag.unlink()
        except OSError:
            pass
    cfg = load_minimax_config(env_file=bc.env_file)
    rows = load_catalog(bc.corpus_dir / "catalog.jsonl")
    todo = [r for r in rows if problem_needs_repair(r, bc.corpus_dir)]

    # Prefer partials (some passes) then zeros; stable catalog order within band.
    def _rank(entry: dict[str, Any]) -> tuple:
        pdir = problem_dir(bc.corpus_dir, str(entry["slug"]))
        meta = _load_meta(pdir / "meta.json")
        best = _best_variant_row(meta) or {}
        tp = int(best.get("tests_passed") or 0)
        tt = int(best.get("tests_total") or 0)
        # higher tp first among non-full; then higher tt
        return (0 if tp > 0 else 1, -tp, -tt, str(entry["slug"]))

    todo.sort(key=_rank)
    if bc.limit is not None:
        todo = todo[: max(0, int(bc.limit))]

    print(
        json.dumps(
            {
                "event": "repair_start",
                "todo": len(todo),
                "workers": bc.workers,
                "aura_bin": bc.aura_bin,
                "ts_local": _shanghai_now(),
            }
        )
    )
    processed = 0
    improved = 0
    deltas = 0
    with ThreadPoolExecutor(max_workers=max(1, bc.workers)) as pool:
        futs = {pool.submit(repair_problem, entry, bc, cfg): entry.get("slug") for entry in todo}
        for fut in as_completed(futs):
            slug = futs[fut]
            try:
                result = fut.result()
            except Exception as exc:  # noqa: BLE001
                result = {
                    "slug": slug,
                    "error": f"{type(exc).__name__}: {exc}",
                    "trace": traceback.format_exc()[-500:],
                }
            processed += 1
            if result.get("improved"):
                improved += 1
                deltas += int(((result.get("repair") or {}).get("delta")) or 0)
            print(json.dumps({"event": "repair_done", **result}, ensure_ascii=False))
            if bc.auto_commit:
                every = max(1, bc.commit_every)
                bucket = processed // every
                if bucket > getattr(bc, "_last_commit_bucket", 0):
                    bc._last_commit_bucket = bucket  # type: ignore[attr-defined]
                    maybe_auto_commit(bc, note=f"repair processed={processed}")
            if _should_stop(bc):
                break
    print(
        json.dumps(
            {
                "event": "repair_complete",
                "processed": processed,
                "improved": improved,
                "sum_delta": deltas,
                "ts_local": _shanghai_now(),
            }
        )
    )
    if bc.auto_commit:
        maybe_auto_commit(bc, note=f"repair final processed={processed}")
    return 0


# ---------------------------------------------------------------------------
# Summary / stop
# ---------------------------------------------------------------------------

def cmd_summary(corpus_dir: Path, run_log: Path | None = None) -> int:
    catalog = load_catalog(corpus_dir / "catalog.jsonl")
    n_problems = 0
    n_variants = 0
    parse_ok = 0
    run_ok = 0
    pass_dist: dict[str, int] = {}
    tokens_prompt = 0
    tokens_completion = 0
    tokens_total = 0
    llm_calls_meta = 0

    for entry in catalog:
        pdir = problem_dir(corpus_dir, str(entry["slug"]))
        if not pdir.is_dir():
            continue
        n_problems += 1
        meta = _load_meta(pdir / "meta.json")
        for v in meta.get("variants", []):
            if not isinstance(v, dict):
                continue
            n_variants += 1
            if v.get("parse_ok"):
                parse_ok += 1
            if v.get("run_ok"):
                run_ok += 1
            tp = int(v.get("tests_passed") or 0)
            tt = int(v.get("tests_total") or 0)
            key = f"{tp}/{tt}"
            pass_dist[key] = pass_dist.get(key, 0) + 1
            usage = v.get("usage") or {}
            if isinstance(usage, dict):
                tokens_prompt += int(usage.get("prompt_tokens") or 0)
                tokens_completion += int(usage.get("completion_tokens") or 0)
                tokens_total += int(usage.get("total_tokens") or 0)
                if usage:
                    llm_calls_meta += 1

    log_stats: dict[str, Any] = {}
    if run_log and run_log.is_file():
        calls = 0
        ok_calls = 0
        t_prompt = 0
        t_comp = 0
        t_total = 0
        t_first = None
        t_last = None
        with run_log.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                calls += 1
                if row.get("ok"):
                    ok_calls += 1
                t_prompt += int(row.get("prompt_tokens") or 0)
                t_comp += int(row.get("completion_tokens") or 0)
                t_total += int(row.get("total_tokens") or 0)
                ts = row.get("ts")
                if ts:
                    if t_first is None:
                        t_first = ts
                    t_last = ts
        hours = None
        if t_first and t_last:
            try:
                fmt = "%Y-%m-%dT%H:%M:%SZ"
                dt0 = datetime.strptime(t_first, fmt).replace(tzinfo=timezone.utc)
                dt1 = datetime.strptime(t_last, fmt).replace(tzinfo=timezone.utc)
                hours = max((dt1 - dt0).total_seconds() / 3600.0, 1e-6)
            except ValueError:
                hours = None
        log_stats = {
            "calls": calls,
            "ok_calls": ok_calls,
            "prompt_tokens": t_prompt,
            "completion_tokens": t_comp,
            "total_tokens": t_total,
            "first_ts": t_first,
            "last_ts": t_last,
            "hours": round(hours, 4) if hours else None,
            "calls_per_hour": round(calls / hours, 2) if hours else None,
            "tokens_per_hour": round(t_total / hours, 2) if hours else None,
        }

    out = {
        "catalog_entries": len(catalog),
        "problem_dirs": n_problems,
        "variants": n_variants,
        "parse_ok": parse_ok,
        "parse_ok_pct": round(100.0 * parse_ok / n_variants, 2) if n_variants else 0.0,
        "run_ok": run_ok,
        "run_ok_pct": round(100.0 * run_ok / n_variants, 2) if n_variants else 0.0,
        "pass_distribution": dict(sorted(pass_dist.items())),
        "tokens_from_meta": {
            "prompt": tokens_prompt,
            "completion": tokens_completion,
            "total": tokens_total,
            "variants_with_usage": llm_calls_meta,
        },
        "run_log": log_stats,
        "ts_local": _shanghai_now(),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_stop(scratch: Path) -> int:
    stop_flag = scratch / "STOP"
    scratch.mkdir(parents=True, exist_ok=True)
    stop_flag.write_text("stop\n", encoding="utf-8")
    pid_path = scratch / "burn.pid"
    killed = False
    if pid_path.is_file():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, signal.SIGTERM)
            killed = True
        except (ValueError, ProcessLookupError, PermissionError) as exc:
            print(json.dumps({"event": "stop", "stop_flag": str(stop_flag), "kill_error": str(exc)}))
            return 0
    print(json.dumps({"event": "stop", "stop_flag": str(stop_flag), "killed": killed, "pid_file": str(pid_path)}))
    return 0


def build_burn_config_from_args(args: Any) -> BurnConfig:
    corpus = Path(getattr(args, "corpus_dir", None) or DEFAULT_CORPUS)
    scratch = Path(getattr(args, "scratch", None) or DEFAULT_SCRATCH)
    run_log = Path(getattr(args, "run_log", None) or (scratch / "run_log.jsonl"))
    temps_raw = getattr(args, "temperatures", None) or "0.3,0.7,0.95"
    temps = [float(x.strip()) for x in str(temps_raw).split(",") if x.strip()]
    return BurnConfig(
        corpus_dir=corpus,
        scratch=scratch,
        run_log=run_log,
        aura_bin=str(getattr(args, "aura_bin", None) or os.environ.get("AURA_BIN") or DEFAULT_AURA_BIN),
        env_file=getattr(args, "env_file", None),
        workers=int(getattr(args, "workers", DEFAULT_WORKERS) or DEFAULT_WORKERS),
        variants=int(getattr(args, "variants", DEFAULT_VARIANTS) or DEFAULT_VARIANTS),
        llm_timeout_s=float(getattr(args, "llm_timeout", LLM_TIMEOUT_S)),
        aura_timeout_s=float(getattr(args, "aura_timeout", AURA_TIMEOUT_S)),
        py_timeout_s=float(getattr(args, "py_timeout", PY_TIMEOUT_S)),
        temperatures=temps or [0.3, 0.7],
        continuous=bool(getattr(args, "continuous", False)),
        limit=getattr(args, "limit", None),
        catalog_extend_batch=int(getattr(args, "catalog_extend", 40) or 40),
        auto_commit=bool(getattr(args, "auto_commit", False)),
        commit_every=int(getattr(args, "commit_every", 20) or 20),
    )
