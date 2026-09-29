"""Soft-serve LeetCode one-problem repair → current-source → corpus file.

Soft --serve denseness → fiber explorers mutate ``solve`` → select-best by
CASE hits vs tests.json → (current-source :workspace :pretty) →
write solution_runtime.aura → Soft oneshot verify → commit corpus.

Hardening:
  - Skip/refuse problems whose tests.json embed lists larger than MAX_LIST_LEN
    (avoids Soft hangs like contains-duplicate CASE7 10k alist).
  - Soft oneshot verify timeout bounded.

No expected-answer hardcoding into display. Never invent fiber_live/incr_proven.

LLM path (--llm / --batch-llm): Soft swarm (ant/pso/abc) local multi-mutation FIRST →
concurrent MiniMax propose seeded by mutated variants + feedback-accumulated prompts →
Soft set-code worldlines → select-best → current-source. Sock re-attach before score.
Prefer fiber http-post when measured; else host MiniMax. Recipes still used when slug matches
and --llm is not forced.
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
from aura_build.soft_select import select_explorer_soft


def _soft_sel_meta(soft_sel: dict[str, Any] | None) -> dict[str, Any]:
    if not soft_sel:
        return {"via": "unset"}
    return {
        k: soft_sel.get(k)
        for k in ("via", "reason", "value", "helper", "soft_value")
        if soft_sel.get(k) is not None or k in ("via", "reason")
    }

DEFAULT_SOFT = "/workspace/aura-grok/build/aura"
# Refuse Soft in-session scoring when any test list JSON exceeds this (chars).
MAX_LIST_JSON_CHARS = 120
SOFT_VERIFY_TIMEOUT_S = 20.0
SOFT_MUTATE_TIMEOUT_S = 20.0
SOFT_SET_CODE_TIMEOUT_S = 18.0
SOFT_EVAL_TIMEOUT_S = 18.0


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


_SINGLE_II = Recipe(
    slug="single-number-ii",
    workspace=r"""
(define (count-of x xs)
  (cond ((null? xs) 0)
        ((equal? (car xs) x) (+ 1 (count-of x (cdr xs))))
        (else (count-of x (cdr xs)))))
(define (find-single xs)
  (let ((all xs))
    (let loop ((ys xs))
      (cond ((null? ys) 0)
            ((= (count-of (car ys) all) 1) (car ys))
            (else (loop (cdr ys)))))))
(define (find-first xs)
  (if (null? xs) 0 (car xs)))
(define (solve nums) (find-single nums))
(define (run-case n nums)
  (display "CASE") (display n) (display "=")
  (display (solve nums)) (newline))
(define (run-cases)
  (begin
    (run-case 0 '(2 2 3 2))
    (run-case 1 '(0 1 0 1 0 1 99))
    (run-case 2 '(-5 -5 -5 -3))
    (run-case 3 '(1))
    (run-case 4 '(7 7 7 5 5 5 9))
    (run-case 5 '(4 4 4 4 4 4 42))
    (run-case 6 '(-1 -1 -1 2))
    (run-case 7 '(3 3 3 -3 -3 -3 8 8 8 100))))
(run-cases)
""",
    explorers=[
        ("freq-count", "(lambda (nums) (find-single nums))"),
        ("first-only", "(lambda (nums) (find-first nums))"),
    ],
)

_FRUIT = Recipe(
    slug="fruit-into-baskets",
    workspace=r"""
(define (length lst)
  (if (null? lst) 0 (+ 1 (length (cdr lst)))))
(define (list-ref lst i)
  (if (= i 0) (car lst) (list-ref (cdr lst) (- i 1))))
(define (fruit-n2 fruits)
  (let ((n (length fruits)))
    (let loop ((i 0) (best 0))
      (if (= i n)
          best
          (let inner ((j i) (seen1 #f) (v1 0) (seen2 #f) (v2 0) (len 0))
            (cond
              ((= j n)
               (loop (+ i 1) (if (> len best) len best)))
              ((not seen1)
               (inner (+ j 1) #t (list-ref fruits j) seen2 v2 (+ len 1)))
              ((and seen1 (not seen2) (= (list-ref fruits j) v1))
               (inner (+ j 1) seen1 v1 seen2 v2 (+ len 1)))
              ((and seen1 (not seen2))
               (inner (+ j 1) seen1 v1 #t (list-ref fruits j) (+ len 1)))
              ((and seen1 seen2 (or (= (list-ref fruits j) v1) (= (list-ref fruits j) v2)))
               (inner (+ j 1) seen1 v1 seen2 v2 (+ len 1)))
              (else
               (loop (+ i 1) (if (> len best) len best)))))))))
(define (fruit-broken fruits)
  (let ((n (length fruits)))
    (let loop ((i 0) (best 0))
      (if (= i n)
          best
          (let inner ((j i) (seen1 #f) (v1 0) (seen2 #f) (v2 0) (len 0))
            (cond
              ((= j n) (if (> len best) len best))
              ((not seen1)
               (inner (+ j 1) #t (list-ref fruits j) seen2 v2 (+ len 1)))
              ((and seen1 (not seen2) (= (list-ref fruits j) v1))
               (inner (+ j 1) seen1 v1 seen2 v2 (+ len 1)))
              ((and seen1 (not seen2))
               (inner (+ j 1) seen1 v1 #t (list-ref fruits j) (+ len 1)))
              ((and seen1 seen2 (or (= (list-ref fruits j) v1) (= (list-ref fruits j) v2)))
               (inner (+ j 1) seen1 v1 seen2 v2 (+ len 1)))
              (else (if (> len best) len best))))))))
(define (solve fruits) (fruit-n2 fruits))
(define (run-case n fruits)
  (display "CASE") (display n) (display "=")
  (display (solve fruits)) (newline))
(define (run-cases)
  (begin
    (run-case 0 '(3 3 3 1 2 1 1 2 3 3 4))
    (run-case 1 '(1 2 1))
    (run-case 2 '(1 2 3 4))
    (run-case 3 '(1 1 1 1))
    (run-case 4 '(1 2))
    (run-case 5 '(2 1 2 1))
    (run-case 6 '(0 1 2 2 3 4 4 5))
    (run-case 7 '(5))))
(run-cases)
""",
    explorers=[
        ("n2-fixed", "(lambda (fruits) (fruit-n2 fruits))"),
        ("n2-broken", "(lambda (fruits) (fruit-broken fruits))"),
    ],
)



_RANSOM = Recipe(
    slug="ransom-note",
    workspace=r"""
(define (make-counts n)
  (if (= n 26) '() (cons 0 (make-counts (+ n 1)))))
(define (add-at counts idx delta)
  (cond ((null? counts) '())
        ((= idx 0) (cons (+ (car counts) delta) (cdr counts)))
        (else (cons (car counts) (add-at (cdr counts) (- idx 1) delta)))))
(define (get-at counts idx)
  (if (= idx 0) (car counts) (get-at (cdr counts) (- idx 1))))
(define (char-idx c) (- (char->integer c) 97))
(define (process-mag i s counts)
  (if (>= i (string-length s))
      counts
      (process-mag (+ i 1) s (add-at counts (char-idx (string-ref s i)) 1))))
(define (process-ransom i s counts)
  (cond ((>= i (string-length s)) #t)
        ((= (get-at counts (char-idx (string-ref s i))) 0) #f)
        (else (process-ransom (+ i 1) s (add-at counts (char-idx (string-ref s i)) -1)))))
(define (can-construct ransom magazine)
  (if (> (string-length ransom) (string-length magazine))
      #f
      (process-ransom 0 ransom (process-mag 0 magazine (make-counts 0)))))
(define (always-true ransom magazine) #t)
(define (always-false ransom magazine) #f)
(define (solve ransom magazine) (can-construct ransom magazine))
(define (run-case n r m)
  (display "CASE") (display n) (display "=")
  (display (if (solve r m) "true" "false")) (newline))
(define (run-cases)
  (begin
    (run-case 0 "a" "b")
    (run-case 1 "aa" "ab")
    (run-case 2 "aa" "aab")
    (run-case 3 "abc" "aabbcc")
    (run-case 4 "abc" "abcc")
    (run-case 5 "abcd" "abc")
    (run-case 6 "" "abc")
    (run-case 7 "aabbcc" "abcabc")))
(run-cases)
""",
    explorers=[
        ("can-construct", "(lambda (ransom magazine) (can-construct ransom magazine))"),
        ("always-true", "(lambda (ransom magazine) (always-true ransom magazine))"),
        ("always-false", "(lambda (ransom magazine) (always-false ransom magazine))"),
    ],
)

_ONLINE = Recipe(
    slug="online-election",
    workspace=r"""
(define (length xs) (if (null? xs) 0 (+ 1 (length (cdr xs)))))
(define (nth xs i)
  (if (= i 0) (car xs) (nth (cdr xs) (- i 1))))
(define (count-vote counts person)
  (cond ((null? counts) (list (cons person 1)))
        ((= (car (car counts)) person)
         (cons (cons person (+ 1 (cdr (car counts)))) (cdr counts)))
        (else (cons (car counts) (count-vote (cdr counts) person)))))
(define (find-leader counts best best-c)
  (cond ((null? counts) best)
        (else
         (let ((p (car (car counts))) (c (cdr (car counts))))
           (if (or (> c best-c) (and (= c best-c) (< p best)))
               (find-leader (cdr counts) p c)
               (find-leader (cdr counts) best best-c))))))
(define (current-leader counts)
  (if (null? counts) #f
      (find-leader (cdr counts) (car (car counts)) (cdr (car counts)))))
(define (build-leaders votes-for)
  (let loop ((i 0) (counts '()) (leaders '()))
    (if (= i (length votes-for))
        (reverse leaders)
        (let ((nc (count-vote counts (nth votes-for i))))
          (loop (+ i 1) nc (cons (current-leader nc) leaders))))))
(define (upper-bound times t)
  (let loop ((lo 0) (hi (length times)))
    (if (>= lo hi) lo
        (let ((mid (quotient (+ lo hi) 2)))
          (if (<= (nth times mid) t)
              (loop (+ mid 1) hi)
              (loop lo mid))))))
(define (query leaders votes-at t)
  (cond ((null? votes-at) #f)
        ((< t (car votes-at)) #f)
        (else
         (let ((idx (- (upper-bound votes-at t) 1)))
           (if (< idx 0) #f (nth leaders idx))))))
(define (query-all leaders votes-at times)
  (let loop ((i 0) (acc '()))
    (if (= i (length times))
        (reverse acc)
        (loop (+ i 1) (cons (query leaders votes-at (nth times i)) acc)))))
(define (solve votes-at votes-for times)
  (query-all (build-leaders votes-for) votes-at times))
(define (solve-zero-sentinel votes-at votes-for times)
  (map (lambda (x) (if x x 0)) (solve votes-at votes-for times)))
(define (disp-one x)
  (cond ((not x) (display "null"))
        (else (display x))))
(define (print-list xs)
  (display "[")
  (cond ((null? xs) (display "]"))
        (else
          (disp-one (car xs))
          (let loop ((rest (cdr xs)))
            (cond ((null? rest) (display "]"))
                  (else (display ",") (disp-one (car rest)) (loop (cdr rest))))))))
(define (run-case n va vf times)
  (display "CASE") (display n) (display "=")
  (print-list (solve va vf times)) (newline))
(define (run-cases)
  (begin
    (run-case 0 '(0 5 10 15) '(1 2 2 1) '(3 12 15 20))
    (run-case 1 '(0 10 20) '(1 1 2) '(-5 0 5))
    (run-case 2 '(0 1 2 3) '(5 5 5 5) '(0 2 3 100))
    (run-case 3 '(0 5 10) '(1 2 3) '(0 5 10 15))
    (run-case 4 '(0 4 8 12 16 20) '(2 1 2 1 2 1) '(1 5 9 13 17 21))
    (run-case 5 '(0) '(42) '(0 1 2))
    (run-case 6 '(0 100 200 300) '(3 1 2 4) '(50 150 250 350))
    (run-case 7 '(0 5 10 15) '(2 1 1 3) '(3 8 12 16))))
(run-cases)
""",
    explorers=[
        ("null-sentinel", "(lambda (votes-at votes-for times) (query-all (build-leaders votes-for) votes-at times))"),
        ("leaders-only", "(lambda (votes-at votes-for times) (build-leaders votes-for))"),
    ],
)


RECIPES: dict[str, Recipe] = {
    r.slug: r
    for r in (_INTERSECTION, _TOP_K, _SINGLE_II, _FRUIT, _RANSOM, _ONLINE)
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
            start_new_session=True,
        )
    except subprocess.TimeoutExpired as exc:
        # Defense-in-depth: Soft #4131 fixed TERM; still killpg on timeout loops.
        try:
            import os
            import signal

            if getattr(exc, "pid", None):
                os.killpg(exc.pid, signal.SIGKILL)
        except Exception:
            pass
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

        # Explorer scoring mutates the parent FlatAST sequentially.
        # fiber:spawn isolation is not reliable for mutate→parent run-cases
        # (mutations may not apply, or leak inconsistently). denseness probe
        # still measures fiber_live; worldline_backend reflects that honesty.
        for name, body in recipe.explorers:
            body_esc = body.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
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
                    "via": "mutate:rebind",
                    "fiber_live_session": fiber_live,
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

        def _rank(e: dict[str, Any]) -> tuple:
            # Prefer more hits; deprioritize known-dummy explorers on ties.
            dummy = 1 if e["name"] in ("zero", "n2-broken", "xor-wrong") else 0
            return (int(e["hits"]), -dummy, e["name"])

        best, soft_sel = select_explorer_soft(
            explorers,
            score_key="hits",
            sess=sess,
            repo=repo,
            tie_key=_rank,
        )
        assert best is not None
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
                "soft_select": _soft_sel_meta(soft_sel),
                "denseness": denseness,
            }

        # Re-bootstrap workspace if any explorer left the serve session unhealthy
        # (failed mutate/eval can make subsequent current-source return empty).
        if any(e.get("mut_status") != "ok" or e.get("run_status") != "ok" for e in explorers):
            boot2 = sess.raw_line(f'(set-code "{esc}")', timeout_s=20.0)
            if boot2.get("status") != "ok":
                return {
                    "ok": False,
                    "reason": f"rebootstrap_failed:{boot2.get('msg') or boot2.get('status')}",
                    "slug": slug,
                    "baseline": baseline,
                    "explorers": explorers,
                    "fiber_live": fiber_live,
                    "aura_issue_candidate": True,
                }
            sess.raw_line("(eval-current)", timeout_s=SOFT_MUTATE_TIMEOUT_S)

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
            "soft_select": _soft_sel_meta(soft_sel),
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



# --- MiniMax Soft-runtime logic repair ------------------------------------

LLM_SYSTEM = """You repair a failing Aura (Lisp-like) program for an algorithm problem.
Rules:
- Output ONE complete Aura program in a ```aura fence (full file, not a patch).
- Keep (solve ...) as the algorithm entry; fix unbound names, parse errors, and wrong logic.
- You may use helpers; prefer plain Scheme-like Aura (define/cond/let/lambda). Avoid require unless needed.
- Study failing CASE diffs (input / got / expected) and stderr carefully: they show WHERE the
  algorithm is wrong (off-by-one, wrong order, missing edge empty/zero/negative, wrong DP base).
- Do NOT hardcode expected CASE outputs as bare display strings without calling solve —
  still compute via solve for each embedded input. Expected values are clues only.
- At the end, for each test input, call solve and print:
  (display "CASEi=") (display <result>) (newline)
  Prefer printing booleans as true/false strings; lists as compact JSON-like [a,b] when tests expect that.
- Prefer #t/#f internally. Keep programs small. No secrets.
"""


def _soft_escape(src: str) -> str:
    return src.strip().replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _pick_baseline(pdir: Path, tests: list[dict[str, Any]], *, aura_bin: str, repo: Path) -> dict[str, Any]:
    baseline: dict[str, Any] = {"ok": False, "hits": 0, "total": len(tests)}
    # Prefer prior Soft runtime partials when present (near-miss retries).
    for cand in (
        "solution_runtime.aura",
        "solution_repair.aura",
        "solution_2.aura",
        "solution.aura",
    ):
        cp = pdir / cand
        if not cp.is_file():
            continue
        sc = score_aura_file(repo, cp, tests, aura_bin=aura_bin)
        if int(sc.get("hits") or 0) >= int(baseline.get("hits") or 0):
            baseline = dict(sc)
            baseline["aura_file"] = cand
            baseline["src"] = cp.read_text(encoding="utf-8")
    return baseline


def _fail_case_details(tests: list[dict[str, Any]], got: dict[Any, str]) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for t in tests:
        tid = int(t.get("id", 0))
        exp = str(t.get("expected", "")).strip()
        g = got.get(tid)
        if g is None:
            g = got.get(str(tid))
        ok = g is not None and _values_match(str(g), exp)
        if not ok:
            details.append(
                {
                    "id": tid,
                    "ok": False,
                    "got": g,
                    "expected": exp,
                    "input": t.get("input"),
                }
            )
    return details


_TREE_HOSTILE_PREFIXES = (
    "binary-tree",
    "same-tree",
    "symmetric-tree",
    "invert-binary",
    "flatten-binary",
    "construct-binary",
    "serialize-and-deserialize",
    "diameter-of-binary",
    "path-sum",
    "minimum-depth-of-binary",
    "maximum-depth-of-binary",
    "balanced-binary",
    "validate-binary",
    "lowest-common-ancestor",
    "count-complete-tree",
)


def _is_tree_hostile(slug: str) -> bool:
    s = slug.lower()
    return any(s.startswith(p) or p in s for p in _TREE_HOSTILE_PREFIXES)


def _list_llm_targets(repo: Path, *, limit: int = 12) -> list[str]:
    """Near-full / mid partials without solution_runtime; skip Soft-hostile trees."""
    root = repo / "corpus" / "leetcode"
    rows: list[tuple[int, int, str]] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or (d / "solution_runtime.aura").is_file():
            continue
        if d.name in RECIPES or _is_tree_hostile(d.name):
            continue
        meta_p, tests_p = d / "meta.json", d / "tests.json"
        if not meta_p.is_file() or not tests_p.is_file():
            continue
        try:
            tests = json.loads(tests_p.read_text(encoding="utf-8"))
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(tests, list) or not tests:
            continue
        emb = max_embedded_list_chars(tests)
        if emb > MAX_LIST_JSON_CHARS:
            continue
        best_p, best_t = -1, 0
        for v in meta.get("variants") or []:
            p = int(v.get("tests_passed") or 0)
            tt = int(v.get("tests_total") or 0)
            if tt and p >= best_p:
                best_p, best_t = p, tt
        if best_t and 0 < best_p < best_t and best_p >= max(1, best_t - 4):
            rows.append((best_t - best_p, -best_p, d.name))
    rows.sort()
    return [name for _, _, name in rows[:limit]]


def _minimax_propose_aura(
    *,
    slug: str,
    problem_md: str,
    prior_src: str,
    stderr_snippet: str,
    fail_details: list[dict[str, Any]],
    tests: list[dict[str, Any]],
    cfg: Any,
    sess: Any | None,
    fiber_llm_ok: bool,
    scratch: Path,
    temperature: float,
    n: int = 2,
    seed_variants: list[dict[str, Any]] | None = None,
    feedback: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """Propose-only MiniMax: return list of aura sources + meta (llm_via measured).

    When ``seed_variants`` (Soft-swarm local multi-mutates) is provided, each
    concurrent worker is seeded with a mutated prior + feedback-accumulated
    prompt variation — not plain single-shot propose from one baseline.
    """
    from aura_build.fiber_llm import fiber_chat_completions
    from aura_build.minimax import chat_completions, extract_aura_source
    from aura_build.prompt_feedback import build_prompt_variation

    fail_lines = []
    for d in fail_details[:16]:
        inp = json.dumps(d.get("input"), ensure_ascii=False)
        if len(inp) > 220:
            inp = inp[:220] + "..."
        fail_lines.append(
            f"- CASE{d.get('id')}: input={inp}"
            f" | got={d.get('got')!r} | expected={d.get('expected')!r}"
            "  (fix algorithm so solve computes expected; do not print expected literally)"
        )
    if not fail_lines:
        fail_lines = ["(no CASE diffs; rely on stderr / prior)"]
    passing = max(0, len(tests) - len(fail_details))
    seeds = list(seed_variants or [])

    def _messages_for(i: int) -> list[dict[str, str]]:
        seed = seeds[i % len(seeds)] if seeds else None
        seed_src = str((seed or {}).get("src") or prior_src)
        seed_ops = list((seed or {}).get("ops") or [])
        seed_name = str((seed or {}).get("name") or "baseline")
        fb_suffix = build_prompt_variation(
            slug=slug,
            fail_details=fail_details,
            feedback=feedback,
            variant_i=i,
            mutate_seed_ops=seed_ops or None,
            mutate_seed_note=f"seed={seed_name}" if seed else None,
        )
        user = (
            f"Slug: {slug}\n"
            f"Soft score context: {passing}/{len(tests)} cases already pass; "
            f"{len(fail_details)} still fail — focus on the failing cases.\n\n"
            f"Problem:\n{problem_md[:2000]}\n\n"
            f"Prior Aura source (swarm-mutated seed={seed_name} ops={seed_ops or ['none']}; fix):\n"
            f"```aura\n{seed_src[:6500]}\n```\n\n"
            f"stderr (truncated):\n{(stderr_snippet or '')[:1000]}\n\n"
            f"Failing CASE diffs (clues only; do NOT hardcode expected into display):\n"
            + "\n".join(fail_lines)
            + "\n\n"
            + fb_suffix
            + "\n\nWrite a repaired complete solution.aura now that still prints CASE lines via solve."
        )
        return [
            {"role": "system", "content": LLM_SYSTEM},
            {"role": "user", "content": user},
        ]

    messages = _messages_for(0)
    sources: list[str] = []
    meta: dict[str, Any] = {"attempts": [], "llm_via": "none", "llm_ok": False}

    # High-speed MiniMax burn: parallel host propose when n>=4 (Soft owns select-best).
    # Cap by AURA_BUILD_LLM_PARALLEL_CAP (default 64) and AURA_BUILD_MINIMAX_CAP (default 32).
    # Fiber path stays available for n<4 denseness honesty / small probes.
    def _caps() -> tuple[int, int]:
        import os
        def _i(name: str, default: int) -> int:
            raw = (os.environ.get(name) or "").strip()
            try:
                return max(1, int(raw)) if raw else default
            except ValueError:
                return default
        return _i("AURA_BUILD_LLM_PARALLEL_CAP", 64), _i("AURA_BUILD_MINIMAX_CAP", 32)

    parallel_cap, minimax_cap = _caps()
    n_eff = max(1, min(int(n), parallel_cap, minimax_cap))
    meta["n_requested"] = int(n)
    meta["n"] = n_eff
    meta["parallel_cap"] = parallel_cap
    meta["minimax_cap"] = minimax_cap

    if n_eff >= 4:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import os

        def _one(i: int) -> tuple[int, str | None, dict[str, Any]]:
            temp = temperature + 0.05 * (i % 8)
            attempt: dict[str, Any] = {
                "i": i,
                "temperature": temp,
                "via": "host_parallel",
                "seeded": bool(seeds),
            }
            if seeds:
                attempt["seed_name"] = str(seeds[i % len(seeds)].get("name") or "")
                attempt["seed_ops"] = list(seeds[i % len(seeds)].get("ops") or [])
            try:
                resp = chat_completions(
                    _messages_for(i),
                    config=cfg,
                    temperature=temp,
                    max_tokens=3500,
                    timeout_s=90.0,
                )
            except Exception as exc:  # noqa: BLE001
                attempt["error"] = f"{type(exc).__name__}:{exc}"
                return i, None, attempt
            attempt["ok"] = bool(resp.get("ok") if isinstance(resp, dict) else False)
            usage = None
            if isinstance(resp, dict):
                usage = resp.get("usage") or (resp.get("data") or {}).get("usage")
                attempt["usage"] = usage
                content = ""
                if resp.get("content"):
                    content = str(resp.get("content") or "")
                elif resp.get("choices"):
                    try:
                        content = str(resp["choices"][0]["message"]["content"] or "")
                    except Exception:
                        content = str(resp.get("text") or "")
                else:
                    content = str(resp.get("text") or resp.get("display") or "")
            else:
                content = str(resp or "")
            src = extract_aura_source(content) if content else None
            attempt["extracted"] = bool(src)
            attempt["content_len"] = len(content or "")
            return i, src if src else None, attempt

        workers = min(n_eff, parallel_cap, minimax_cap, 32)
        meta["workers"] = workers
        meta["llm_via"] = "host_parallel"
        token_sum = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(_one, i) for i in range(n_eff)]
            for fut in as_completed(futs):
                i, src, attempt = fut.result()
                meta["attempts"].append(attempt)
                u = attempt.get("usage") if isinstance(attempt.get("usage"), dict) else None
                if u:
                    for k in token_sum:
                        try:
                            token_sum[k] += int(u.get(k) or 0)
                        except (TypeError, ValueError):
                            pass
                if src:
                    sources.append(src)
                    meta["llm_ok"] = True
        meta["tokens"] = token_sum
        meta["n_ok"] = len(sources)
        meta["seeded_n"] = len(seeds)
        meta["feedback_notes"] = len((feedback or {}).get("notes") or [])
        # Prefer Soft fiber denseness honesty stamp when measured (propose still host_parallel)
        if fiber_llm_ok:
            meta["fiber_llm_ok"] = True
            meta["propose_path"] = (
                "swarm_mutate_then_host_parallel_soft_select"
                if seeds
                else "host_parallel_soft_select"
            )
        elif seeds:
            meta["propose_path"] = "swarm_mutate_then_host_parallel"
        return sources, meta

    for i in range(max(1, n_eff)):
        temp = temperature + 0.15 * i
        attempt: dict[str, Any] = {"i": i, "temperature": temp}
        resp: dict[str, Any] = {}
        via = "host"
        if fiber_llm_ok and sess is not None:
            try:
                resp = fiber_chat_completions(
                    sess,
                    messages,
                    config=cfg,
                    scratch_dir=scratch,
                    temperature=temp,
                    max_tokens=3500,
                    timeout_s=120.0,
                )
                if resp.get("ok"):
                    via = "fiber"
                else:
                    attempt["fiber_err"] = resp.get("error") or resp.get("reason") or "fiber_not_ok"
                    # honest fallback to host MiniMax
                    resp = chat_completions(
                        messages,
                        config=cfg,
                        temperature=temp,
                        max_tokens=3500,
                        timeout_s=90.0,
                    )
                    via = "host_after_fiber_fail"
            except Exception as exc:  # noqa: BLE001
                resp = chat_completions(
                    messages,
                    config=cfg,
                    temperature=temp,
                    max_tokens=3500,
                    timeout_s=90.0,
                )
                via = "host_after_fiber_exc"
                attempt["fiber_exc"] = f"{type(exc).__name__}:{exc}"
        else:
            resp = chat_completions(
                messages,
                config=cfg,
                temperature=temp,
                max_tokens=3500,
                timeout_s=90.0,
            )
            via = "host"
        attempt["via"] = via
        attempt["ok"] = bool(resp.get("ok"))
        attempt["error"] = resp.get("error") or ""
        meta["attempts"].append(attempt)
        if not resp.get("ok"):
            continue
        src = extract_aura_source(str(resp.get("content") or ""))
        if src and "solve" in src and len(src) < 24000:
            sources.append(src)
            meta["llm_ok"] = True
            meta["llm_via"] = via if meta["llm_via"] == "none" else meta["llm_via"]
            meta["model"] = resp.get("model") or getattr(cfg, "model", "")
    # Prefer reporting fiber if any attempt used it successfully
    if any(a.get("via") == "fiber" and a.get("ok") for a in meta["attempts"]):
        meta["llm_via"] = "fiber"
    return sources, meta



def _is_session_transient(msg: object) -> bool:
    from aura_build.serve_session import is_session_transient

    return is_session_transient(msg)


def _stop_quiet(sess: Any) -> None:
    from aura_build.serve_session import stop_quiet

    stop_quiet(sess)


def _restart_soft_session(
    *,
    aura_bin: str,
    harness_root: Path,
    scratch: Path,
    cfg: Any,
) -> tuple[Any, bool, bool, dict[str, Any]]:
    """Restart Soft serve via shared serve_session.restart_session; re-probe denseness/fiber-llm."""
    from aura_build.fiber_llm import fiber_llm_probe
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import restart_session

    sess = restart_session(aura_bin=aura_bin, harness_root=harness_root)
    denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
    fiber_live = bool(denseness.get("ok"))
    probe = fiber_llm_probe(sess, scratch_dir=scratch, timeout_s=30.0, config=cfg)
    fiber_llm_ok = bool(probe.get("ok"))
    return sess, fiber_live, fiber_llm_ok, denseness



def _session_score_src(
    sess: Any,
    src: str,
    tests: list[dict[str, Any]],
    *,
    timeout_s: float = SOFT_EVAL_TIMEOUT_S,
) -> dict[str, Any]:
    esc = _soft_escape(src)
    boot = sess.raw_line(
        f'(set-code "{esc}")', timeout_s=min(SOFT_SET_CODE_TIMEOUT_S, timeout_s + 2)
    )
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "hits": 0,
            "total": len(tests),
            "status": boot.get("status"),
            "msg": msg,
            "reason": "set_code_failed",
            "transient": _is_session_transient(msg),
        }
    ev = sess.raw_line("(eval-current)", timeout_s=timeout_s)
    if _is_session_transient(ev.get("msg") or ev.get("status")):
        return {
            "ok": False,
            "hits": 0,
            "total": len(tests),
            "status": ev.get("status"),
            "msg": ev.get("msg"),
            "reason": "eval_transient",
            "transient": True,
        }
    # Top-level CASE prints often appear during eval-current
    stdout = str(ev.get("display") or "")
    if "CASE" not in stdout:
        run = sess.raw_line("(run-cases)", timeout_s=timeout_s)
        if _is_session_transient(run.get("msg") or run.get("status")):
            return {
                "ok": False,
                "hits": 0,
                "total": len(tests),
                "status": run.get("status"),
                "msg": run.get("msg"),
                "reason": "run_transient",
                "transient": True,
            }
        if run.get("status") == "ok":
            stdout = str(run.get("display") or "")
        else:
            # try common harness names
            for form in ("(run-tests)", "(main)", "(test-all)"):
                run = sess.raw_line(form, timeout_s=timeout_s)
                if "CASE" in str(run.get("display") or ""):
                    stdout = str(run.get("display") or "")
                    break
    hits, total, got = _score_stdout(stdout, tests)
    return {
        "ok": hits == total and total > 0,
        "hits": hits,
        "total": total,
        "got": {str(k): v for k, v in got.items()},
        "eval_status": ev.get("status"),
        "stdout_head": stdout[:240],
        "transient": False,
    }


def repair_llm(
    repo: Path,
    slug: str,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
    env_file: str | Path | None = None,
    proposals: int = 32,
) -> dict[str, Any]:
    """Soft serve + MiniMax propose-only → set-code worldlines → current-source."""
    from aura_build.fiber_llm import fiber_llm_probe
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.minimax import load_minimax_config
    from aura_build.serve_session import start_session

    pdir = repo / "corpus" / "leetcode" / slug
    if not pdir.is_dir():
        return {"ok": False, "reason": "missing_problem", "slug": slug}
    tests = json.loads((pdir / "tests.json").read_text(encoding="utf-8"))
    emb = max_embedded_list_chars(tests)
    if emb > MAX_LIST_JSON_CHARS:
        return {
            "ok": False,
            "reason": f"tests_too_large:{emb}>{MAX_LIST_JSON_CHARS}",
            "slug": slug,
            "skipped": True,
        }
    problem_md = ""
    if (pdir / "problem.md").is_file():
        problem_md = (pdir / "problem.md").read_text(encoding="utf-8")

    baseline = _pick_baseline(pdir, tests, aura_bin=aura_bin, repo=repo)
    if not baseline.get("src"):
        return {"ok": False, "reason": "no_baseline_src", "slug": slug, "baseline": baseline}

    if (pdir / "solution_runtime.aura").is_file():
        prev = score_aura_file(repo, pdir / "solution_runtime.aura", tests, aura_bin=aura_bin)
        if prev.get("ok"):
            return {
                "ok": True,
                "reason": "already_full_runtime",
                "slug": slug,
                "baseline": {k: baseline.get(k) for k in ("hits", "total", "aura_file", "ok")},
                "verify": prev,
                "skipped": True,
                "fiber_live": False,
                "out_path": str((pdir / "solution_runtime.aura").relative_to(repo)),
            }

    env_path = Path(env_file or Path.home() / ".config/aura-build/minimax.env")
    try:
        cfg = load_minimax_config(env_file=env_path)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"minimax_config:{exc}", "slug": slug}

    # oneshot baseline stderr for prompt
    env = _aura_env(repo, aura_bin)
    base_path = pdir / str(baseline.get("aura_file"))
    try:
        proc = subprocess.run(
            [aura_bin, str(base_path)],
            cwd=str(repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=SOFT_VERIFY_TIMEOUT_S,
            check=False,
            start_new_session=True,
        )
        stderr_snippet = (proc.stderr or "")[:1200]
        got_map = {}
        for line in (proc.stdout or "").splitlines():
            if line.startswith("CASE") and "=" in line:
                k, v = line.split("=", 1)
                try:
                    got_map[int(k[4:])] = v.strip()
                except ValueError:
                    pass
    except Exception as exc:  # noqa: BLE001
        stderr_snippet = f"timeout_or_err:{exc}"
        got_map = {}
    fail_details = _fail_case_details(tests, got_map)

    hroot = harness_root or (repo / ".aura-build")
    scratch = hroot / "soft_leetcode_llm" / slug
    scratch.mkdir(parents=True, exist_ok=True)
    sess = None
    fiber_live = False
    fiber_llm_ok = False
    denseness: dict[str, Any] = {}
    llm_meta: dict[str, Any] = {}
    explorers: list[dict[str, Any]] = []

    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        denseness = fiber_fanout_probe(sess, n=3, timeout_s=8.0)
        fiber_live = bool(denseness.get("ok"))
        probe = fiber_llm_probe(sess, scratch_dir=scratch, timeout_s=45.0, config=cfg)
        fiber_llm_ok = bool(probe.get("ok"))

        # --- Soft swarm local multi-mutation FIRST (ant/pso/abc rank → host mutate) ---
        from aura_build.prompt_feedback import load_feedback
        from aura_build.soft_swarm_mutate import swarm_mutate_candidates

        feedback_state = load_feedback(repo, hroot)
        mut_n = max(8, min(24, int(proposals)))
        mut_cands, mut_meta = swarm_mutate_candidates(
            str(baseline.get("src") or ""),
            n=mut_n,
            aura_bin=aura_bin,
            seed=424242 + (abs(hash(slug)) % 10000),
            prefer_kinds=["pso", "abc"],
            slug=slug,
            harness_root=hroot,
        )

        # Concurrent MiniMax burn seeded by mutated variants (not plain single-shot)
        proposals, llm_meta = _minimax_propose_aura(
            slug=slug,
            problem_md=problem_md,
            prior_src=str(baseline.get("src") or ""),
            stderr_snippet=stderr_snippet,
            fail_details=fail_details,
            tests=tests,
            cfg=cfg,
            sess=sess,
            fiber_llm_ok=fiber_llm_ok,
            scratch=scratch,
            temperature=0.25,
            n=proposals,
            seed_variants=mut_cands,
            feedback=feedback_state,
        )
        llm_meta["fiber_llm_probe"] = {
            "ok": probe.get("ok"),
            "reason": probe.get("reason") or probe.get("note"),
        }
        llm_meta["swarm_mutate"] = mut_meta

        candidates: list[tuple[str, str]] = [("baseline", str(baseline["src"]))]
        # Include local swarm-mutated lines as Soft-scored explorers (rule+mutate mix)
        for mc in mut_cands:
            candidates.append((str(mc.get("name") or "mut"), str(mc.get("src") or "")))
        for i, src in enumerate(proposals):
            candidates.append((f"llm-{i}", src))

        # After long host_parallel MiniMax proposes, Soft sock may be stale —
        # re-attach/ping before any set-code scoring (host fix; do not invent Ready).
        from aura_build.serve_session import ensure_session_ready

        sess, ready_meta = ensure_session_ready(
            sess, aura_bin=aura_bin, harness_root=hroot
        )
        llm_meta["pre_score_session"] = ready_meta
        if ready_meta.get("via") in ("restart", "cold_start"):
            denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
            fiber_live = bool(denseness.get("ok"))
            probe = fiber_llm_probe(sess, scratch_dir=scratch, timeout_s=30.0, config=cfg)
            fiber_llm_ok = bool(probe.get("ok"))

        # Restart budget scales with parallel propose fanout (was hard-capped at 2,
        # so after sock death mid-batch the remaining explorers all set_code_failed
        # → Soft select saw only zeros → honest no_gain).
        max_restarts = max(2, min(8, 2 + len(candidates) // 8))
        restarts = 0
        consecutive_fail = 0
        for name, src in candidates:
            sc = _session_score_src(sess, src, tests)
            need_restart = bool(sc.get("transient")) or (
                sc.get("reason") == "set_code_failed" and consecutive_fail >= 1
            )
            if need_restart and restarts < max_restarts:
                _stop_quiet(sess)
                sess, fiber_live, fiber_llm_ok, denseness = _restart_soft_session(
                    aura_bin=aura_bin,
                    harness_root=hroot,
                    scratch=scratch,
                    cfg=cfg,
                )
                # ensure sock actually answers before retry score
                sess, _ready2 = ensure_session_ready(
                    sess, aura_bin=aura_bin, harness_root=hroot
                )
                restarts += 1
                consecutive_fail = 0
                sc = _session_score_src(sess, src, tests)
            if sc.get("transient") or sc.get("reason") == "set_code_failed":
                consecutive_fail += 1
            else:
                consecutive_fail = 0
            explorers.append(
                {
                    "name": name,
                    "hits": int(sc.get("hits") or 0),
                    "total": int(sc.get("total") or 0),
                    "via": "set-code",
                    "ok": bool(sc.get("ok")),
                    "reason": sc.get("reason"),
                    "src": src,
                    "stdout_head": sc.get("stdout_head"),
                    "transient": bool(sc.get("transient")),
                    "session_restarts": restarts,
                }
            )
        llm_meta["score_session_restarts"] = restarts
        llm_meta["score_max_restarts"] = max_restarts

        if not explorers:
            return {
                "ok": False,
                "reason": "no_candidates",
                "slug": slug,
                "baseline": baseline,
                "llm": llm_meta,
                "fiber_live": fiber_live,
            }

        def _llm_rank(e: dict[str, Any]) -> tuple:
            return (int(e["hits"]), 0 if e["name"] != "baseline" else -1, e["name"])

        best, soft_sel = select_explorer_soft(
            explorers,
            score_key="hits",
            sess=sess,
            repo=repo,
            tie_key=_llm_rank,
        )
        # Soft pick-best sock transient after parallel propose → re-attach + retry once
        if soft_sel.get("transient") or str(soft_sel.get("reason") or "").startswith(
            "transient:"
        ):
            sess, ready_sel = ensure_session_ready(
                sess, aura_bin=aura_bin, harness_root=hroot
            )
            if not ready_sel.get("ok"):
                _stop_quiet(sess)
                sess, fiber_live, fiber_llm_ok, denseness = _restart_soft_session(
                    aura_bin=aura_bin,
                    harness_root=hroot,
                    scratch=scratch,
                    cfg=cfg,
                )
            best, soft_sel = select_explorer_soft(
                explorers,
                score_key="hits",
                sess=sess,
                repo=repo,
                tie_key=_llm_rank,
            )
            soft_sel = {**soft_sel, "pre_select_session": ready_sel}
        assert best is not None
        base_hits = int(baseline.get("hits") or 0)
        best_hits = int(best["hits"])
        # Strict improvement only (do not rewrite already-full Soft baselines).
        if best_hits <= base_hits:
            return {
                "ok": False,
                "reason": "no_gain_vs_baseline",
                "slug": slug,
                "baseline": {k: baseline.get(k) for k in ("hits", "total", "aura_file", "ok")},
                "selected": {k: best.get(k) for k in ("name", "hits", "total", "via")},
                "explorers": [
                    {k: e.get(k) for k in ("name", "hits", "total", "via", "ok", "reason")}
                    for e in explorers
                ],
                "llm": llm_meta,
                "fiber_live": fiber_live,
                "fiber_llm_ok": fiber_llm_ok,
                "soft_select": _soft_sel_meta(soft_sel),
                "denseness": {"ok": denseness.get("ok"), "note": denseness.get("note")},
            }

        # Materialize winner via set-code + current-source (restart once on transient sock errors)
        win_src = str(best.get("src") or "")
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=SOFT_SET_CODE_TIMEOUT_S
        )
        if boot.get("status") != "ok" and _is_session_transient(boot.get("msg")):
            _stop_quiet(sess)
            sess, fiber_live, fiber_llm_ok, denseness = _restart_soft_session(
                aura_bin=aura_bin,
                harness_root=hroot,
                scratch=scratch,
                cfg=cfg,
            )
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=SOFT_SET_CODE_TIMEOUT_S
            )
        if boot.get("status") != "ok":
            out_path = pdir / "solution_runtime.aura"
            note = str(boot.get("msg") or boot.get("status") or "set_code_failed")
            banner = (
                f"; soft_leetcode_runtime slug={slug} path=llm\n"
                f"; materialize=proposed_source_fallback worldline_backend="
                f"{'fiber_graph' if fiber_live else 'serve_mutate'}\n"
                f"; fiber_live={'true' if fiber_live else 'false'} incr_proven=false\n"
                f"; llm_via={llm_meta.get('llm_via')} note=winner_set_code_failed:{note}\n"
                f"; selected={best['name']} hits={best['hits']}/{best['total']}\n"
                f"; baseline_hits={baseline.get('hits')}/{baseline.get('total')}\n"
                "; Expected values used only for host scoring / LLM context, not hardcoded into display.\n"
            )
            out_path.write_text(banner + win_src + "\n", encoding="utf-8")
            verify = score_aura_file(repo, out_path, tests, aura_bin=aura_bin)
            improved = int(verify.get("hits") or 0) > int(baseline.get("hits") or 0)
            full = bool(verify.get("ok"))
            return {
                "ok": full or improved,
                "reason": (
                    "full"
                    if full
                    else ("improved" if improved else "winner_set_code_failed_fallback")
                ),
                "slug": slug,
                "out_path": str(out_path.relative_to(repo)),
                "baseline": {k: baseline.get(k) for k in ("hits", "total", "aura_file", "ok")},
                "verify": verify,
                "selected": {k: best.get(k) for k in ("name", "hits", "total", "via")},
                "explorers": [
                    {k: e.get(k) for k in ("name", "hits", "total", "via", "ok", "reason")}
                    for e in explorers
                ],
                "fiber_live": fiber_live,
                "fiber_llm_ok": fiber_llm_ok,
                "incr_proven": False,
                "worldline_backend": "fiber_graph" if fiber_live else "serve_mutate",
                "llm_ok": bool(llm_meta.get("llm_ok")),
                "llm_via": llm_meta.get("llm_via"),
                "model": llm_meta.get("model"),
                "llm": llm_meta,
                "materialize": "proposed_source_fallback",
                "improved": improved,
                "full": full,
                "aura_issue_candidate": False,
            }
        sess.raw_line("(eval-current)", timeout_s=SOFT_EVAL_TIMEOUT_S)
        cs = sess.raw_line("(display (current-source :workspace :pretty))", timeout_s=20.0)
        src_out = str(cs.get("display") or "").strip()
        materialize = "current-source"
        if not src_out or "solve" not in src_out:
            # Honest fallback: write proposed source (not Soft unparse)
            src_out = win_src
            materialize = "proposed_source_fallback"
        out_path = pdir / "solution_runtime.aura"
        banner = (
            f"; soft_leetcode_runtime slug={slug} path=llm\n"
            f"; materialize={materialize} worldline_backend="
            f"{'fiber_graph' if fiber_live else 'serve_mutate'}\n"
            f"; fiber_live={'true' if fiber_live else 'false'} incr_proven=false\n"
            f"; llm_via={llm_meta.get('llm_via')} fiber_llm_ok={'true' if fiber_llm_ok else 'false'}\n"
            f"; selected={best['name']} hits={best['hits']}/{best['total']}\n"
            f"; baseline_hits={baseline.get('hits')}/{baseline.get('total')}\n"
            "; Expected values used only for host scoring / LLM context, not hardcoded into display.\n"
        )
        out_path.write_text(banner + src_out + "\n", encoding="utf-8")
        verify = score_aura_file(repo, out_path, tests, aura_bin=aura_bin)
        # If current-source unparse broke scoring, fall back to raw proposed source
        if (
            materialize == "current-source"
            and int(verify.get("hits") or 0) < int(best["hits"])
            and win_src
        ):
            out_path.write_text(
                banner.replace("materialize=current-source", "materialize=proposed_source_fallback")
                + win_src
                + "\n",
                encoding="utf-8",
            )
            verify = score_aura_file(repo, out_path, tests, aura_bin=aura_bin)
            materialize = "proposed_source_fallback"
        improved = int(verify.get("hits") or 0) > base_hits
        full = bool(verify.get("ok"))
        return {
            "ok": full or improved,
            "reason": "full" if full else ("improved" if improved else "verify_no_gain"),
            "slug": slug,
            "out_path": str(out_path.relative_to(repo)),
            "baseline": {k: baseline.get(k) for k in ("hits", "total", "aura_file", "ok")},
            "verify": verify,
            "selected": {k: best.get(k) for k in ("name", "hits", "total", "via")},
            "explorers": [
                {k: e.get(k) for k in ("name", "hits", "total", "via", "ok", "reason")}
                for e in explorers
            ],
            "fiber_live": fiber_live,
            "fiber_llm_ok": fiber_llm_ok,
            "soft_select": _soft_sel_meta(soft_sel),
            "incr_proven": False,
            "worldline_backend": "fiber_graph" if fiber_live else "serve_mutate",
            "denseness": {"ok": denseness.get("ok"), "note": denseness.get("note")},
            "llm_ok": bool(llm_meta.get("llm_ok")),
            "llm_via": llm_meta.get("llm_via"),
            "model": llm_meta.get("model"),
            "llm": llm_meta,
            "materialize": materialize,
            "src_len": len(src_out),
            "improved": improved,
            "full": full,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"exc:{type(exc).__name__}:{exc}",
            "slug": slug,
            "baseline": {k: baseline.get(k) for k in ("hits", "total", "aura_file", "ok")},
            "llm": llm_meta,
            "fiber_live": fiber_live,
            "aura_issue_candidate": True,
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
            "model": str(result.get("model") or "soft-serve-fiber"),
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "llm_ok": bool(result.get("llm_ok")),
            "llm_via": result.get("llm_via"),
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
    """LeetCode Soft transform path — first-class when inventory nonempty.

    Latency breakdown + adaptive explorer/worldline policy serve dual goal:
    throughput AND accuracy of code transforms while aura-build self-evolves.
    """
    from aura_build.self_evolve_strategy import (
        LatencyClock,
        effective_explorer_cap,
        effective_worldlines,
        leetcode_inventory_nonempty,
        load_strategy,
        observe_llm_round,
        save_strategy,
    )

    repo = Path(getattr(args, "repo", None) or Path.cwd()).resolve()
    aura_bin = (
        getattr(args, "aura_bin", None)
        or os.environ.get("AURA_BIN")
        or DEFAULT_SOFT
    )
    _lc_clock = LatencyClock(session="soft_leetcode")
    _lc_state = load_strategy(repo)
    _lc_inv = leetcode_inventory_nonempty(repo)
    print(
        json.dumps(
            {
                "event": "soft_leetcode_strategy",
                "inventory_nonempty": _lc_inv,
                "worldlines": effective_worldlines(_lc_state),
                "explorer_cap": effective_explorer_cap(_lc_state),
                "mix_explorers": _lc_state.get("mix_explorers") or ["rule", "mutate", "llm"],
                "llm_rounds": _lc_state.get("llm_rounds") or 0,
                "note": (
                    "first-class transform path when inventory nonempty; "
                    "mix explorers=rule+mutate+MiniMax propose-only (Soft select-best); "
                    "skip invent soft_* only when combat/leetcode empty; "
                    "prefer Soft-native; never invent Soft Ready"
                ),
            },
            ensure_ascii=False,
        )
    )
    # per-slug wall timed inside loop (transform closed-loop)
    slug = getattr(args, "slug", None) or ""
    batch = bool(getattr(args, "batch", False))
    batch_llm = bool(getattr(args, "batch_llm", False))
    force_llm = bool(getattr(args, "llm", False))
    proposals = int(getattr(args, "proposals", 32) or 32)
    harness_root = Path(getattr(args, "harness_root", None) or (repo / ".aura-build"))
    env_file = getattr(args, "env_file", None) or str(
        Path.home() / ".config/aura-build/minimax.env"
    )

    slugs: list[str] = []
    mode = "recipe"
    if batch_llm or (force_llm and batch):
        mode = "llm"
        lim = int(getattr(args, "limit", 8) or 8)
        slugs = _list_llm_targets(repo, limit=lim)
        if not slugs:
            print(json.dumps({"ok": False, "reason": "no_llm_targets"}))
            return 2
    elif batch:
        mode = "recipe"
        slugs = [s for s in RECIPES if s != "intersection-of-two-arrays"]
        inter = repo / "corpus/leetcode/intersection-of-two-arrays/solution_runtime.aura"
        if not inter.is_file():
            slugs = ["intersection-of-two-arrays"] + slugs
    elif force_llm or (slug and slug not in RECIPES):
        mode = "llm"
        if not slug:
            # default: first LLM target
            targets = _list_llm_targets(repo, limit=1)
            if not targets:
                print(json.dumps({"ok": False, "reason": "no_llm_targets"}))
                return 2
            slug = targets[0]
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
        slugs = [slug]
    else:
        mode = "recipe"
        if not slug:
            slug = "top-k-frequent-elements"
        if slug == "contains-duplicate":
            print(
                json.dumps(
                    {
                        "ok": False,
                        "reason": "contains_duplicate_deferred_case7_too_large",
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
                        "hint": "pass --llm for MiniMax Soft path on any small partial",
                    }
                )
            )
            return 2
        slugs = [slug]

    results: list[dict[str, Any]] = []
    commit_paths: list[str] = ["src/aura_build/soft_leetcode_runtime.py"]
    for s in slugs:
        _lc_clock.start("pursue_round")
        if mode == "llm":
            result = repair_llm(
                repo,
                s,
                aura_bin=str(aura_bin),
                harness_root=harness_root,
                env_file=env_file,
                proposals=proposals,
            )
        else:
            result = repair_recipe(
                repo, RECIPES[s], aura_bin=str(aura_bin), harness_root=harness_root
            )
        _lc_clock.end(
            "pursue_round",
            ok=bool(result.get("ok")),
            fiber_live=bool(result.get("fiber_live")) if "fiber_live" in result else None,
            extra={"slug": result.get("slug") or s},
        )
        result["latency"] = _lc_clock.summary(
            fiber_live=bool(result.get("fiber_live")) if "fiber_live" in result else None
        )
        print(json.dumps({"event": "soft_leetcode_runtime", **result}, ensure_ascii=False))
        print(json.dumps({"event": "soft_leetcode_latency", **result["latency"]}, ensure_ascii=False))
        # Continuous strategy evolution from latency+accuracy (MiniMax propose + Soft verify)
        vfy = result.get("verify") or {}
        base = result.get("baseline") or {}
        # Prefer post-verify hits; on no_gain Soft may omit verify — use selected/baseline.
        # When sock death zeroed session scores, selected.hits can be 0 while oneshot
        # baseline still holds — report max for strategy accuracy (never invent gain).
        selected = result.get("selected") or {}
        passed = vfy.get("hits")
        if passed is None:
            sel_h = selected.get("hits")
            base_h = base.get("hits")
            if sel_h is not None and base_h is not None:
                passed = max(int(sel_h), int(base_h))
            elif sel_h is not None:
                passed = sel_h
            else:
                passed = base_h
        total = vfy.get("total") or selected.get("total") or base.get("total")
        lat = result.get("latency") or {}
        llm_meta = result.get("llm") or {}
        llm_via = (
            result.get("llm_via")
            or llm_meta.get("llm_via")
            or ("recipe" if mode != "llm" else None)
        )
        if not llm_via:
            llm_via = "recipe" if mode != "llm" else "none"
        tokens = (
            result.get("tokens")
            or result.get("llm_tokens")
            or llm_meta.get("tokens")
        )
        _lc_state = observe_llm_round(
            _lc_state,
            slug=str(result.get("slug") or s),
            ok=bool(result.get("ok")),
            llm_via=str(llm_via) if llm_via is not None else None,
            proposals=int(
                result.get("proposals_n")
                or result.get("n_proposals")
                or llm_meta.get("n_ok")
                or llm_meta.get("n")
                or len(result.get("explorers") or [])
                or proposals
                or 0
            ),
            passed=int(passed) if passed is not None else None,
            total=int(total) if total is not None else None,
            latency_ms=int(lat.get("total_ms") or 0) or None,
            fiber_live=bool(result.get("fiber_live")) if "fiber_live" in result else None,
            tokens=tokens,
        )
        save_strategy(repo, _lc_state, harness_root)
        # Durable feedback-accumulated prompts + sock-vs-quality no_gain analysis
        from aura_build.prompt_feedback import (
            classify_no_gain_cause,
            load_feedback,
            observe_transform_feedback,
            save_feedback,
        )

        cause = None
        if not result.get("ok"):
            cause = classify_no_gain_cause(
                explorers=list(result.get("explorers") or []),
                soft_select=result.get("soft_select") if isinstance(result.get("soft_select"), dict) else None,
                baseline_hits=int(base.get("hits")) if base.get("hits") is not None else None,
                selected_hits=int(selected.get("hits")) if selected.get("hits") is not None else None,
                pre_score_session=(llm_meta.get("pre_score_session") or {}),
            )
            result["no_gain_cause"] = cause
            _lc_state["last_no_gain_cause"] = cause
            save_strategy(repo, _lc_state, harness_root)
        fb = load_feedback(repo, harness_root)
        mut_ops = []
        sm = llm_meta.get("swarm_mutate") or {}
        if isinstance(sm.get("ranked_ops"), list):
            mut_ops = list(sm.get("ranked_ops") or [])[:6]
        fb = observe_transform_feedback(
            fb,
            slug=str(result.get("slug") or s),
            ok=bool(result.get("ok")),
            reason=str(result.get("reason") or ""),
            fail_details=None,
            selected_hits=int(selected.get("hits")) if selected.get("hits") is not None else None,
            baseline_hits=int(base.get("hits")) if base.get("hits") is not None else None,
            total=int(total) if total is not None else None,
            no_gain_cause=cause if not result.get("ok") else "gain",
            llm_via=str(llm_via) if llm_via else None,
            mutate_ops=mut_ops,
            harness_root=harness_root,
            aura_bin=aura_bin,
        )
        save_feedback(repo, fb, harness_root)
        print(
            json.dumps(
                {
                    "event": "soft_leetcode_feedback",
                    "slug": result.get("slug") or s,
                    "no_gain_cause": cause,
                    "feedback_notes": len(fb.get("notes") or []),
                    "swarm_rank_via": sm.get("rank_via"),
                    "swarm_n": sm.get("n"),
                    "propose_path": llm_meta.get("propose_path"),
                },
                ensure_ascii=False,
            )
        )
        print(
            json.dumps(
                {
                    "event": "self_evolve_strategy_llm",
                    "slug": result.get("slug") or s,
                    "llm_via": _lc_state.get("last_llm_via"),
                    "pass_rate": _lc_state.get("last_transform_pass_rate"),
                    "problems_per_min": _lc_state.get("last_problems_per_min"),
                    "worldlines": _lc_state.get("worldlines"),
                    "mix_explorers": _lc_state.get("mix_explorers"),
                    "llm_rounds": _lc_state.get("llm_rounds"),
                },
                ensure_ascii=False,
            )
        )
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
                "mode": mode,
                "attempted": len(results),
                "full": [r.get("slug") for r in fulls],
                "improved": [r.get("slug") for r in improved],
                "failed": [
                    r.get("slug") for r in results if not r.get("ok") and not r.get("skipped")
                ],
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
    llm_any = any(r.get("llm_ok") for r in winners)
    msg = (
        "chore(corpus): soft runtime repair "
        + ", ".join(parts)
        + f" materialize=current-source fiber_live={'true' if fl_any else 'false'}"
        + (f" llm_via={winners[0].get('llm_via')}" if llm_any else "")
    )
    seen: set[str] = set()
    uniq = []
    for pth in commit_paths:
        if pth not in seen:
            seen.add(pth)
            uniq.append(pth)

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
