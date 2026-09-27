"""Soft-serve LeetCode one-problem repair → current-source → corpus file.

Real-work dogfood (default: intersection-of-two-arrays 7/8 order fix):
  Soft --serve denseness → fiber explorers mutate ``solve`` → select-best by
  CASE hits vs tests.json → (current-source :workspace :pretty) →
  write solution_runtime.aura → Soft oneshot verify → commit corpus.

No expected-answer hardcoding into display. Never invent fiber_live/incr_proven.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aura_build.self_evolve_host import git_commit_and_maybe_push

DEFAULT_SOFT = "/workspace/aura-grok/build_soft4079/aura"

_INTERSECTION_WORKSPACE = r"""
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
"""

# mutate:rebind bodies for solve — order variants (no gold literals in display)
_SOLVE_EXPLORERS = [
    ("order-a", "(lambda (a b) (intersect-raw a b))"),
    ("sort-asc", "(lambda (a b) (sort-asc (intersect-raw a b)))"),
    ("sort-desc", "(lambda (a b) (reverse-list (sort-asc (intersect-raw a b))))"),
]


def _aura_env(repo: Path, aura_bin: str) -> dict[str, str]:
    env = os.environ.copy()
    env["AURA_SANDBOX"] = env.get("AURA_SANDBOX") or "off"
    env["AURA_PIPELINE_STRICT"] = env.get("AURA_PIPELINE_STRICT") or "0"
    env["AURA_PATH"] = env.get("AURA_PATH") or f"{repo.parent}/aura-grok/lib:{repo}/aura"
    return env


def _values_match(got: str, expected: str) -> bool:
    g = got.strip()
    e = expected.strip()
    if g == e:
        return True
    try:
        return json.loads(g) == json.loads(e)
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
    timeout_s: float = 15.0,
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


def repair_intersection(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import start_session

    slug = "intersection-of-two-arrays"
    pdir = repo / "corpus" / "leetcode" / slug
    tests = json.loads((pdir / "tests.json").read_text(encoding="utf-8"))
    baseline = score_aura_file(
        repo, pdir / "solution.aura", tests, aura_bin=aura_bin
    )

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
            _INTERSECTION_WORKSPACE.strip()
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
        )
        boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=20.0)
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"set_code_failed:{boot.get('msg') or boot.get('status')}",
                "baseline": baseline,
                "denseness": denseness,
                "aura_issue_candidate": True,
            }
        sess.raw_line("(eval-current)", timeout_s=20.0)

        for name, body in _SOLVE_EXPLORERS:
            # Escape body for embedding in mutate string (body uses only " already)
            body_esc = body.replace("\\", "\\\\").replace('"', '\\"')
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
            mut = sess.raw_line(line, timeout_s=20.0)
            run = sess.raw_line("(run-cases)", timeout_s=20.0)
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
                    "case4": got.get(4),
                }
            )

        best = max(explorers, key=lambda e: (int(e["hits"]), e["name"]))
        win_esc = best["body"].replace("\\", "\\\\").replace('"', '\\"')
        sess.raw_line(
            f'(begin (mutate:rebind "solve" "{win_esc}" "winner") (eval-current))',
            timeout_s=20.0,
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
            "; Inputs embedded; expected values only used for host scoring, not display.\n"
        )
        out_path.write_text(banner + src + "\n", encoding="utf-8")
        verify = score_aura_file(repo, out_path, tests, aura_bin=aura_bin)
        improved = int(verify.get("hits") or 0) > int(baseline.get("hits") or 0)
        full = bool(verify.get("ok"))
        return {
            "ok": full or improved,
            "reason": "full" if full else ("improved" if improved else "no_gain"),
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


def cmd_soft_leetcode(args: Any) -> int:
    repo = Path(getattr(args, "repo", None) or Path.cwd()).resolve()
    aura_bin = (
        getattr(args, "aura_bin", None)
        or os.environ.get("AURA_BIN")
        or DEFAULT_SOFT
    )
    slug = getattr(args, "slug", None) or "intersection-of-two-arrays"
    if slug not in ("intersection-of-two-arrays", "contains-duplicate"):
        # contains-duplicate large CASE7 hung Soft; only intersection shipped for now
        if slug == "contains-duplicate":
            print(
                json.dumps(
                    {
                        "ok": False,
                        "reason": "contains_duplicate_deferred_case7_too_large",
                        "hint": "use intersection-of-two-arrays",
                    }
                )
            )
            return 2
        print(json.dumps({"ok": False, "reason": f"unsupported_slug:{slug}"}))
        return 2

    # Always use intersection path for shipped dogfood
    result = repair_intersection(
        repo,
        aura_bin=str(aura_bin),
        harness_root=Path(getattr(args, "harness_root", None) or (repo / ".aura-build")),
    )
    print(json.dumps({"event": "soft_leetcode_runtime", **result}, ensure_ascii=False))

    if result.get("aura_issue_candidate") and not result.get("ok"):
        print(
            "soft-leetcode: Soft anomaly candidate — file Aura issue with tip SHA + repro",
            file=sys.stderr,
        )
        return 1
    if not result.get("ok"):
        return 1

    if getattr(args, "no_commit", False):
        print("soft-leetcode: --no-commit; skip git")
        return 0

    paths = [result["out_path"], "src/aura_build/soft_leetcode_runtime.py"]
    pdir = repo / "corpus" / "leetcode" / result["slug"]
    meta_path = pdir / "meta.json"
    if meta_path.is_file():
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
        paths.append(str(meta_path.relative_to(repo)))

    fl = "true" if result.get("fiber_live") else "false"
    msg = (
        f"chore(corpus): soft runtime repair {result.get('slug')} "
        f"{(result.get('baseline') or {}).get('hits')}/{(result.get('baseline') or {}).get('total')}"
        f"→{(result.get('verify') or {}).get('hits')}/{(result.get('verify') or {}).get('total')} "
        f"materialize=current-source fiber_live={fl}"
    )
    # Also stage CLI wiring if dirty
    for extra in (
        "src/aura_build/cli.py",
        "src/aura_build/cli_parser.py",
    ):
        if (repo / extra).exists() and extra not in paths:
            paths.append(extra)

    git_res = git_commit_and_maybe_push(
        repo,
        message=msg,
        paths=paths,
        no_push=bool(getattr(args, "no_push", False)),
    )
    print(json.dumps({"event": "git", **git_res}, ensure_ascii=False))
    if not git_res.get("committed") and git_res.get("reason") != "nothing_to_commit":
        return 1
    return 0
