"""Multi-file Aura PROJECT corpus burner — MiniMax quota into repair targets.

Layout under ``corpus/projects/<slug>/`` aligned with llm-dogfood / combat
``--project`` contracts (GOAL.md + dogfood.json + stub/ + cli_multi).

Expected KEY=value lines live ONLY in tests.json (measured from ref/).
Aura sources must compute scenario outputs via defined APIs (anti-hardcode).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aura_build.minimax import (
    MiniMaxConfig,
    chat_completions,
    extract_aura_source,
    extract_aura_sources,
    load_minimax_config,
    redact_secrets,
)
from aura_build.runtime import resolve_aura_bin

DEFAULT_CORPUS = Path("corpus/projects")
DEFAULT_SCRATCH = Path("scratch/corpus_gen_projects")
DEFAULT_AURA_BIN = "/workspace/aura-grok/build_soft4055/aura"
LLM_TIMEOUT_S = 120.0
AURA_TIMEOUT_S = 25.0
PY_TIMEOUT_S = 25.0
DEFAULT_WORKERS = 5
DEFAULT_VARIANTS = 2
DEFAULT_CATALOG_TARGET = 120

DOMAINS = [
    "storage_wal",
    "query_engines",
    "parsers",
    "caches",
    "schedulers",
    "consensus_log",
    "networking",
    "commerce",
    "compilers_vm",
    "ledgers",
    "event_sourcing",
    "rate_limits",
    "diff_index",
    "markup",
    "vcs_objects",
    "messaging",
    "matching",
    "interpreters",
    "security_auth",
    "stream_processing",
]

AURA_PRIMER = """Aura (Lisp-like) primer — NOT Python:
(define x 1) (define (f a b) ...) (lambda (x) ...) (if t a b) (cond (t e) (else e))
(let ((a 1)) ...) (begin ...) (set! x v)
Lists: '() (cons a b) (car xs) (cdr xs) (null? xs) (list a b) (reverse xs) (member x xs)
+ - * / modulo quotient  < > <= >= =  equal? number? string? null?  #t #f  and or not
(display x) (newline) (number->string n) (string-append a b) (string=? a b)
Recursion OK. No Python/dict/comprehensions. Prefer lists + set! for mutable state.
Multi-file: each file is loaded in order on one Aura CLI invocation (shared top-level).
FORBIDDEN (not in Aura runtime): define-record, struct, match, hash tables, vector-set!,
Racket/Scheme SRFI extras, char ports beyond basic display. Use lists/alists only.
"""

SYSTEM_CATALOG = """You invent NON-TRIVIAL multi-file systems-programming project ideas
suitable for an Aura (Lisp-like) multi-file dogfood/combat corpus.
Return ONLY a JSON array. Each item:
{"slug":"mini-kv-wal","title":"KV store with WAL","domain":"storage_wal",
 "blurb":"1-2 sentence description","n_files":12}
Rules: slug kebab-case unique; domain must be one of the requested set;
n_files between 8 and 20 inclusive; prefer distinct architectures (not LeetCode).
No secrets. No markdown outside JSON."""

SYSTEM_SPEC = f"""You write a combat-ready multi-file Aura project GOAL.md.
{AURA_PRIMER}
Output markdown with:
1. Title + short overview
2. Exact stdout contract: KEY=value lines (8-16 keys) the scenario must print, in order
3. Module table: filename → required (define (api …)) forms (8-20 .aura files; last is main.aura)
4. Scenario steps that call those APIs (main.aura only prints after computing via APIs)
5. Anti-hardcode: main must not only display expected strings without calling module APIs
6. How to run: `aura file1.aura … main.aura`
Keep APIs small enough for a toy in-memory implementation. No Python. No secrets.
Also end with a JSON fence ```json dogfood containing:
{{"files":[...],"entry":"main.aura","run_mode":"cli_multi",
  "expect_keys":["KEY1","KEY2",...],
  "source_res":["\\\\(define\\\\s+\\\\(api-name\\\\b", ...]}}
expect values are NOT included (measured later from Python ref).
"""

SYSTEM_REF = """You write a Python 3 reference for a multi-file Aura project GOAL.
Output ONE self-contained script in a fence:
```python run_scenarios.py
...
```
Requirements:
- Single file only (import only stdlib). Implement toy in-memory semantics for the GOAL scenario.
- When run as __main__, print AT LEAST 5 lines of KEY=value (keys from GOAL expect list),
  each on its own line, values COMPUTED by running the scenario — no blank output.
- Example shape:
  WAL_MAGIC=1
  RECORDS_APPENDED=3
  ...
- No assert/unittest that aborts before prints; no network; runtime << 2s.
- Valid Python only (no Scheme ? in identifiers).
- Do NOT print JSON or prose — ONLY KEY=value lines on stdout.
"""

SYSTEM_AURA_FILE = f"""You write ONE Aura source file for a multi-file project.
{AURA_PRIMER}
Output a single ```aura <filename> fence with that file's complete source.
Implement the required (define …) APIs for THIS file only.
Do not print scenario KEY= lines unless this file is main.aura.
If main.aura: run the GOAL scenario via module APIs and print KEY=value lines
(computed — do not hardcode expected values as the sole logic).
No Python. No secrets.
"""

_SLUG_RE = re.compile(r"^[a-z][a-z0-9\-]{1,80}$")
_KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", re.MULTILINE)
_FENCE_JSON = re.compile(r"```(?:json)?(?:\s+dogfood)?\s*\n([\s\S]*?)```", re.IGNORECASE)
_FENCE_PY_NAMED = re.compile(
    r"```(?:python|py)(?:\s+|:)([\w./-]+\.py)\s*\n([\s\S]*?)```", re.IGNORECASE
)
_FENCE_PY = re.compile(r"```(?:python|py)\s*\n([\s\S]*?)```", re.IGNORECASE)
_FENCE_AURA_NAMED = re.compile(
    r"```(?:aura|scheme|lisp)?(?::|\s+)([\w./-]+\.aura)\s*\n([\s\S]*?)```",
    re.IGNORECASE,
)

_log_lock = threading.Lock()
_rate_errors = 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _local_now() -> str:
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
        n_files = int(row.get("n_files") or 12)
        n_files = max(8, min(20, n_files))
        lines.append(
            json.dumps(
                {
                    "slug": slug,
                    "title": str(row.get("title") or slug),
                    "domain": str(row.get("domain") or "storage_wal"),
                    "blurb": str(row.get("blurb") or "")[:600],
                    "n_files": n_files,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _extract_json_obj(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    for m in _FENCE_JSON.finditer(text):
        body = m.group(1).strip()
        try:
            obj = json.loads(body)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    return None


def _extract_json_array(text: str) -> list[Any]:
    if not text:
        return []
    m = _FENCE_JSON.search(text)
    body = m.group(1).strip() if m else text.strip()
    start = body.find("[")
    end = body.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        obj = json.loads(body[start : end + 1])
    except json.JSONDecodeError:
        return []
    return obj if isinstance(obj, list) else []


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
        is_rate = "429" in err or "rate" in err.lower()
        usage = last.get("usage") if isinstance(last.get("usage"), dict) else {}
        rec = {
            "ts": _utc_now(),
            "ts_local": _local_now(),
            "track": "projects",
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
            with _log_lock:
                _rate_errors = max(0, _rate_errors - 1)
            return last
        if is_rate:
            with _log_lock:
                _rate_errors += 1
                backoff = min(60.0, 2.0 ** attempt + _rate_errors)
            time.sleep(backoff)
            continue
        break
    return last


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
            out = (
                exc.stdout.decode("utf-8", errors="replace")
                if isinstance(exc.stdout, bytes)
                else str(exc.stdout)
            )
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": out,
            "stderr": err[:2000],
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


# ----- catalog -----

def generate_catalog_batch(
    *,
    domain: str,
    existing: set[str],
    cfg: MiniMaxConfig,
    batch_size: int,
    run_log: Path | None,
) -> list[dict[str, Any]]:
    avoid = ", ".join(sorted(existing)[:60])
    user = (
        f"Domain: {domain}\nReturn ~{batch_size} distinct project ideas.\n"
        f"Avoid slugs: {avoid or '(none)'}\n"
        f"Allowed domains (use exactly '{domain}'): {', '.join(DOMAINS)}\n"
        "Examples of spirit (do not copy slugs): mini-kv-wal, mini-sql, mini-regex, "
        "mini-json, mini-lru-ttl, mini-job-deps, mini-raft-log, mini-http-router, "
        "mini-inventory, mini-expr-vm, mini-ledger, mini-event-store, mini-ratelimit, "
        "mini-myers-diff, mini-btree, mini-md-html, mini-git-objects, mini-pubsub, "
        "mini-match-engine, mini-lisp-interp.\n"
    )
    resp = _llm(
        [{"role": "system", "content": SYSTEM_CATALOG}, {"role": "user", "content": user}],
        cfg=cfg,
        temperature=0.85,
        max_tokens=4096,
        timeout_s=LLM_TIMEOUT_S,
        run_log=run_log,
        tag="catalog",
        slug=domain,
    )
    if not resp.get("ok"):
        return []
    rows: list[dict[str, Any]] = []
    for item in _extract_json_array(str(resp.get("content") or "")):
        if not isinstance(item, dict):
            continue
        slug = str(item.get("slug") or "").strip().lower().replace("_", "-").replace(" ", "-")
        slug = re.sub(r"[^a-z0-9\-]", "", slug)
        if not _SLUG_RE.match(slug) or slug in existing:
            continue
        n_files = int(item.get("n_files") or 12)
        rows.append(
            {
                "slug": slug,
                "title": str(item.get("title") or slug),
                "domain": domain,
                "blurb": str(item.get("blurb") or "")[:600],
                "n_files": max(8, min(20, n_files)),
            }
        )
        existing.add(slug)
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
    print(json.dumps({"event": "projects_catalog_start", "have": len(rows), "target": target}))
    idx = 0
    stagnant = 0
    while len(rows) < target:
        domain = DOMAINS[idx % len(DOMAINS)]
        idx += 1
        before = len(rows)
        batch = generate_catalog_batch(
            domain=domain,
            existing=existing,
            cfg=cfg,
            batch_size=min(12, target - len(rows)),
            run_log=run_log,
        )
        rows.extend(batch)
        save_catalog(catalog_path, rows)
        print(
            json.dumps(
                {
                    "event": "projects_catalog_batch",
                    "domain": domain,
                    "added": len(batch),
                    "total": len(rows),
                }
            )
        )
        if len(rows) == before:
            stagnant += 1
            if stagnant > len(DOMAINS) * 2:
                break
        else:
            stagnant = 0
    save_catalog(catalog_path, rows)
    (corpus_dir / "HARNESS.md").write_text(_HARNESS_MD, encoding="utf-8")
    print(json.dumps({"event": "projects_catalog_done", "total": len(rows), "path": str(catalog_path)}))
    return 0


_HARNESS_MD = """# Projects Aura corpus harness

Combat/dogfood-aligned multi-file systems (8–20 `.aura` files).

## Layout per `corpus/projects/<slug>/`

| Path | Role |
|------|------|
| `GOAL.md` | Requirements + module APIs + scenario (same as dogfood projects) |
| `spec.md` | Copy of GOAL.md |
| `dogfood.json` | `files`, `entry`, `run_mode=cli_multi`, `expect` / `expect_res` from tests |
| `ref/` | Python reference + `run_scenarios.py` |
| `tests.json` | Measured KEY=value expect lines (only place for expected outputs) |
| `src/` / `src_2/` | MiniMax Aura candidates (variants) |
| `stub/` | Copy of primary `src/` for `aura-build llm-dogfood --project` / combat |
| `meta.json` | Measured parse/run/pass + tokens |

## Run convention

```bash
$AURA_BIN $(jq -r '.files[]' dogfood.json | sed 's|^|src/|')
# or from stub/:
$AURA_BIN file1.aura … main.aura
```

## Expect

Stdout KEY=value lines; expected values ONLY in `tests.json` / dogfood `expect`
(measured by running `ref/run_scenarios.py`). Anti-hardcode applies to Aura sources.
"""


@dataclass
class ProjectBurnConfig:
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
    temperatures: list[float] = field(default_factory=lambda: [0.35, 0.75])
    continuous: bool = False
    limit: int | None = None
    catalog_extend_batch: int = 20
    stop_flag: Path | None = None
    auto_commit: bool = False
    commit_every: int = 5


def project_dir(corpus: Path, slug: str) -> Path:
    return corpus / slug


def _load_meta(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"variants": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"variants": []}


def _should_stop(bc: ProjectBurnConfig) -> bool:
    return bool(bc.stop_flag and bc.stop_flag.is_file())


def generate_goal(
    entry: dict[str, Any],
    *,
    cfg: MiniMaxConfig,
    bc: ProjectBurnConfig,
) -> tuple[str, dict[str, Any]]:
    user = (
        f"Slug: {entry.get('slug')}\nTitle: {entry.get('title')}\n"
        f"Domain: {entry.get('domain')}\nTarget files: {entry.get('n_files')}\n"
        f"Blurb: {entry.get('blurb')}\n"
        "Write GOAL.md + trailing ```json dogfood fence now."
    )
    resp = _llm(
        [{"role": "system", "content": SYSTEM_SPEC}, {"role": "user", "content": user}],
        cfg=cfg,
        temperature=0.4,
        max_tokens=6000,
        timeout_s=bc.llm_timeout_s,
        run_log=bc.run_log,
        tag="goal",
        slug=str(entry.get("slug")),
    )
    meta = {"ok": bool(resp.get("ok")), "usage": resp.get("usage") or {}, "error": resp.get("error") or "", "model": resp.get("model")}
    if not resp.get("ok"):
        return "", meta
    return str(resp.get("content") or "").strip() + "\n", meta


def _parse_goal_and_dogfood(text: str, entry: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    dog = _extract_json_obj(text) or {}
    # strip json fence from goal markdown for GOAL.md body
    goal = _FENCE_JSON.sub("", text).strip() + "\n"
    files = dog.get("files") if isinstance(dog.get("files"), list) else []
    files = [str(f) for f in files if str(f).endswith(".aura")]
    if not files:
        # synthesize filenames from n_files
        n = int(entry.get("n_files") or 10)
        base = str(entry.get("slug") or "mod").replace("-", "_")[:20]
        files = [f"mod{i}.aura" for i in range(1, n)]
        files[-1] = "main.aura"
    if files[-1] != "main.aura":
        if "main.aura" in files:
            files = [f for f in files if f != "main.aura"] + ["main.aura"]
        else:
            files.append("main.aura")
    files = files[:20]
    if len(files) < 8:
        # pad
        i = 1
        while len(files) < 8:
            name = f"extra{i}.aura"
            if name not in files and name != "main.aura":
                files.insert(-1, name)
            i += 1
    expect_keys = dog.get("expect_keys") if isinstance(dog.get("expect_keys"), list) else []
    expect_keys = [str(k) for k in expect_keys]
    source_res = dog.get("source_res") if isinstance(dog.get("source_res"), list) else []
    source_res = [str(s) for s in source_res]
    dogfood = {
        "label": str(entry.get("slug")),
        "files": files,
        "entry": "main.aura",
        "run_mode": "cli_multi",
        "expect": "",  # filled after ref
        "expect_res": [],
        "source_res": source_res,
        "expect_keys": expect_keys,
        "seed_from_stub": True,
        "user_extra": f"Multi-file project {entry.get('slug')}; implement GOAL.md APIs; print KEY=value via main.aura using module calls.",
    }
    return goal, dogfood


def generate_ref(
    entry: dict[str, Any],
    goal: str,
    dogfood: dict[str, Any],
    *,
    cfg: MiniMaxConfig,
    bc: ProjectBurnConfig,
) -> tuple[dict[str, str], dict[str, Any]]:
    user = (
        f"Slug: {entry.get('slug')}\nFiles: {dogfood.get('files')}\n"
        f"Expect keys: {dogfood.get('expect_keys')}\n\nGOAL.md:\n{goal[:5000]}\n"
        "Write Python ref files now (named fences; include run_scenarios.py)."
    )
    resp = _llm(
        [{"role": "system", "content": SYSTEM_REF}, {"role": "user", "content": user}],
        cfg=cfg,
        temperature=0.25,
        max_tokens=6000,
        timeout_s=bc.llm_timeout_s,
        run_log=bc.run_log,
        tag="ref",
        slug=str(entry.get("slug")),
    )
    meta = {"ok": bool(resp.get("ok")), "usage": resp.get("usage") or {}, "error": resp.get("error") or ""}
    if not resp.get("ok"):
        return {}, meta
    text = str(resp.get("content") or "")
    files: dict[str, str] = {}
    for m in _FENCE_PY_NAMED.finditer(text):
        body = m.group(2).strip()
        if len(body) < 40:
            continue
        files[m.group(1).strip()] = body + "\n"
    if "run_scenarios.py" not in files:
        # any substantial unnamed/named python fence
        for m in _FENCE_PY.finditer(text):
            body = m.group(1).strip()
            if len(body) >= 40 and ("print" in body or "KEY" in body or "__main__" in body):
                files["run_scenarios.py"] = body + "\n"
                break
    if "run_scenarios.py" not in files:
        # last resort: whole reply if it looks like python
        stripped = text.strip()
        if "def " in stripped and "print" in stripped and len(stripped) > 80:
            files["run_scenarios.py"] = stripped + "\n"
    # drop empty stubs
    files = {k: v for k, v in files.items() if len(v.strip()) >= 40}
    if "run_scenarios.py" not in files:
        meta["ok"] = False
        meta["error"] = meta.get("error") or "no_run_scenarios_extracted"
        return {}, meta
    return {"run_scenarios.py": files["run_scenarios.py"]}, meta


def run_ref(ref_dir: Path, tests_path: Path, *, timeout_s: float) -> dict[str, Any]:
    runner = ref_dir / "run_scenarios.py"
    if not runner.is_file():
        # pick any .py
        pys = list(ref_dir.glob("*.py"))
        if not pys:
            return {"ref_ok": False, "stderr": "no_python", "exit_code": 2, "n_lines": 0}
        runner = pys[0]
    r = _run_subprocess(
        ["python3", str(runner.resolve())],
        timeout_s=timeout_s,
        cwd=str(ref_dir.resolve()),
        env={**os.environ, "PYTHONPATH": str(ref_dir.resolve())},
    )
    out = {
        "ref_ok": False,
        "exit_code": r["exit_code"],
        "stderr": r["stderr"][:500],
        "duration_s": r["duration_s"],
        "timeout": r["timeout"],
        "n_lines": 0,
        "expect": "",
    }
    if not r["ok"]:
        return out
    lines = []
    for raw in (r["stdout"] or "").splitlines():
        m = _KV_RE.match(raw.strip())
        if m:
            lines.append(f"{m.group(1)}={m.group(2)}")
    if len(lines) < 3:
        out["stderr"] = (out["stderr"] + " | too_few_kv_lines").strip(" |")
        return out
    expect = "\n".join(lines)
    tests = {
        "expect": expect,
        "lines": [{"key": ln.split("=", 1)[0], "value": ln.split("=", 1)[1]} for ln in lines],
        "measured_from": "ref/run_scenarios.py",
        "ts": _utc_now(),
    }
    tests_path.write_text(json.dumps(tests, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out["ref_ok"] = True
    out["n_lines"] = len(lines)
    out["expect"] = expect
    return out


def generate_aura_file(
    *,
    entry: dict[str, Any],
    goal: str,
    filename: str,
    files_order: list[str],
    prior: dict[str, str],
    cfg: MiniMaxConfig,
    bc: ProjectBurnConfig,
    temperature: float,
    variant: int,
) -> tuple[str, dict[str, Any]]:
    prior_snip = []
    budget = 6000
    for fn, src in prior.items():
        chunk = src[:800]
        prior_snip.append(f"### already generated: {fn}\n```aura\n{chunk}\n```")
        budget -= len(chunk)
        if budget <= 0:
            break
    user = (
        f"Project: {entry.get('slug')} variant={variant}\n"
        f"All files in order: {files_order}\n"
        f"NOW write ONLY: {filename}\n\n"
        f"GOAL excerpt:\n{goal[:3500]}\n\n"
        + "\n".join(prior_snip[-6:])
        + f"\nWrite ```aura {filename} now."
    )
    resp = _llm(
        [{"role": "system", "content": SYSTEM_AURA_FILE}, {"role": "user", "content": user}],
        cfg=cfg,
        temperature=temperature,
        max_tokens=3500,
        timeout_s=bc.llm_timeout_s,
        run_log=bc.run_log,
        tag=f"aura_v{variant}_{filename}",
        slug=str(entry.get("slug")),
    )
    meta = {
        "ok": bool(resp.get("ok")),
        "usage": resp.get("usage") or {},
        "error": resp.get("error") or "",
        "file": filename,
        "temperature": temperature,
    }
    if not resp.get("ok"):
        return "", meta
    text = str(resp.get("content") or "")
    # prefer named extract
    sources = extract_aura_sources(text, filenames=[filename])
    if filename in sources and sources[filename].strip():
        return sources[filename], meta
    # named fence search
    for m in _FENCE_AURA_NAMED.finditer(text):
        if m.group(1).strip() == filename:
            return m.group(2).strip() + "\n", meta
    src = extract_aura_source(text)
    return src, meta


def run_aura_project(
    src_dir: Path,
    files: list[str],
    expect: str,
    *,
    aura_bin: str,
    timeout_s: float,
) -> dict[str, Any]:
    paths = []
    per_file: dict[str, Any] = {}
    for fn in files:
        p = src_dir / fn
        exists = p.is_file() and p.stat().st_size > 0
        per_file[fn] = {"exists": exists, "bytes": p.stat().st_size if exists else 0}
        if exists:
            paths.append(str(p.resolve()))
    if len(paths) != len(files):
        return {
            "parse_ok": False,
            "run_ok": False,
            "exit_code": 2,
            "scenarios_passed": 0,
            "scenarios_total": len(expect.splitlines()) if expect else 0,
            "stderr_snippet": "missing_files",
            "stdout_snippet": "",
            "per_file": per_file,
            "duration_s": 0,
            "timeout": False,
        }
    r = _run_subprocess([aura_bin, *paths], timeout_s=timeout_s)
    stderr = r["stderr"]
    stdout = r["stdout"]
    has_err = bool(re.search(r"(?i)\berror:|\bsyntax\b|\bunbound variable\b", stderr + stdout))
    run_ok = r["exit_code"] == 0 and not r["timeout"] and not has_err
    # per-file: if overall run_ok, mark all parse_ok; else unknown (no per-file aura parse)
    for fn in per_file:
        per_file[fn]["parse_ok"] = bool(run_ok)  # honest: only measured jointly
    got = {}
    for m in _KV_RE.finditer(stdout):
        got[m.group(1)] = m.group(2).strip()
    exp_lines = [ln for ln in expect.splitlines() if "=" in ln]
    passed = 0
    details = []
    for ln in exp_lines:
        k, v = ln.split("=", 1)
        actual = got.get(k)
        ok = actual is not None and actual.strip() == v.strip()
        if ok:
            passed += 1
        details.append({"key": k, "expected": v, "got": actual, "ok": ok})
    return {
        "parse_ok": bool(run_ok),
        "run_ok": bool(run_ok),
        "exit_code": r["exit_code"],
        "timeout": r["timeout"],
        "duration_s": r["duration_s"],
        "stderr_snippet": stderr[:500],
        "stdout_snippet": stdout[:800],
        "scenarios_passed": passed,
        "scenarios_total": len(exp_lines),
        "case_details": details,
        "per_file": per_file,
    }


def _sync_stub(src_dir: Path, stub_dir: Path, files: list[str]) -> None:
    if stub_dir.exists():
        shutil.rmtree(stub_dir)
    stub_dir.mkdir(parents=True, exist_ok=True)
    for fn in files:
        src = src_dir / fn
        if src.is_file():
            shutil.copy2(src, stub_dir / fn)


def _write_dogfood_with_expect(path: Path, dogfood: dict[str, Any], expect: str) -> None:
    dog = dict(dogfood)
    dog["expect"] = expect
    dog["expect_res"] = [
        re.escape(k) + r"\s*=\s*" + re.escape(v)
        for ln in expect.splitlines()
        if "=" in ln
        for k, v in [ln.split("=", 1)]
    ]
    path.write_text(json.dumps(dog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def process_project(entry: dict[str, Any], bc: ProjectBurnConfig, cfg: MiniMaxConfig) -> dict[str, Any]:
    slug = str(entry["slug"])
    pdir = project_dir(bc.corpus_dir, slug)
    pdir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {"slug": slug, "track": "projects", "actions": []}

    if _should_stop(bc):
        summary["stopped"] = True
        return summary

    goal_path = pdir / "GOAL.md"
    spec_path = pdir / "spec.md"
    dog_path = pdir / "dogfood.json"

    if not goal_path.is_file():
        text, gmeta = generate_goal(entry, cfg=cfg, bc=bc)
        summary["actions"].append("goal")
        if not text.strip():
            summary["goal_failed"] = gmeta.get("error") or "empty"
            return summary
        goal, dogfood = _parse_goal_and_dogfood(text, entry)
        goal_path.write_text(goal, encoding="utf-8")
        spec_path.write_text(goal, encoding="utf-8")
        dog_path.write_text(json.dumps(dogfood, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        goal = goal_path.read_text(encoding="utf-8")
        if dog_path.is_file():
            dogfood = json.loads(dog_path.read_text(encoding="utf-8"))
        else:
            _, dogfood = _parse_goal_and_dogfood(goal, entry)
            dog_path.write_text(json.dumps(dogfood, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    files = list(dogfood.get("files") or [])
    tests_path = pdir / "tests.json"
    ref_dir = pdir / "ref"

    if not tests_path.is_file():
        # (re)generate ref
        if ref_dir.exists() and not (ref_dir / "run_scenarios.py").is_file():
            # maybe quarantine leftover
            pass
        need_ref = not (ref_dir / "run_scenarios.py").is_file()
        if need_ref:
            ref_files, rmeta = generate_ref(entry, goal, dogfood, cfg=cfg, bc=bc)
            summary["actions"].append("ref")
            if not ref_files:
                summary["ref_failed"] = rmeta.get("error") or "empty"
                return summary
            if ref_dir.exists():
                shutil.rmtree(ref_dir)
            ref_dir.mkdir(parents=True, exist_ok=True)
            for fn, src in ref_files.items():
                (ref_dir / Path(fn).name).write_text(src, encoding="utf-8")
        run_info = run_ref(ref_dir, tests_path, timeout_s=bc.py_timeout_s)
        summary["actions"].append("run_ref")
        summary["ref_run"] = {k: run_info[k] for k in ("ref_ok", "exit_code", "n_lines", "stderr") if k in run_info}
        if not run_info.get("ref_ok"):
            bad = pdir / "ref.bad"
            if bad.exists():
                shutil.rmtree(bad)
            try:
                ref_dir.rename(bad)
            except OSError:
                pass
            (pdir / "meta.json").write_text(
                json.dumps(
                    {
                        "slug": slug,
                        "ref": run_info,
                        "updated_at": _utc_now(),
                        "variants": [],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            return summary
        _write_dogfood_with_expect(dog_path, dogfood, run_info["expect"])
        dogfood = json.loads(dog_path.read_text(encoding="utf-8"))

    tests = json.loads(tests_path.read_text(encoding="utf-8"))
    expect = str(tests.get("expect") or "")
    if expect and not dogfood.get("expect"):
        _write_dogfood_with_expect(dog_path, dogfood, expect)
        dogfood = json.loads(dog_path.read_text(encoding="utf-8"))

    meta = _load_meta(pdir / "meta.json")
    meta["slug"] = slug
    meta["title"] = entry.get("title")
    meta["domain"] = entry.get("domain")
    meta["files"] = files
    meta.setdefault("variants", [])

    temps = bc.temperatures
    for v_i in range(1, bc.variants + 1):
        if _should_stop(bc):
            summary["stopped"] = True
            break
        src_name = "src" if v_i == 1 else f"src_{v_i}"
        src_dir = pdir / src_name
        # skip if complete
        if src_dir.is_dir() and all((src_dir / f).is_file() for f in files):
            if any(isinstance(v, dict) and v.get("variant") == v_i and v.get("src_dir") for v in meta["variants"]):
                continue
        src_dir.mkdir(parents=True, exist_ok=True)
        temp = temps[(v_i - 1) % len(temps)]
        prior: dict[str, str] = {}
        file_metas = []
        usage_sum = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        for fn in files:
            if _should_stop(bc):
                break
            existing = src_dir / fn
            if existing.is_file() and existing.stat().st_size > 20:
                prior[fn] = existing.read_text(encoding="utf-8")
                file_metas.append({"file": fn, "skipped_existing": True, "parse_ok": None})
                continue
            src, fmeta = generate_aura_file(
                entry=entry,
                goal=goal,
                filename=fn,
                files_order=files,
                prior=prior,
                cfg=cfg,
                bc=bc,
                temperature=temp,
                variant=v_i,
            )
            summary["actions"].append(f"aura_v{v_i}:{fn}")
            if not src.strip():
                src = f"; empty generation for {fn}\n(define (placeholder-{fn.replace('.', '-')} ) 0)\n"
            existing.write_text(src, encoding="utf-8")
            prior[fn] = src
            usage = fmeta.get("usage") or {}
            for k in usage_sum:
                usage_sum[k] += int(usage.get(k) or 0)
            file_metas.append(fmeta)

        run = run_aura_project(
            src_dir, files, expect, aura_bin=bc.aura_bin, timeout_s=bc.aura_timeout_s
        )
        # attach per-file parse from joint run
        for fm in file_metas:
            fn = fm.get("file")
            if fn and fn in (run.get("per_file") or {}):
                fm["parse_ok"] = run["per_file"][fn].get("parse_ok")
                fm["exists"] = run["per_file"][fn].get("exists")

        if v_i == 1:
            _sync_stub(src_dir, pdir / "stub", files)

        meta["variants"] = [v for v in meta["variants"] if v.get("variant") != v_i]
        meta["variants"].append(
            {
                "variant": v_i,
                "src_dir": src_name,
                "temperature": temp,
                "ts": _utc_now(),
                "ts_local": _local_now(),
                "usage": usage_sum,
                "files": file_metas,
                "parse_ok": run["parse_ok"],
                "run_ok": run["run_ok"],
                "exit_code": run["exit_code"],
                "timeout": run["timeout"],
                "duration_s": run["duration_s"],
                "scenarios_passed": run["scenarios_passed"],
                "scenarios_total": run["scenarios_total"],
                "stderr_snippet": run["stderr_snippet"],
                "stdout_snippet": run.get("stdout_snippet", "")[:400],
            }
        )
        summary.setdefault("variants_done", []).append(
            {
                "variant": v_i,
                "parse_ok": run["parse_ok"],
                "run_ok": run["run_ok"],
                "passed": run["scenarios_passed"],
                "total": run["scenarios_total"],
                "n_files": len(files),
            }
        )

    meta["updated_at"] = _utc_now()
    meta["updated_at_local"] = _local_now()
    (pdir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def project_needs_work(entry: dict[str, Any], bc: ProjectBurnConfig) -> bool:
    pdir = project_dir(bc.corpus_dir, str(entry["slug"]))
    if not (pdir / "tests.json").is_file():
        return True
    meta = _load_meta(pdir / "meta.json")
    dog = {}
    if (pdir / "dogfood.json").is_file():
        try:
            dog = json.loads((pdir / "dogfood.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            dog = {}
    files = list(dog.get("files") or [])
    done = {
        int(v.get("variant", 0))
        for v in meta.get("variants", [])
        if isinstance(v, dict) and v.get("src_dir")
    }
    for v_i in range(1, bc.variants + 1):
        if v_i in done:
            src = pdir / ("src" if v_i == 1 else f"src_{v_i}")
            if files and all((src / f).is_file() for f in files):
                continue
        return True
    return False


def extend_catalog(bc: ProjectBurnConfig, cfg: MiniMaxConfig, extra: int) -> int:
    catalog_path = bc.corpus_dir / "catalog.jsonl"
    rows = load_catalog(catalog_path)
    existing = {str(r["slug"]) for r in rows}
    before = len(rows)
    for domain in DOMAINS:
        if len(rows) - before >= extra:
            break
        batch = generate_catalog_batch(
            domain=domain,
            existing=existing,
            cfg=cfg,
            batch_size=min(10, extra - (len(rows) - before)),
            run_log=bc.run_log,
        )
        rows.extend(batch)
        save_catalog(catalog_path, rows)
    return len(rows) - before


def maybe_auto_commit(bc: ProjectBurnConfig, *, note: str) -> None:
    if not bc.auto_commit:
        return
    repo = Path.cwd()
    try:
        subprocess.run(
            ["git", "add", "corpus/projects", "src/aura_build/corpus_projects.py"],
            cwd=repo,
            check=False,
            capture_output=True,
            timeout=60,
        )
        st = subprocess.run(
            ["git", "status", "--porcelain", "corpus/projects"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if not (st.stdout or "").strip():
            return
        subprocess.run(
            ["git", "commit", "-m", f"chore(corpus): projects burn chunk — {note}"],
            cwd=repo,
            check=False,
            capture_output=True,
            timeout=180,
        )
        subprocess.run(
            ["git", "push", "origin", "HEAD"],
            cwd=repo,
            check=False,
            capture_output=True,
            timeout=180,
        )
        print(json.dumps({"event": "auto_commit", "track": "projects", "note": note, "ts_local": _local_now()}))
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"event": "auto_commit_error", "error": str(exc)[:200]}))


def cmd_burn(bc: ProjectBurnConfig) -> int:
    ensure_dirs(bc.corpus_dir, bc.scratch)
    if not (bc.corpus_dir / "HARNESS.md").is_file():
        (bc.corpus_dir / "HARNESS.md").write_text(_HARNESS_MD, encoding="utf-8")
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
    try:
        while True:
            if _should_stop(bc):
                print(json.dumps({"event": "stop_flag", "track": "projects", "processed": processed}))
                break
            catalog_path = bc.corpus_dir / "catalog.jsonl"
            rows = load_catalog(catalog_path)
            if not rows:
                cmd_catalog(
                    corpus_dir=bc.corpus_dir,
                    target=min(40, DEFAULT_CATALOG_TARGET),
                    env_file=bc.env_file,
                    run_log=bc.run_log,
                    scratch=bc.scratch,
                )
                rows = load_catalog(catalog_path)
            todo = [r for r in rows if project_needs_work(r, bc)]
            if not todo:
                if not bc.continuous:
                    print(json.dumps({"event": "done_no_work", "track": "projects", "processed": processed}))
                    break
                added = extend_catalog(bc, cfg, bc.catalog_extend_batch)
                if added == 0:
                    bc.variants += 1
                    print(json.dumps({"event": "bump_variants", "track": "projects", "variants": bc.variants}))
                else:
                    print(json.dumps({"event": "catalog_extended", "track": "projects", "added": added}))
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
                        "track": "projects",
                        "todo": len(todo),
                        "workers": bc.workers,
                        "variants": bc.variants,
                        "ts_local": _local_now(),
                    }
                )
            )
            with ThreadPoolExecutor(max_workers=max(1, bc.workers)) as pool:
                futs = {pool.submit(process_project, e, bc, cfg): e.get("slug") for e in todo}
                for fut in as_completed(futs):
                    slug = futs[fut]
                    try:
                        result = fut.result()
                    except Exception as exc:  # noqa: BLE001
                        result = {
                            "slug": slug,
                            "track": "projects",
                            "error": f"{type(exc).__name__}: {exc}",
                            "trace": traceback.format_exc()[-400:],
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
                        stop_flag.write_text("limit\n", encoding="utf-8")
            if bc.limit is not None and processed >= bc.limit:
                print(json.dumps({"event": "limit_reached", "track": "projects", "processed": processed}))
                break
            if not bc.continuous:
                still = [r for r in load_catalog(catalog_path) if project_needs_work(r, bc)]
                if not still:
                    print(json.dumps({"event": "pass_complete", "track": "projects", "processed": processed}))
                    break
    finally:
        if pid_path.is_file():
            try:
                if pid_path.read_text(encoding="utf-8").strip() == str(os.getpid()):
                    pid_path.unlink()
            except OSError:
                pass
    return 0


def cmd_summary(corpus_dir: Path, run_log: Path | None = None) -> dict[str, Any]:
    catalog = load_catalog(corpus_dir / "catalog.jsonl")
    n_projects = 0
    n_variants = 0
    parse_ok = 0
    run_ok = 0
    file_parse_ok = 0
    file_parse_total = 0
    pass_dist: dict[str, int] = {}
    tokens_total = 0
    for entry in catalog:
        pdir = project_dir(corpus_dir, str(entry["slug"]))
        if not pdir.is_dir():
            continue
        n_projects += 1
        meta = _load_meta(pdir / "meta.json")
        for v in meta.get("variants", []):
            if not isinstance(v, dict):
                continue
            n_variants += 1
            if v.get("parse_ok"):
                parse_ok += 1
            if v.get("run_ok"):
                run_ok += 1
            sp = int(v.get("scenarios_passed") or 0)
            st = int(v.get("scenarios_total") or 0)
            key = f"{sp}/{st}"
            pass_dist[key] = pass_dist.get(key, 0) + 1
            usage = v.get("usage") or {}
            tokens_total += int(usage.get("total_tokens") or 0)
            for fm in v.get("files") or []:
                if not isinstance(fm, dict):
                    continue
                if "parse_ok" in fm and fm.get("parse_ok") is not None:
                    file_parse_total += 1
                    if fm.get("parse_ok"):
                        file_parse_ok += 1
    log_stats: dict[str, Any] = {}
    if run_log and run_log.is_file():
        calls = 0
        t_total = 0
        t_first = t_last = None
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
                t_total += int(row.get("total_tokens") or 0)
                ts = row.get("ts")
                if ts:
                    t_first = t_first or ts
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
            "total_tokens": t_total,
            "first_ts": t_first,
            "last_ts": t_last,
            "hours": round(hours, 4) if hours else None,
            "calls_per_hour": round(calls / hours, 2) if hours else None,
            "tokens_per_hour": round(t_total / hours, 2) if hours else None,
        }
    return {
        "track": "projects",
        "catalog_entries": len(catalog),
        "project_dirs": n_projects,
        "variants": n_variants,
        "parse_ok": parse_ok,
        "parse_ok_pct": round(100.0 * parse_ok / n_variants, 2) if n_variants else 0.0,
        "run_ok": run_ok,
        "run_ok_pct": round(100.0 * run_ok / n_variants, 2) if n_variants else 0.0,
        "per_file_parse_ok": file_parse_ok,
        "per_file_parse_total": file_parse_total,
        "per_file_parse_pct": round(100.0 * file_parse_ok / file_parse_total, 2) if file_parse_total else 0.0,
        "pass_distribution": dict(sorted(pass_dist.items())),
        "tokens_from_meta": tokens_total,
        "run_log": log_stats,
        "ts_local": _local_now(),
    }


def cmd_stop(scratch: Path) -> dict[str, Any]:
    stop_flag = scratch / "STOP"
    scratch.mkdir(parents=True, exist_ok=True)
    stop_flag.write_text("stop\n", encoding="utf-8")
    pid_path = scratch / "burn.pid"
    killed = False
    err = ""
    if pid_path.is_file():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, signal.SIGTERM)
            killed = True
        except (ValueError, ProcessLookupError, PermissionError) as exc:
            err = str(exc)
    return {"track": "projects", "stop_flag": str(stop_flag), "killed": killed, "error": err, "pid_file": str(pid_path)}


def build_config_from_args(args: Any) -> ProjectBurnConfig:
    corpus = Path(getattr(args, "corpus_dir", None) or DEFAULT_CORPUS)
    scratch = Path(getattr(args, "scratch", None) or DEFAULT_SCRATCH)
    run_log = Path(getattr(args, "run_log", None) or (scratch / "run_log.jsonl"))
    temps_raw = getattr(args, "temperatures", None) or "0.35,0.75"
    temps = [float(x.strip()) for x in str(temps_raw).split(",") if x.strip()]
    return ProjectBurnConfig(
        corpus_dir=corpus,
        scratch=scratch,
        run_log=run_log,
        aura_bin=str(
            getattr(args, "aura_bin", None) or os.environ.get("AURA_BIN") or DEFAULT_AURA_BIN
        ),
        env_file=getattr(args, "env_file", None),
        workers=int(getattr(args, "workers", DEFAULT_WORKERS) or DEFAULT_WORKERS),
        variants=int(getattr(args, "variants", DEFAULT_VARIANTS) or DEFAULT_VARIANTS),
        llm_timeout_s=float(getattr(args, "llm_timeout", LLM_TIMEOUT_S)),
        aura_timeout_s=float(getattr(args, "aura_timeout", AURA_TIMEOUT_S)),
        py_timeout_s=float(getattr(args, "py_timeout", PY_TIMEOUT_S)),
        temperatures=temps or [0.35, 0.75],
        continuous=bool(getattr(args, "continuous", False)),
        limit=getattr(args, "limit", None),
        catalog_extend_batch=int(getattr(args, "catalog_extend", 20) or 20),
        auto_commit=bool(getattr(args, "auto_commit", False)),
        commit_every=int(getattr(args, "commit_every", 5) or 5),
    )
