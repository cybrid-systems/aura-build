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

DEFAULT_SOFT = "/workspace/aura-grok/build_soft4079/aura"
RUNTIME_KERNEL = "aura/self_evolve_runtime.aura"
STAMP_PATH = "aura/self_evolve_stamp.aura"
DEFAULT_BUMPS = (2, 9, 4, 7, 1)

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


def _run_serve_fiber(
    repo: Path,
    *,
    aura_bin: str,
    worldlines: int = 3,
    bumps: tuple[int, ...] | list[int] | None = None,
    harness_root: Path | None = None,
) -> dict[str, Any]:
    """Long-lived Soft serve + denseness + fiber explorer worldlines → current-source."""
    from aura_build.llm_dogfood import fiber_fanout_probe
    from aura_build.serve_session import start_session

    hroot = harness_root or (repo / ".aura-build")
    bumps_list = list(bumps) if bumps else list(DEFAULT_BUMPS[: max(1, int(worldlines))])
    if len(bumps_list) < int(worldlines):
        # pad uniquely
        x = max(bumps_list) + 1 if bumps_list else 1
        while len(bumps_list) < int(worldlines):
            bumps_list.append(x)
            x += 1

    sess = None
    try:
        sess = start_session(aura_bin=aura_bin, harness_root=hroot, force=True)
        if not sess.alive():
            return {"ok": False, "reason": "serve_not_alive", "fallback_ok": True}

        probe = fiber_fanout_probe(sess, n=max(1, int(worldlines)), timeout_s=8.0)
        denseness_ok = bool(probe.get("ok"))
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

        boot = sess.raw_line('(set-code "(define (cand) 0)")', timeout_s=10.0)
        if boot.get("status") != "ok":
            return {
                "ok": False,
                "reason": f"set_code_failed:{boot.get('msg') or boot.get('status')}",
                "fallback_ok": True,
                "denseness": probe,
            }
        ev0 = sess.raw_line("(eval-current)", timeout_s=10.0)
        # Soft may return status=closure for define forms — accept ok or closure
        st0 = str(ev0.get("status") or "")
        if st0 not in ("ok", "closure") and ev0.get("status") not in ("ok",):
            # still continue if mutate works later
            pass

        explorers: list[dict[str, Any]] = []
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
            ok = r.get("status") == "ok" and _as_num(val) > -999_999
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
        if not ok_ex:
            return {
                "ok": False,
                "reason": "fiber_explorers_all_failed",
                "explorers": explorers,
                "denseness": probe,
                "fallback_ok": True,
                "aura_issue_candidate": True,
            }

        best = max(ok_ex, key=lambda e: (int(e["observed"]), int(e["bump"])))
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
        if not v.get("ok"):
            return {
                **v,
                "explorers": explorers,
                "denseness": probe,
                "aura_issue_candidate": True,
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
        if sess is not None:
            try:
                sess.stop()
            except Exception:  # noqa: BLE001
                pass


# Back-compat alias used by tests / older call sites
def _run_soft_runtime(
    repo: Path,
    *,
    aura_bin: str,
    timeout_s: float = 60.0,
) -> dict[str, Any]:
    return _run_soft_oneshot(repo, aura_bin=aura_bin, timeout_s=timeout_s)


def cmd_runtime(args: Any) -> int:
    repo = Path(getattr(args, "repo", None) or Path.cwd()).resolve()
    aura_bin = (
        getattr(args, "aura_bin", None)
        or os.environ.get("AURA_BIN")
        or DEFAULT_SOFT
    )
    force_oneshot = bool(getattr(args, "force_oneshot", False))
    prefer_serve = not force_oneshot and bool(getattr(args, "prefer_serve", True))
    worldlines = int(getattr(args, "worldlines", None) or 3)
    harness_root = Path(
        getattr(args, "harness_root", None) or (repo / ".aura-build")
    )

    result: dict[str, Any]
    if prefer_serve:
        result = _run_serve_fiber(
            repo,
            aura_bin=str(aura_bin),
            worldlines=worldlines,
            harness_root=harness_root,
        )
        print(json.dumps({"event": "self_evolve_runtime_serve", **result}, ensure_ascii=False))
        if not result.get("ok") and result.get("fallback_ok", True):
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
    else:
        result = _run_soft_oneshot(repo, aura_bin=str(aura_bin))

    print(json.dumps({"event": "self_evolve_runtime", **result}, ensure_ascii=False))
    if not result.get("ok"):
        if result.get("aura_issue_candidate"):
            print(
                "self-evolve runtime: Soft/current-source/fiber anomaly candidate — "
                "file Aura issue with tip SHA + repro (do not invent Soft Ready)",
                file=sys.stderr,
            )
        return 1

    verify_mode = getattr(args, "verify", "stamp") or "stamp"
    verify = run_host_verify(
        repo,
        verify_mode,
        aura_bin=str(aura_bin),
        harness_root=harness_root,
    )
    print(json.dumps({"event": "host_verify", **verify}, ensure_ascii=False))
    if not verify.get("ok"):
        print(
            f"self-evolve runtime: verify failed reason={verify.get('reason')} (no commit)",
            file=sys.stderr,
        )
        return int(verify.get("exit_code") or 1)

    if getattr(args, "no_commit", False):
        print("self-evolve runtime: --no-commit; skip git")
        return 0

    paths = [STAMP_PATH, RUNTIME_KERNEL, "src/aura_build/self_evolve_runtime.py"]
    fl = "true" if result.get("fiber_live") else "false"
    backend = result.get("worldline_backend") or "unknown"
    msg = (
        f"self-evolve(runtime): materialize=current-source "
        f"backend={backend} selected={result.get('selected')} "
        f"observed={result.get('observed')} "
        f"kernel=aura incr_proven=false fiber_live={fl}"
    )
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
