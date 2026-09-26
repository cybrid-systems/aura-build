"""Host loop: MiniMax proposes one aura-build diff; a human applies it.

Propose never runs pytest. ``--apply-diff`` is the accept. v1 does not push
and does not call ``unshare``. Combat is a different command.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from aura_build.minimax import redact_secrets
from aura_build.schema import validate_episode
from aura_build.self_evolve_host import git_commit_and_maybe_push

_FORBIDDEN = {
    "self_evolve_product.py",
    "self_evolve_host.py",
    "cli.py",
    "cli_parser.py",
    "minimax.py",
}
_SECRET_ENV = ("LLM_API_KEY", "MINIMAX_API_KEY", "OPENAI_API_KEY", "AUTHORIZATION")
_DENY = ("open(", "os.environ", "subprocess", "socket", "urllib", "urlopen", "/proc")
_DEFAULT_AURA = "/home/dev/code/grok-dev/aura-grok/build_soft4079/aura"
_SYSTEM = (
    "You propose a unified diff and nothing else.\n"
    "No prose, no markdown fence, no new files.\n"
    "Touch only the allowlisted path.\n"
    "Do not add secrets, URLs with credentials, or network calls.\n"
    "Do not set incr_proven or fiber_live to true.\n"
)

ProposeFn = Callable[..., dict[str, Any]]
PytestFn = Callable[[list[str], dict[str, str], Path], subprocess.CompletedProcess[str]]


def cmd_product(args: Any, **kwargs: Any) -> int:
    result = run_product(args, **kwargs)
    payload = _public(result)
    text = redact_secrets(json.dumps(payload), extra=result.get("_api_key"))
    if getattr(args, "json", False):
        print(text)
    else:
        print(
            f"self-evolve product reason={payload.get('reason')} "
            f"exit={payload.get('exit_code')}"
        )
    return int(result.get("exit_code") or 0)


def run_product(args: Any, *, propose: ProposeFn | None = None, pytest_run: PytestFn | None = None) -> dict[str, Any]:
    repo = Path(getattr(args, "repo", None) or Path.cwd()).resolve()
    allow = _check_allow(repo, str(getattr(args, "allow", "") or ""))
    if isinstance(allow, dict):
        return _finish(repo, None, allow, api_key=None)
    session = _check_session(repo, str(getattr(args, "session", "") or ""))
    if isinstance(session, dict):
        return _finish(repo, None, session, api_key=None)
    pytest_paths = _check_pytest(getattr(args, "pytest", None) or [])
    if isinstance(pytest_paths, dict):
        return _finish(repo, session, pytest_paths, api_key=None)
    cap = min(int(getattr(args, "max_rounds", 3) or 3), 3)
    pre = _preflight(repo)
    if not pre.get("ok"):
        return _finish(repo, session, pre, api_key=None)
    apply_diff = getattr(args, "apply_diff", None)
    if apply_diff:
        return _apply(
            repo,
            session,
            allow,
            pytest_paths,
            Path(apply_diff),
            pre,
            pytest_run or _default_pytest,
        )
    goal = str(getattr(args, "goal", "") or "")
    if not goal.strip():
        return _finish(repo, session, _refuse("goal_required"), api_key=None)
    return _propose(
        repo,
        session,
        allow,
        pytest_paths,
        goal,
        cap,
        pre,
        propose,
        aura_bin=getattr(args, "aura_bin", None),
        env_file=getattr(args, "env_file", None),
    )


def _propose(
    repo: Path,
    session: Path,
    allow: str,
    pytest_paths: list[str],
    goal: str,
    cap: int,
    pre: dict[str, Any],
    propose: ProposeFn | None,
    *,
    aura_bin: str | None,
    env_file: Path | None,
) -> dict[str, Any]:
    stop = session / "stop"
    if stop.is_file():
        reason = stop.read_text(encoding="utf-8").strip() or "minimax_http_401"
        return _finish(repo, session, _refuse(reason, pre=pre), api_key=None)
    n = _read_int(session / "completions")
    if n >= cap:
        return _finish(
            repo,
            session,
            {"ok": False, "reason": "max_rounds_3", "exit_code": 1, "pre": pre, "llm_via": None},
            api_key=None,
        )
    n += 1
    (session / "completions").write_text(f"{n}\n", encoding="utf-8")
    api_key = None
    if propose is None:
        try:
            from aura_build.minimax import load_minimax_config

            cfg = load_minimax_config(env_file=env_file)
            api_key = cfg.api_key
        except SystemExit as exc:
            return _finish(
                repo,
                session,
                _refuse("minimax_key_missing", detail=str(exc), pre=pre, completions=n),
                api_key=None,
            )
    messages = _messages(repo, session, allow, goal)
    if propose is None:
        raw = _live_propose(session, messages, aura_bin, env_file)
    else:
        raw = propose(messages=messages, session=session, n=n)
    raw = raw if isinstance(raw, dict) else {"ok": False, "error": "bad_propose"}
    api_key = api_key or raw.get("_api_key")
    content = str(raw.get("content") or "")
    if api_key and api_key in content:
        (session / "stop").write_text("secret_in_output\n", encoding="utf-8")
        return _episode_return(
            repo, session, allow, pytest_paths, goal, pre, n,
            _refuse("secret_in_output", pre=pre, completions=n, llm_via=raw.get("llm_via")),
            api_key=str(api_key),
            notes="secret_in_output",
        )
    if raw.get("action") == "refuse" or raw.get("reason") == "serve_session_timeout":
        (session / "stop").write_text("serve_session_timeout\n", encoding="utf-8")
        out = _refuse("serve_session_timeout", pre=pre, completions=n)
        out["llm_via"] = None
        out["llm_parallel"] = "none"
        out["fiber_error"] = raw.get("error")
        return _episode_return(
            repo, session, allow, pytest_paths, goal, pre, n, out,
            api_key=str(api_key or ""), notes="serve_session_timeout",
        )
    err = str(raw.get("error") or "")
    if raw.get("http_status") == 401 or "401" in err:
        (session / "stop").write_text("minimax_http_401\n", encoding="utf-8")
        return _episode_return(
            repo, session, allow, pytest_paths, goal, pre, n,
            _refuse("minimax_http_401", pre=pre, completions=n, llm_via=raw.get("llm_via")),
            api_key=str(api_key or ""), notes="minimax_http_401",
        )
    if not raw.get("ok"):
        _write_failure(session, n, "minimax_http")
        reason = "max_rounds_3" if n >= cap else "minimax_http"
        code = 1
        return _episode_return(
            repo, session, allow, pytest_paths, goal, pre, n,
            {
                "ok": False,
                "reason": reason,
                "exit_code": code,
                "pre": pre,
                "completions": n,
                "llm_via": raw.get("llm_via"),
                "llm_parallel": raw.get("llm_parallel") or "none",
                "fiber_error": err,
            },
            api_key=str(api_key or ""),
            notes="minimax_http",
        )
    checked = _static_diff(repo, content, allow)
    if not checked.get("ok"):
        _write_failure(
            session,
            n,
            "\n".join(
                [
                    str(checked.get("reason") or "diff_rejected"),
                    str(checked.get("detail") or ""),
                    str(checked.get("diff") or "")[:1500],
                ]
            ),
        )
        reason = "max_rounds_3" if n >= cap else str(checked.get("reason"))
        return _episode_return(
            repo, session, allow, pytest_paths, goal, pre, n,
            {
                "ok": False,
                "reason": reason,
                "exit_code": 1,
                "pre": pre,
                "completions": n,
                "llm_via": raw.get("llm_via"),
                "llm_parallel": raw.get("llm_parallel"),
                "numstat": checked.get("numstat"),
            },
            api_key=str(api_key or ""),
            notes=str(checked.get("reason")),
        )
    diff = str(checked["diff"])
    (session / f"round-{n}.diff").write_text(diff, encoding="utf-8")
    return _episode_return(
        repo, session, allow, pytest_paths, goal, pre, n,
        {
            "ok": True,
            "reason": "diff_ready",
            "exit_code": 0,
            "pre": pre,
            "completions": n,
            "llm_via": raw.get("llm_via"),
            "llm_parallel": raw.get("llm_parallel"),
            "numstat": checked.get("numstat"),
            "diff_path": str(session / f"round-{n}.diff"),
        },
        api_key=str(api_key or ""),
        notes="diff_ready",
        fitness=0.0,
    )


def _apply(
    repo: Path,
    session: Path,
    allow: str,
    pytest_paths: list[str],
    diff_path: Path,
    pre: dict[str, Any],
    pytest_run: PytestFn,
) -> dict[str, Any]:
    resolved = diff_path if diff_path.is_absolute() else (repo / diff_path)
    try:
        resolved = resolved.resolve()
        resolved.relative_to(session.resolve())
    except ValueError:
        return _finish(repo, session, _refuse("session_rejected", pre=pre), api_key=None)
    if not resolved.is_file() or not re.fullmatch(r"round-\d+\.diff", resolved.name):
        return _finish(repo, session, _refuse("session_rejected", pre=pre), api_key=None)
    n = int(resolved.stem.split("-", 1)[1])
    text = resolved.read_text(encoding="utf-8")
    checked = _static_diff(repo, text, allow)
    if not checked.get("ok"):
        _write_failure(session, n, str(checked.get("reason")))
        return _episode_return(
            repo, session, allow, pytest_paths, "", pre, n,
            {"ok": False, "reason": checked.get("reason"), "exit_code": 1, "pre": pre},
            api_key="", notes=str(checked.get("reason")),
        )
    diff = str(checked["diff"])
    chk = _git(repo, ["git", "apply", "--check"], input_text=diff)
    if chk.returncode != 0:
        _write_failure(session, n, redact_secrets(chk.stderr or chk.stdout or "apply_check"))
        return _episode_return(
            repo, session, allow, pytest_paths, "", pre, n,
            {"ok": False, "reason": "apply_check", "exit_code": 1, "pre": pre},
            api_key="", notes="apply_check",
        )
    applied = _git(repo, ["git", "apply"], input_text=diff)
    if applied.returncode != 0:
        _restore(repo, str(pre["pre_sha"]), session)
        _write_failure(session, n, "apply_failed")
        return _episode_return(
            repo, session, allow, pytest_paths, "", pre, n,
            {"ok": False, "reason": "diff_spill", "exit_code": 2, "pre": pre},
            api_key="", notes="diff_spill",
        )
    if not _porcelain_only_allow(repo, allow):
        restored = _restore(repo, str(pre["pre_sha"]), session)
        reason = "diff_spill" if restored else "restore_incomplete"
        _write_failure(session, n, reason)
        return _episode_return(
            repo, session, allow, pytest_paths, "", pre, n,
            {"ok": False, "reason": reason, "exit_code": 2, "pre": pre},
            api_key="", notes=reason,
        )
    env = os.environ.copy()
    for name in _SECRET_ENV:
        env.pop(name, None)
    py = repo / ".venv" / "bin" / "python"
    exe = str(py) if py.is_file() else sys.executable
    argv = [exe, "-m", "pytest", "-q", *pytest_paths]
    try:
        proc = pytest_run(argv, env, repo)
        timed_out = False
    except subprocess.TimeoutExpired:
        proc = subprocess.CompletedProcess(argv, 1, "", "pytest timed out")
        timed_out = True
    tail = redact_secrets(((proc.stdout or "") + (proc.stderr or ""))[-2048:])
    if timed_out or proc.returncode != 0:
        restored = _restore(repo, str(pre["pre_sha"]), session)
        reason = "pytest_timeout" if timed_out else "pytest_red"
        if not restored:
            reason = "restore_incomplete"
        _write_failure(session, n, tail or reason)
        code = 2 if reason == "restore_incomplete" else 1
        return _episode_return(
            repo, session, allow, pytest_paths, "", pre, n,
            {"ok": False, "reason": reason, "exit_code": code, "pre": pre, "pytest_argv": argv},
            api_key="", notes=tail or reason, pytest_exit=proc.returncode,
        )
    via, parallel = _last_llm(session)
    message = (
        "self-evolve product: stamp_banner_agrees\n\n"
        f"verify=pytest {' '.join(pytest_paths)}\n"
        f"llm_via={via} llm_parallel={parallel} incr_proven=false fiber_live=false\n"
    )
    committed = git_commit_and_maybe_push(
        repo, message=message, paths=[allow], no_push=True
    )
    ok = bool(committed.get("committed"))
    return _episode_return(
        repo, session, allow, pytest_paths, "", pre, n,
        {
            "ok": ok,
            "reason": "committed_no_push" if ok else committed.get("reason"),
            "exit_code": 0 if ok else 1,
            "pre": pre,
            "committed": ok,
            "pushed": False,
            "tip": committed.get("tip"),
            "pytest_argv": argv,
            "llm_via": via,
            "llm_parallel": parallel,
        },
        api_key="",
        notes="committed_no_push",
        fitness=1.0 if ok else 0.0,
        passed=ok,
        pytest_exit=0,
    )


def _live_propose(
    session: Path,
    messages: list[dict[str, str]],
    aura_bin: str | None,
    env_file: Path | None,
) -> dict[str, Any]:
    from aura_build.fiber_llm import fiber_chat_completions, fiber_llm_probe
    from aura_build.minimax import chat_completions, load_minimax_config
    from aura_build.serve_session import start_session, stop_session

    cfg = load_minimax_config(env_file=env_file)
    bin_path = aura_bin or os.environ.get("AURA_BIN") or _DEFAULT_AURA
    os.environ["AURA_BIN"] = bin_path
    os.environ.setdefault("AURA_SANDBOX", "off")
    lib = Path(bin_path).resolve().parents[1] / "lib"
    if lib.is_dir():
        os.environ.setdefault("AURA_PATH", str(lib))
    harness = session / "serve"
    holder = None
    try:
        holder = start_session(aura_bin=bin_path, harness_root=harness, force=True)
        probe = fiber_llm_probe(holder, scratch_dir=session / "fiber", config=cfg)
        result = fiber_chat_completions(
            holder,
            messages,
            config=cfg,
            scratch_dir=session / "fiber",
            temperature=0.2,
            max_tokens=4096,
            thinking_disabled=True,
            timeout_s=120.0,
        )
        result["probe_ok"] = bool(probe.get("ok"))
        result["probe_reason"] = probe.get("reason")
        result["_api_key"] = cfg.api_key
        err = str(result.get("error") or "")
        if "serve_session_timeout" in err:
            result["action"] = "refuse"
            result["llm_via"] = None
            return result
        if result.get("ok") and result.get("llm_via") == "fiber":
            result["llm_parallel"] = "fiber_serial"
            return result
        if result.get("llm_via") == "fiber" and str(result.get("content") or "").strip():
            result["ok"] = False
            result["llm_parallel"] = "fiber_serial"
            return result
        host = chat_completions(
            messages,
            config=cfg,
            temperature=0.2,
            max_tokens=4096,
            thinking_disabled=True,
            timeout_s=90.0,
        )
        host["llm_via"] = "host"
        host["llm_parallel"] = "none"
        host["fiber_error"] = err
        host["probe_ok"] = result.get("probe_ok")
        host["probe_reason"] = result.get("probe_reason")
        host["_api_key"] = cfg.api_key
        return host
    except Exception as exc:  # noqa: BLE001 — propose must stop the session
        err = str(exc)
        if "serve_session_timeout" in err:
            return {"ok": False, "action": "refuse", "error": err, "llm_via": None}
        return {"ok": False, "error": err, "llm_via": "host", "llm_parallel": "none"}
    finally:
        for name in _SECRET_ENV:
            os.environ.pop(name, None)
        try:
            stop_session(harness_root=harness)
        except Exception:
            pass
        del holder


def _static_diff(repo: Path, raw: str, allow: str) -> dict[str, Any]:
    text = raw.strip()
    fence = re.match(r"^```(?:diff)?\s*\n([\s\S]*?)\n```$", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("diff --git ")
    if start > 0:
        text = text[start:]
    if not text.startswith("diff --git "):
        return {"ok": False, "reason": "diff_parse"}
    headers = re.findall(r"^diff --git a/(\S+) b/(\S+)", text, flags=re.M)
    if not headers:
        return {"ok": False, "reason": "diff_parse"}
    paths: set[str] = set()
    for a_path, b_path in headers:
        paths.add(a_path)
        paths.add(b_path)
    for line in text.splitlines():
        if line.startswith("--- "):
            paths.add(_diff_path(line[4:].strip()))
        elif line.startswith("+++ "):
            paths.add(_diff_path(line[4:].strip()))
    if paths != {allow}:
        return {"ok": False, "reason": "diff_path"}
    numstat = 0
    for line in text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+") or line.startswith("-"):
            numstat += 1
            if line.startswith("+") and _denied_add(line[1:]):
                return {"ok": False, "reason": "denylist", "numstat": numstat}
    if numstat > 120:
        return {"ok": False, "reason": "numstat", "numstat": numstat}
    chk = _git(repo, ["git", "apply", "--check"], input_text=text + "\n")
    if chk.returncode != 0:
        return {
            "ok": False,
            "reason": "apply_check",
            "detail": (chk.stderr or chk.stdout or "")[-500:],
            "diff": text,
            "numstat": numstat,
        }
    return {"ok": True, "diff": text + "\n", "numstat": numstat}


def _diff_path(token: str) -> str:
    if token.startswith("a/") or token.startswith("b/"):
        return token[2:]
    return token


def _denied_add(body: str) -> bool:
    stripped = body.strip()
    if stripped.startswith("import ") or stripped.startswith("from "):
        if stripped.startswith("import re") or stripped.startswith("from re "):
            return False
        return True
    return any(tok in body for tok in _DENY)


def _check_allow(repo: Path, allow: str) -> str | dict[str, Any]:
    path = Path(allow)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".py":
        return _refuse("allow_rejected")
    if not allow.startswith("src/aura_build/"):
        return _refuse("allow_rejected")
    if path.name in _FORBIDDEN:
        return _refuse("allow_rejected")
    full = repo / allow
    if not full.is_file() or full.stat().st_size > 64 * 1024:
        return _refuse("allow_rejected")
    return allow


def _check_pytest(values: list[str]) -> list[str] | dict[str, Any]:
    if not values:
        return _refuse("pytest_rejected")
    out: list[str] = []
    for raw in values:
        path = Path(raw)
        if path.is_absolute() or ".." in path.parts:
            return _refuse("pytest_rejected")
        if not re.fullmatch(r"tests/test_.*\.py", raw):
            return _refuse("pytest_rejected")
        out.append(raw)
    return out


def _check_session(repo: Path, raw: str) -> Path | dict[str, Any]:
    if not raw:
        return _refuse("session_rejected")
    path = Path(raw)
    if path.is_absolute():
        full = path.resolve()
    else:
        full = (repo / path).resolve()
    root = (repo / "scratch" / "self_evolve_product").resolve()
    try:
        full.relative_to(root)
    except ValueError:
        return _refuse("session_rejected")
    full.mkdir(parents=True, exist_ok=True)
    return full


def _preflight(repo: Path) -> dict[str, Any]:
    status = _git(repo, ["git", "status", "--porcelain"])
    if status.returncode != 0:
        return _refuse("dirty_tree")
    if status.stdout.strip():
        return _refuse("dirty_tree")
    branch = _git(repo, ["git", "branch", "--show-current"])
    name = (branch.stdout or "").strip()
    if not name:
        return _refuse("detached_head")
    sha = _git(repo, ["git", "rev-parse", "HEAD"])
    if sha.returncode != 0 or not (sha.stdout or "").strip():
        return _refuse("detached_head")
    return {"ok": True, "pre_sha": sha.stdout.strip(), "branch": name}


def _porcelain_only_allow(repo: Path, allow: str) -> bool:
    lines = [
        ln for ln in (_git(repo, ["git", "status", "--porcelain"]).stdout or "").splitlines() if ln.strip()
    ]
    if len(lines) != 1:
        return False
    line = lines[0]
    xy, path = line[:2], line[3:]
    if path != allow:
        return False
    if "D" in xy or "?" in xy:
        return False
    return "M" in xy


def _restore(repo: Path, pre_sha: str, session: Path) -> bool:
    head = (_git(repo, ["git", "rev-parse", "HEAD"]).stdout or "").strip()
    if head != pre_sha:
        return False
    names = set()
    for args in (
        ["git", "diff", "--name-only"],
        ["git", "diff", "--cached", "--name-only"],
    ):
        proc = _git(repo, args)
        names.update(ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip())
    if names:
        _git(
            repo,
            ["git", "restore", f"--source={pre_sha}", "--worktree", "--staged", "--", *sorted(names)],
        )
    session_rel = session.resolve()
    porcelain = _git(repo, ["git", "status", "--porcelain"]).stdout or ""
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        if line[:2] != "??":
            continue
        rel = line[3:]
        full = (repo / rel).resolve()
        try:
            full.relative_to(session_rel)
            continue
        except ValueError:
            pass
        if full.is_file():
            full.unlink()
        elif full.is_dir():
            _rm_tree(full)
    left = (_git(repo, ["git", "status", "--porcelain"]).stdout or "").strip()
    return left == ""


def _rm_tree(path: Path) -> None:
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    path.rmdir()


def _default_pytest(
    argv: list[str], env: dict[str, str], repo: Path
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.Popen(
        argv,
        cwd=str(repo),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise
    return subprocess.CompletedProcess(argv, proc.returncode or 0, out, err)


def _git(
    repo: Path, args: list[str], *, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(repo),
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )


def _messages(repo: Path, session: Path, allow: str, goal: str) -> list[dict[str, str]]:
    current = (repo / allow).read_text(encoding="utf-8")
    prev = _highest(session, "round-", ".diff")
    fail = _highest(session, "round-", ".failure.txt")
    user = goal + "\n\nCurrent file:\n" + current
    if prev:
        user += "\n\nPrevious diff:\n" + redact_secrets(prev.read_text(encoding="utf-8"))
    if fail:
        user += "\n\nPrevious failure:\n" + redact_secrets(fail.read_text(encoding="utf-8"))
    return [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}]


def _last_llm(session: Path) -> tuple[Any, Any]:
    path = session / "episodes.jsonl"
    if not path.is_file():
        return None, None
    last = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            last = json.loads(line)
    if not isinstance(last, dict):
        return None, None
    runtime = last.get("runtime") if isinstance(last.get("runtime"), dict) else {}
    return runtime.get("llm_via"), runtime.get("llm_parallel")


def _highest(session: Path, prefix: str, suffix: str) -> Path | None:
    best: tuple[int, Path] | None = None
    for path in session.glob(f"{prefix}*{suffix}"):
        mid = path.name[len(prefix) : -len(suffix)] if suffix else path.name[len(prefix) :]
        if not mid.isdigit():
            continue
        n = int(mid)
        if best is None or n > best[0]:
            best = (n, path)
    return best[1] if best else None


def _write_failure(session: Path, n: int, text: str) -> None:
    (session / f"round-{n}.failure.txt").write_text(redact_secrets(text)[:2048], encoding="utf-8")


def _read_int(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        return int(path.read_text(encoding="utf-8").strip() or "0")
    except ValueError:
        return 0


def _refuse(reason: str, **extra: Any) -> dict[str, Any]:
    out = {"ok": False, "reason": reason, "exit_code": 2}
    out.update(extra)
    return out


def _episode_return(
    repo: Path,
    session: Path,
    allow: str,
    pytest_paths: list[str],
    goal: str,
    pre: dict[str, Any],
    n: int,
    result: dict[str, Any],
    *,
    api_key: str,
    notes: str,
    fitness: float = 0.0,
    passed: bool = False,
    pytest_exit: int | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    via = result.get("llm_via")
    if via == "fiber" and result.get("reason") == "serve_session_timeout":
        via = None
    if pytest_exit is not None:
        result["pytest_exit"] = pytest_exit
    episode = {
        "schema_version": "trajectory.v0",
        "episode_id": f"sep-{now.strftime('%Y%m%dT%H%M%S')}-r{n}",
        "ts_start": stamp,
        "ts_end": stamp,
        "prompt": goal,
        "runtime": {
            "mode": "host_pytest",
            "requested_mode": "host_pytest",
            "kernel": "host",
            "llm_via": via,
            "llm_parallel": result.get("llm_parallel"),
            "fiber_live": False,
            "incr_proven": False,
            "fitness_source": "pytest_exit",
            "product_loop": True,
            "pre_sha": pre.get("pre_sha"),
            "allow": [allow],
            "verify_argv": ["python", "-m", "pytest", "-q", *pytest_paths],
            "propose": {
                "probe_ok": result.get("probe_ok"),
                "probe_reason": result.get("probe_reason"),
            },
        },
        "harness": {
            "l1_strategy_id": "self_evolve_product.v0",
            "l2_weights_id": None,
            "l3_online": False,
            "outcome": result.get("reason"),
        },
        "worldlines": [
            {
                "id": "wl-0",
                "parent_id": None,
                "mutations": [
                    {
                        "op": "unified_diff",
                        "target_id": allow,
                        "summary": str(result.get("numstat") or 0),
                    }
                ],
                "eval": {
                    "fitness": fitness,
                    "passed": passed,
                    "metrics": {"pytest_exit": pytest_exit, "incr_proven": False},
                    "notes": redact_secrets(notes, extra=api_key or None)[:500],
                },
            }
        ],
        "selected_id": "wl-0",
        "selection_reason": "pytest_exit",
        "privacy": {"redacted": True, "retention_class": "dogfood"},
    }
    validate_episode(episode)
    line = redact_secrets(json.dumps(episode), extra=api_key or None)
    with (session / "episodes.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    result["completions"] = n
    result["episode_id"] = episode["episode_id"]
    return _finish(repo, session, result, api_key=api_key or None)


def _finish(
    repo: Path, session: Path | None, result: dict[str, Any], *, api_key: str | None
) -> dict[str, Any]:
    result.setdefault("pushed", False)
    result["_api_key"] = api_key
    if session is not None:
        pre = result.get("pre") if isinstance(result.get("pre"), dict) else {}
        ok = "true" if result.get("ok") else "false"
        body = "\n".join(
            [
                f"ts={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
                f"branch={pre.get('branch', '')}",
                f"pre_sha={pre.get('pre_sha', '')}",
                f"commit={result.get('tip') or 'none'}",
                f"completions={result.get('completions', _read_int(session / 'completions'))}",
                f"pytest_exit={result.get('pytest_exit', 'not_run')}",
                f"llm_via={result.get('llm_via')}",
                f"llm_parallel={result.get('llm_parallel')}",
                "push=false",
                "incr_proven=false",
                "fiber_live=false",
                f"ok={ok}",
                f"reason={result.get('reason')}",
            ]
        )
        (session / "PRODUCT1.md").write_text(body + "\n", encoding="utf-8")
    return result


def _public(result: dict[str, Any]) -> dict[str, Any]:
    skip = {"_api_key", "pre"}
    out = {k: v for k, v in result.items() if k not in skip and "key" not in k.lower()}
    return out
