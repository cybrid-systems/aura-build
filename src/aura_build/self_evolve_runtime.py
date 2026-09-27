"""Soft runtime self-evolve: Soft tip mutate → select-best → current-source → commit.

North-star dogfood (not corpus-gen repair):
  Soft oneshot runs ``aura/self_evolve_runtime.aura`` which:
    set-code → mutate:rebind candidates → observe → select-best →
    (current-source :workspace :pretty) → write-file aura/self_evolve_stamp.aura
  Host verifies stamp banner honesty, then commits+pushes only the selected
  materialized stamp (and the runtime kernel file when changed).

Never invents fiber_live / incr_proven / Soft Ready.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from aura_build.self_evolve_host import git_commit_and_maybe_push, run_host_verify
from aura_build.stamp_banner import stamp_banner_agrees

DEFAULT_SOFT = "/workspace/aura-grok/build_soft4079/aura"
RUNTIME_KERNEL = "aura/self_evolve_runtime.aura"
STAMP_PATH = "aura/self_evolve_stamp.aura"

_RUNTIME_OK_RE = re.compile(
    r"RUNTIME_OK\s+selected=(?P<selected>\S+)\s+observed=(?P<observed>\S+)"
    r"\s+src_len=(?P<src_len>\d+)\s+wrote=(?P<wrote>\S+)"
)


def _run_soft_runtime(
    repo: Path,
    *,
    aura_bin: str,
    timeout_s: float = 60.0,
) -> dict[str, Any]:
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
        }
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    m = _RUNTIME_OK_RE.search(out)
    fail = "RUNTIME_FAIL" in out or "current-source-empty" in out
    if proc.returncode != 0 and not m:
        return {
            "ok": False,
            "reason": "soft_nonzero_exit",
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "")[-2000:],
            "stderr": (proc.stderr or "")[-2000:],
        }
    if fail or not m:
        # Soft/kernel anomaly candidate
        return {
            "ok": False,
            "reason": "runtime_fail_or_unparsed",
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "")[-2000:],
            "stderr": (proc.stderr or "")[-2000:],
            "aura_issue_candidate": True,
            "tip_note": "Soft current-source materialize failed; file Aura issue with tip SHA + repro",
        }
    wrote = m.group("wrote")
    stamp = repo / STAMP_PATH
    if wrote == "none" or not stamp.is_file():
        return {
            "ok": False,
            "reason": "stamp_not_written",
            "wrote": wrote,
            "aura_issue_candidate": True,
        }
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
    return {
        "ok": True,
        "reason": "runtime_ok",
        "selected": m.group("selected"),
        "observed": m.group("observed"),
        "src_len": int(m.group("src_len")),
        "wrote": wrote,
        "stamp_path": STAMP_PATH,
        "materialize": "current-source",
        "incr_proven": False,
        "fiber_live": False,
        "kernel": "aura",
        "stdout": (proc.stdout or "")[-1500:],
        "exit_code": proc.returncode,
    }


def cmd_runtime(args: Any) -> int:
    repo = Path(getattr(args, "repo", None) or Path.cwd()).resolve()
    # Prefer Soft tip; allow override
    aura_bin = (
        getattr(args, "aura_bin", None)
        or os.environ.get("AURA_BIN")
        or DEFAULT_SOFT
    )
    result = _run_soft_runtime(repo, aura_bin=str(aura_bin))
    print(json.dumps({"event": "self_evolve_runtime", **result}, ensure_ascii=False))
    if not result.get("ok"):
        if result.get("aura_issue_candidate"):
            print(
                "self-evolve runtime: Soft/current-source anomaly candidate — "
                "file Aura issue with tip SHA + repro (do not invent Soft Ready)",
                file=sys.stderr,
            )
        return 1

    verify_mode = getattr(args, "verify", "stamp") or "stamp"
    verify = run_host_verify(
        repo,
        verify_mode,
        aura_bin=str(aura_bin),
        harness_root=Path(getattr(args, "harness_root", None) or (repo / ".aura-build")),
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

    paths = [STAMP_PATH, RUNTIME_KERNEL]
    # Only commit paths that exist and changed
    msg = (
        f"self-evolve(runtime): materialize=current-source "
        f"selected={result.get('selected')} observed={result.get('observed')} "
        f"kernel=aura incr_proven=false fiber_live=false"
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
