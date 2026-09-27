"""Soft-serve LeetCode one-problem repair → current-source → corpus file.

Soft --serve denseness → fiber explorers mutate ``solve`` → select-best by
CASE hits vs tests.json → (current-source :workspace :pretty) →
write solution_runtime.aura → Soft oneshot verify → commit corpus.

Hardening:
  - Skip/refuse problems whose tests.json embed lists larger than MAX_LIST_LEN
    (avoids Soft hangs like contains-duplicate CASE7 10k alist).
  - Soft oneshot verify timeout bounded.

No expected-answer hardcoding into display. Never invent fiber_live/incr_proven.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from aura_build.self_evolve_host import git_commit_and_maybe_push

DEFAULT_SOFT = "/workspace/aura-grok/build_soft4079/aura"
# Refuse Soft in-session scoring when any test list JSON exceeds this (chars).
MAX_LIST_JSON_CHARS = 120
SOFT_VERIFY_TIMEOUT_S = 20.0
SOFT_MUTATE_TIMEOUT_S = 25.0


@dataclass(frozen=True)
class Recipe:
    slug: str
    workspace: str
    explorers: list[tuple[str, str]]  # (name, solve-lambda body)


# --- recipes (small inputs only) ----------------------------------------

_INTERSECTION = Recipe(
    slug="intersection-of-two-arrays",
    workspace=r"""
(define (member? x lst)
  (cond ((null? lst) #f)
        ((equal? (car lst) x) #t)
        (else (member? x (cdr lst)))))
(define (remove-dups lst)
  (cond ((null? lst) '())
        ((member? (car lst) (cdr lst)) (remove-dups (cdr lst)))
        (else (cons (car lst) (remove-dups (cdr lst))))))
(define (filter pred lst)
  (cond ((null? lst) '())
        ((pred (car lst)) (cons (car lst) (filter pred (cdr lst))))
        (else (filter pred (cdr lst)))))
(define (insert-sorted x xs)
  (cond ((null? xs) (list x))
        ((<= x (car xs)) (cons x xs))
        (else (cons (car xs) (insert-sorted x (cdr xs))))))
(define (sort-asc xs)
  (if (null? xs) '() (insert-sorted (car xs) (sort-asc (cdr xs)))))
(define (reverse-list xs)
  (let loop ((ys xs) (acc '()))
    (if (null? ys) acc (loop (cdr ys) (cons (car ys) acc)))))
(define (intersect-raw a b)
  (let ((da (remove-dups a)))
    (filter (lambda (x) (member? x b)) da)))
(define (solve a b) (intersect-raw a b))
(define (print-list xs)
  (display "[")
  (cond ((null? xs) (display "]"))
        (else
          (display (car xs))
          (let loop ((rest (cdr xs)))
            (cond ((null? rest) (display "]"))
                  (else (display ",") (display (car rest)) (loop (cdr rest))))))))
(define (run-case n a b)
  (display "CASE") (display n) (display "=")
  (print-list (solve a b)) (newline))
(define (run-cases)
  (begin
    (run-case 0 '(1 2 2 3) '(2 3 4))
    (run-case 1 '(1 2 3) '(4 5 6))
    (run-case 2 '() '(1 2 3))
    (run-case 3 '(1 1 1) '(1 2 3))
    (run-case 4 '(-1 -2 -3) '(-2 -3 -4))
    (run-case 5 '(1 2 3 4 5) '(3 4 5 6 7))
    (run-case 6 '(0 0 0) '(0))
    (run-case 7 '(1 2 3) '())))
(run-cases)
""",
    explorers=[
        ("order-a", "(lambda (a b) (intersect-raw a b))"),
        ("sort-asc", "(lambda (a b) (sort-asc (intersect-raw a b)))"),
        ("sort-desc", "(lambda (a b) (reverse-list (sort-asc (intersect-raw a b))))"),
    ],
)

_TOP_K = Recipe(
    slug="top-k-frequent-elements",
    workspace=r"""
(define (assoc-key key alist)
  (cond ((null? alist) #f)
        ((equal? (car (car alist)) key) (car alist))
        (else (assoc-key key (cdr alist)))))
(define (remove-key key alist)
  (cond ((null? alist) '())
        ((equal? (car (car alist)) key) (cdr alist))
        (else (cons (car alist) (remove-key key (cdr alist))))))
(define (count-freq lst)
  (letrec ((aux
            (lambda (xs acc)
              (if (null? xs)
                  acc
                  (let ((pair (assoc-key (car xs) acc)))
                    (if pair
                        (aux (cdr xs)
                             (cons (cons (car pair) (+ (cdr pair) 1))
                                   (remove-key (car xs) acc)))
                        (aux (cdr xs) (cons (cons (car xs) 1) acc))))))))
    (aux lst '())))
(define (insert-by-count pair sorted)
  (cond ((null? sorted) (list pair))
        ((> (cdr pair) (cdr (car sorted))) (cons pair sorted))
        (else (cons (car sorted) (insert-by-count pair (cdr sorted))))))
(define (sort-by-count pairs)
  (if (null? pairs) '()
      (insert-by-count (car pairs) (sort-by-count (cdr pairs)))))
(define (take n lst)
  (cond ((or (= n 0) (null? lst)) '())
        (else (cons (car lst) (take (- n 1) (cdr lst))))))
(define (map-car xs)
  (if (null? xs) '() (cons (car (car xs)) (map-car (cdr xs)))))
(define (insert-sorted x xs)
  (cond ((null? xs) (list x))
        ((<= x (car xs)) (cons x xs))
        (else (cons (car xs) (insert-sorted x (cdr xs))))))
(define (sort-asc xs)
  (if (null? xs) '() (insert-sorted (car xs) (sort-asc (cdr xs)))))
(define (reverse-list xs)
  (let loop ((ys xs) (acc '()))
    (if (null? ys) acc (loop (cdr ys) (cons (car ys) acc)))))
(define (top-k-raw nums k)
  (take k (map-car (sort-by-count (count-freq nums)))))
(define (solve nums k) (top-k-raw nums k))
(define (print-list xs)
  (display "[")
  (cond ((null? xs) (display "]"))
        (else
          (display (car xs))
          (let loop ((rest (cdr xs)))
            (cond ((null? rest) (display "]"))
                  (else (display ",") (display (car rest)) (loop (cdr rest))))))))
(define (run-case n nums k)
  (display "CASE") (display n) (display "=")
  (print-list (solve nums k)) (newline))
(define (run-cases)
  (begin
    (run-case 0 '(1 1 1 2 2 3) 2)
    (run-case 1 '(1) 1)
    (run-case 2 '(4 4 4 5 5 6 7 7 7 7 8) 3)
    (run-case 3 '(-1 -1 -2 -2 -2 3) 2)
    (run-case 4 '(1 2 3 4 5) 5)
    (run-case 5 '(2 2 3 3 4 4 5 5 6 6 7) 4)
    (run-case 6 '(10 10 10 10 20) 1)
    (run-case 7 '(0 0 0 0 0) 1)))
(run-cases)
""",
    explorers=[
        ("freq-desc", "(lambda (nums k) (top-k-raw nums k))"),
        ("sort-asc", "(lambda (nums k) (sort-asc (top-k-raw nums k)))"),
        ("sort-desc", "(lambda (nums k) (reverse-list (sort-asc (top-k-raw nums k))))"),
    ],
)

# two-sum style order: if tests expect sorted pairs

RECIPES: dict[str, Recipe] = {
    r.slug: r
    for r in (_INTERSECTION, _TOP_K)
}


def _aura_env(repo: Path, aura_bin: str) -> dict[str, str]:
    env = os.environ.copy()
    env["AURA_SANDBOX"] = env.get("AURA_SANDBOX") or "off"
    env["AURA_PIPELINE_STRICT"] = env.get("AURA_PIPELINE_STRICT") or "0"
    env["AURA_PATH"] = env.get("AURA_PATH") or f"{repo.parent}/aura-grok/lib:{repo}/aura"
    return env


def max_embedded_list_chars(tests: list[dict[str, Any]]) -> int:
    m = 0
    for t in tests:
        inp = t.get("input")
        vals: list[Any] = []
        if isinstance(inp, dict):
            vals = list(inp.values())
        elif isinstance(inp, list):
            vals = [inp]
        for v in vals:
            if isinstance(v, list):
                m = max(m, len(json.dumps(v, separators=(",", ":"))))
            elif isinstance(v, str):
                m = max(m, len(v))
    return m


def _values_match(got: str, expected: str) -> bool:
    g = got.strip()
    e = expected.strip()
    if g == e:
        return True
    aliases = {"#t": "true", "#f": "false", "True": "true", "False": "false"}
    if aliases.get(g, g) == aliases.get(e, e):
        return True
    try:
        return json.loads(g) == json.loads(e)
    except Exception:
        # tolerate spaces after commas
        try:
            return json.loads(g.replace(", ", ",")) == json.loads(e)
        except Exception:
            return False


def _score_stdout(stdout: str, tests: list[dict[str, Any]]) -> tuple[int, int, dict[int, str]]:
    got: dict[int, str] = {}
    for line in (stdout or "").splitlines():
        if line.startswith("CASE") and "=" in line:
            k, v = line.split("=", 1)
            try:
                got[int(k[4:])] = v.strip()
            except ValueError:
                continue
    hits = 0
    for t in tests:
        tid = int(t.get("id", 0))
        exp = str(t.get("expected", "")).strip()
        g = got.get(tid)
        if g is not None and _values_match(g, exp):
            hits += 1
    return hits, len(tests), got


def score_aura_file(
    repo: Path,
    path: Path,
    tests: list[dict[str, Any]],
    *,
    aura_bin: str,
    timeout_s: float = SOFT_VERIFY_TIMEOUT_S,
) -> dict[str, Any]:
    env = _aura_env(repo, aura_bin)
    try:
        proc = subprocess.run(
            [aura_bin, str(path)],
            cwd=str(repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "hits": 0, "total": len(tests), "reason": "timeout"}
    hits, total, got = _score_stdout(proc.stdout or "", tests)
    return {
        "ok": hits == total and total > 0,
        "hits": hits,
        "total": total,
        "exit_code": proc.returncode,
        "got": {str(k): v for k, v in got.items()},
    }


def repair_recipe(
    repo: Path,
    recipe: Recipe,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import start_session

    slug = recipe.slug
    pdir = repo / "corpus" / "leetcode" / slug
    tests = json.loads((pdir / "tests.json").read_text(encoding="utf-8"))
    emb = max_embedded_list_chars(tests)
    if emb > MAX_LIST_JSON_CHARS:
        return {
            "ok": False,
            "reason": f"tests_too_large:{emb}>{MAX_LIST_JSON_CHARS}",
            "slug": slug,
            "skipped": True,
        }

    baseline_file = pdir / "solution.aura"
    for cand in ("solution_repair.aura", "solution_2.aura", "solution.aura"):
        if (pdir / cand).is_file():
            # prefer highest live score among existing
            pass
    # score available baselines; pick best existing as baseline metric
    baseline = {"ok": False, "hits": 0, "total": len(tests)}
    for cand in ("solution_repair.aura", "solution.aura", "solution_2.aura"):
        cp = pdir / cand
        if cp.is_file():
            sc = score_aura_file(repo, cp, tests, aura_bin=aura_bin)
            if int(sc.get("hits") or 0) >= int(baseline.get("hits") or 0):
                baseline = sc
                baseline["aura_file"] = cand

    if (pdir / "solution_runtime.aura").is_file():
        prev = score_aura_file(repo, pdir / "solution_runtime.aura", tests, aura_bin=aura_bin)
        if prev.get("ok"):
            return {
                "ok": True,
                "reason": "already_full_runtime",
                "slug": slug,
                "baseline": baseline,
                "verify": prev,
                "skipped": True,
                "fiber_live": False,
                "out_path": str((pdir / "solution_runtime.aura").relative_to(repo)),
            }

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    fiber_live = False
    denseness: dict[str, Any] = {}
    explorers: list[dict[str, Any]] = []

    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        denseness = fiber_fanout_probe(sess, n=3, timeout_s=8.0)
        fiber_live = bool(denseness.get("ok"))

        esc = (
            recipe.workspace.strip()
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
        )
        boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=20.0)
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"set_code_failed:{boot.get('msg') or boot.get('status')}",
                "slug": slug,
                "baseline": baseline,
                "denseness": denseness,
                "aura_issue_candidate": True,
            }
        sess.raw_line("(eval-current)", timeout_s=SOFT_MUTATE_TIMEOUT_S)

        for name, body in recipe.explorers:
            body_esc = body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
            if fiber_live:
                line = (
                    f'(fiber:join (fiber:spawn (lambda () '
                    f'(begin (mutate:rebind "solve" "{body_esc}" "exp-{name}") '
                    f'(eval-current) 1))))'
                )
            else:
                line = (
                    f'(begin (mutate:rebind "solve" "{body_esc}" "exp-{name}") '
                    f'(eval-current) 1)'
                )
            mut = sess.raw_line(line, timeout_s=SOFT_MUTATE_TIMEOUT_S)
            run = sess.raw_line("(run-cases)", timeout_s=SOFT_MUTATE_TIMEOUT_S)
            stdout = str(run.get("display") or "")
            hits, total, got = _score_stdout(stdout, tests)
            explorers.append(
                {
                    "name": name,
                    "body": body,
                    "hits": hits,
                    "total": total,
                    "via": "fiber:spawn" if fiber_live else "mutate:rebind",
                    "mut_status": mut.get("status"),
                    "run_status": run.get("status"),
                }
            )

        if not explorers:
            return {
                "ok": False,
                "reason": "no_explorers",
                "slug": slug,
                "baseline": baseline,
                "denseness": denseness,
            }

        best = max(explorers, key=lambda e: (int(e["hits"]), e["name"]))
        # only materialize if beats baseline or is full
        if int(best["hits"]) < int(baseline.get("hits") or 0):
            return {
                "ok": False,
                "reason": "no_gain_vs_baseline",
                "slug": slug,
                "baseline": baseline,
                "selected": best,
                "explorers": explorers,
                "fiber_live": fiber_live,
                "denseness": denseness,
            }

        win_esc = best["body"].replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        sess.raw_line(
            f'(begin (mutate:rebind "solve" "{win_esc}" "winner") (eval-current))',
            timeout_s=SOFT_MUTATE_TIMEOUT_S,
        )
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))",
            timeout_s=20.0,
        )
        src = str(cs.get("display") or "").strip()
        if not src or "solve" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty",
                "slug": slug,
                "baseline": baseline,
                "explorers": explorers,
                "denseness": denseness,
                "fiber_live": fiber_live,
                "aura_issue_candidate": True,
                "display_head": src[:200],
            }

        out_path = pdir / "solution_runtime.aura"
        banner = (
            f"; soft_leetcode_runtime slug={slug}\n"
            f"; materialize=current-source worldline_backend="
            f"{'fiber_graph' if fiber_live else 'serve_mutate'}\n"
            f"; fiber_live={'true' if fiber_live else 'false'} incr_proven=false\n"
            f"; selected_explorer={best['name']} hits={best['hits']}/{best['total']}\n"
            f"; baseline_hits={baseline.get('hits')}/{baseline.get('total')}\n"
            "; Expected values used only for host scoring, not hardcoded into display.\n"
        )
        out_path.write_text(banner + src + "\n", encoding="utf-8")
        verify = score_aura_file(repo, out_path, tests, aura_bin=aura_bin)
        improved = int(verify.get("hits") or 0) > int(baseline.get("hits") or 0)
        full = bool(verify.get("ok"))
        return {
            "ok": full or improved,
            "reason": "full" if full else ("improved" if improved else "verify_no_gain"),
            "slug": slug,
            "out_path": str(out_path.relative_to(repo)),
            "baseline": baseline,
            "verify": verify,
            "selected": best,
            "explorers": explorers,
            "fiber_live": fiber_live,
            "incr_proven": False,
            "worldline_backend": "fiber_graph" if fiber_live else "serve_mutate",
            "denseness": {
                "ok": denseness.get("ok"),
                "note": denseness.get("note") or denseness.get("reason"),
            },
            "src_len": len(src),
            "improved": improved,
            "full": full,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"exc:{type(exc).__name__}:{exc}",
            "slug": slug,
            "baseline": baseline,
            "aura_issue_candidate": True,
            "fiber_live": fiber_live,
        }
    finally:
        if sess is not None:
            try:
                sess.stop()
            except Exception:  # noqa: BLE001
                pass


def _update_meta(repo: Path, result: dict[str, Any]) -> str | None:
    slug = result.get("slug")
    if not slug:
        return None
    pdir = repo / "corpus" / "leetcode" / slug
    meta_path = pdir / "meta.json"
    if not meta_path.is_file():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    variants = [
        v
        for v in meta.get("variants") or []
        if v.get("aura_file") != "solution_runtime.aura"
    ]
    vfy = result.get("verify") or {}
    variants.append(
        {
            "variant": 91,
            "aura_file": "solution_runtime.aura",
            "model": "soft-serve-fiber",
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "llm_ok": False,
            "parse_ok": True,
            "run_ok": bool(vfy.get("ok")),
            "tests_passed": int(vfy.get("hits") or 0),
            "tests_total": int(vfy.get("total") or 0),
            "fiber_live": bool(result.get("fiber_live")),
            "incr_proven": False,
            "materialize": "current-source",
            "worldline_backend": result.get("worldline_backend"),
            "selected_explorer": (result.get("selected") or {}).get("name"),
        }
    )
    meta["variants"] = variants
    meta["updated_at"] = variants[-1]["ts"]
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return str(meta_path.relative_to(repo))


def cmd_soft_leetcode(args: Any) -> int:
    repo = Path(getattr(args, "repo", None) or Path.cwd()).resolve()
    aura_bin = (
        getattr(args, "aura_bin", None)
        or os.environ.get("AURA_BIN")
        or DEFAULT_SOFT
    )
    slug = getattr(args, "slug", None) or "top-k-frequent-elements"
    batch = bool(getattr(args, "batch", False))
    harness_root = Path(getattr(args, "harness_root", None) or (repo / ".aura-build"))

    slugs: list[str]
    if batch:
        slugs = [s for s in RECIPES if s != "intersection-of-two-arrays"]
        # include intersection only if not already full runtime
        inter = repo / "corpus/leetcode/intersection-of-two-arrays/solution_runtime.aura"
        if not inter.is_file():
            slugs = ["intersection-of-two-arrays"] + slugs
    else:
        if slug == "contains-duplicate":
            print(
                json.dumps(
                    {
                        "ok": False,
                        "reason": "contains_duplicate_deferred_case7_too_large",
                        "hint": f"MAX_LIST_JSON_CHARS={MAX_LIST_JSON_CHARS}",
                    }
                )
            )
            return 2
        if slug not in RECIPES:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "reason": f"unsupported_slug:{slug}",
                        "supported": sorted(RECIPES.keys()),
                    }
                )
            )
            return 2
        slugs = [slug]

    results: list[dict[str, Any]] = []
    commit_paths: list[str] = ["src/aura_build/soft_leetcode_runtime.py"]
    for s in slugs:
        recipe = RECIPES[s]
        result = repair_recipe(
            repo, recipe, aura_bin=str(aura_bin), harness_root=harness_root
        )
        print(json.dumps({"event": "soft_leetcode_runtime", **result}, ensure_ascii=False))
        results.append(result)
        if result.get("aura_issue_candidate") and not result.get("ok"):
            print(
                "soft-leetcode: Soft anomaly candidate — file Aura issue with tip SHA + repro",
                file=sys.stderr,
            )
        if result.get("ok") and result.get("out_path") and not result.get("skipped"):
            commit_paths.append(result["out_path"])
            meta_rel = _update_meta(repo, result)
            if meta_rel:
                commit_paths.append(meta_rel)

    fulls = [r for r in results if r.get("full")]
    improved = [r for r in results if r.get("improved") and not r.get("full")]
    print(
        json.dumps(
            {
                "event": "soft_leetcode_batch_summary",
                "attempted": len(results),
                "full": [r.get("slug") for r in fulls],
                "improved": [r.get("slug") for r in improved],
                "failed": [r.get("slug") for r in results if not r.get("ok") and not r.get("skipped")],
            },
            ensure_ascii=False,
        )
    )

    if getattr(args, "no_commit", False):
        print("soft-leetcode: --no-commit; skip git")
        return 0 if fulls or improved else 1

    winners = [r for r in results if r.get("ok") and r.get("out_path") and not r.get("skipped")]
    if not winners:
        return 1 if any(not r.get("skipped") for r in results) else 0

    for extra in ("src/aura_build/cli.py", "src/aura_build/cli_parser.py"):
        if (repo / extra).exists() and extra not in commit_paths:
            commit_paths.append(extra)

    parts = [
        f"{r.get('slug')} {(r.get('baseline') or {}).get('hits')}/{(r.get('baseline') or {}).get('total')}"
        f"→{(r.get('verify') or {}).get('hits')}/{(r.get('verify') or {}).get('total')}"
        for r in winners
    ]
    fl_any = any(r.get("fiber_live") for r in winners)
    msg = (
        "chore(corpus): soft runtime repair "
        + ", ".join(parts)
        + f" materialize=current-source fiber_live={'true' if fl_any else 'false'}"
    )
    # dedupe paths
    seen: set[str] = set()
    uniq = []
    for p in commit_paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)

    git_res = git_commit_and_maybe_push(
        repo,
        message=msg,
        paths=uniq,
        no_push=bool(getattr(args, "no_push", False)),
    )
    print(json.dumps({"event": "git", **git_res}, ensure_ascii=False))
    if not git_res.get("committed") and git_res.get("reason") != "nothing_to_commit":
        return 1
    return 0
