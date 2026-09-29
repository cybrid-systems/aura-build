"""Soft runtime self-evolve: Soft serve fiber worldlines → current-source → commit.

North-star dogfood (not corpus-gen repair):

1. Prefer long-lived Soft ``--serve`` when attach works.
2. Denseness probe ``(fiber:join (fiber:spawn …))`` — never invent fiber_live.
3. When denseness ok: spawn N fiber explorers (sequential Soft Ready oneshots;
   each ``fiber:spawn`` + ``mutate:rebind`` + observe on the same FlatAST),
   select-best, rebind winner, ``(current-source :workspace :pretty)``, write stamp
   with ``fiber_live=true`` only when probe measured.
4. On denseness / serve fail: honest fallback to oneshot
   ``aura/self_evolve_runtime.aura`` (mutate → select → current-source) with
   ``fiber_live=false``.

Host verifies stamp banner honesty, then commits+pushes only the selected
materialized stamp (and runtime kernel when changed).

Latency breakdown (wall-clock phases) emits in JSON events + progress summary
via ``self_evolve_strategy.LatencyClock``. Adaptive strategy shortens rounds:
skip Soft-native-green / already-green denseness rematerialize, early oneshot
on explorer hang, shrink worldlines after fast soft_ready pursue. Soft bugs →
Aura issues only. Combat/LeetCode inventory nonempty → first-class transforms;
skip invent soft_* only when empty.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from aura_build.self_evolve_host import git_commit_and_maybe_push, run_host_verify
from aura_build.stamp_banner import stamp_banner_agrees

DEFAULT_SOFT = "/workspace/aura-grok/build/aura"
RUNTIME_KERNEL = "aura/self_evolve_runtime.aura"
STAMP_PATH = "aura/self_evolve_stamp.aura"
HELPER_PATH = "aura/soft_worldline_pick.aura"
STARTS_HELPER_PATH = "aura/soft_starts_with.aura"
ENDS_HELPER_PATH = "aura/soft_ends_with.aura"
CONTAINS_HELPER_PATH = "aura/soft_contains.aura"
SPLIT_HELPER_PATH = "aura/soft_split.aura"
REPLACE_HELPER_PATH = "aura/soft_replace.aura"
TRIM_HELPER_PATH = "aura/soft_trim.aura"
DOWNCASE_HELPER_PATH = "aura/soft_downcase.aura"
UPCASE_HELPER_PATH = "aura/soft_upcase.aura"
PAD_HELPER_PATH = "aura/soft_pad.aura"
TAKE_HELPER_PATH = "aura/soft_take.aura"
DROP_HELPER_PATH = "aura/soft_drop.aura"
LIST_TAKE_HELPER_PATH = "aura/soft_list_take.aura"
LIST_DROP_HELPER_PATH = "aura/soft_list_drop.aura"
MAKE_LIST_HELPER_PATH = "aura/soft_make_list.aura"
FOR_EACH_HELPER_PATH = "aura/soft_for_each.aura"
HASH_FOR_EACH_HELPER_PATH = "aura/soft_hash_for_each.aura"
HASH_FOLD_HELPER_PATH = "aura/soft_hash_fold.aura"
FOLDR_HELPER_PATH = "aura/soft_foldr.aura"
HASH_EMPTY_HELPER_PATH = "aura/soft_hash_empty.aura"
HASH_TO_LIST_HELPER_PATH = "aura/soft_hash_to_list.aura"
ANY_HELPER_PATH = "aura/soft_any.aura"
ALL_HELPER_PATH = "aura/soft_all.aura"
LAST_HELPER_PATH = "aura/soft_last.aura"
FIND_HELPER_PATH = "aura/soft_find.aura"
COUNT_HELPER_PATH = "aura/soft_count.aura"
REMOVE_HELPER_PATH = "aura/soft_remove.aura"
DELETE_HELPER_PATH = "aura/soft_delete.aura"
DEFAULT_BUMPS = (2, 9, 4, 7, 1)
# Soft fiber:spawn+mutate:rebind oneshots hang past ~64 sequential joins
# (fiber:join WARN defuse_version storm → sock stall). Cap explorers;
# denseness honesty remains fiber_fanout_probe (1 spawn+join). Prefer
# Soft prefer-session for wl=256 pursue; runtime stamp does not need 256 joins.
# Adaptive strategy (self_evolve_strategy) may LOWER effective cap on hang
# observations — never raise above this ceiling. Do not invent Soft Ready.
FIBER_EXPLORER_CAP = 32

_RUNTIME_OK_RE = re.compile(
    r"RUNTIME_OK\s+selected=(?P<selected>\S+)\s+observed=(?P<observed>\S+)"
    r"\s+src_len=(?P<src_len>\d+)\s+wrote=(?P<wrote>\S+)"
)


def _as_num(v: Any) -> int:
    try:
        return int(float(str(v)))
    except (TypeError, ValueError):
        return -999_999


def _build_stamp_body(
    *,
    src: str,
    traj: str,
    gen: int,
    selected: int,
    observed: int,
    src_len: int,
    fiber_live: bool,
    worldline_backend: str,
    denseness_note: str,
) -> str:
    fl = "true" if fiber_live else "false"
    fl_lit = "#t" if fiber_live else "#f"
    return (
        "; aura-build self-evolve stamp — materialized via (current-source :workspace :pretty)\n"
        "; Not Soft Ready invent. fiber_live / incr_proven only when measured.\n"
        f"; traj_id={traj}\n"
        f"; generation={gen}\n"
        f"; selected={selected}\n"
        f"; observed={observed}\n"
        f"; src_len={src_len}\n"
        "; verify_ok=true\n"
        "; incr_proven=false\n"
        f"; fiber_live={fl}\n"
        "; kernel=aura\n"
        "; materialize=current-source\n"
        f"; worldline_backend={worldline_backend}\n"
        f"; denseness={denseness_note}\n"
        "(export stamp-info)\n"
        "(define (stamp-info)\n"
        f'  (hash "traj_id" "{traj}"\n'
        f'        "generation" {gen}\n'
        f'        "selected" {selected}\n'
        f'        "observed" {observed}\n'
        '        "kernel" "aura"\n'
        '        "materialize" "current-source"\n'
        f'        "worldline_backend" "{worldline_backend}"\n'
        '        "incr_proven" #f\n'
        f'        "fiber_live" {fl_lit}))\n'
        "; --- winner FlatAST unparse ---\n"
        f"{src.rstrip()}\n"
    )


def _validate_stamp(repo: Path, *, expect_fiber_live: bool | None = None) -> dict[str, Any]:
    stamp = repo / STAMP_PATH
    if not stamp.is_file():
        return {"ok": False, "reason": "stamp_not_written"}
    text = stamp.read_text(encoding="utf-8")
    if "materialize=current-source" not in text:
        return {"ok": False, "reason": "stamp_missing_materialize_tag"}
    if "(define cand" not in text and "(define (cand" not in text:
        return {
            "ok": False,
            "reason": "stamp_missing_unparse_body",
            "aura_issue_candidate": True,
        }
    if not stamp_banner_agrees(text):
        return {"ok": False, "reason": "stamp_banner_mismatch"}
    if expect_fiber_live is True and "; fiber_live=true" not in text:
        return {"ok": False, "reason": "stamp_expected_fiber_live_true"}
    if expect_fiber_live is False and "; fiber_live=false" not in text:
        return {"ok": False, "reason": "stamp_expected_fiber_live_false"}
    return {"ok": True, "text": text}


def _run_soft_oneshot(
    repo: Path,
    *,
    aura_bin: str,
    timeout_s: float = 60.0,
) -> dict[str, Any]:
    """Fallback: cold Soft oneshot kernel (fiber_live=false)."""
    env = os.environ.copy()
    env["AURA_SANDBOX"] = env.get("AURA_SANDBOX") or "off"
    env["AURA_PIPELINE_STRICT"] = env.get("AURA_PIPELINE_STRICT") or "0"
    aura_path = env.get("AURA_PATH") or f"{repo.parent}/aura-grok/lib:{repo}/aura"
    env["AURA_PATH"] = aura_path
    kernel = repo / RUNTIME_KERNEL
    if not kernel.is_file():
        return {"ok": False, "reason": "runtime_kernel_missing", "path": str(kernel)}
    if not Path(aura_bin).is_file():
        return {"ok": False, "reason": "aura_bin_missing", "aura_bin": aura_bin}
    try:
        proc = subprocess.run(
            [aura_bin, str(kernel)],
            cwd=str(repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "reason": "soft_timeout",
            "stdout": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else "",
            "aura_issue_candidate": True,
        }
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    m = _RUNTIME_OK_RE.search(out)
    fail = "RUNTIME_FAIL" in out or "current-source-empty" in out
    if (proc.returncode != 0 and not m) or fail or not m:
        return {
            "ok": False,
            "reason": "oneshot_fail_or_unparsed",
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "")[-2000:],
            "stderr": (proc.stderr or "")[-2000:],
            "aura_issue_candidate": True,
            "tip_note": "Soft oneshot current-source materialize failed",
        }
    v = _validate_stamp(repo, expect_fiber_live=False)
    if not v.get("ok"):
        return {**v, "selected": m.group("selected"), "observed": m.group("observed")}
    return {
        "ok": True,
        "reason": "oneshot_ok",
        "selected": m.group("selected"),
        "observed": m.group("observed"),
        "src_len": int(m.group("src_len")),
        "wrote": m.group("wrote"),
        "stamp_path": STAMP_PATH,
        "materialize": "current-source",
        "worldline_backend": "oneshot_mutate",
        "incr_proven": False,
        "fiber_live": False,
        "session_model": "oneshot",
        "kernel": "aura",
        "stdout": (proc.stdout or "")[-1500:],
        "exit_code": proc.returncode,
        "fallback": True,
    }



def _soft_escape(code: str) -> str:
    return (
        code.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


# Candidate Soft worldline-pick helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "max-loop",
        "(export pick-best)\n"
        "(define (pick-best xs)\n"
        "  (let loop ((rest xs) (best -999999))\n"
        "    (if (null? rest)\n"
        "        best\n"
        "        (loop (cdr rest)\n"
        "              (if (> (car rest) best) (car rest) best)))))\n",
    ),
    (
        "max-fold",
        "(export pick-best)\n"
        "(define (pick-best xs)\n"
        "  (if (null? xs)\n"
        "      -999999\n"
        "      (let ((h (car xs)) (t (cdr xs)))\n"
        "        (if (null? t)\n"
        "            h\n"
        "            (let ((r (pick-best t)))\n"
        "              (if (> h r) h r))))))\n",
    ),
    (
        "max-scan",
        "(export pick-best)\n"
        "(define (pick-best xs)\n"
        "  (define (go rest best)\n"
        "    (if (null? rest)\n"
        "        best\n"
        "        (go (cdr rest) (if (> (car rest) best) (car rest) best))))\n"
        "  (if (null? xs) -999999 (go (cdr xs) (car xs))))\n",
    ),
]


def _score_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score a pick-best helper: known vector must select 9."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    r = sess.raw_line("(pick-best (list 2 9 4 7 1))", timeout_s=timeout_s)
    msg = r.get("msg") or r.get("status")
    if is_session_transient(msg):
        return {"ok": False, "observed": None, "msg": msg, "transient": True}
    obs = _as_num(r.get("value"))
    ok = r.get("status") == "ok" and obs == 9
    return {
        "ok": ok,
        "observed": obs if r.get("status") == "ok" else None,
        "status": r.get("status"),
        "msg": msg,
        "transient": False,
    }


def _run_soft_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → helper candidates → select-best → current-source.

    Materializes ``aura/soft_worldline_pick.aura`` (real kernel helper, not stamp-only).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _HELPER_CANDIDATES:
            sc = _score_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        best = next((e for e in ok_ex if e["name"] == "max-loop"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "pick-best" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_worldline_pick",
            }

        # Soft tip cbae122+: #4132 fixed — export names come from Soft unparse;
        # do not host-restore or invent soft_export_restored.
        if "(export pick-best)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized worldline pick helper (self-evolve runtime)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Not stamp dogfood — real kernel helper used by Soft runtime path.\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line("(pick-best (list 2 9 4 7 1))", timeout_s=8.0)
        v_ok = verify.get("status") == "ok" and _as_num(verify.get("value")) == 9

        return {
            "ok": bool(v_ok),
            "reason": "helper_evolved" if v_ok else "helper_verify_fail",
            "path": HELPER_PATH,
            "selected": best["name"],
            "observed": 9,
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)


# Candidate Soft starts-with? helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
_STARTS_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "prefix-loop",
        "(export starts-with?)\n"
        "(define (starts-with? s pre)\n"
        "  (let ((n (string-length pre))\n"
        "        (m (string-length s)))\n"
        "    (if (> n m)\n"
        "        #f\n"
        "        (equal? (substring s 0 n) pre))))\n",
    ),
    (
        "prefix-nested",
        "(export starts-with?)\n"
        "(define (starts-with? s pre)\n"
        "  (let ((n (string-length pre)))\n"
        "    (let ((m (string-length s)))\n"
        "      (if (> n m)\n"
        "          #f\n"
        "          (equal? (substring s 0 n) pre)))))\n",
    ),
    (
        "prefix-cond",
        "(export starts-with?)\n"
        "(define (starts-with? s pre)\n"
        "  (let ((n (string-length pre))\n"
        "        (m (string-length s)))\n"
        "    (cond ((> n m) #f)\n"
        "          (else (equal? (substring s 0 n) pre)))))\n",
    ),
]


def _truthy_soft(v: Any) -> bool:
    s = str(v).strip().lower()
    return s in ("#t", "true", "1")


def _score_starts_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score starts-with? helper against a small known vector."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        ('(starts-with? "hello" "he")', True),
        ('(starts-with? "hello" "hex")', False),
        ('(starts-with? "hi" "hello")', False),
        ('(starts-with? "abc" "")', True),
        ('(starts-with? "" "a")', False),
    ]
    hits = 0
    last_msg = None
    for expr, want in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        got = _truthy_soft(r.get("value"))
        if got == want:
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_starts_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → starts-with? candidates → select-best → current-source.

    Materializes ``aura/soft_starts_with.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _STARTS_HELPER_CANDIDATES:
            sc = _score_starts_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_starts_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "starts_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        best = next((e for e in ok_ex if e["name"] == "prefix-loop"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "starts-with?" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_starts_with",
            }

        if "(export starts-with?)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized starts-with? helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / STARTS_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line('(starts-with? "hello" "he")', timeout_s=8.0)
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "starts_helper_evolved" if v_ok else "starts_helper_verify_fail",
            "path": STARTS_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"starts_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)



# Candidate Soft ends-with? helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
# Product use: export.aura ends-with-jsonl? and path suffix checks.
_ENDS_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "suffix-loop",
        "(export ends-with?)\n"
        "(define (ends-with? s suf)\n"
        "  (let ((n (string-length suf))\n"
        "        (m (string-length s)))\n"
        "    (if (> n m)\n"
        "        #f\n"
        "        (equal? (substring s (- m n) m) suf))))\n",
    ),
    (
        "suffix-nested",
        "(export ends-with?)\n"
        "(define (ends-with? s suf)\n"
        "  (let ((n (string-length suf)))\n"
        "    (let ((m (string-length s)))\n"
        "      (if (> n m)\n"
        "          #f\n"
        "          (equal? (substring s (- m n) m) suf)))))\n",
    ),
    (
        "suffix-cond",
        "(export ends-with?)\n"
        "(define (ends-with? s suf)\n"
        "  (let ((n (string-length suf))\n"
        "        (m (string-length s)))\n"
        "    (cond ((> n m) #f)\n"
        "          (else (equal? (substring s (- m n) m) suf)))))\n",
    ),
]


def _score_ends_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score ends-with? helper against a small known vector."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        ('(ends-with? "hello" "lo")', True),
        ('(ends-with? "hello" "hex")', False),
        ('(ends-with? "hi" "hello")', False),
        ('(ends-with? "abc" "")', True),
        ('(ends-with? "" "a")', False),
        ('(ends-with? "report.jsonl" ".jsonl")', True),
    ]
    hits = 0
    last_msg = None
    for expr, want in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        got = _truthy_soft(r.get("value"))
        if got == want:
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_ends_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → ends-with? candidates → select-best → current-source.

    Materializes ``aura/soft_ends_with.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _ENDS_HELPER_CANDIDATES:
            sc = _score_ends_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_ends_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "ends_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        best = next((e for e in ok_ex if e["name"] == "suffix-loop"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "ends-with?" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_ends_with",
            }

        if "(export ends-with?)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized ends-with? helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: path/export suffix checks (e.g. ends-with-jsonl?)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / ENDS_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line('(ends-with? "hello" "lo")', timeout_s=8.0)
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "ends_helper_evolved" if v_ok else "ends_helper_verify_fail",
            "path": ENDS_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"ends_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)



# Candidate Soft contains? helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
# Product use: export/redaction substring checks, path/needle search in kernel.
_CONTAINS_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "scan-letrec",
        "(export contains?)\n"
        "(define (contains? s sub)\n"
        "  (let ((n (string-length sub))\n"
        "        (m (string-length s)))\n"
        "    (if (= n 0)\n"
        "        #t\n"
        "        (letrec ((loop (lambda (i)\n"
        "                         (if (> (+ i n) m)\n"
        "                             #f\n"
        "                             (if (equal? (substring s i (+ i n)) sub)\n"
        "                                 #t\n"
        "                                 (loop (+ i 1)))))))\n"
        "          (loop 0)))))\n",
    ),
    (
        "scan-named",
        "(export contains?)\n"
        "(define (contains? s sub)\n"
        "  (let ((n (string-length sub))\n"
        "        (m (string-length s)))\n"
        "    (if (= n 0)\n"
        "        #t\n"
        "        (let loop ((i 0))\n"
        "          (if (> (+ i n) m)\n"
        "              #f\n"
        "              (if (equal? (substring s i (+ i n)) sub)\n"
        "                  #t\n"
        "                  (loop (+ i 1))))))))\n",
    ),
    (
        "scan-cond",
        "(export contains?)\n"
        "(define (contains? s sub)\n"
        "  (let ((n (string-length sub))\n"
        "        (m (string-length s)))\n"
        "    (cond ((= n 0) #t)\n"
        "          (else\n"
        "           (letrec ((loop (lambda (i)\n"
        "                            (cond ((> (+ i n) m) #f)\n"
        "                                  ((equal? (substring s i (+ i n)) sub) #t)\n"
        "                                  (else (loop (+ i 1)))))))\n"
        "             (loop 0))))))\n",
    ),
]


def _score_contains_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score contains? helper against a small known vector."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        ('(contains? "hello" "ell")', True),
        ('(contains? "hello" "xyz")', False),
        ('(contains? "hello" "")', True),
        ('(contains? "" "a")', False),
        ('(contains? "report.jsonl" ".json")', True),
        ('(contains? "abc" "abcd")', False),
        ('(contains? "mississippi" "issi")', True),
    ]
    hits = 0
    last_msg = None
    for expr, want in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        got = _truthy_soft(r.get("value"))
        if got == want:
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_contains_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → contains? candidates → select-best → current-source.

    Materializes ``aura/soft_contains.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _CONTAINS_HELPER_CANDIDATES:
            sc = _score_contains_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_contains_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "contains_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        best = next((e for e in ok_ex if e["name"] == "scan-letrec"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "contains?" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_contains",
            }

        if "(export contains?)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized contains? helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: substring needle checks (export/redaction/path search)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / CONTAINS_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line('(contains? "hello" "ell")', timeout_s=8.0)
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "contains_helper_evolved" if v_ok else "contains_helper_verify_fail",
            "path": CONTAINS_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"contains_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)



# Candidate Soft string-split helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
# Product use: export/leetcode/l2/catalog line splits (Soft lacks string-split prim).
_SPLIT_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "scan-letrec",
        "(export string-split)\n"
        "(define (string-split s sep)\n"
        "  (let ((n (string-length sep))\n"
        "        (m (string-length s)))\n"
        "    (if (= n 0)\n"
        "        (list s)\n"
        "        (letrec ((loop (lambda (i start acc)\n"
        "                         (if (> (+ i n) m)\n"
        "                             (reverse (cons (substring s start m) acc))\n"
        "                             (if (equal? (substring s i (+ i n)) sep)\n"
        "                                 (loop (+ i n) (+ i n)\n"
        "                                       (cons (substring s start i) acc))\n"
        "                                 (loop (+ i 1) start acc))))))\n"
        "          (loop 0 0 (list))))))\n",
    ),
    (
        "scan-named",
        "(export string-split)\n"
        "(define (string-split s sep)\n"
        "  (let ((n (string-length sep))\n"
        "        (m (string-length s)))\n"
        "    (if (= n 0)\n"
        "        (list s)\n"
        "        (let loop ((i 0) (start 0) (acc (list)))\n"
        "          (if (> (+ i n) m)\n"
        "              (reverse (cons (substring s start m) acc))\n"
        "              (if (equal? (substring s i (+ i n)) sep)\n"
        "                  (loop (+ i n) (+ i n)\n"
        "                        (cons (substring s start i) acc))\n"
        "                  (loop (+ i 1) start acc)))))))\n",
    ),
    (
        "scan-cond",
        "(export string-split)\n"
        "(define (string-split s sep)\n"
        "  (let ((n (string-length sep))\n"
        "        (m (string-length s)))\n"
        "    (cond ((= n 0) (list s))\n"
        "          (else\n"
        "           (letrec ((loop (lambda (i start acc)\n"
        "                            (cond ((> (+ i n) m)\n"
        "                                   (reverse (cons (substring s start m) acc)))\n"
        "                                  ((equal? (substring s i (+ i n)) sep)\n"
        "                                   (loop (+ i n) (+ i n)\n"
        "                                         (cons (substring s start i) acc)))\n"
        "                                  (else (loop (+ i 1) start acc))))))\n"
        "             (loop 0 0 (list)))))))\n",
    ),
]


def _score_split_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score string-split helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    # Cases use Soft equal? so list values compare correctly.
    cases = [
        '(equal? (string-split "a,b,c" ",") (list "a" "b" "c"))',
        '(equal? (string-split "hello\\nworld" "\\n") (list "hello" "world"))',
        '(equal? (string-split "ab" "") (list "ab"))',
        '(equal? (string-split "" ",") (list ""))',
        '(equal? (string-split "a,,b" ",") (list "a" "" "b"))',
        '(equal? (string-split "solo" ",") (list "solo"))',
        '(equal? (string-split "x--y--z" "--") (list "x" "y" "z"))',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_split_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → string-split candidates → select-best → current-source.

    Materializes ``aura/soft_split.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _SPLIT_HELPER_CANDIDATES:
            sc = _score_split_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_split_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "split_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        best = next((e for e in ok_ex if e["name"] == "scan-letrec"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "string-split" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_split",
            }

        if "(export string-split)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized string-split helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: line/catalog/export splits (Soft lacks string-split prim)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / SPLIT_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (string-split "a,b,c" ",") (list "a" "b" "c"))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "split_helper_evolved" if v_ok else "split_helper_verify_fail",
            "path": SPLIT_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"split_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)




# Candidate Soft string-replace helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
# Product use: export redaction / path rewrite (Soft oneshot lacks string-replace
# without std/string; Soft-materialized pure letrec works denseness path).
_REPLACE_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "scan-letrec",
        "(export string-replace)\n"
        "(define (string-replace s old new)\n"
        "  (let ((slen (string-length s))\n"
        "        (olen (string-length old)))\n"
        "    (if (or (= olen 0) (> olen slen))\n"
        "        s\n"
        "        (letrec ((loop (lambda (i result)\n"
        "                         (if (>= i slen)\n"
        "                             result\n"
        "                             (if (and (<= (+ i olen) slen)\n"
        "                                      (equal? (substring s i (+ i olen)) old))\n"
        "                                 (loop (+ i olen) (string-append result new))\n"
        "                                 (loop (+ i 1)\n"
        "                                       (string-append result\n"
        "                                         (substring s i (+ i 1)))))))))\n"
        "          (loop 0 \"\")))))\n",
    ),
    (
        "scan-named",
        "(export string-replace)\n"
        "(define (string-replace s old new)\n"
        "  (let ((slen (string-length s))\n"
        "        (olen (string-length old)))\n"
        "    (if (or (= olen 0) (> olen slen))\n"
        "        s\n"
        "        (let loop ((i 0) (result \"\"))\n"
        "          (if (>= i slen)\n"
        "              result\n"
        "              (if (and (<= (+ i olen) slen)\n"
        "                       (equal? (substring s i (+ i olen)) old))\n"
        "                  (loop (+ i olen) (string-append result new))\n"
        "                  (loop (+ i 1)\n"
        "                        (string-append result\n"
        "                          (substring s i (+ i 1))))))))))\n",
    ),
    (
        "scan-cond",
        "(export string-replace)\n"
        "(define (string-replace s old new)\n"
        "  (let ((slen (string-length s))\n"
        "        (olen (string-length old)))\n"
        "    (cond ((or (= olen 0) (> olen slen)) s)\n"
        "          (else\n"
        "           (letrec ((loop (lambda (i result)\n"
        "                            (cond ((>= i slen) result)\n"
        "                                  ((and (<= (+ i olen) slen)\n"
        "                                        (equal? (substring s i (+ i olen)) old))\n"
        "                                   (loop (+ i olen) (string-append result new)))\n"
        "                                  (else\n"
        "                                   (loop (+ i 1)\n"
        "                                         (string-append result\n"
        "                                           (substring s i (+ i 1)))))))))\n"
        "             (loop 0 \"\"))))))\n",
    ),
]


def _score_replace_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score string-replace helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        '(equal? (string-replace "abc" "b" "X") "aXc")',
        '(equal? (string-replace "abab" "ab" "X") "XX")',
        '(equal? (string-replace "hello" "" "X") "hello")',
        '(equal? (string-replace "aaa" "a" "b") "bbb")',
        '(equal? (string-replace "abc" "d" "X") "abc")',
        '(equal? (string-replace "foo--bar--baz" "--" "|") "foo|bar|baz")',
        '(equal? (string-replace "" "a" "b") "")',
        '(equal? (string-replace "xx" "xxx" "Y") "xx")',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_replace_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → string-replace candidates → select-best → current-source.

    Materializes ``aura/soft_replace.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _REPLACE_HELPER_CANDIDATES:
            sc = _score_replace_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_replace_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "replace_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        best = next((e for e in ok_ex if e["name"] == "scan-letrec"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "string-replace" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_replace",
            }

        if "(export string-replace)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized string-replace helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: export redaction / rewrite (Soft oneshot lacks string-replace prim)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / REPLACE_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (string-replace "abc" "b" "X") "aXc")',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "replace_helper_evolved" if v_ok else "replace_helper_verify_fail",
            "path": REPLACE_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"replace_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)




# Candidate Soft string-trim helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
# Product use: util/prove/acp/self_evolve read-file trim (Soft oneshot lacks
# string-trim without std/string; Soft-materialized pure letrec denseness path).
_TRIM_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "scan-letrec",
        "(export string-trim)\n"
        "(define (string-trim s)\n"
        "  (let ((n (string-length s)))\n"
        "    (letrec ((l (lambda (i)\n"
        "                  (if (or (>= i n) (> (string-ref s i) 32))\n"
        "                      (letrec ((r (lambda (j)\n"
        "                                    (if (or (< j i) (> (string-ref s j) 32))\n"
        "                                        (substring s i (+ j 1))\n"
        "                                        (r (- j 1))))))\n"
        "                        (r (- n 1)))\n"
        "                      (l (+ i 1))))))\n"
        "      (l 0))))\n",
    ),
    (
        "scan-named",
        "(export string-trim)\n"
        "(define (string-trim s)\n"
        "  (let ((n (string-length s)))\n"
        "    (let loop ((i 0))\n"
        "      (if (or (>= i n) (> (string-ref s i) 32))\n"
        "          (let loop2 ((j (- n 1)))\n"
        "            (if (or (< j i) (> (string-ref s j) 32))\n"
        "                (substring s i (+ j 1))\n"
        "                (loop2 (- j 1))))\n"
        "          (loop (+ i 1))))))\n",
    ),
    (
        "scan-cond",
        "(export string-trim)\n"
        "(define (string-trim s)\n"
        "  (let ((n (string-length s)))\n"
        "    (letrec ((l (lambda (i)\n"
        "                  (cond ((or (>= i n) (> (string-ref s i) 32))\n"
        "                         (letrec ((r (lambda (j)\n"
        "                                       (cond ((or (< j i) (> (string-ref s j) 32))\n"
        "                                              (substring s i (+ j 1)))\n"
        "                                             (else (r (- j 1)))))))\n"
        "                           (r (- n 1))))\n"
        "                        (else (l (+ i 1))))))\n"
        "      (l 0))))\n",
    ),
]


def _score_trim_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score string-trim helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        '(equal? (string-trim "  hi ") "hi")',
        '(equal? (string-trim "hi") "hi")',
        '(equal? (string-trim "   ") "")',
        '(equal? (string-trim "") "")',
        '(equal? (string-trim "\\thi\\t") "hi")',
        '(equal? (string-trim "  a  b  ") "a  b")',
        '(equal? (string-trim "\\n\\r x \\n") "x")',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_trim_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → string-trim candidates → select-best → current-source.

    Materializes ``aura/soft_trim.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _TRIM_HELPER_CANDIDATES:
            sc = _score_trim_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_trim_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "trim_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        best = next((e for e in ok_ex if e["name"] == "scan-letrec"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "string-trim" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_trim",
            }

        if "(export string-trim)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized string-trim helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: util/prove/acp trim (Soft oneshot lacks string-trim prim)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / TRIM_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (string-trim "  hi ") "hi")',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "trim_helper_evolved" if v_ok else "trim_helper_verify_fail",
            "path": TRIM_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"trim_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)





# Candidate Soft string-downcase helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
# Product use: util env-bool / pursue predicate / worldline backend normalize
# (Soft oneshot lacks string-downcase prim; Soft-materialized pure denseness path).
_DOWNCASE_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "map-list",
        "(export string-downcase)\n"
        "(define (string-downcase s)\n"
        "  (list->string\n"
        "    (map (lambda (c)\n"
        "           (if (and (>= c 65) (<= c 90)) (+ c 32) c))\n"
        "         (string->list s))))\n",
    ),
    (
        "scan-letrec",
        "(export string-downcase)\n"
        "(define (string-downcase s)\n"
        "  (let ((n (string-length s)))\n"
        "    (letrec ((loop (lambda (i acc)\n"
        "                     (if (>= i n)\n"
        "                         (list->string (reverse acc))\n"
        "                         (let ((c (string-ref s i)))\n"
        "                           (loop (+ i 1)\n"
        "                                 (cons (if (and (>= c 65) (<= c 90))\n"
        "                                           (+ c 32) c)\n"
        "                                       acc)))))))\n"
        "      (loop 0 (list)))))\n",
    ),
    (
        "scan-named",
        "(export string-downcase)\n"
        "(define (string-downcase s)\n"
        "  (let ((n (string-length s)))\n"
        "    (let loop ((i 0) (acc (list)))\n"
        "      (if (>= i n)\n"
        "          (list->string (reverse acc))\n"
        "          (let ((c (string-ref s i)))\n"
        "            (loop (+ i 1)\n"
        "                  (cons (if (and (>= c 65) (<= c 90)) (+ c 32) c)\n"
        "                        acc)))))))\n",
    ),
]


def _score_downcase_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score string-downcase helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        '(equal? (string-downcase "Hi") "hi")',
        '(equal? (string-downcase "ABC") "abc")',
        '(equal? (string-downcase "") "")',
        '(equal? (string-downcase "a1Z") "a1z")',
        '(equal? (string-downcase "TRUE") "true")',
        '(equal? (string-downcase "Yes") "yes")',
        '(equal? (string-downcase "already") "already")',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_downcase_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → string-downcase candidates → select-best → current-source.

    Materializes ``aura/soft_downcase.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _DOWNCASE_HELPER_CANDIDATES:
            sc = _score_downcase_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_downcase_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "downcase_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer map-list (matches util.aura product shape) when green.
        best = next((e for e in ok_ex if e["name"] == "map-list"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "string-downcase" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_downcase",
            }

        if "(export string-downcase)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized string-downcase helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: util/pursue/worldline normalize (Soft oneshot lacks string-downcase prim)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / DOWNCASE_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (string-downcase "Hi") "hi")',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "downcase_helper_evolved" if v_ok else "downcase_helper_verify_fail",
            "path": DOWNCASE_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"downcase_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)


# Candidate Soft string-upcase helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
# Product use: util/orch/harness normalize (Soft oneshot lacks string-upcase prim;
# Soft-materialized pure denseness path; pair with soft_downcase).
_UPCASE_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "map-list",
        "(export string-upcase)\n"
        "(define (string-upcase s)\n"
        "  (list->string\n"
        "    (map (lambda (c)\n"
        "           (if (and (>= c 97) (<= c 122)) (- c 32) c))\n"
        "         (string->list s))))\n",
    ),
    (
        "scan-letrec",
        "(export string-upcase)\n"
        "(define (string-upcase s)\n"
        "  (let ((n (string-length s)))\n"
        "    (letrec ((loop (lambda (i acc)\n"
        "                     (if (>= i n)\n"
        "                         (list->string (reverse acc))\n"
        "                         (let ((c (string-ref s i)))\n"
        "                           (loop (+ i 1)\n"
        "                                 (cons (if (and (>= c 97) (<= c 122))\n"
        "                                           (- c 32) c)\n"
        "                                       acc)))))))\n"
        "      (loop 0 (list)))))\n",
    ),
    (
        "scan-named",
        "(export string-upcase)\n"
        "(define (string-upcase s)\n"
        "  (let ((n (string-length s)))\n"
        "    (let loop ((i 0) (acc (list)))\n"
        "      (if (>= i n)\n"
        "          (list->string (reverse acc))\n"
        "          (let ((c (string-ref s i)))\n"
        "            (loop (+ i 1)\n"
        "                  (cons (if (and (>= c 97) (<= c 122)) (- c 32) c)\n"
        "                        acc)))))))\n",
    ),
]


def _score_upcase_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score string-upcase helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        '(equal? (string-upcase "Hi") "HI")',
        '(equal? (string-upcase "abc") "ABC")',
        '(equal? (string-upcase "") "")',
        '(equal? (string-upcase "a1Z") "A1Z")',
        '(equal? (string-upcase "true") "TRUE")',
        '(equal? (string-upcase "Yes") "YES")',
        '(equal? (string-upcase "ALREADY") "ALREADY")',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_upcase_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → string-upcase candidates → select-best → current-source.

    Materializes ``aura/soft_upcase.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _UPCASE_HELPER_CANDIDATES:
            sc = _score_upcase_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_upcase_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "upcase_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer map-list (matches util.aura / soft_downcase product shape) when green.
        best = next((e for e in ok_ex if e["name"] == "map-list"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "string-upcase" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_upcase",
            }

        if "(export string-upcase)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized string-upcase helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: util/orch/harness normalize (Soft oneshot lacks string-upcase prim)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / UPCASE_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (string-upcase "Hi") "HI")',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "upcase_helper_evolved" if v_ok else "upcase_helper_verify_fail",
            "path": UPCASE_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"upcase_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)



# Candidate Soft string-pad helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
# Product use: orch/pursue/harness/self_evolve stamp alignment (Soft oneshot
# lacks string-pad / make-string prims; Soft-materialized pure denseness path).
_PAD_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "scan-letrec-list",
        "(export string-pad)\n"
        "(define (string-pad s width)\n"
        "  (let ((n (string-length s)))\n"
        "    (if (>= n width)\n"
        "        s\n"
        "        (letrec ((loop (lambda (k acc)\n"
        "                         (if (<= k 0)\n"
        "                             (list->string acc)\n"
        "                             (loop (- k 1) (cons 32 acc))))))\n"
        "          (string-append (loop (- width n) (list)) s)))))\n",
    ),
    (
        "scan-append",
        "(export string-pad)\n"
        "(define (string-pad s width)\n"
        "  (let ((n (string-length s)))\n"
        "    (if (>= n width)\n"
        "        s\n"
        "        (letrec ((spaces (lambda (k)\n"
        "                           (if (<= k 0)\n"
        "                               \"\"\n"
        "                               (string-append \" \" (spaces (- k 1)))))))\n"
        "          (string-append (spaces (- width n)) s)))))\n",
    ),
    (
        "scan-named",
        "(export string-pad)\n"
        "(define (string-pad s width)\n"
        "  (let ((n (string-length s)))\n"
        "    (if (>= n width)\n"
        "        s\n"
        "        (let loop ((k (- width n)) (acc (list)))\n"
        "          (if (<= k 0)\n"
        "              (string-append (list->string acc) s)\n"
        "              (loop (- k 1) (cons 32 acc)))))))\n",
    ),
]


def _score_pad_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score string-pad helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        '(equal? (string-pad "hi" 5) "   hi")',
        '(equal? (string-pad "hello" 3) "hello")',
        '(equal? (string-pad "" 2) "  ")',
        '(equal? (string-pad "x" 1) "x")',
        '(equal? (string-pad "ab" 4) "  ab")',
        '(equal? (string-pad "z" 0) "z")',
        '(equal? (string-pad "pad" 3) "pad")',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_pad_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → string-pad candidates → select-best → current-source.

    Materializes ``aura/soft_pad.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _PAD_HELPER_CANDIDATES:
            sc = _score_pad_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_pad_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "pad_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer scan-letrec-list (no recursive string-append depth) when green.
        best = next((e for e in ok_ex if e["name"] == "scan-letrec-list"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "string-pad" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_pad",
            }

        if "(export string-pad)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized string-pad helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: orch/pursue/harness/self_evolve stamp align (Soft oneshot lacks string-pad/make-string)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / PAD_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (string-pad "hi" 5) "   hi")',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "pad_helper_evolved" if v_ok else "pad_helper_verify_fail",
            "path": PAD_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"pad_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)





# Candidate Soft string-take helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
# Product use: orch/pursue/harness/self_evolve prompt trunc (Soft oneshot
# lacks string-take prim; Soft-materialized pure denseness path via substring).
_TAKE_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "substr-guard",
        "(export string-take)\n"
        "(define (string-take s n)\n"
        "  (let ((len (string-length s)))\n"
        "    (if (<= n 0)\n"
        "        \"\"\n"
        "        (if (>= n len)\n"
        "            s\n"
        "            (substring s 0 n)))))\n",
    ),
    (
        "substr-cond",
        "(export string-take)\n"
        "(define (string-take s n)\n"
        "  (cond\n"
        "    ((<= n 0) \"\")\n"
        "    ((>= n (string-length s)) s)\n"
        "    (else (substring s 0 n))))\n",
    ),
    (
        "substr-letrec",
        "(export string-take)\n"
        "(define (string-take s n)\n"
        "  (letrec ((go (lambda (s n)\n"
        "                 (let ((len (string-length s)))\n"
        "                   (if (<= n 0)\n"
        "                       \"\"\n"
        "                       (if (>= n len) s (substring s 0 n)))))))\n"
        "    (go s n)))\n",
    ),
]


def _score_take_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score string-take helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        '(equal? (string-take "hello" 2) "he")',
        '(equal? (string-take "hi" 5) "hi")',
        '(equal? (string-take "abc" 0) "")',
        '(equal? (string-take "xyz" 3) "xyz")',
        '(equal? (string-take "" 2) "")',
        '(equal? (string-take "pad" 1) "p")',
        '(equal? (string-take "world" 4) "worl")',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_take_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → string-take candidates → select-best → current-source.

    Materializes ``aura/soft_take.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _TAKE_HELPER_CANDIDATES:
            sc = _score_take_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_take_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "take_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer substr-guard (plain if/let) when green.
        best = next((e for e in ok_ex if e["name"] == "substr-guard"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "string-take" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_take",
            }

        if "(export string-take)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized string-take helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: orch/pursue/harness/self_evolve prompt trunc (Soft oneshot lacks string-take)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / TAKE_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (string-take "hello" 2) "he")',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "take_helper_evolved" if v_ok else "take_helper_verify_fail",
            "path": TAKE_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"take_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)






# Candidate Soft string-drop helpers. Soft scores each via set-code + eval;
# winner is materialized via (current-source :workspace :pretty).
# Product use: pursue fitness_ge: parse / orch prefix strip (Soft oneshot
# lacks string-drop prim; Soft-materialized pure denseness path via substring).
# Complement of soft_take — not endless string trivia: real Soft oneshot gap
# used by pursue-parse-min-fitness + orch prompt suffix after take.
_DROP_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "substr-guard",
        "(export string-drop)\n"
        "(define (string-drop s n)\n"
        "  (let ((len (string-length s)))\n"
        "    (if (<= n 0)\n"
        "        s\n"
        "        (if (>= n len)\n"
        "            \"\"\n"
        "            (substring s n len)))))\n",
    ),
    (
        "substr-cond",
        "(export string-drop)\n"
        "(define (string-drop s n)\n"
        "  (cond\n"
        "    ((<= n 0) s)\n"
        "    ((>= n (string-length s)) \"\")\n"
        "    (else (substring s n (string-length s)))))\n",
    ),
    (
        "substr-letrec",
        "(export string-drop)\n"
        "(define (string-drop s n)\n"
        "  (letrec ((go (lambda (s n)\n"
        "                 (let ((len (string-length s)))\n"
        "                   (if (<= n 0)\n"
        "                       s\n"
        "                       (if (>= n len) \"\" (substring s n len)))))))\n"
        "    (go s n)))\n",
    ),
]


def _score_drop_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score string-drop helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        '(equal? (string-drop "hello" 2) "llo")',
        '(equal? (string-drop "hi" 5) "")',
        '(equal? (string-drop "abc" 0) "abc")',
        '(equal? (string-drop "xyz" 3) "")',
        '(equal? (string-drop "" 2) "")',
        '(equal? (string-drop "pad" 1) "ad")',
        '(equal? (string-drop "world" 4) "d")',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_drop_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → string-drop candidates → select-best → current-source.

    Materializes ``aura/soft_drop.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _DROP_HELPER_CANDIDATES:
            sc = _score_drop_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_drop_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "drop_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer substr-guard (plain if/let) when green.
        best = next((e for e in ok_ex if e["name"] == "substr-guard"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "string-drop" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_drop",
            }

        if "(export string-drop)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized string-drop helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: pursue fitness_ge: parse / orch prefix strip (Soft oneshot lacks string-drop)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / DROP_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (string-drop "hello" 2) "llo")',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "drop_helper_evolved" if v_ok else "drop_helper_verify_fail",
            "path": DROP_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"drop_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)


# Soft oneshot native `take` is bound but returns an opaque unprintable value
# (display/write → <unknown>/<error>; pair?/null? fail). Real Soft oneshot gap —
# not string trivia. Product: orch/worldline cap evaluated/candidate lists.
_LIST_TAKE_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "letrec-go",
        "(export list-take)\n"
        "(define (list-take xs n)\n"
        "  (letrec ((go (lambda (xs n)\n"
        "                 (if (or (<= n 0) (null? xs))\n"
        "                     (list)\n"
        "                     (cons (car xs) (go (cdr xs) (- n 1)))))))\n"
        "    (go xs n)))\n",
    ),
    (
        "named-let",
        "(export list-take)\n"
        "(define (list-take xs n)\n"
        "  (let loop ((xs xs) (n n) (out (list)))\n"
        "    (if (or (<= n 0) (null? xs))\n"
        "        (reverse out)\n"
        "        (loop (cdr xs) (- n 1) (cons (car xs) out)))))\n",
    ),
    (
        "cond-go",
        "(export list-take)\n"
        "(define (list-take xs n)\n"
        "  (cond\n"
        "    ((or (<= n 0) (null? xs)) (list))\n"
        "    (else (cons (car xs) (list-take (cdr xs) (- n 1))))))\n",
    ),
]


def _score_list_take_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score list-take helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        '(equal? (list-take (list 1 2 3 4) 2) (list 1 2))',
        '(equal? (list-take (list 1 2) 5) (list 1 2))',
        '(equal? (list-take (list 1 2 3) 0) (list))',
        '(equal? (list-take (list) 3) (list))',
        '(equal? (list-take (list 9) 1) (list 9))',
        '(equal? (list-take (list 1 2 3) 3) (list 1 2 3))',
        '(equal? (list-take (list "a" "b" "c") 2) (list "a" "b"))',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_list_take_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → list-take candidates → select-best → current-source.

    Materializes ``aura/soft_list_take.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    Soft oneshot native ``take`` returns opaque unprintable — Soft gap.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _LIST_TAKE_HELPER_CANDIDATES:
            sc = _score_list_take_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_list_take_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "list_take_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer letrec-go when green.
        best = next((e for e in ok_ex if e["name"] == "letrec-go"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "list-take" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_list_take",
            }

        if "(export list-take)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized list-take helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: orch/worldline cap evaluated lists (Soft oneshot take opaque)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / LIST_TAKE_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (list-take (list 1 2 3) 2) (list 1 2))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "list_take_helper_evolved" if v_ok else "list_take_helper_verify_fail",
            "path": LIST_TAKE_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"list_take_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)



# Soft oneshot native `drop` is bound but returns an opaque unprintable value
# (display/write → <unknown>/<error>; pair?/null? fail) — same Soft gap as `take`
# (#4177). Complement of list-take. Product: orch overflow honesty after list-take
# cap; select-best starts with list-drop rest.
_LIST_DROP_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "letrec-go",
        "(export list-drop)\n"
        "(define (list-drop xs n)\n"
        "  (letrec ((go (lambda (xs n)\n"
        "                 (if (or (<= n 0) (null? xs))\n"
        "                     xs\n"
        "                     (go (cdr xs) (- n 1))))))\n"
        "    (go xs n)))\n",
    ),
    (
        "named-let",
        "(export list-drop)\n"
        "(define (list-drop xs n)\n"
        "  (let loop ((xs xs) (n n))\n"
        "    (if (or (<= n 0) (null? xs))\n"
        "        xs\n"
        "        (loop (cdr xs) (- n 1)))))\n",
    ),
    (
        "cond-go",
        "(export list-drop)\n"
        "(define (list-drop xs n)\n"
        "  (cond\n"
        "    ((or (<= n 0) (null? xs)) xs)\n"
        "    (else (list-drop (cdr xs) (- n 1)))))\n",
    ),
]


def _score_list_drop_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score list-drop helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        '(equal? (list-drop (list 1 2 3 4) 2) (list 3 4))',
        '(equal? (list-drop (list 1 2) 5) (list))',
        '(equal? (list-drop (list 1 2 3) 0) (list 1 2 3))',
        '(equal? (list-drop (list) 3) (list))',
        '(equal? (list-drop (list 9) 1) (list))',
        '(equal? (list-drop (list 1 2 3) 3) (list))',
        '(equal? (list-drop (list "a" "b" "c") 1) (list "b" "c"))',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_list_drop_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → list-drop candidates → select-best → current-source.

    Materializes ``aura/soft_list_drop.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    Soft oneshot native ``drop`` returns opaque unprintable — Soft gap (#4177).
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _LIST_DROP_HELPER_CANDIDATES:
            sc = _score_list_drop_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_list_drop_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "list_drop_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer letrec-go when green.
        best = next((e for e in ok_ex if e["name"] == "letrec-go"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "list-drop" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_list_drop",
            }

        if "(export list-drop)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized list-drop helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: orch overflow honesty after list-take cap (Soft oneshot drop opaque)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / LIST_DROP_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (list-drop (list 1 2 3) 1) (list 2 3))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "list_drop_helper_evolved" if v_ok else "list_drop_helper_verify_fail",
            "path": LIST_DROP_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"list_drop_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)


# Soft oneshot lacks R7RS `make-list` (unbound). Soft self_evolve_select already
# denseness-evolves make-list bodies; leetcode_observe notes unbound make-list.
# Soft-materialize aura/soft_make_list.aura via denseness current-source (not trivia).
_MAKE_LIST_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "recur-cons",
        "(export make-list)\n"
        "(define (make-list n fill)\n"
        "  (if (<= n 0)\n"
        "      (list)\n"
        "      (cons fill (make-list (- n 1) fill))))\n",
    ),
    (
        "letrec-go",
        "(export make-list)\n"
        "(define (make-list n fill)\n"
        "  (letrec ((go (lambda (n fill)\n"
        "                 (if (<= n 0)\n"
        "                     (list)\n"
        "                     (cons fill (go (- n 1) fill))))))\n"
        "    (go n fill)))\n",
    ),
    (
        "named-let",
        "(export make-list)\n"
        "(define (make-list n fill)\n"
        "  (let loop ((n n) (acc (list)))\n"
        "    (if (<= n 0)\n"
        "        acc\n"
        "        (loop (- n 1) (cons fill acc)))))\n",
    ),
]


def _score_make_list_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score make-list helper against a small known vector (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        '(equal? (make-list 3 7) (list 7 7 7))',
        '(equal? (make-list 0 9) (list))',
        '(equal? (make-list 1 "x") (list "x"))',
        '(equal? (make-list 2 0) (list 0 0))',
        '(equal? (length (make-list 5 1)) 5)',
        '(equal? (make-list 4 #t) (list #t #t #t #t))',
        '(equal? (make-list (- 1) 3) (list))',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_make_list_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → make-list candidates → select-best → current-source.

    Materializes ``aura/soft_make_list.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    Soft oneshot lacks R7RS make-list (unbound) — Soft gap (self_evolve_select / leetcode).
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _MAKE_LIST_HELPER_CANDIDATES:
            sc = _score_make_list_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_make_list_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "make_list_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer recur-cons (matches Soft self_evolve_select good-body) when green.
        best = next((e for e in ok_ex if e["name"] == "recur-cons"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "make-list" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_make_list",
            }

        if "(export make-list)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized make-list helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot lacks make-list (self_evolve_select / leetcode gap)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / MAKE_LIST_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (make-list 3 7) (list 7 7 7))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "make_list_helper_evolved" if v_ok else "make_list_helper_verify_fail",
            "path": MAKE_LIST_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"make_list_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)



# Soft-materialize aura/soft_for_each.aura via denseness current-source (not trivia).
# Soft oneshot unbound for-each; orch/worldline/acp/export redefine locally — product util gap.
_FOR_EACH_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "recur-begin",
        "(export for-each)\n"
        "(define (for-each f xs)\n"
        "  (if (null? xs)\n"
        "      #t\n"
        "      (begin (f (car xs)) (for-each f (cdr xs)))))\n",
    ),
    (
        "letrec-go",
        "(export for-each)\n"
        "(define (for-each f xs)\n"
        "  (letrec ((go (lambda (f xs)\n"
        "                 (if (null? xs)\n"
        "                     #t\n"
        "                     (begin (f (car xs)) (go f (cdr xs)))))))\n"
        "    (go f xs)))\n",
    ),
    (
        "named-let",
        "(export for-each)\n"
        "(define (for-each f xs)\n"
        "  (let loop ((xs xs))\n"
        "    (if (null? xs)\n"
        "        #t\n"
        "        (begin (f (car xs)) (loop (cdr xs))))))\n",
    ),
]


def _score_for_each_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score for-each helper via set! side-effects (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    # Each case is a fresh begin that uses for-each + set! accumulator.
    cases = [
        (
            "(begin (define acc (list))"
            " (for-each (lambda (x) (set! acc (cons x acc))) (list 1 2 3))"
            " (equal? acc (list 3 2 1)))"
        ),
        (
            "(begin (define n 0)"
            " (for-each (lambda (x) (set! n (+ n 1))) (list 1 2 3 4))"
            " (equal? n 4))"
        ),
        (
            "(begin (define n 0)"
            " (for-each (lambda (x) (set! n (+ n 1))) (list))"
            " (equal? n 0))"
        ),
        (
            "(begin (define acc (list))"
            " (for-each (lambda (x) (set! acc (cons x acc))) (list \"a\" \"b\"))"
            " (equal? acc (list \"b\" \"a\")))"
        ),
        (
            "(begin (define n 0)"
            " (for-each (lambda (x) (set! n (+ n x))) (list 10 20 30))"
            " (equal? n 60))"
        ),
        (
            "(begin (define acc (list))"
            " (for-each (lambda (x) (set! acc (cons (* x 2) acc))) (list 1 2))"
            " (equal? acc (list 4 2)))"
        ),
        (
            "(begin (define seen #f)"
            " (for-each (lambda (x) (set! seen #t)) (list 9))"
            " (equal? seen #t))"
        ),
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_for_each_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → for-each candidates → select-best → current-source.

    Materializes ``aura/soft_for_each.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    Soft oneshot lacks for-each (unbound) — orch/worldline/acp/export redefine locally.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _FOR_EACH_HELPER_CANDIDATES:
            sc = _score_for_each_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_for_each_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "for_each_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer recur-begin (matches orch.aura local define shape) when green.
        best = next((e for e in ok_ex if e["name"] == "recur-begin"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "for-each" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_for_each",
            }

        if "(export for-each)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized for-each helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound for-each (orch/worldline/acp/export redefine)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / FOR_EACH_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            "(begin (define n 0) (for-each (lambda (x) (set! n (+ n 1))) (list 1 2 3)) (equal? n 3))",
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "for_each_helper_evolved" if v_ok else "for_each_helper_verify_fail",
            "path": FOR_EACH_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"for_each_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)





_HASH_FOR_EACH_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "named-let-keys",
        "(export hash-for-each)\n"
        "(define (hash-for-each h f)\n"
        "  (let loop ((ks (hash-keys h)))\n"
        "    (if (null? ks)\n"
        "        #t\n"
        "        (begin\n"
        "          (f (car ks) (hash-ref h (car ks)))\n"
        "          (loop (cdr ks))))))\n",
    ),
    (
        "letrec-go",
        "(export hash-for-each)\n"
        "(define (hash-for-each h f)\n"
        "  (letrec ((go (lambda (ks)\n"
        "                 (if (null? ks)\n"
        "                     #t\n"
        "                     (begin\n"
        "                       (f (car ks) (hash-ref h (car ks)))\n"
        "                       (go (cdr ks)))))))\n"
        "    (go (hash-keys h))))\n",
    ),
    (
        "recur-keys",
        "(export hash-for-each)\n"
        "(define (hash-for-each h f)\n"
        "  (define (go ks)\n"
        "    (if (null? ks)\n"
        "        #t\n"
        "        (begin\n"
        "          (f (car ks) (hash-ref h (car ks)))\n"
        "          (go (cdr ks)))))\n"
        "  (go (hash-keys h)))\n",
    ),
]


def _score_hash_for_each_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score hash-for-each helper via set! side-effects (Soft equal?)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    # Soft oneshot: hash-keys returns string keys for string hash-set!.
    cases = [
        (
            "(begin (define n 0)"
            " (define h (hash))"
            " (hash-for-each h (lambda (k v) (set! n (+ n 1))))"
            " (equal? n 0))"
        ),
        (
            "(begin (define n 0)"
            " (define h (hash)) (hash-set! h \"a\" 1) (hash-set! h \"b\" 2)"
            " (hash-for-each h (lambda (k v) (set! n (+ n v))))"
            " (equal? n 3))"
        ),
        (
            "(begin (define acc (list))"
            " (define h (hash)) (hash-set! h \"x\" 9)"
            " (hash-for-each h (lambda (k v) (set! acc (cons k acc))))"
            " (equal? acc (list \"x\")))"
        ),
        (
            "(begin (define acc (list))"
            " (define h (hash)) (hash-set! h \"a\" 10) (hash-set! h \"b\" 20)"
            " (hash-for-each h (lambda (k v) (set! acc (cons v acc))))"
            " (or (equal? acc (list 10 20)) (equal? acc (list 20 10))))"
        ),
        (
            "(begin (define seen #f)"
            " (define h (hash)) (hash-set! h \"k\" 1)"
            " (hash-for-each h (lambda (k v) (set! seen #t)))"
            " (equal? seen #t))"
        ),
        (
            "(begin (define n 0)"
            " (define h (hash)) (hash-set! h \"only\" 7)"
            " (hash-for-each h (lambda (k v) (set! n (+ n v))))"
            " (equal? n 7))"
        ),
        (
            "(begin (define n 0)"
            " (define h (hash)) (hash-set! h \"a\" 1) (hash-set! h \"b\" 1) (hash-set! h \"c\" 1)"
            " (hash-for-each h (lambda (k v) (set! n (+ n 1))))"
            " (equal? n 3))"
        ),
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_hash_for_each_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → hash-for-each candidates → select-best → current-source.

    Materializes ``aura/soft_hash_for_each.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    Soft oneshot lacks hash-for-each (unbound) — orch/harness/export use it;
    Soft std/hash.aura defines it but Soft oneshot does not load std/hash.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _HASH_FOR_EACH_HELPER_CANDIDATES:
            sc = _score_hash_for_each_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_hash_for_each_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "hash_for_each_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer named-let-keys (matches Soft std/hash.aura hash-keys loop) when green.
        best = next((e for e in ok_ex if e["name"] == "named-let-keys"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "hash-for-each" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_hash_for_each",
            }

        if "(export hash-for-each)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized hash-for-each helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound hash-for-each (orch/harness/export use it;\n"
            "; Soft std/hash.aura defines it but Soft oneshot does not auto-load std/hash)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / HASH_FOR_EACH_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(begin (define n 0) (define h (hash)) (hash-set! h "a" 1) (hash-set! h "b" 2)'
            " (hash-for-each h (lambda (k v) (set! n (+ n v)))) (equal? n 3))",
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "hash_for_each_helper_evolved" if v_ok else "hash_for_each_helper_verify_fail",
            "path": HASH_FOR_EACH_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"hash_for_each_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)




_HASH_FOLD_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "named-let-keys",
        "(export hash-fold)\n"
        "(define (hash-fold h f init)\n"
        "  (let loop ((ks (hash-keys h)) (acc init))\n"
        "    (if (null? ks)\n"
        "        acc\n"
        "        (loop (cdr ks) (f (car ks) (hash-ref h (car ks)) acc)))))\n",
    ),
    (
        "foldl-keys",
        "(export hash-fold)\n"
        "(define (hash-fold h f init)\n"
        "  (foldl (lambda (acc k) (f k (hash-ref h k) acc)) init (hash-keys h)))\n",
    ),
    (
        "recur-keys",
        "(export hash-fold)\n"
        "(define (hash-fold h f init)\n"
        "  (define (go ks acc)\n"
        "    (if (null? ks)\n"
        "        acc\n"
        "        (go (cdr ks) (f (car ks) (hash-ref h (car ks)) acc))))\n"
        "  (go (hash-keys h) init))\n",
    ),
]


def _score_hash_fold_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score hash-fold helper (Soft equal?). Soft std/hash shape: (hash-fold h f init)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        (
            "(begin (define h (hash))"
            " (equal? (hash-fold h (lambda (k v acc) (+ acc v)) 0) 0))"
        ),
        (
            "(begin (define h (hash)) (hash-set! h \"a\" 1) (hash-set! h \"b\" 2)"
            " (equal? (hash-fold h (lambda (k v acc) (+ acc v)) 0) 3))"
        ),
        (
            "(begin (define h (hash)) (hash-set! h \"x\" 9)"
            " (equal? (hash-fold h (lambda (k v acc) (cons k acc)) (list)) (list \"x\")))"
        ),
        (
            "(begin (define h (hash)) (hash-set! h \"a\" 10) (hash-set! h \"b\" 20)"
            " (let ((acc (hash-fold h (lambda (k v acc) (cons v acc)) (list))))"
            "   (or (equal? acc (list 10 20)) (equal? acc (list 20 10)))))"
        ),
        (
            "(begin (define h (hash)) (hash-set! h \"only\" 7)"
            " (equal? (hash-fold h (lambda (k v acc) (+ acc v)) 0) 7))"
        ),
        (
            "(begin (define h (hash)) (hash-set! h \"a\" 1) (hash-set! h \"b\" 1) (hash-set! h \"c\" 1)"
            " (equal? (hash-fold h (lambda (k v acc) (+ acc 1)) 0) 3))"
        ),
        (
            "(begin (define h (hash)) (hash-set! h \"k\" 5)"
            " (equal? (hash-fold h (lambda (k v acc) (+ acc v)) 10) 15))"
        ),
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_hash_fold_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → hash-fold candidates → select-best → current-source.

    Materializes ``aura/soft_hash_fold.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    Soft oneshot lacks hash-fold (unbound) — Soft std/hash.aura defines it via
    foldr (also Soft oneshot unbound); Soft oneshot does not auto-load std/hash.
    Product denseness sibling of hash-for-each; orch/harness fold-over-hash path.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _HASH_FOLD_HELPER_CANDIDATES:
            sc = _score_hash_fold_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_hash_fold_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "hash_fold_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer named-let-keys (no Soft foldr; Soft oneshot has foldl but
        # Soft std/hash uses foldr — named-let is denseness-portable).
        best = next((e for e in ok_ex if e["name"] == "named-let-keys"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "hash-fold" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_hash_fold",
            }

        if "(export hash-fold)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized hash-fold helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound hash-fold (Soft std/hash defines via foldr;\n"
            "; Soft oneshot lacks foldr + does not auto-load std/hash; sibling of hash-for-each)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / HASH_FOLD_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(begin (define h (hash)) (hash-set! h "a" 1) (hash-set! h "b" 2)'
            " (equal? (hash-fold h (lambda (k v acc) (+ acc v)) 0) 3))",
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "hash_fold_helper_evolved" if v_ok else "hash_fold_helper_verify_fail",
            "path": HASH_FOLD_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"hash_fold_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)





# Soft-materialize aura/soft_foldr.aura via denseness current-source (not trivia).
# Soft oneshot has foldl but unbound foldr; Soft std/list.aura defines foldr via
# reverse+foldl (#1549 iterative). Soft std/hash hash-fold depends on foldr.
# Product denseness path for Soft oneshot without auto-loading std/list.


_FOLDR_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "reverse-foldl",
        "(export foldr)\n"
        "(define (foldr f init lst)\n"
        "  (foldl (lambda (acc x) (f x acc)) init (reverse lst)))\n",
    ),
    (
        "named-let-rev",
        "(export foldr)\n"
        "(define (foldr f init lst)\n"
        "  (let loop ((xs (reverse lst)) (acc init))\n"
        "    (if (null? xs)\n"
        "        acc\n"
        "        (loop (cdr xs) (f (car xs) acc)))))\n",
    ),
    (
        "recur-rev",
        "(export foldr)\n"
        "(define (foldr f init lst)\n"
        "  (define (go xs acc)\n"
        "    (if (null? xs)\n"
        "        acc\n"
        "        (go (cdr xs) (f (car xs) acc))))\n"
        "  (go (reverse lst) init))\n",
    ),
]


def _score_foldr_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score foldr helper (Soft equal?). Soft std shape: (foldr f init lst); f(x, acc)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        (
            "(equal? (foldr (lambda (x acc) (+ x acc)) 0 (list)) 0)"
        ),
        (
            "(equal? (foldr (lambda (x acc) (+ x acc)) 0 (list 1 2 3)) 6)"
        ),
        (
            "(equal? (foldr (lambda (x acc) (cons x acc)) (list) (list 1 2 3)) (list 1 2 3))"
        ),
        (
            "(equal? (foldr (lambda (x acc) (cons x acc)) (list 9) (list 1 2)) (list 1 2 9))"
        ),
        (
            "(equal? (foldr (lambda (x acc) (+ x acc)) 10 (list 1 2)) 13)"
        ),
        (
            "(equal? (foldr (lambda (x acc) (string-append (number->string x) acc)) \"\" (list 1 2 3)) \"123\")"
        ),
        (
            "(equal? (foldr (lambda (x acc) (+ (* acc 10) x)) 0 (list 1 2 3)) 321)"
        ),
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_foldr_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → foldr candidates → select-best → current-source.

    Materializes ``aura/soft_foldr.aura`` (real kernel helper).
    Honesty: fiber_live only when denseness probe measured ok.
    Soft oneshot has foldl but unbound foldr — Soft std/list defines foldr via
    reverse+foldl; Soft std/hash hash-fold depends on foldr; Soft oneshot does
    not auto-load std/list. Product denseness foundation for Soft std hash-fold.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _FOLDR_HELPER_CANDIDATES:
            sc = _score_foldr_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_foldr_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "foldr_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer reverse-foldl (matches Soft std/list.aura foldr) when green.
        best = next((e for e in ok_ex if e["name"] == "reverse-foldl"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "foldr" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_foldr",
            }

        if "(export foldr)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized foldr helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot has foldl but unbound foldr (Soft std/list defines\n"
            "; via reverse+foldl; Soft std/hash hash-fold depends on foldr; Soft oneshot\n"
            "; does not auto-load std/list)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / FOLDR_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(equal? (foldr (lambda (x acc) (cons x acc)) (list) (list 1 2 3)) (list 1 2 3))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "foldr_helper_evolved" if v_ok else "foldr_helper_verify_fail",
            "path": FOLDR_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"foldr_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)




# Soft-materialize aura/soft_hash_empty.aura via denseness current-source (not trivia).
# Soft oneshot unbound hash-empty? (Soft std/hash.aura defines via hash-length;
# Soft oneshot does not auto-load std/hash). Orch/harness honesty empty-hash path.


_HASH_EMPTY_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "hash-length-eq",
        "(export hash-empty?)\n"
        "(define (hash-empty? h)\n"
        "  (= (hash-length h) 0))\n",
    ),
    (
        "null-keys",
        "(export hash-empty?)\n"
        "(define (hash-empty? h)\n"
        "  (null? (hash-keys h)))\n",
    ),
    (
        "zero-fold",
        "(export hash-empty?)\n"
        "(define (hash-empty? h)\n"
        "  (let loop ((ks (hash-keys h)))\n"
        "    (null? ks)))\n",
    ),
]


def _score_hash_empty_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score hash-empty? helper (Soft equal?). Soft std: (hash-empty? h) via hash-length."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        "(begin (define h (hash)) (equal? (hash-empty? h) #t))",
        '(begin (define h (hash)) (hash-set! h "a" 1) (equal? (hash-empty? h) #f))',
        '(begin (define h (hash)) (hash-set! h "a" 1) (hash-set! h "b" 2) (equal? (hash-empty? h) #f))',
        "(begin (define h (hash)) (equal? (hash-empty? h) (null? (hash-keys h))))",
        '(begin (define h (hash)) (hash-set! h "only" 7) (equal? (hash-empty? h) #f))',
        "(begin (define h (hash)) (and (hash-empty? h) (= (hash-length h) 0)))",
        '(begin (define h (hash)) (hash-set! h "x" 1) (not (hash-empty? h)))',
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_hash_empty_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → hash-empty? candidates → select-best → current-source.

    Materializes ``aura/soft_hash_empty.aura`` (real kernel helper).
    Soft oneshot unbound hash-empty? — Soft std/hash defines via hash-length;
    Soft oneshot does not auto-load std/hash. Sibling of hash-fold/hash-for-each.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _HASH_EMPTY_HELPER_CANDIDATES:
            sc = _score_hash_empty_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_hash_empty_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "hash_empty_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer hash-length-eq (matches Soft std/hash.aura) when green.
        best = next((e for e in ok_ex if e["name"] == "hash-length-eq"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "hash-empty?" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_hash_empty",
            }

        if "(export hash-empty?)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized hash-empty? helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound hash-empty? (Soft std/hash defines via\n"
            "; hash-length; Soft oneshot does not auto-load std/hash; sibling of hash-fold)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / HASH_EMPTY_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(begin (define h (hash)) (and (hash-empty? h)'
            ' (begin (hash-set! h "a" 1) (not (hash-empty? h)))))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "hash_empty_helper_evolved" if v_ok else "hash_empty_helper_verify_fail",
            "path": HASH_EMPTY_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"hash_empty_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)



# Soft-materialize aura/soft_hash_to_list.aura via denseness current-source (not trivia).
# Soft oneshot unbound hash->list (Soft std/hash.aura defines via map+hash-keys+hash-ref;
# Soft oneshot does not auto-load std/hash). Sibling of hash-empty?/hash-fold/hash-for-each.
# Orch/pursue/harness honesty: dump hash as alist for stamp/align.

_HASH_TO_LIST_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "map-keys",
        "(export hash->list)\n"
        "(define (hash->list h)\n"
        "  (map (lambda (k) (list k (hash-ref h k))) (hash-keys h)))\n",
    ),
    (
        "named-let-keys",
        "(export hash->list)\n"
        "(define (hash->list h)\n"
        "  (let loop ((ks (hash-keys h)) (acc (list)))\n"
        "    (if (null? ks)\n"
        "      (reverse acc)\n"
        "      (loop (cdr ks) (cons (list (car ks) (hash-ref h (car ks))) acc)))))\n",
    ),
    (
        "foldl-cons",
        "(export hash->list)\n"
        "(define (hash->list h)\n"
        "  (reverse (foldl (lambda (acc k) (cons (list k (hash-ref h k)) acc))\n"
        "                  (list) (hash-keys h))))\n",
    ),
]


def _score_hash_to_list_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score hash->list helper. Soft std: (hash->list h) → ((k v) ...) via map+keys."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        "(begin (define h (hash)) (equal? (hash->list h) (list)))",
        '(begin (define h (hash)) (hash-set! h "a" 1) (equal? (length (hash->list h)) 1))',
        '(begin (define h (hash)) (hash-set! h "a" 1) (equal? (car (car (hash->list h))) "a"))',
        '(begin (define h (hash)) (hash-set! h "a" 1) (equal? (car (cdr (car (hash->list h)))) 1))',
        '(begin (define h (hash)) (hash-set! h "a" 1) (hash-set! h "b" 2) (equal? (length (hash->list h)) 2))',
        '(begin (define h (hash)) (hash-set! h "x" 7) (equal? (hash-ref h (car (car (hash->list h)))) 7))',
        "(begin (define h (hash)) (null? (hash->list h)))",
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_hash_to_list_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → hash->list candidates → select-best → current-source.

    Materializes ``aura/soft_hash_to_list.aura`` (real kernel helper).
    Soft oneshot unbound hash->list — Soft std/hash defines via map+keys+ref;
    Soft oneshot does not auto-load std/hash. Sibling of hash-empty?/hash-fold.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _HASH_TO_LIST_HELPER_CANDIDATES:
            sc = _score_hash_to_list_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_hash_to_list_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "hash_to_list_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer map-keys (matches Soft std/hash.aura) when green.
        best = next((e for e in ok_ex if e["name"] == "map-keys"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "hash->list" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_hash_to_list",
            }

        if "(export hash->list)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized hash->list helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound hash->list (Soft std/hash defines via\n"
            "; map+hash-keys+hash-ref; Soft oneshot does not auto-load std/hash;\n"
            "; sibling of hash-empty?/hash-fold/hash-for-each)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / HASH_TO_LIST_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(begin (define h (hash)) (hash-set! h "a" 1)'
            ' (and (= (length (hash->list h)) 1)'
            '      (equal? (car (car (hash->list h))) "a")))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "hash_to_list_helper_evolved" if v_ok else "hash_to_list_helper_verify_fail",
            "path": HASH_TO_LIST_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"hash_to_list_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)




# Soft-materialize aura/soft_any.aura via denseness current-source (not trivia).
# Soft oneshot unbound any (Soft std/list.aura defines iterative any/all #928;
# Soft oneshot does not auto-load std/list). Sibling of foldr; orch/pursue honesty
# short-circuit predicate scans.

_ANY_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "named-let",
        "(export any)\n"
        "(define (any pred lst)\n"
        "  (let loop ((xs lst))\n"
        "    (if (null? xs) #f\n"
        "      (if (pred (car xs)) #t (loop (cdr xs))))))\n",
    ),
    (
        "letrec-go",
        "(export any)\n"
        "(define (any pred lst)\n"
        "  (letrec ((go (lambda (xs)\n"
        "                 (if (null? xs) #f\n"
        "                   (if (pred (car xs)) #t (go (cdr xs)))))))\n"
        "    (go lst)))\n",
    ),
    (
        "cond-recur",
        "(export any)\n"
        "(define (any pred lst)\n"
        "  (cond ((null? lst) #f)\n"
        "        ((pred (car lst)) #t)\n"
        "        (else (any pred (cdr lst)))))\n",
    ),
]


def _score_any_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score any helper. Soft std: (any pred lst) iterative short-circuit (#928)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        "(equal? (any (lambda (x) (> x 2)) (quote (1 2 3))) #t)",
        "(equal? (any (lambda (x) (> x 9)) (quote (1 2 3))) #f)",
        "(equal? (any (lambda (x) #t) (quote ())) #f)",
        "(equal? (any (lambda (x) (= x 1)) (quote (1 2))) #t)",
        "(equal? (any (lambda (x) (= x 2)) (quote (1 2 3))) #t)",
        "(begin (define seen 0) (any (lambda (x) (set! seen (+ seen 1)) (> x 1)) (quote (0 2 9))) (equal? seen 2))",
        "(equal? (any (lambda (x) #f) (quote (1 2 3))) #f)",
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_any_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → any candidates → select-best → current-source.

    Materializes ``aura/soft_any.aura`` (real kernel helper).
    Soft oneshot unbound any — Soft std/list defines iterative any/all #928;
    Soft oneshot does not auto-load std/list. Sibling of foldr.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _ANY_HELPER_CANDIDATES:
            sc = _score_any_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_any_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "any_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer named-let (matches Soft std/list.aura) when green.
        best = next((e for e in ok_ex if e["name"] == "named-let"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "any" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_any",
            }

        if "(export any)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized any helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound any (Soft std/list defines iterative\n"
            "; any/all #928; Soft oneshot does not auto-load std/list; sibling of foldr)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / ANY_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(and (any (lambda (x) (> x 2)) (quote (1 2 3)))'
            ' (not (any (lambda (x) (> x 9)) (quote (1 2 3))))'
            ' (not (any (lambda (x) #t) (quote ()))))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "any_helper_evolved" if v_ok else "any_helper_verify_fail",
            "path": ANY_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"any_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)



# Soft-materialize aura/soft_all.aura via denseness current-source (not trivia).
# Soft oneshot unbound all (Soft std/list.aura defines iterative any/all #928;
# Soft oneshot does not auto-load std/list). Sibling of any; orch/pursue honesty
# universal predicate scans.

_ALL_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "named-let",
        "(export all)\n"
        "(define (all pred lst)\n"
        "  (let loop ((xs lst))\n"
        "    (if (null? xs) #t\n"
        "      (if (pred (car xs)) (loop (cdr xs)) #f))))\n",
    ),
    (
        "letrec-go",
        "(export all)\n"
        "(define (all pred lst)\n"
        "  (letrec ((go (lambda (xs)\n"
        "                 (if (null? xs) #t\n"
        "                   (if (pred (car xs)) (go (cdr xs)) #f)))))\n"
        "    (go lst)))\n",
    ),
    (
        "cond-recur",
        "(export all)\n"
        "(define (all pred lst)\n"
        "  (cond ((null? lst) #t)\n"
        "        ((pred (car lst)) (all pred (cdr lst)))\n"
        "        (else #f)))\n",
    ),
]


def _score_all_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score all helper. Soft std: (all pred lst) iterative short-circuit (#928)."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        "(equal? (all (lambda (x) (> x 0)) (quote (1 2 3))) #t)",
        "(equal? (all (lambda (x) (> x 2)) (quote (1 2 3))) #f)",
        "(equal? (all (lambda (x) #t) (quote ())) #t)",
        "(equal? (all (lambda (x) (= x 1)) (quote (1 1))) #t)",
        "(equal? (all (lambda (x) (= x 2)) (quote (2 1 2))) #f)",
        "(begin (define seen 0) (all (lambda (x) (set! seen (+ seen 1)) (> x 0)) (quote (1 0 9))) (equal? seen 2))",
        "(equal? (all (lambda (x) #f) (quote (1 2 3))) #f)",
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_all_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → all candidates → select-best → current-source.

    Materializes ``aura/soft_all.aura`` (real kernel helper).
    Soft oneshot unbound all — Soft std/list defines iterative any/all #928;
    Soft oneshot does not auto-load std/list. Sibling of any.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _ALL_HELPER_CANDIDATES:
            sc = _score_all_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_all_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "all_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer named-let (matches Soft std/list.aura) when green.
        best = next((e for e in ok_ex if e["name"] == "named-let"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "all" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_all",
            }

        if "(export all)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized all helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound all (Soft std/list defines iterative\n"
            "; any/all #928; Soft oneshot does not auto-load std/list; sibling of any)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / ALL_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(and (all (lambda (x) (> x 0)) (quote (1 2 3)))'
            ' (not (all (lambda (x) (> x 2)) (quote (1 2 3))))'
            ' (all (lambda (x) #t) (quote ())))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "all_helper_evolved" if v_ok else "all_helper_verify_fail",
            "path": ALL_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"all_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)




# Soft-materialize aura/soft_last.aura via denseness current-source (not trivia).
# Soft oneshot unbound last (Soft std/list.aura defines iterative last;
# Soft oneshot does not auto-load std/list). Sibling of any/all; orch/pursue
# honesty last-candidate / traj tail picks.

_LAST_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "named-let",
        "(export last)\n"
        "(define (last lst)\n"
        "  (if (null? lst) (quote ())\n"
        "    (let loop ((xs lst))\n"
        "      (if (null? (cdr xs)) (car xs)\n"
        "        (loop (cdr xs))))))\n",
    ),
    (
        "letrec-go",
        "(export last)\n"
        "(define (last lst)\n"
        "  (if (null? lst) (quote ())\n"
        "    (letrec ((go (lambda (xs)\n"
        "                   (if (null? (cdr xs)) (car xs) (go (cdr xs))))))\n"
        "      (go lst))))\n",
    ),
    (
        "cond-recur",
        "(export last)\n"
        "(define (last lst)\n"
        "  (cond ((null? lst) (quote ()))\n"
        "        ((null? (cdr lst)) (car lst))\n"
        "        (else (last (cdr lst)))))\n",
    ),
]


def _score_last_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score last helper. Soft std: (last lst) iterative; empty → ()."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        "(equal? (last (quote (1 2 3))) 3)",
        "(equal? (last (quote (7))) 7)",
        "(equal? (last (quote ())) (quote ()))",
        "(equal? (last (quote (a b c d))) (quote d))",
        "(equal? (last (quote (1 2))) 2)",
        "(equal? (last (list 9 8 7)) 7)",
        "(begin (define xs (quote (10 20 30))) (equal? (last xs) 30))",
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_last_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → last candidates → select-best → current-source.

    Materializes ``aura/soft_last.aura`` (real kernel helper).
    Soft oneshot unbound last — Soft std/list defines iterative last;
    Soft oneshot does not auto-load std/list. Sibling of any/all.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _LAST_HELPER_CANDIDATES:
            sc = _score_last_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_last_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "last_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        best = next((e for e in ok_ex if e["name"] == "named-let"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "last" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_last",
            }

        if "(export last)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized last helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound last (Soft std/list defines iterative\n"
            "; last; Soft oneshot does not auto-load std/list; sibling of any/all)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / LAST_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(and (equal? (last (quote (1 2 3))) 3)'
            ' (equal? (last (quote (7))) 7)'
            ' (equal? (last (quote ())) (quote ())))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "last_helper_evolved" if v_ok else "last_helper_verify_fail",
            "path": LAST_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"last_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)






# Soft-materialize aura/soft_find.aura via denseness current-source (not trivia).
# Soft oneshot unbound find — Soft std/list does NOT export find (SRFI-1 gap).
# Product: orch/pursue worldline-by-id / first-matching candidate; sibling of any/all.

_FIND_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "named-let",
        "(export find)\n"
        "(define (find pred lst)\n"
        "  (let loop ((xs lst))\n"
        "    (if (null? xs) (quote ())\n"
        "      (if (pred (car xs)) (car xs)\n"
        "        (loop (cdr xs))))))\n",
    ),
    (
        "letrec-go",
        "(export find)\n"
        "(define (find pred lst)\n"
        "  (letrec ((go (lambda (xs)\n"
        "                 (if (null? xs) (quote ())\n"
        "                   (if (pred (car xs)) (car xs) (go (cdr xs)))))))\n"
        "    (go lst)))\n",
    ),
    (
        "cond-recur",
        "(export find)\n"
        "(define (find pred lst)\n"
        "  (cond ((null? lst) (quote ()))\n"
        "        ((pred (car lst)) (car lst))\n"
        "        (else (find pred (cdr lst)))))\n",
    ),
]


def _score_find_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score find helper. Soft: (find pred lst) → first match or ()."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        # Soft serve set-code workspace lacks even?/odd? (math not re-bound) —
        # use lambda predicates only (same denseness honesty as product find).
        "(equal? (find (lambda (x) (= (modulo x 2) 0)) (quote (1 2 3))) 2)",
        "(equal? (find (lambda (x) (= (modulo x 2) 1)) (quote (2 4 5))) 5)",
        "(equal? (find (lambda (x) #t) (quote ())) (quote ()))",
        "(equal? (find (lambda (x) (> x 9)) (quote (1 2 3))) (quote ()))",
        "(equal? (find (lambda (x) (= x 3)) (quote (1 2 3 4))) 3)",
        "(equal? (find (lambda (x) #t) (quote (7))) 7)",
        "(begin (define xs (quote (10 20 30))) (equal? (find (lambda (x) (> x 15)) xs) 20))",
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_find_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → find candidates → select-best → current-source.

    Materializes ``aura/soft_find.aura`` (real kernel helper).
    Soft oneshot unbound find — Soft std/list does not export find (SRFI-1 gap).
    Product: orch worldline-by-id / first-matching candidate.
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _FIND_HELPER_CANDIDATES:
            sc = _score_find_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_find_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "find_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        best = next((e for e in ok_ex if e["name"] == "named-let"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "find" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_find",
            }

        if "(export find)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized find helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound find (Soft std/list does not export\n"
            "; find — SRFI-1 gap; Soft oneshot auto-loads list/string/hash/math only)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / FIND_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(and (equal? (find (lambda (x) (= (modulo x 2) 0)) (quote (1 2 3))) 2)'
            ' (equal? (find (lambda (x) (= (modulo x 2) 1)) (quote (2 4 5))) 5)'
            ' (equal? (find (lambda (x) #t) (quote ())) (quote ())))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "find_helper_evolved" if v_ok else "find_helper_verify_fail",
            "path": FIND_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"find_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)





# Soft-materialize aura/soft_count.aura via denseness current-source (not trivia).
# Soft oneshot unbound count — Soft std/list does NOT export count (SRFI-1 gap).
# Product: orch/harness count-passed / worldline green tallies; sibling of find/any.

_COUNT_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "named-let",
        "(export count)\n"
        "(define (count pred lst)\n"
        "  (let loop ((xs lst) (n 0))\n"
        "    (if (null? xs) n\n"
        "      (loop (cdr xs) (if (pred (car xs)) (+ n 1) n)))))\n",
    ),
    (
        "letrec-go",
        "(export count)\n"
        "(define (count pred lst)\n"
        "  (letrec ((go (lambda (xs n)\n"
        "                 (if (null? xs) n\n"
        "                   (go (cdr xs) (if (pred (car xs)) (+ n 1) n))))))\n"
        "    (go lst 0)))\n",
    ),
    (
        "foldl-inc",
        "(export count)\n"
        "(define (count pred lst)\n"
        "  (foldl (lambda (acc x) (if (pred x) (+ acc 1) acc)) 0 lst))\n",
    ),
]


def _score_count_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score count helper. Soft: (count pred lst) → integer; empty → 0."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        "(equal? (count (lambda (x) (= (modulo x 2) 0)) (quote (1 2 3 4))) 2)",
        "(equal? (count (lambda (x) (= (modulo x 2) 1)) (quote (1 2 3 4))) 2)",
        "(equal? (count (lambda (x) #t) (quote ())) 0)",
        "(equal? (count (lambda (x) (> x 9)) (quote (1 2 3))) 0)",
        "(equal? (count (lambda (x) (= x 3)) (quote (1 2 3 3))) 2)",
        "(equal? (count (lambda (x) #t) (quote (7))) 1)",
        "(begin (define xs (quote (10 20 30))) (equal? (count (lambda (x) (> x 15)) xs) 2))",
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_count_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → count candidates → select-best → current-source.

    Materializes ``aura/soft_count.aura`` (real kernel helper).
    Soft oneshot unbound count — Soft std/list does not export count (SRFI-1 gap).
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _COUNT_HELPER_CANDIDATES:
            sc = _score_count_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_count_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "count_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer named-let (iterative Soft style) when green; foldl needs Soft foldl.
        best = next((e for e in ok_ex if e["name"] == "named-let"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "count" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_count",
            }

        if "(export count)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized count helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound count (Soft std/list does not export\n"
            "; count — SRFI-1 gap; Soft oneshot auto-loads list/string/hash/math only)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / COUNT_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(and (equal? (count (lambda (x) (= (modulo x 2) 0)) (quote (1 2 3 4))) 2)'
            ' (equal? (count (lambda (x) #t) (quote ())) 0)'
            ' (equal? (count (lambda (x) #t) (quote (7))) 1))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "count_helper_evolved" if v_ok else "count_helper_verify_fail",
            "path": COUNT_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"count_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)



# Soft-materialize aura/soft_remove.aura via denseness current-source (not trivia).
# Soft oneshot unbound remove — Soft std/list does NOT export remove (SRFI-1 gap #4224).
# Soft tip 5954717 gold find/count/filter/partition; still no remove.
# Product: orch filter-truth / worldlines-without-id; sibling of find/count/filter.

_REMOVE_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "named-let",
        "(export remove)\n"
        "(define (remove pred lst)\n"
        "  (let loop ((xs lst) (acc (quote ())))\n"
        "    (if (null? xs) (reverse acc)\n"
        "      (loop (cdr xs) (if (pred (car xs)) acc (cons (car xs) acc))))))\n",
    ),
    (
        "letrec-go",
        "(export remove)\n"
        "(define (remove pred lst)\n"
        "  (letrec ((go (lambda (xs acc)\n"
        "                 (if (null? xs) (reverse acc)\n"
        "                   (go (cdr xs) (if (pred (car xs)) acc (cons (car xs) acc)))))))\n"
        "    (go lst (quote ()))))\n",
    ),
    (
        "filter-not",
        "(export remove)\n"
        "(define (remove pred lst)\n"
        "  (filter (lambda (x) (not (pred x))) lst))\n",
    ),
]


def _score_remove_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score remove helper. Soft: (remove pred lst) → keep where pred false."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        "(equal? (remove (lambda (x) (= (modulo x 2) 0)) (quote (1 2 3 4))) (quote (1 3)))",
        "(equal? (remove (lambda (x) (= (modulo x 2) 1)) (quote (1 2 3 4))) (quote (2 4)))",
        "(equal? (remove (lambda (x) #t) (quote ())) (quote ()))",
        "(equal? (remove (lambda (x) #f) (quote (1 2))) (quote (1 2)))",
        "(equal? (remove (lambda (x) (= x 2)) (quote (1 2 3 2))) (quote (1 3)))",
        "(equal? (remove (lambda (x) #t) (quote (7))) (quote ()))",
        "(begin (define xs (quote (10 20 30))) (equal? (remove (lambda (x) (> x 15)) xs) (quote (10))))",
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_remove_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → remove candidates → select-best → current-source.

    Materializes ``aura/soft_remove.aura`` (real kernel helper).
    Soft oneshot unbound remove — Soft std/list does not export remove (SRFI-1 #4224).
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _REMOVE_HELPER_CANDIDATES:
            sc = _score_remove_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_remove_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "remove_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer named-let (iterative Soft style) when green; filter-not needs Soft filter.
        best = next((e for e in ok_ex if e["name"] == "named-let"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "remove" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_remove",
            }

        if "(export remove)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized remove helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound remove (Soft std/list does not export\n"
            "; remove — SRFI-1 gap #4224; Soft tip 5954717 has find/count/filter)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / REMOVE_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(and (equal? (remove (lambda (x) (= (modulo x 2) 0)) (quote (1 2 3 4))) (quote (1 3)))'
            ' (equal? (remove (lambda (x) #t) (quote ())) (quote ()))'
            ' (equal? (remove (lambda (x) #t) (quote (7))) (quote ())))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "remove_helper_evolved" if v_ok else "remove_helper_verify_fail",
            "path": REMOVE_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"remove_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)




# Soft-materialize aura/soft_delete.aura via denseness current-source (not trivia).
# Soft oneshot unbound delete — Soft std/list does NOT export delete (SRFI-1 gap).
# Soft tip 5954717 gold find/count/filter/partition; still no remove/delete.
# Product: orch ids-without / discard id lists; sibling of remove (pred) vs delete (equal?).

_DELETE_HELPER_CANDIDATES: list[tuple[str, str]] = [
    (
        "named-let",
        "(export delete)\n"
        "(define (delete x lst)\n"
        "  (let loop ((xs lst) (acc (quote ())))\n"
        "    (if (null? xs) (reverse acc)\n"
        "      (loop (cdr xs) (if (equal? (car xs) x) acc (cons (car xs) acc))))))\n",
    ),
    (
        "letrec-go",
        "(export delete)\n"
        "(define (delete x lst)\n"
        "  (letrec ((go (lambda (xs acc)\n"
        "                 (if (null? xs) (reverse acc)\n"
        "                   (go (cdr xs) (if (equal? (car xs) x) acc (cons (car xs) acc)))))))\n"
        "    (go lst (quote ()))))\n",
    ),
    (
        "filter-ne",
        "(export delete)\n"
        "(define (delete x lst)\n"
        "  (filter (lambda (y) (not (equal? y x))) lst))\n",
    ),
]


def _score_delete_helper_src(sess: Any, src: str, *, timeout_s: float = 12.0) -> dict[str, Any]:
    """Score delete helper. Soft: (delete x lst) → drop elements equal? to x."""
    from aura_build.serve_session import is_session_transient

    esc = _soft_escape(src)
    boot = sess.raw_line(f'(set-code "{esc}")', timeout_s=timeout_s)
    if boot.get("status") != "ok":
        msg = boot.get("msg") or boot.get("status")
        return {
            "ok": False,
            "observed": None,
            "msg": msg,
            "transient": is_session_transient(msg),
        }
    sess.raw_line("(eval-current)", timeout_s=timeout_s)
    cases = [
        "(equal? (delete 2 (quote (1 2 3 2))) (quote (1 3)))",
        "(equal? (delete 1 (quote (1 1 1))) (quote ()))",
        "(equal? (delete 9 (quote (1 2 3))) (quote (1 2 3)))",
        "(equal? (delete 0 (quote ())) (quote ()))",
        "(equal? (delete \"b\" (quote (\"a\" \"b\" \"c\"))) (quote (\"a\" \"c\")))",
        "(equal? (delete 7 (quote (7))) (quote ()))",
        "(begin (define xs (quote (10 20 10))) (equal? (delete 10 xs) (quote (20))))",
    ]
    hits = 0
    last_msg = None
    for expr in cases:
        r = sess.raw_line(expr, timeout_s=timeout_s)
        msg = r.get("msg") or r.get("status")
        if is_session_transient(msg):
            return {"ok": False, "observed": hits, "msg": msg, "transient": True}
        if r.get("status") != "ok":
            last_msg = msg
            continue
        if _truthy_soft(r.get("value")):
            hits += 1
        last_msg = msg
    ok = hits == len(cases)
    return {
        "ok": ok,
        "observed": hits,
        "status": "ok" if ok else "partial",
        "msg": last_msg,
        "transient": False,
    }


def _run_soft_delete_helper_evolve(
    repo: Path,
    *,
    aura_bin: str,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Soft serve denseness → delete candidates → select-best → current-source.

    Materializes ``aura/soft_delete.aura`` (real kernel helper).
    Soft oneshot unbound delete — Soft std/list does not export delete (SRFI-1).
    """
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import (
        is_session_transient,
        restart_session,
        start_session,
        stop_quiet,
    )

    hroot = harness_root or (repo / ".aura-build")
    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fiber_live": False}

        probe = fiber_fanout_probe(sess, n=2, timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fiber_live": False,
            }

        explorers: list[dict[str, Any]] = []
        restarts = 0
        for name, src in _DELETE_HELPER_CANDIDATES:
            sc = _score_delete_helper_src(sess, src)
            if sc.get("transient") and restarts < 2:
                stop_quiet(sess)
                sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
                denseness = fiber_fanout_probe(sess, n=2, timeout_s=6.0)
                denseness_ok = bool(denseness.get("ok"))
                denseness_note = str(denseness.get("note") or denseness_note)
                restarts += 1
                if not denseness_ok:
                    return {
                        "ok": False,
                        "reason": "denseness_lost_after_restart",
                        "fiber_live": False,
                        "restarts": restarts,
                    }
                sc = _score_delete_helper_src(sess, src)
            explorers.append(
                {
                    "name": name,
                    "ok": bool(sc.get("ok")),
                    "observed": sc.get("observed"),
                    "src": src,
                    "transient": bool(sc.get("transient")),
                    "msg": sc.get("msg"),
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        if not ok_ex:
            return {
                "ok": False,
                "reason": "delete_helper_candidates_all_failed",
                "explorers": [
                    {k: e.get(k) for k in ("name", "ok", "observed", "msg")}
                    for e in explorers
                ],
                "fiber_live": True,
                "denseness_note": denseness_note,
                "aura_issue_candidate": True,
            }

        # Prefer named-let (iterative Soft style) when green; filter-ne needs Soft filter.
        best = next((e for e in ok_ex if e["name"] == "named-let"), ok_ex[0])
        win_src = str(best["src"])
        boot = sess.raw_line(
            f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
        )
        if boot.get("status") != "ok" and is_session_transient(boot.get("msg")):
            stop_quiet(sess)
            sess = restart_session(aura_bin=aura_bin, harness_root=hroot)
            boot = sess.raw_line(
                f'(set-code "{_soft_escape(win_src)}")', timeout_s=12.0
            )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fiber_live": True,
                "selected": best["name"],
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))", timeout_s=10.0
        )
        src = str(cs.get("display") or "").strip()
        if not src or "delete" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source failed for soft_delete",
            }

        if "(export delete)" not in src:
            return {
                "ok": False,
                "reason": "current_source_missing_export_names",
                "display": src[:200],
                "fiber_live": True,
                "aura_issue_candidate": True,
                "tip_note": "Soft current-source dropped export names (#4132 should be fixed)",
                "selected": best["name"],
            }

        banner = (
            "; Soft-materialized delete helper (self-evolve Soft path)\n"
            "; materialize=current-source  fiber_live=true when denseness measured\n"
            f"; selected={best['name']}  denseness={denseness_note}\n"
            "; incr_proven=false\n"
            "; Product: Soft oneshot unbound delete (Soft std/list does not export\n"
            "; delete — SRFI-1 gap; Soft tip 5954717 has find/count/filter)\n"
        )
        body = banner + src.rstrip() + "\n"

        out = repo / DELETE_HELPER_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")

        verify = sess.raw_line(
            '(and (equal? (delete 2 (quote (1 2 3 2))) (quote (1 3)))'
            ' (equal? (delete 0 (quote ())) (quote ()))'
            ' (equal? (delete 7 (quote (7))) (quote ())))',
            timeout_s=8.0,
        )
        v_ok = verify.get("status") == "ok" and _truthy_soft(verify.get("value"))

        return {
            "ok": bool(v_ok),
            "reason": "delete_helper_evolved" if v_ok else "delete_helper_verify_fail",
            "path": DELETE_HELPER_PATH,
            "selected": best["name"],
            "observed": next((e.get("observed") for e in explorers if e["name"] == best["name"]), None),
            "src_len": len(src),
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "fiber_live": True,
            "incr_proven": False,
            "denseness_note": denseness_note,
            "explorers": [
                {k: e.get(k) for k in ("name", "ok", "observed")} for e in explorers
            ],
            "session_restarts": restarts,
            "verify_ok": v_ok,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"delete_helper_evolve_exc:{type(exc).__name__}:{exc}",
            "fiber_live": False,
        }
    finally:
        stop_quiet(sess)




def _run_serve_fiber(
    repo: Path,
    *,
    aura_bin: str,
    worldlines: int = 256,
    bumps: tuple[int, ...] | list[int] | None = None,
    harness_root: Path | None = None,
    explorer_cap: int | None = None,
    latency_clock: Any = None,
) -> dict[str, Any]:
    """Long-lived Soft serve + denseness + fiber explorer worldlines → current-source."""
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import start_session

    hroot = harness_root or (repo / ".aura-build")
    # Cap Soft fiber explorers — full wl=256 sequential fiber:spawn+mutate
    # stalls Soft serve (sock hang after fiber:join defuse WARN storm).
    # Adaptive strategy may lower effective cap; never raise above FIBER_EXPLORER_CAP.
    eff_cap = int(FIBER_EXPLORER_CAP)
    if explorer_cap is not None:
        eff_cap = max(1, min(int(FIBER_EXPLORER_CAP), int(explorer_cap)))
    n_explore = max(1, min(int(worldlines), eff_cap))
    bumps_list = list(bumps) if bumps else list(DEFAULT_BUMPS[:n_explore])
    if len(bumps_list) < n_explore:
        # pad uniquely up to cap (not full worldlines)
        x = max(bumps_list) + 1 if bumps_list else 1
        while len(bumps_list) < n_explore:
            bumps_list.append(x)
            x += 1

    sess = None
    phase_ms: dict[str, int] = {}
    hang_or_timeout = False
    try:
        t_sess = time.monotonic()
        if latency_clock is not None:
            latency_clock.start("session_start")
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        phase_ms["session_start"] = max(0, int((time.monotonic() - t_sess) * 1000))
        if latency_clock is not None:
            latency_clock.end("session_start", ok=bool(sess and sess.alive()))
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fallback_ok": True, "latency_ms": phase_ms}

        t_den = time.monotonic()
        if latency_clock is not None:
            latency_clock.start("denseness_probe")
        probe = fiber_fanout_probe(sess, n=max(1, int(worldlines)), timeout_s=8.0)
        phase_ms["denseness_probe"] = max(0, int((time.monotonic() - t_den) * 1000))
        denseness_ok = bool(probe.get("ok"))
        if latency_clock is not None:
            latency_clock.end(
                "denseness_probe",
                ok=denseness_ok,
                fiber_live=denseness_ok,
                n=max(1, int(worldlines)),
            )
        denseness_note = str(
            probe.get("note") or probe.get("reason") or ("ok" if denseness_ok else "fail")
        )
        if not denseness_ok:
            return {
                "ok": False,
                "reason": "denseness_probe_failed",
                "denseness": probe,
                "fallback_ok": True,
                "fiber_live": False,
            }

        from aura_build.serve_session import is_session_transient, raw_line_resilient, restart_session, stop_quiet

        sess, boot = raw_line_resilient(
            sess,
            '(set-code "(define (cand) 0)")',
            aura_bin=aura_bin,
            harness_root=hroot,
            timeout_s=10.0,
            max_restarts=1,
        )
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fallback_ok": True,
                "denseness": probe,
                "transient": is_session_transient(boot.get("msg") or boot.get("status")),
            }
        ev0 = sess.raw_line("(eval-current)", timeout_s=10.0)
        # Soft may return status=closure for define forms — accept ok or closure
        st0 = str(ev0.get("status") or "")
        if st0 not in ("ok", "closure") and ev0.get("status") not in ("ok",):
            # still continue if mutate works later
            pass

        explorers: list[dict[str, Any]] = []
        t_ex = time.monotonic()
        if latency_clock is not None:
            latency_clock.start("explorer_loop")
        hang_or_timeout = False
        for b in bumps_list:
            body = (
                f"(fiber:join (fiber:spawn (lambda () "
                f"(begin "
                f'(mutate:rebind "cand" "(lambda () {int(b)})" "fib-{int(b)}") '
                f"(eval-current) "
                f"(cand)))))"
            )
            t0 = time.monotonic()
            r = sess.raw_line(body, timeout_s=15.0)
            ms = max(1, int((time.monotonic() - t0) * 1000))
            val = r.get("value")
            st = str(r.get("status") or "")
            ok = st == "ok" and _as_num(val) > -999_999
            if st in ("timeout", "error", "hang") or ms >= 14000:
                hang_or_timeout = True
            explorers.append(
                {
                    "bump": int(b),
                    "value": val,
                    "observed": _as_num(val) if ok else None,
                    "status": r.get("status"),
                    "ok": ok,
                    "ms": ms,
                    "via": "fiber:spawn+mutate:rebind",
                }
            )

        ok_ex = [e for e in explorers if e.get("ok")]
        phase_ms["explorer_loop"] = max(0, int((time.monotonic() - t_ex) * 1000))
        if latency_clock is not None:
            latency_clock.end(
                "explorer_loop",
                ok=bool(ok_ex),
                fiber_live=True,
                n=len(explorers),
                extra={
                    "ok_n": len(ok_ex),
                    "hang_or_timeout": hang_or_timeout,
                    "explorer_cap": eff_cap,
                },
            )
        if not ok_ex:
            return {
                "ok": False,
                "reason": "fiber_explorers_all_failed",
                "explorers": explorers,
                "denseness": probe,
                "fallback_ok": True,
                "aura_issue_candidate": True,
            }

        from aura_build.soft_select import select_explorer_soft

        best, soft_sel = select_explorer_soft(
            ok_ex,
            score_key="observed",
            sess=sess,
            repo=repo,
            tie_key=lambda e: (int(e["observed"]), int(e["bump"])),
            require_ok=True,
        )
        assert best is not None
        best_b = int(best["bump"])
        best_v = int(best["observed"])

        mut = sess.raw_line(
            f'(mutate:rebind "cand" "(lambda () {best_b})" "rt-winner")',
            timeout_s=10.0,
        )
        if mut.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"winner_rebind_failed:{mut.get('msg') or mut.get('status')}",
                "explorers": explorers,
                "denseness": probe,
                "fallback_ok": True,
                "aura_issue_candidate": True,
            }
        sess.raw_line("(eval-current)", timeout_s=10.0)
        cs = sess.raw_line(
            "(display (current-source :workspace :pretty))",
            timeout_s=10.0,
        )
        src = str(cs.get("display") or "").strip()
        if not src or "cand" not in src:
            return {
                "ok": False,
                "reason": "current_source_empty_or_bad",
                "display": src[:200],
                "status": cs.get("status"),
                "explorers": explorers,
                "denseness": probe,
                "fallback_ok": False,
                "aura_issue_candidate": True,
                "tip_note": "Soft serve current-source failed after fiber select-best",
            }

        traj = f"serve-fiber-{best_b}-{best_v}"
        t_stamp = time.monotonic()
        if latency_clock is not None:
            latency_clock.start("stamp")
        body = _build_stamp_body(
            src=src,
            traj=traj,
            gen=1,
            selected=best_b,
            observed=best_v,
            src_len=len(src),
            fiber_live=True,
            worldline_backend="fiber_graph",
            denseness_note=denseness_note,
        )
        stamp_path = repo / STAMP_PATH
        stamp_path.parent.mkdir(parents=True, exist_ok=True)
        stamp_path.write_text(body, encoding="utf-8")
        v = _validate_stamp(repo, expect_fiber_live=True)
        phase_ms["stamp"] = max(0, int((time.monotonic() - t_stamp) * 1000))
        if latency_clock is not None:
            latency_clock.end("stamp", ok=bool(v.get("ok")), fiber_live=True)
        if not v.get("ok"):
            return {
                **v,
                "explorers": explorers,
                "denseness": probe,
                "aura_issue_candidate": True,
                "latency_ms": phase_ms,
                "hang_or_timeout": hang_or_timeout,
            }

        return {
            "ok": True,
            "reason": "serve_fiber_ok",
            "selected": str(best_b),
            "observed": str(best_v),
            "src_len": len(src),
            "wrote": STAMP_PATH,
            "stamp_path": STAMP_PATH,
            "materialize": "current-source",
            "worldline_backend": "fiber_graph",
            "explore_parallel": "fiber_sequential_oneshots",
            "incr_proven": False,
            "fiber_live": True,
            "explorer_cap": eff_cap,
            "hang_or_timeout": hang_or_timeout,
            "latency_ms": phase_ms,
            "soft_select": {
                "via": soft_sel.get("via"),
                "reason": soft_sel.get("reason"),
                "value": soft_sel.get("value"),
                "helper": soft_sel.get("helper"),
            },
            "session_model": "serve",
            "denseness": {
                "ok": True,
                "note": denseness_note,
                "join_value": probe.get("join_value"),
                "worldline_backend": probe.get("worldline_backend"),
            },
            "explorers": explorers,
            "kernel": "aura",
            "fallback": False,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "reason": f"serve_fiber_exc:{type(exc).__name__}:{exc}",
            "fallback_ok": True,
            "aura_issue_candidate": "hang" in str(exc).lower() or "timeout" in str(exc).lower(),
        }
    finally:
        from aura_build.serve_session import stop_quiet as _stop_quiet_sess
        _stop_quiet_sess(sess)


# Back-compat alias used by tests / older call sites
def _run_soft_runtime(
    repo: Path,
    *,
    aura_bin: str,
    timeout_s: float = 60.0,
) -> dict[str, Any]:
    return _run_soft_oneshot(repo, aura_bin=aura_bin, timeout_s=timeout_s)


def cmd_runtime(args: Any) -> int:
    """Soft runtime self-evolve with latency breakdown + adaptive strategy.

    High-speed evolution repair: skip redundant Soft-native / already-green
    denseness rematerialize, adaptive explorer cap / early oneshot on hang,
    emit wall-clock phases in JSON. Prefer Soft-native; never invent Soft Ready.
    """
    from aura_build.self_evolve_strategy import (
        LatencyClock,
        combat_inventory_nonempty,
        effective_explorer_cap,
        effective_worldlines,
        load_strategy,
        observe_runtime_round,
        probe_soft_native,
        save_strategy,
        should_prefer_oneshot,
        should_skip_helper_rematerialize,
        skipped_helper_stub,
    )

    repo = Path(getattr(args, "repo", None) or Path.cwd()).resolve()
    aura_bin = (
        getattr(args, "aura_bin", None)
        or os.environ.get("AURA_BIN")
        or DEFAULT_SOFT
    )
    force_oneshot = bool(getattr(args, "force_oneshot", False))
    prefer_serve = not force_oneshot and bool(getattr(args, "prefer_serve", True))
    worldlines_cli = int(getattr(args, "worldlines", None) or 256)
    harness_root = Path(
        getattr(args, "harness_root", None) or (repo / ".aura-build")
    )

    clock = LatencyClock(session="self_evolve_runtime")
    state = load_strategy(repo, harness_root)
    worldlines = effective_worldlines(state, requested=worldlines_cli)
    explorer_cap = effective_explorer_cap(state)
    prefer_oneshot_early = should_prefer_oneshot(state) and not force_oneshot

    print(
        json.dumps(
            {
                "event": "self_evolve_strategy",
                "worldlines": worldlines,
                "worldlines_cli": worldlines_cli,
                "explorer_cap": explorer_cap,
                "explorer_cap_ceiling": FIBER_EXPLORER_CAP,
                "prefer_oneshot_early": prefer_oneshot_early,
                "prefer_serve": prefer_serve,
                "combat_or_leetcode_inventory": combat_inventory_nonempty(repo),
                "last_helpers_all_green": state.get("last_helpers_all_green"),
                "last_nothing_to_commit": state.get("last_nothing_to_commit"),
                "last_explorer_hang": state.get("last_explorer_hang"),
                "policy": (
                    "skip Soft-native-green denseness; skip rematerialize when "
                    "already_green+nothing_to_commit; lower explorer_cap / early "
                    "oneshot on hang; shrink worldlines after fast soft_ready pursue; "
                    "combat/leetcode inventory nonempty → first-class transforms; "
                    "never invent Soft Ready"
                ),
            },
            ensure_ascii=False,
        )
    )

    # Soft-native probe (aggregate denseness skip input) — host metrics only.
    soft_native: dict[str, Any] = {"ok": False, "green": {}, "ms": 0}
    clock.start("soft_native_probe")
    if prefer_serve:
        soft_native = probe_soft_native(str(aura_bin))
        state["soft_native_green"] = dict(soft_native.get("green") or {})
    clock.end(
        "soft_native_probe",
        ok=bool(soft_native.get("ok")),
        n=int(soft_native.get("n_green") or 0),
        extra={"n_total": soft_native.get("n_total"), "ms_probe": soft_native.get("ms")},
    )
    print(
        json.dumps(
            {
                "event": "self_evolve_soft_native_probe",
                "ok": soft_native.get("ok"),
                "n_green": soft_native.get("n_green"),
                "n_total": soft_native.get("n_total"),
                "ms": soft_native.get("ms"),
                "green": soft_native.get("green"),
            },
            ensure_ascii=False,
        )
    )

    # Helper pipeline: (result_key, event_name, path_const, evolve_fn)
    helper_specs: list[tuple[str, str, str, Any]] = [
        ("helper", "self_evolve_helper", HELPER_PATH, _run_soft_helper_evolve),
        ("starts_helper", "self_evolve_starts_helper", STARTS_HELPER_PATH, _run_soft_starts_helper_evolve),
        ("ends_helper", "self_evolve_ends_helper", ENDS_HELPER_PATH, _run_soft_ends_helper_evolve),
        ("contains_helper", "self_evolve_contains_helper", CONTAINS_HELPER_PATH, _run_soft_contains_helper_evolve),
        ("split_helper", "self_evolve_split_helper", SPLIT_HELPER_PATH, _run_soft_split_helper_evolve),
        ("replace_helper", "self_evolve_replace_helper", REPLACE_HELPER_PATH, _run_soft_replace_helper_evolve),
        ("trim_helper", "self_evolve_trim_helper", TRIM_HELPER_PATH, _run_soft_trim_helper_evolve),
        ("downcase_helper", "self_evolve_downcase_helper", DOWNCASE_HELPER_PATH, _run_soft_downcase_helper_evolve),
        ("upcase_helper", "self_evolve_upcase_helper", UPCASE_HELPER_PATH, _run_soft_upcase_helper_evolve),
        ("pad_helper", "self_evolve_pad_helper", PAD_HELPER_PATH, _run_soft_pad_helper_evolve),
        ("take_helper", "self_evolve_take_helper", TAKE_HELPER_PATH, _run_soft_take_helper_evolve),
        ("drop_helper", "self_evolve_drop_helper", DROP_HELPER_PATH, _run_soft_drop_helper_evolve),
        ("list_take_helper", "self_evolve_list_take_helper", LIST_TAKE_HELPER_PATH, _run_soft_list_take_helper_evolve),
        ("list_drop_helper", "self_evolve_list_drop_helper", LIST_DROP_HELPER_PATH, _run_soft_list_drop_helper_evolve),
        ("make_list_helper", "self_evolve_make_list_helper", MAKE_LIST_HELPER_PATH, _run_soft_make_list_helper_evolve),
        ("for_each_helper", "self_evolve_for_each_helper", FOR_EACH_HELPER_PATH, _run_soft_for_each_helper_evolve),
        ("hash_for_each_helper", "self_evolve_hash_for_each_helper", HASH_FOR_EACH_HELPER_PATH, _run_soft_hash_for_each_helper_evolve),
        ("hash_fold_helper", "self_evolve_hash_fold_helper", HASH_FOLD_HELPER_PATH, _run_soft_hash_fold_helper_evolve),
        ("foldr_helper", "self_evolve_foldr_helper", FOLDR_HELPER_PATH, _run_soft_foldr_helper_evolve),
        ("hash_empty_helper", "self_evolve_hash_empty_helper", HASH_EMPTY_HELPER_PATH, _run_soft_hash_empty_helper_evolve),
        ("hash_to_list_helper", "self_evolve_hash_to_list_helper", HASH_TO_LIST_HELPER_PATH, _run_soft_hash_to_list_helper_evolve),
        ("any_helper", "self_evolve_any_helper", ANY_HELPER_PATH, _run_soft_any_helper_evolve),
        ("all_helper", "self_evolve_all_helper", ALL_HELPER_PATH, _run_soft_all_helper_evolve),
        ("last_helper", "self_evolve_last_helper", LAST_HELPER_PATH, _run_soft_last_helper_evolve),
        ("find_helper", "self_evolve_find_helper", FIND_HELPER_PATH, _run_soft_find_helper_evolve),
        ("count_helper", "self_evolve_count_helper", COUNT_HELPER_PATH, _run_soft_count_helper_evolve),
        ("remove_helper", "self_evolve_remove_helper", REMOVE_HELPER_PATH, _run_soft_remove_helper_evolve),
        ("delete_helper", "self_evolve_delete_helper", DELETE_HELPER_PATH, _run_soft_delete_helper_evolve),
    ]

    helper_results: dict[str, dict[str, Any]] = {
        key: {"ok": False, "reason": "skipped"} for key, *_ in helper_specs
    }
    denseness_agg = {
        "n": 0,
        "ok_n": 0,
        "skip_n": 0,
        "fail_n": 0,
        "ms": 0,
        "skipped": [],
        "ran": [],
    }

    if prefer_serve and not prefer_oneshot_early:
        clock.start("denseness_per_helper")
        for key, event, path_rel, fn in helper_specs:
            hpath = repo / path_rel
            skip, skip_reason = should_skip_helper_rematerialize(
                state,
                helper_key=key,
                helper_path=hpath,
                soft_native_green=state.get("soft_native_green") or {},
            )
            denseness_agg["n"] += 1
            if skip:
                out = skipped_helper_stub(path=path_rel, reason=skip_reason)
                helper_results[key] = out
                denseness_agg["skip_n"] += 1
                denseness_agg["ok_n"] += 1
                denseness_agg["skipped"].append({"key": key, "reason": skip_reason})
                print(json.dumps({"event": event, **out, "ms": 0}, ensure_ascii=False))
                continue
            t0 = time.monotonic()
            out = fn(repo, aura_bin=str(aura_bin), harness_root=harness_root)
            ms = max(0, int((time.monotonic() - t0) * 1000))
            out = dict(out)
            out["ms"] = ms
            helper_results[key] = out
            denseness_agg["ms"] += ms
            denseness_agg["ran"].append({"key": key, "ok": bool(out.get("ok")), "ms": ms})
            if out.get("ok"):
                denseness_agg["ok_n"] += 1
            else:
                denseness_agg["fail_n"] += 1
            print(json.dumps({"event": event, **out}, ensure_ascii=False))
        clock.end(
            "denseness_per_helper",
            ok=denseness_agg["fail_n"] == 0,
            n=denseness_agg["n"],
            extra={
                "ok_n": denseness_agg["ok_n"],
                "skip_n": denseness_agg["skip_n"],
                "fail_n": denseness_agg["fail_n"],
                "helpers_ms": denseness_agg["ms"],
            },
        )
        print(
            json.dumps(
                {"event": "self_evolve_denseness_aggregate", **denseness_agg},
                ensure_ascii=False,
            )
        )
    elif prefer_oneshot_early:
        clock.mark(
            "denseness_per_helper",
            ok=True,
            n=0,
            ms=0,
            extra={"skipped_all": True, "reason": "prefer_oneshot_early"},
        )
        print(
            json.dumps(
                {
                    "event": "self_evolve_denseness_aggregate",
                    "n": 0,
                    "ok_n": 0,
                    "skip_n": 0,
                    "fail_n": 0,
                    "ms": 0,
                    "skipped_all": True,
                    "reason": "prefer_oneshot_early",
                },
                ensure_ascii=False,
            )
        )

    result: dict[str, Any]
    fallback_oneshot = False
    hang_or_timeout = False
    if prefer_serve and not prefer_oneshot_early:
        # session_start / denseness_probe / explorer_loop / stamp timed inside _run_serve_fiber
        result = _run_serve_fiber(
            repo,
            aura_bin=str(aura_bin),
            worldlines=worldlines,
            harness_root=harness_root,
            explorer_cap=explorer_cap,
            latency_clock=clock,
        )
        hang_or_timeout = bool(result.get("hang_or_timeout"))
        print(json.dumps({"event": "self_evolve_runtime_serve", **result}, ensure_ascii=False))
        if not result.get("ok") and result.get("fallback_ok", True):
            fallback_oneshot = True
            clock.start("oneshot_fallback")
            print(
                json.dumps(
                    {
                        "event": "self_evolve_runtime_fallback",
                        "from": result.get("reason"),
                        "to": "oneshot_mutate",
                    },
                    ensure_ascii=False,
                )
            )
            result = _run_soft_oneshot(repo, aura_bin=str(aura_bin))
            result["fallback_from"] = "serve_fiber"
            clock.end(
                "oneshot_fallback",
                ok=bool(result.get("ok")),
                fiber_live=False,
            )
    else:
        if prefer_oneshot_early:
            print(
                json.dumps(
                    {
                        "event": "self_evolve_runtime_fallback",
                        "from": "prefer_oneshot_early",
                        "to": "oneshot_mutate",
                        "fiber_live": False,
                    },
                    ensure_ascii=False,
                )
            )
            clock.start("oneshot_fallback")
            result = _run_soft_oneshot(repo, aura_bin=str(aura_bin))
            result["fallback_from"] = "prefer_oneshot_early"
            clock.end(
                "oneshot_fallback",
                ok=bool(result.get("ok")),
                fiber_live=False,
            )
            fallback_oneshot = True
        else:
            clock.start("oneshot_fallback")
            result = _run_soft_oneshot(repo, aura_bin=str(aura_bin))
            clock.end(
                "oneshot_fallback",
                ok=bool(result.get("ok")),
                fiber_live=False,
            )

    _helper_keys = (
        "ok",
        "reason",
        "path",
        "selected",
        "fiber_live",
        "materialize",
        "src_len",
        "denseness_note",
        "ms",
        "skipped",
    )
    for key, *_rest in helper_specs:
        src_h = helper_results.get(key) or {}
        result[key] = {k: src_h.get(k) for k in _helper_keys}

    result["soft_native_probe"] = {
        "n_green": soft_native.get("n_green"),
        "n_total": soft_native.get("n_total"),
        "ms": soft_native.get("ms"),
        "green": soft_native.get("green"),
    }
    result["strategy"] = {
        "worldlines": worldlines,
        "explorer_cap": explorer_cap,
        "prefer_oneshot_early": prefer_oneshot_early,
        "denseness_skip_n": denseness_agg.get("skip_n"),
        "denseness_ran_n": len(denseness_agg.get("ran") or []),
    }
    latency = clock.summary(fiber_live=bool(result.get("fiber_live")))
    result["latency"] = latency
    print(json.dumps({"event": "self_evolve_runtime", **result}, ensure_ascii=False))
    print(
        json.dumps(
            {"event": "self_evolve_latency", **latency},
            ensure_ascii=False,
        )
    )
    print(f"self-evolve latency: {latency.get('progress')}", file=sys.stderr)

    if not result.get("ok"):
        if result.get("aura_issue_candidate"):
            print(
                "self-evolve runtime: Soft/current-source/fiber anomaly candidate — "
                "file Aura issue with tip SHA + repro (do not invent Soft Ready)",
                file=sys.stderr,
            )
        # still persist strategy observations on fail
        helpers_for_obs = {k: result.get(k) for k, *_ in helper_specs}
        state = observe_runtime_round(
            state,
            helpers=helpers_for_obs,
            explorers=result.get("explorers") if isinstance(result.get("explorers"), list) else None,
            fiber_live=bool(result.get("fiber_live")),
            fallback_oneshot=fallback_oneshot,
            hang_or_timeout=hang_or_timeout,
            nothing_to_commit=False,
            latency=latency,
        )
        save_strategy(repo, state, harness_root)
        return 1

    verify_mode = getattr(args, "verify", "stamp") or "stamp"
    clock.start("materialize_commit")
    verify = run_host_verify(
        repo,
        verify_mode,
        aura_bin=str(aura_bin),
        harness_root=harness_root,
    )
    print(json.dumps({"event": "host_verify", **verify}, ensure_ascii=False))
    if not verify.get("ok"):
        clock.end("materialize_commit", ok=False)
        print(
            f"self-evolve runtime: verify failed reason={verify.get('reason')} (no commit)",
            file=sys.stderr,
        )
        save_strategy(repo, state, harness_root)
        return int(verify.get("exit_code") or 1)

    if getattr(args, "no_commit", False):
        clock.end("materialize_commit", ok=True, extra={"no_commit": True})
        latency = clock.summary(fiber_live=bool(result.get("fiber_live")))
        print(json.dumps({"event": "self_evolve_latency", **latency}, ensure_ascii=False))
        print("self-evolve runtime: --no-commit; skip git")
        helpers_for_obs = {k: result.get(k) for k, *_ in helper_specs}
        state = observe_runtime_round(
            state,
            helpers=helpers_for_obs,
            explorers=result.get("explorers") if isinstance(result.get("explorers"), list) else None,
            fiber_live=bool(result.get("fiber_live")),
            fallback_oneshot=fallback_oneshot,
            hang_or_timeout=hang_or_timeout,
            nothing_to_commit=False,
            latency=latency,
        )
        save_strategy(repo, state, harness_root)
        return 0

    paths = [
        STAMP_PATH,
        RUNTIME_KERNEL,
        HELPER_PATH,
        STARTS_HELPER_PATH,
        ENDS_HELPER_PATH,
        CONTAINS_HELPER_PATH,
        SPLIT_HELPER_PATH,
        REPLACE_HELPER_PATH,
        TRIM_HELPER_PATH,
        DOWNCASE_HELPER_PATH,
        UPCASE_HELPER_PATH,
        PAD_HELPER_PATH,
        TAKE_HELPER_PATH,
        DROP_HELPER_PATH,
        LIST_TAKE_HELPER_PATH,
        LIST_DROP_HELPER_PATH,
        MAKE_LIST_HELPER_PATH,
        FOR_EACH_HELPER_PATH,
        HASH_FOR_EACH_HELPER_PATH,
        HASH_FOLD_HELPER_PATH,
        FOLDR_HELPER_PATH,
        HASH_EMPTY_HELPER_PATH,
        HASH_TO_LIST_HELPER_PATH,
        ANY_HELPER_PATH,
        ALL_HELPER_PATH,
        LAST_HELPER_PATH,
        FIND_HELPER_PATH,
        COUNT_HELPER_PATH,
        REMOVE_HELPER_PATH,
        DELETE_HELPER_PATH,
        "src/aura_build/self_evolve_runtime.py",
        "src/aura_build/self_evolve_strategy.py",
        "src/aura_build/serve_session.py",
        "src/aura_build/soft_leetcode_runtime.py",
        "tests/test_serve_session.py",
        "tests/test_self_evolve.py",
        "tests/test_self_evolve_strategy.py",
    ]
    fl = "true" if result.get("fiber_live") else "false"
    backend = result.get("worldline_backend") or "unknown"
    helper_sel = (result.get("helper") or {}).get("selected") or "-"
    skip_n = denseness_agg.get("skip_n") or 0
    msg = (
        f"self-evolve(runtime): materialize=current-source "
        f"backend={backend} selected={result.get('selected')} "
        f"observed={result.get('observed')} "
        f"helper={helper_sel} "
        f"denseness_skip={skip_n} "
        f"explorer_cap={explorer_cap} "
        f"kernel=aura incr_proven=false fiber_live={fl}"
    )
    git_res = git_commit_and_maybe_push(
        repo,
        message=msg,
        paths=paths,
        no_push=bool(getattr(args, "no_push", False)),
    )
    clock.end(
        "materialize_commit",
        ok=bool(git_res.get("ok") or git_res.get("reason") == "nothing_to_commit"),
        extra={"committed": bool(git_res.get("committed")), "reason": git_res.get("reason")},
    )
    print(json.dumps({"event": "git", **git_res}, ensure_ascii=False))

    latency = clock.summary(fiber_live=bool(result.get("fiber_live")))
    print(json.dumps({"event": "self_evolve_latency", **latency}, ensure_ascii=False))
    print(f"self-evolve latency: {latency.get('progress')}", file=sys.stderr)

    nothing = git_res.get("reason") == "nothing_to_commit"
    helpers_for_obs = {k: result.get(k) for k, *_ in helper_specs}
    state = observe_runtime_round(
        state,
        helpers=helpers_for_obs,
        explorers=result.get("explorers") if isinstance(result.get("explorers"), list) else None,
        fiber_live=bool(result.get("fiber_live")),
        fallback_oneshot=fallback_oneshot,
        hang_or_timeout=hang_or_timeout,
        nothing_to_commit=bool(nothing),
        latency=latency,
    )
    save_strategy(repo, state, harness_root)

    if not git_res.get("committed") and not nothing:
        return 1
    return 0
