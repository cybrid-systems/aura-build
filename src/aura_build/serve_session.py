"""Host-managed long-lived Aura ``--serve`` session (optimal-loop MVP).

Architecture:
- ``session start`` spawns a **holder daemon** that owns ``aura --serve`` pipes
  and listens on ``.aura-build/serve.sock``.
- CLI / verify clients talk JSON-lines over the socket (host IPC only).
- Honesty: ``session_model=serve`` only when daemon+aura pid alive (not env).
- Soft boxes use ``--serve`` (not ``--serve-async`` multi-worker).
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aura_build.runtime import aura_subprocess_env, resolve_aura_bin

SESSION_SERVE = "serve"
SESSION_SHARED = "shared_workspace_subprocess"
SESSION_FIBER = "fiber_denseness_in_process"

MARKER_NAME = "serve-session.json"
SOCK_NAME = "serve.sock"
DEFAULT_MODE = "serve"

_ATTACHED: "ServeSession | None" = None


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def marker_path(harness_root: Path | str | None = None) -> Path:
    root = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or ".aura-build"
    )
    return root / MARKER_NAME


def sock_path(harness_root: Path | str | None = None) -> Path:
    root = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or ".aura-build"
    )
    return root / SOCK_NAME


def _escape_aura_string(code: str) -> str:
    return (
        code.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def read_marker(harness_root: Path | str | None = None) -> dict[str, Any] | None:
    path = marker_path(harness_root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_marker(data: dict[str, Any], harness_root: Path | str | None = None) -> Path:
    path = marker_path(harness_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def clear_marker(harness_root: Path | str | None = None) -> None:
    path = marker_path(harness_root)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
    sp = sock_path(harness_root)
    try:
        sp.unlink(missing_ok=True)
    except OSError:
        pass


def _sock_request(
    harness_root: Path,
    payload: dict[str, Any],
    *,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    sp = sock_path(harness_root)
    if not sp.exists():
        return {"status": "error", "msg": "serve_sock_missing"}
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout_s)
            sock.connect(str(sp))
            sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            buf = b""
            while b"\n" not in buf:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
            if not buf:
                return {"status": "error", "msg": "serve_sock_empty"}
            return json.loads(buf.decode("utf-8").splitlines()[0])
    except (OSError, json.JSONDecodeError, TimeoutError) as exc:
        return {"status": "error", "msg": f"serve_sock_error:{exc}"}


def _aura_send_line(
    proc: subprocess.Popen[str],
    line: str,
    *,
    timeout_s: float = 10.0,
) -> dict[str, Any]:
    if proc.poll() is not None:
        return {"status": "error", "msg": "serve_session_dead", "display": ""}
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write(line.rstrip("\n") + "\n")
    proc.stdin.flush()
    display_parts: list[str] = []
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        raw = proc.stdout.readline()
        if raw == "" and proc.poll() is not None:
            break
        s = raw.rstrip("\n")
        if not s:
            continue
        brace = s.rfind("{")
        if brace >= 0:
            prefix = s[:brace]
            if prefix:
                display_parts.append(prefix)
            try:
                obj = json.loads(s[brace:])
            except json.JSONDecodeError:
                display_parts.append(s)
                continue
            if isinstance(obj, dict) and "status" in obj:
                obj = dict(obj)
                obj["display"] = "".join(display_parts)
                return obj
            display_parts.append(s)
        else:
            display_parts.append(s)
    return {
        "status": "error",
        "msg": "serve_session_timeout",
        "display": "".join(display_parts),
    }


def _holder_main(harness_root: str, aura_bin: str) -> None:
    """Daemon entry: own aura --serve + unix socket."""
    hroot = Path(harness_root)
    hroot.mkdir(parents=True, exist_ok=True)
    env = aura_subprocess_env(aura_bin)
    stderr_path = hroot / "serve.stderr.log"
    err_fh = open(stderr_path, "w", encoding="utf-8")  # noqa: SIM115
    proc = subprocess.Popen(
        [aura_bin, "--serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=err_fh,
        text=True,
        env=env,
        bufsize=1,
        start_new_session=True,
    )
    # Warm ping
    warm = _aura_send_line(proc, "(+ 1 1)", timeout_s=8.0)
    if warm.get("status") != "ok":
        try:
            proc.kill()
        except OSError:
            pass
        err_fh.close()
        clear_marker(hroot)
        sys.exit(2)

    sp = sock_path(hroot)
    try:
        sp.unlink(missing_ok=True)
    except OSError:
        pass
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sp))
    server.listen(8)
    write_marker(
        {
            "pid": proc.pid,
            "holder_pid": os.getpid(),
            "aura_bin": aura_bin,
            "mode": DEFAULT_MODE,
            "session_model": SESSION_SERVE,
            "started_at": _iso_now(),
            "harness_root": str(hroot),
            "sock": str(sp),
            "protocol": "unix-sock → aura --serve stdin",
            "notes": (
                "MVP long-lived --serve via holder daemon; "
                "--serve-async Soft multi-worker deferred; "
                "serve_cross_session_shared_ast=false"
            ),
            "serve_cross_session_shared_ast": False,
        },
        hroot,
    )

    lock = threading.Lock()

    def handle(conn: socket.socket) -> None:
        try:
            data = b""
            while b"\n" not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
            if not data:
                return
            req = json.loads(data.decode("utf-8").splitlines()[0])
            op = req.get("op") or "ping"
            with lock:
                if op == "stop":
                    resp = {"status": "ok", "msg": "stopping"}
                    conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
                    try:
                        proc.send_signal(signal.SIGTERM)
                        proc.wait(timeout=3)
                    except Exception:
                        try:
                            proc.kill()
                        except OSError:
                            pass
                    clear_marker(hroot)
                    os._exit(0)
                if op == "ping":
                    r = _aura_send_line(proc, "(+ 1 1)", timeout_s=5.0)
                    resp = {
                        "status": "ok" if r.get("status") == "ok" else "error",
                        "pid": proc.pid,
                        "alive": proc.poll() is None,
                        "value": r.get("value"),
                        "msg": r.get("msg"),
                    }
                elif op == "eval":
                    source = str(req.get("source") or "")
                    timeout_s = float(req.get("timeout_s") or 15.0)
                    t0 = time.monotonic()
                    esc = _escape_aura_string(source)
                    set_r = _aura_send_line(
                        proc, f'(set-code "{esc}")', timeout_s=timeout_s
                    )
                    if set_r.get("status") != "ok":
                        resp = {
                            "status": "error",
                            "ok": False,
                            "msg": set_r.get("msg") or "set-code failed",
                            "stdout": set_r.get("display") or "",
                            "stderr": str(set_r.get("msg") or ""),
                            "ms": int((time.monotonic() - t0) * 1000),
                            "via": "serve_session",
                            "session_model": SESSION_SERVE,
                        }
                    else:
                        ev = _aura_send_line(proc, "(eval-current)", timeout_s=timeout_s)
                        display = str(ev.get("display") or "")
                        msg = str(ev.get("msg") or "")
                        status = ev.get("status")
                        import re as _re

                        has_error = status == "error" or bool(
                            _re.search(
                                r"(?i)\berror:|\bunbound variable\b|\bsyntax\b",
                                display + msg,
                            )
                        )
                        resp = {
                            "status": status,
                            "ok": status == "ok" and not has_error,
                            "msg": msg,
                            "stdout": display,
                            "stderr": msg if has_error else "",
                            "ms": max(1, int((time.monotonic() - t0) * 1000)),
                            "via": "serve_session",
                            "session_model": SESSION_SERVE,
                            "value": ev.get("value"),
                        }
                elif op == "raw":
                    line = str(req.get("line") or "")
                    r = _aura_send_line(
                        proc, line, timeout_s=float(req.get("timeout_s") or 10.0)
                    )
                    resp = r
                else:
                    resp = {"status": "error", "msg": f"unknown_op:{op}"}
            conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
        except Exception as exc:
            try:
                conn.sendall(
                    (json.dumps({"status": "error", "msg": str(exc)}) + "\n").encode()
                )
            except OSError:
                pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    try:
        while True:
            if proc.poll() is not None:
                clear_marker(hroot)
                break
            server.settimeout(1.0)
            try:
                conn, _ = server.accept()
            except socket.timeout:
                continue
            threading.Thread(target=handle, args=(conn,), daemon=True).start()
    finally:
        try:
            server.close()
        except OSError:
            pass
        err_fh.close()
        clear_marker(hroot)


@dataclass
class ServeSession:
    """Client handle to the holder daemon (or in-process for tests)."""

    harness_root: Path
    aura_bin: str
    mode: str = DEFAULT_MODE
    started_at: str = ""
    pid: int = 0
    holder_pid: int = 0

    def alive(self) -> bool:
        st = session_status(harness_root=self.harness_root)
        return bool(st.get("serve_attach_ok"))

    def ping(self, *, timeout_s: float = 5.0) -> bool:
        r = _sock_request(self.harness_root, {"op": "ping"}, timeout_s=timeout_s)
        return r.get("status") == "ok"

    def eval_source(self, source: str, *, timeout_s: float = 15.0) -> dict[str, Any]:
        r = _sock_request(
            self.harness_root,
            {"op": "eval", "source": source, "timeout_s": timeout_s},
            timeout_s=timeout_s + 2.0,
        )
        if "via" not in r:
            r["via"] = "serve_session"
            r["session_model"] = SESSION_SERVE
        if "ms" in r and int(r["ms"] or 0) == 0:
            r["ms"] = 1
        return r

    def stop(self, *, clear: bool = True) -> None:
        _sock_request(self.harness_root, {"op": "stop"}, timeout_s=5.0)
        marker = read_marker(self.harness_root)
        if marker:
            for key in ("holder_pid", "pid"):
                pid = int(marker.get(key) or 0)
                if _pid_alive(pid):
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except OSError:
                        pass
        if clear:
            clear_marker(self.harness_root)


def start_session(
    *,
    aura_bin: str | None = None,
    harness_root: Path | str | None = None,
    force: bool = False,
) -> ServeSession:
    """Start holder daemon + aura --serve; durable across CLI process exit."""
    global _ATTACHED
    hroot = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or ".aura-build"
    )
    hroot.mkdir(parents=True, exist_ok=True)

    existing = attach_session(harness_root=hroot, aura_bin=aura_bin)
    if existing is not None and existing.alive() and not force:
        return existing
    if existing is not None and force:
        existing.stop(clear=True)
    else:
        # Clear stale
        stop_session(harness_root=hroot)

    bin_path = resolve_aura_bin(aura_bin)
    if not bin_path:
        raise RuntimeError("aura_binary_missing: set AURA_BIN / --aura-bin")

    # Spawn holder as detached python -m
    cmd = [
        sys.executable,
        "-c",
        (
            "from aura_build.serve_session import _holder_main; "
            f"_holder_main({str(hroot)!r}, {bin_path!r})"
        ),
    ]
    subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        cwd=str(Path.cwd()),
        env=os.environ.copy(),
    )
    # Wait for marker + ping
    sess: ServeSession | None = None
    deadline = time.monotonic() + 12.0
    while time.monotonic() < deadline:
        marker = read_marker(hroot)
        if marker and sock_path(hroot).exists():
            sess = ServeSession(
                harness_root=hroot,
                aura_bin=bin_path,
                mode=DEFAULT_MODE,
                started_at=str(marker.get("started_at") or _iso_now()),
                pid=int(marker.get("pid") or 0),
                holder_pid=int(marker.get("holder_pid") or 0),
            )
            if sess.ping(timeout_s=2.0):
                _ATTACHED = sess
                return sess
        time.sleep(0.1)
    raise RuntimeError("serve_session_start_timeout: holder did not become ready")


def attach_session(
    *,
    harness_root: Path | str | None = None,
    aura_bin: str | None = None,
) -> ServeSession | None:
    hroot = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or ".aura-build"
    )
    marker = read_marker(hroot)
    if not marker:
        return None
    holder = int(marker.get("holder_pid") or 0)
    aura_pid = int(marker.get("pid") or 0)
    if not (_pid_alive(holder) or _pid_alive(aura_pid)):
        clear_marker(hroot)
        return None
    if not sock_path(hroot).exists():
        return None
    bin_path = str(marker.get("aura_bin") or resolve_aura_bin(aura_bin) or "")
    return ServeSession(
        harness_root=hroot,
        aura_bin=bin_path,
        mode=str(marker.get("mode") or DEFAULT_MODE),
        started_at=str(marker.get("started_at") or ""),
        pid=aura_pid,
        holder_pid=holder,
    )


def session_status(
    *,
    harness_root: Path | str | None = None,
    aura_bin: str | None = None,
) -> dict[str, Any]:
    hroot = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or ".aura-build"
    )
    marker = read_marker(hroot)
    attached = attach_session(harness_root=hroot, aura_bin=aura_bin)
    ping_ok = False
    if attached is not None:
        ping_ok = attached.ping(timeout_s=3.0)
    aura_pid = int((marker or {}).get("pid") or 0)
    holder_pid = int((marker or {}).get("holder_pid") or 0)
    pid_ok = _pid_alive(aura_pid) or _pid_alive(holder_pid)
    serve_attach_ok = bool(ping_ok)
    # If sock dead but pids alive, still not ok (cannot eval)
    session_model = SESSION_SERVE if serve_attach_ok else SESSION_SHARED
    return {
        "serve_attach_ok": serve_attach_ok,
        "serve_session_ok": serve_attach_ok,
        "eval_available": serve_attach_ok,
        "session_model": session_model,
        "pid": aura_pid if _pid_alive(aura_pid) else None,
        "holder_pid": holder_pid if _pid_alive(holder_pid) else None,
        "marker": marker,
        "mode": (marker or {}).get("mode") or DEFAULT_MODE,
        "aura_bin": (marker or {}).get("aura_bin") or resolve_aura_bin(aura_bin),
        "serve_cross_session_shared_ast": False,
        "notes": (
            "session_model=serve when holder daemon + aura --serve ping ok; "
            "cold subprocess fallback otherwise; env cannot fake ok"
        ),
        "pid_alive_hint": pid_ok,
    }


def stop_session(*, harness_root: Path | str | None = None) -> dict[str, Any]:
    global _ATTACHED
    hroot = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or ".aura-build"
    )
    marker = read_marker(hroot)
    stopped = False
    if sock_path(hroot).exists():
        r = _sock_request(hroot, {"op": "stop"}, timeout_s=5.0)
        stopped = r.get("status") == "ok"
        time.sleep(0.15)
    if marker:
        for key in ("holder_pid", "pid"):
            pid = int(marker.get(key) or 0)
            if _pid_alive(pid):
                try:
                    os.kill(pid, signal.SIGTERM)
                    stopped = True
                except OSError:
                    pass
                time.sleep(0.05)
                if _pid_alive(pid):
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except OSError:
                        pass
    clear_marker(hroot)
    _ATTACHED = None
    return {"stopped": stopped or marker is not None, "serve_attach_ok": False}


def prefer_session_verify(
    *,
    harness_root: Path | str | None = None,
    env: dict[str, str] | None = None,
) -> bool:
    e = env if env is not None else os.environ
    flag = (e.get("AURA_BUILD_SESSION") or "").strip().lower()
    if flag in ("0", "false", "off", "no", "cold"):
        return False
    want = flag in ("1", "true", "yes", "on", "serve")
    st = session_status(harness_root=harness_root)
    if st.get("eval_available"):
        return True
    return want


def ensure_eval_session(
    *,
    aura_bin: str | None = None,
    harness_root: Path | str | None = None,
) -> ServeSession | None:
    hroot = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or ".aura-build"
    )
    attached = attach_session(harness_root=hroot, aura_bin=aura_bin)
    if attached is not None and attached.alive():
        return attached
    if prefer_session_verify(harness_root=hroot):
        try:
            return start_session(aura_bin=aura_bin, harness_root=hroot)
        except RuntimeError:
            return None
    return None


def run_session_dogfood(
    *,
    rounds: int = 3,
    aura_bin: str | None = None,
    harness_root: Path | str | None = None,
    out: Path | str | None = None,
    compare_cold: bool = True,
) -> dict[str, Any]:
    """Closed-loop in-session verify dogfood (no MiniMax)."""
    import re
    import uuid

    hroot = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or ".aura-build"
    )
    sess = start_session(aura_bin=aura_bin, harness_root=hroot)
    expect = re.compile(r"GREET\s*=\s*aura")
    candidates = [
        '(display "GREET=aura")(newline)',
        '(display "GREET=wrong")(newline)',
        '(display "GREET=aura")(newline)(display "extra")(newline)',
        '(define (g) "GREET=aura")(display (g))(newline)',
    ]
    rounds = max(1, int(rounds))
    session_ms: list[int] = []
    results: list[dict[str, Any]] = []
    for r in range(rounds):
        round_wls = []
        for i in range(3):
            body = candidates[0] if i == 0 else candidates[(i + r) % len(candidates)]
            ev = sess.eval_source(body, timeout_s=10.0)
            stdout = ev.get("stdout") or ""
            matched = bool(expect.search(stdout))
            passed = matched and bool(ev.get("ok")) and "extra" not in stdout
            ms = int(ev.get("ms") or 0)
            session_ms.append(ms)
            round_wls.append(
                {
                    "id": f"wl-{i}",
                    "passed": passed,
                    "fitness": 1.0 if passed else 0.2,
                    "ms": ms,
                    "via": "serve_session",
                    "stdout": stdout[-200:],
                }
            )
        selected = max(round_wls, key=lambda w: (w["fitness"], w["id"]))
        results.append(
            {
                "round": r,
                "selected_id": selected["id"],
                "passed": selected["passed"],
                "fitness": selected["fitness"],
                "worldlines": round_wls,
            }
        )

    cold_ms: list[int] = []
    cold_spawns = 0
    bin_path = resolve_aura_bin(aura_bin) or sess.aura_bin
    if compare_cold and bin_path:
        env = aura_subprocess_env(bin_path)
        for _r in range(rounds):
            for i in range(3):
                body = candidates[0] if i == 0 else candidates[1]
                with tempfile.NamedTemporaryFile(
                    "w", suffix=".aura", delete=False, encoding="utf-8"
                ) as fh:
                    fh.write(body + "\n")
                    tmp = fh.name
                t0 = time.monotonic()
                subprocess.run(
                    [bin_path, tmp],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    env=env,
                    check=False,
                )
                cold_ms.append(max(1, int((time.monotonic() - t0) * 1000)))
                cold_spawns += 1
                try:
                    Path(tmp).unlink(missing_ok=True)
                except OSError:
                    pass

    traj_id = f"serve-dogfood-{uuid.uuid4().hex[:10]}"
    episode = {
        "schema_version": "trajectory.v0",
        "episode_id": traj_id,
        "ts_start": _iso_now(),
        "ts_end": _iso_now(),
        "prompt": "session dogfood: in-serve greet predicate",
        "runtime": {
            "mode": "aura",
            "kernel": "aura",
            "incr_proven": False,
            "fiber_live": False,
            "measured": False,
            "session_model": SESSION_SERVE,
            "serve_session_ok": True,
            "serve_cross_session_shared_ast": False,
            "dogfood": {
                "kind": "session",
                "rounds": rounds,
                "session_ms_total": sum(session_ms),
                "session_ms_mean": (
                    round(sum(session_ms) / len(session_ms), 2) if session_ms else 0
                ),
                "cold_ms_total": sum(cold_ms),
                "cold_ms_mean": (
                    round(sum(cold_ms) / len(cold_ms), 2) if cold_ms else 0
                ),
                "cold_spawns": cold_spawns,
                "session_evals": len(session_ms),
            },
        },
        "harness": {
            "l1_strategy_id": "session_dogfood.v0",
            "l3_online": False,
            "outcome": "pass" if all(x["passed"] for x in results) else "partial",
            "actions": [
                {"op": "session_start", "via": "serve"},
                {"op": "in_session_eval", "count": len(session_ms)},
                {"op": "select_best"},
            ],
        },
        "worldlines": results[-1]["worldlines"] if results else [],
        "selected_id": results[-1]["selected_id"] if results else None,
        "privacy": {"redacted": True, "retention_class": "dogfood"},
    }

    out_path = Path(out) if out else Path("trajectories/session_dogfood.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(episode, sort_keys=True) + "\n")

    return {
        "ok": True,
        "traj_id": traj_id,
        "path": str(out_path),
        "session_model": SESSION_SERVE,
        "serve_session_ok": True,
        "rounds": results,
        "timing": episode["runtime"]["dogfood"],
        "pid": sess.pid,
        "kernel": "aura",
        "reason": "session_dogfood",
    }
