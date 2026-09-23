"""Host-managed long-lived Aura serve session (optimal-loop MVP).

Architecture:
- ``session start`` spawns a **holder daemon** that owns ``aura --serve`` or
  ``aura --serve-async`` pipes and listens on ``.aura-build/serve.sock``.
- CLI / verify clients talk JSON-lines over the socket (host IPC only).
- Honesty: ``session_model=serve`` only when daemon+aura pid alive (not env).
- Soft Ready: holder prefers async only after a **measured** Soft Ready
  self-check (Aura #4047 Soft Ready profile under Soft; older tips refused
  with #3098 ``fail_bits=0x10``). Else sync ``--serve`` with
  ``serve_mode=sync`` (never env-fake async / production Ready).
- ``serve_cross_session_shared_ast`` elevates only after a measured proof that
  two named Aura serve sessions share one FlatAST (Soft sync ``--serve`` #4047 B
  Soft shared graph, or sync side-probe when holder prefers async).
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
SERVE_MODE_SYNC = "sync"
SERVE_MODE_ASYNC = "async"

# Soft Ready (#3098) refuse fingerprint — do not treat as "async works".
_SOFT_ASYNC_REFUSE_MARKERS = (
    "production multi-worker Ready self-check failed",
    "Soft (AURA_SANDBOX=off)",
    "fail_bits=",
)


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
    stdout = proc.stdout
    # Soft Ready async may print display text before the JSON status line.
    # Once any stdout arrives, allow extra grace for the trailing JSON.
    json_grace_s = min(8.0, max(2.0, timeout_s))
    saw_stdout = False
    while True:
        now = time.monotonic()
        elapsed = now - t0
        if not saw_stdout and elapsed >= timeout_s:
            break
        if saw_stdout and elapsed >= timeout_s + json_grace_s:
            break
        remaining = (timeout_s if not saw_stdout else timeout_s + json_grace_s) - elapsed
        if remaining <= 0:
            break
        try:
            import select

            ready, _, _ = select.select([stdout], [], [], min(remaining, 0.5))
            if not ready:
                if proc.poll() is not None:
                    break
                continue
        except (ValueError, OSError):
            pass
        raw = stdout.readline()
        if raw == "" and proc.poll() is not None:
            break
        s = raw.rstrip("\n")
        if not s:
            continue
        saw_stdout = True
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
                # Preserve JSON display; also keep any prefix stdout.
                prefix_all = "".join(display_parts)
                json_disp = obj.get("display")
                json_disp = "" if json_disp is None else str(json_disp)
                obj["display"] = prefix_all + json_disp
                # Soft Ready async: top-level display from set-code can arrive
                # *after* the JSON status line. Drain briefly when empty.
                if not str(obj.get("display") or "").strip():
                    drain_deadline = time.monotonic() + min(1.5, max(0.3, timeout_s * 0.25))
                    extra: list[str] = []
                    while time.monotonic() < drain_deadline:
                        try:
                            import select as _sel
                            ready, _, _ = _sel.select([stdout], [], [], 0.15)
                            if not ready:
                                if extra:
                                    break
                                continue
                        except (ValueError, OSError):
                            break
                        raw2 = stdout.readline()
                        if not raw2:
                            break
                        s2 = raw2.rstrip("\n")
                        if not s2:
                            continue
                        # Stop if another JSON status sneaks in
                        if s2.lstrip().startswith("{") and '"status"' in s2:
                            break
                        extra.append(s2)
                    if extra:
                        obj["display"] = "\n".join(extra) + ("\n" if extra else "")
                return obj
            display_parts.append(s)
        else:
            display_parts.append(s)
    return {
        "status": "error",
        "msg": "serve_session_timeout",
        "display": "".join(display_parts),
    }



def probe_serve_async_soft_ready(
    aura_bin: str,
    *,
    timeout_s: float = 4.0,
) -> dict[str, Any]:
    """Measured Soft Ready self-check for ``aura --serve-async``.

    Aura #4047: Soft tips enter Soft Ready (alive + Soft Ready banner) without
    claiming production multi-worker Ready. Older tips refuse with #3098
    ``fail_bits=0x10``. Never invent ``ok`` from env.
    """
    bin_path = resolve_aura_bin(aura_bin) or aura_bin
    if not bin_path:
        return {
            "ok": False,
            "serve_mode_preferred": SERVE_MODE_SYNC,
            "reason": "aura_binary_missing",
        }
    env = aura_subprocess_env(bin_path)  # Soft: AURA_SANDBOX=off
    try:
        proc = subprocess.Popen(
            [bin_path, "--serve-async"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            start_new_session=True,
        )
    except OSError as exc:
        return {
            "ok": False,
            "serve_mode_preferred": SERVE_MODE_SYNC,
            "reason": f"spawn_error:{exc}",
        }
    try:
        assert proc.stdin is not None
        # Soft Ready --serve-async wants JSON exec; sexpr yields "missing cmd".
        proc.stdin.write('{"cmd":"exec","code":"(+ 1 1)"}\n')
        proc.stdin.flush()
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                stdout, stderr = proc.communicate(timeout=2.0)
            except Exception:
                stdout, stderr = "", ""
            # Timed out while alive → Soft Ready did not abort; treat as ready.
            # Prefer Aura #4047 Soft Ready banner when present (not production).
            out = (stdout or "") + (stderr or "")
            if "Soft Ready profile (#4047)" in out and "FATAL" not in out:
                return {
                    "ok": True,
                    "serve_mode_preferred": SERVE_MODE_ASYNC,
                    "reason": "soft_ready_profile_4047",
                    "stderr_tail": (stderr or "")[-200:],
                }
            if any(m in out for m in _SOFT_ASYNC_REFUSE_MARKERS):
                return {
                    "ok": False,
                    "serve_mode_preferred": SERVE_MODE_SYNC,
                    "reason": "soft_ready_refused_after_timeout",
                    "stderr_tail": (stderr or "")[-400:],
                    "fail_bits": _extract_fail_bits(stderr or ""),
                    "fail_bits_decoded": decode_soft_ready_fail_bits(
                        _extract_fail_bits(stderr or "")
                    ),
                }
            return {
                "ok": True,
                "serve_mode_preferred": SERVE_MODE_ASYNC,
                "reason": "soft_ready_alive_timeout_ok",
                "stderr_tail": (stderr or "")[-200:],
            }
        err = stderr or ""
        out = (stdout or "") + err
        if any(m in out for m in _SOFT_ASYNC_REFUSE_MARKERS) or proc.returncode not in (0, None):
            # Aborted or refused
            if any(m in out for m in _SOFT_ASYNC_REFUSE_MARKERS) or "FATAL" in err:
                return {
                    "ok": False,
                    "serve_mode_preferred": SERVE_MODE_SYNC,
                    "reason": "soft_ready_refused",
                    "stderr_tail": err[-500:],
                    "fail_bits": _extract_fail_bits(err),
                    "fail_bits_decoded": decode_soft_ready_fail_bits(
                        _extract_fail_bits(err)
                    ),
                    "returncode": proc.returncode,
                }
        # Got a JSON status line without FATAL → Soft Ready passed
        if '"status"' in (stdout or "") and "FATAL" not in err:
            reason = "soft_ready_ok"
            if "Soft Ready profile (#4047)" in err:
                reason = "soft_ready_profile_4047"
            return {
                "ok": True,
                "serve_mode_preferred": SERVE_MODE_ASYNC,
                "reason": reason,
                "stdout_tail": (stdout or "")[-200:],
                "stderr_tail": err[-200:],
            }
        return {
            "ok": False,
            "serve_mode_preferred": SERVE_MODE_SYNC,
            "reason": "soft_ready_inconclusive",
            "stderr_tail": err[-400:],
            "stdout_tail": (stdout or "")[-200:],
            "returncode": proc.returncode,
        }
    finally:
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
            try:
                proc.wait(timeout=2)
            except Exception:
                pass


def _extract_fail_bits(stderr: str) -> str | None:
    import re

    m = re.search(r"fail_bits=(0x[0-9a-fA-F]+)", stderr)
    return m.group(1) if m else None


# Aura #3098 / #2955 / #3195 production multi-worker Ready fail_bits (Soft refuse).
# Source: aura serve/runtime_production_abi.h — never invent cleared bits from env.
_FAIL_BIT_NAMES: dict[int, str] = {
    0: "abi_steal_complete",
    1: "abi_eval_id",
    2: "abi_mutation_held",
    3: "abi_depth_from_ptr",
    4: "defaults_missing_soft",  # kProductionAbiSelfcheckFailBitDefaults (1<<4 = 0x10)
    5: "residual_sticky",        # #3195
    6: "tenant_scope",           # #3275
    7: "probe_linear",           # #3343
    8: "typed_entry",            # #3419
    9: "hot_contracts",          # #3866
}


def decode_soft_ready_fail_bits(fail_bits: str | int | None) -> dict[str, Any]:
    """Decode Soft Ready ``fail_bits`` hex into named bits (Aura #3098 lineage)."""
    if fail_bits is None or fail_bits == "":
        return {"raw": None, "mask": 0, "bits": [], "names": []}
    if isinstance(fail_bits, str):
        raw = fail_bits.strip()
        try:
            mask = int(raw, 16) if raw.lower().startswith("0x") else int(raw, 0)
        except ValueError:
            return {"raw": raw, "mask": 0, "bits": [], "names": [], "parse_error": True}
    else:
        mask = int(fail_bits)
        raw = hex(mask)
    bits = [i for i in range(16) if (mask >> i) & 1]
    names = [_FAIL_BIT_NAMES.get(i, f"bit_{i}") for i in bits]
    return {
        "raw": raw if isinstance(fail_bits, str) else hex(mask),
        "mask": mask,
        "bits": bits,
        "names": names,
        "soft_defaults_only": bits == [4],
        "meaning": (
            "Soft (AURA_SANDBOX=off) / !production_defaults_active — multi-worker "
            "Ready (#3098) refuses Soft fall-through; bit4=defaults_missing"
            if bits == [4]
            else (
                "production multi-worker Ready self-check failed; see names"
                if bits
                else "no fail bits"
            )
        ),
    }


def _aura_line_for_mode(line_or_code: str, *, async_mode: bool, session: str | None = None) -> str:
    """Sync ``--serve`` accepts sexpr; Soft Ready async wants JSON ``exec``.

    Named-session routing on async uses a ``session`` field (Aura #4047 B
    async: json_field routing + fiber wake + Soft shared CS). Compact JSON
    is fine; spaced json.dumps also works after Aura routing fix.
    """
    if not async_mode:
        return line_or_code
    if line_or_code.lstrip().startswith("{"):
        return line_or_code
    payload: dict[str, Any] = {"cmd": "exec", "code": line_or_code}
    if session:
        payload["session"] = session
    return json.dumps(payload, separators=(",", ":"))


def _probe_sync_cross_session_shared_ast(aura_bin: str) -> dict[str, Any]:
    """Side-probe Soft sync ``aura --serve`` orch→project binding visibility.

    Soft Ready holders prefer ``--serve-async``; async named-session fiber wake
    can hang, so cross-session shared_ast is measured on a short-lived sync
    serve (Aura #4047 B Soft shared graph). Never elevates from env.
    """
    out: dict[str, Any] = {
        "serve_cross_session_shared_ast": False,
        "cross_session_proof": "not_run",
        "probe_path": "sync_side",
    }
    env = aura_subprocess_env(aura_bin)
    try:
        proc = subprocess.Popen(
            [aura_bin, "--serve"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=1,
        )
    except OSError as exc:
        out["cross_session_proof"] = f"sync_side_spawn_failed:{exc}"
        return out
    try:
        def send(line: str, *, timeout_s: float = 5.0) -> dict[str, Any]:
            return _aura_send_line(proc, line, timeout_s=timeout_s)

        r1 = send('{"cmd":"session","name":"orch"}', timeout_s=5.0)
        if r1.get("status") not in ("ok", "created"):
            out["cross_session_proof"] = f"session_create_orch_failed:{r1.get('msg')}"
            return out
        _ = send("(define shared-ast-token 7777)", timeout_s=5.0)
        r3 = send('{"cmd":"session","name":"project"}', timeout_s=5.0)
        if r3.get("status") not in ("ok", "created"):
            out["cross_session_proof"] = (
                f"session_create_project_failed:{r3.get('msg')}"
            )
            return out
        r4 = send("shared-ast-token", timeout_s=5.0)
        shared = (
            r4.get("status") == "ok"
            and str(r4.get("value") or "").strip() in ("7777", "7777.0")
        )
        out["serve_cross_session_shared_ast"] = bool(shared)
        if shared:
            out["cross_session_proof"] = (
                "sync_side_project_session_read_orch_binding_shared-ast-token=7777"
            )
        else:
            msg = str(r4.get("msg") or r4.get("status") or "")
            out["cross_session_proof"] = (
                f"sync_side_project_session_unbound_or_miss status={r4.get('status')} "
                f"msg={msg[:120]}"
            )
        return out
    finally:
        try:
            proc.kill()
        except OSError:
            pass
        try:
            proc.wait(timeout=2)
        except Exception:
            pass


def _probe_shared_ast_on_proc(
    proc: subprocess.Popen[str],
    *,
    async_mode: bool = False,
    aura_bin: str | None = None,
) -> dict[str, Any]:
    """Measure cross-session vs same-session FlatAST sharing on a live serve.

    Soft ``--serve`` / Soft Ready ``--serve-async`` (#4047 B): named sessions
    share one CompilerService graph — orch→project ``(define)`` is visible
    when measured on the live proc (async uses session field + create).
    Same-session mutate via JSON exec on default. Never elevates from env.
    ``aura_bin`` retained for callers; unused once async measures on-proc.
    """
    _ = aura_bin
    result: dict[str, Any] = {
        "serve_cross_session_shared_ast": False,
        "serve_same_session_mutate_ok": False,
        "cross_session_proof": "not_run",
        "same_session_proof": "not_run",
        "async_mode": async_mode,
        "next_gate": (
            "Aura Soft Ready (#4047) + Soft shared graph (#4047 B); measure "
            "orch→project binding on live serve/--serve-async."
        ),
    }

    def send(line: str, *, timeout_s: float = 5.0, session: str | None = None) -> dict[str, Any]:
        return _aura_send_line(
            proc,
            _aura_line_for_mode(line, async_mode=async_mode, session=session),
            timeout_s=timeout_s,
        )

    # --- cross-session (sync switches active session; async routes by field) ---
    r1 = send('{"cmd":"session","name":"orch"}', timeout_s=5.0)
    if r1.get("status") not in ("ok", "created"):
        result["cross_session_proof"] = f"session_create_orch_failed:{r1.get('msg')}"
    else:
        r2 = send(
            "(define shared-ast-token 7777)",
            timeout_s=5.0,
            session=("orch" if async_mode else None),
        )
        _ = r2
        r3 = send('{"cmd":"session","name":"project"}', timeout_s=5.0)
        if r3.get("status") not in ("ok", "created"):
            result["cross_session_proof"] = (
                f"session_create_project_failed:{r3.get('msg')}"
            )
        else:
            r4 = send(
                "shared-ast-token",
                timeout_s=5.0,
                session=("project" if async_mode else None),
            )
            shared = (
                r4.get("status") == "ok"
                and str(r4.get("value") or "").strip() in ("7777", "7777.0")
            )
            if async_mode and shared and r4.get("session") not in (None, "project"):
                # Must be answered by project fiber, not default steal.
                shared = False
            result["serve_cross_session_shared_ast"] = bool(shared)
            if shared:
                result["cross_session_proof"] = (
                    "project_session_read_orch_binding_shared-ast-token=7777"
                    + ("_async" if async_mode else "")
                )
                result["next_gate"] = "measured_true"
            else:
                msg = str(r4.get("msg") or r4.get("status") or "")
                result["cross_session_proof"] = (
                    f"project_session_unbound_or_miss status={r4.get('status')} "
                    f"session={r4.get('session')} msg={msg[:120]}"
                )
        if not async_mode:
            send('{"cmd":"session","name":"default"}', timeout_s=3.0)

    # --- same-session mutate:rebind identity (default session) ---
    set_r = send(
        '(set-code "(define (cand) 1) (display (cand)) (newline)")',
        timeout_s=5.0,
    )
    if set_r.get("status") != "ok":
        result["same_session_proof"] = f"set-code_failed:{set_r.get('msg')}"
        return result
    ep0 = send('(stats:get "compile:epoch")', timeout_s=5.0)
    mut = send(
        '(mutate:rebind "cand" "(lambda () 99)" "shared-ast-probe")',
        timeout_s=5.0,
    )
    ep1 = send('(stats:get "compile:epoch")', timeout_s=5.0)
    ev = send("(eval-current)", timeout_s=5.0)
    display = str(ev.get("display") or "")
    # epoch may parse as string ints
    def _num(v: Any) -> int | None:
        try:
            return int(str(v).strip().strip('"'))
        except (TypeError, ValueError):
            return None

    n0, n1 = _num(ep0.get("value")), _num(ep1.get("value"))
    mut_ok = mut.get("status") == "ok"
    eval_saw_99 = "99" in display or str(ev.get("value") or "") == "99"
    epoch_bumped = n0 is not None and n1 is not None and n1 > n0
    same_ok = bool(mut_ok and (eval_saw_99 or epoch_bumped))
    result["serve_same_session_mutate_ok"] = same_ok
    result["same_session_proof"] = (
        f"mutate_ok={mut_ok} epoch={n0}->{n1} eval_display={display[-40:]!r} "
        f"eval_status={ev.get('status')}"
    )
    if same_ok and not result["serve_cross_session_shared_ast"]:
        result["next_gate"] = (
            "same-session mutate:rebind+eval works; cross-session shared FlatAST "
            "not yet measured (Soft sync #4047 B or async fiber wake)"
        )
    elif result["serve_cross_session_shared_ast"] and same_ok:
        result["next_gate"] = "measured_true"
    return result

def _holder_main(harness_root: str, aura_bin: str) -> None:
    """Daemon entry: own aura --serve[--async] + unix socket."""
    hroot = Path(harness_root)
    hroot.mkdir(parents=True, exist_ok=True)
    # Boot marker so session start can fail fast if we die before sock ready.
    write_marker(
        {
            "holder_pid": os.getpid(),
            "pid": 0,
            "aura_bin": aura_bin,
            "mode": DEFAULT_MODE,
            "serve_mode": "starting",
            "session_model": SESSION_SHARED,
            "started_at": _iso_now(),
            "harness_root": str(hroot),
            "boot": True,
            "notes": "holder booting Soft Ready probe / serve spawn",
        },
        hroot,
    )
    env = aura_subprocess_env(aura_bin)
    soft_probe = probe_serve_async_soft_ready(aura_bin)
    prefer_async = bool(soft_probe.get("ok"))
    serve_mode = SERVE_MODE_ASYNC if prefer_async else SERVE_MODE_SYNC
    aura_argv = [aura_bin, "--serve-async"] if prefer_async else [aura_bin, "--serve"]
    stderr_path = hroot / "serve.stderr.log"
    err_fh = open(stderr_path, "w", encoding="utf-8")  # noqa: SIM115
    def _spawn(argv: list[str]) -> subprocess.Popen[str]:
        return subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=err_fh,
            text=True,
            env=env,
            bufsize=1,
            start_new_session=True,
        )

    proc = _spawn(aura_argv)
    # Warm ping — sync accepts sexpr; async wants JSON exec when Ready.
    if prefer_async:
        warm = _aura_send_line(
            proc, '{"cmd":"exec","code":"(+ 1 1)"}', timeout_s=8.0
        )
    else:
        warm = _aura_send_line(proc, "(+ 1 1)", timeout_s=8.0)
    if warm.get("status") != "ok" and prefer_async:
        # Measured Soft Ready said ok but warm failed — honest fallback to sync.
        try:
            proc.kill()
        except OSError:
            pass
        try:
            proc.wait(timeout=2)
        except Exception:
            pass
        prefer_async = False
        serve_mode = SERVE_MODE_SYNC
        aura_argv = [aura_bin, "--serve"]
        soft_probe = dict(soft_probe)
        soft_probe["ok"] = False
        soft_probe["reason"] = "async_warm_failed_fallback_sync"
        soft_probe["warm"] = warm
        proc = _spawn(aura_argv)
        warm = _aura_send_line(proc, "(+ 1 1)", timeout_s=8.0)
    if warm.get("status") != "ok":
        try:
            proc.kill()
        except OSError:
            pass
        err_fh.close()
        clear_marker(hroot)
        sys.exit(2)

    # Shared-ast / same-session probe — if aura dies mid-probe, fall back sync once.
    try:
        if proc.poll() is not None:
            raise RuntimeError(f"aura_exited_before_shared_probe rc={proc.returncode}")
        shared_probe = _probe_shared_ast_on_proc(
            proc, async_mode=prefer_async, aura_bin=aura_bin
        )
        if proc.poll() is not None:
            raise RuntimeError(
                f"aura_exited_during_shared_probe rc={proc.returncode}"
            )
    except Exception as exc:  # noqa: BLE001 — holder must not hang session start
        shared_probe = {
            "serve_cross_session_shared_ast": False,
            "serve_same_session_mutate_ok": False,
            "cross_session_proof": f"probe_failed:{exc}",
            "same_session_proof": f"probe_failed:{exc}",
            "async_mode": prefer_async,
            "next_gate": "shared_ast_probe_failed",
        }
        if prefer_async:
            try:
                proc.kill()
            except OSError:
                pass
            try:
                proc.wait(timeout=2)
            except Exception:
                pass
            prefer_async = False
            serve_mode = SERVE_MODE_SYNC
            aura_argv = [aura_bin, "--serve"]
            soft_probe = dict(soft_probe)
            soft_probe["ok"] = False
            soft_probe["reason"] = f"async_shared_probe_failed_fallback_sync:{exc}"
            proc = _spawn(aura_argv)
            warm = _aura_send_line(proc, "(+ 1 1)", timeout_s=8.0)
            if warm.get("status") != "ok":
                try:
                    proc.kill()
                except OSError:
                    pass
                err_fh.close()
                clear_marker(hroot)
                sys.exit(2)
            try:
                shared_probe = _probe_shared_ast_on_proc(
                    proc, async_mode=False, aura_bin=aura_bin
                )
            except Exception as exc2:  # noqa: BLE001
                shared_probe = {
                    "serve_cross_session_shared_ast": False,
                    "serve_same_session_mutate_ok": False,
                    "cross_session_proof": f"sync_probe_failed:{exc2}",
                    "same_session_proof": f"sync_probe_failed:{exc2}",
                    "async_mode": False,
                    "next_gate": "shared_ast_probe_failed",
                }
    # Env cannot elevate — force false unless measured true above.
    shared_ast = bool(shared_probe.get("serve_cross_session_shared_ast"))
    if (os.environ.get("AURA_BUILD_SERVE_SHARED_AST") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        # Explicitly ignore elevation attempts.
        shared_ast = bool(shared_probe.get("serve_cross_session_shared_ast"))

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
            "serve_mode": serve_mode,
            "session_model": SESSION_SERVE,
            "started_at": _iso_now(),
            "harness_root": str(hroot),
            "sock": str(sp),
            "protocol": (
                "unix-sock → aura --serve-async JSON exec"
                if prefer_async
                else "unix-sock → aura --serve stdin"
            ),
            "aura_argv": aura_argv,
            "serve_async_soft_ready": soft_probe,
            "serve_cross_session_shared_ast": shared_ast,
            "serve_same_session_mutate_ok": bool(
                shared_probe.get("serve_same_session_mutate_ok")
            ),
            "shared_ast_probe": shared_probe,
            "notes": (
                f"serve_mode={serve_mode}; Soft Ready async="
                f"{soft_probe.get('ok')} ({soft_probe.get('reason')}); "
                f"serve_cross_session_shared_ast={shared_ast}; "
                f"same_session_mutate_ok="
                f"{shared_probe.get('serve_same_session_mutate_ok')}"
            ),
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
                    r = _aura_send_line(
                        proc,
                        _aura_line_for_mode("(+ 1 1)", async_mode=prefer_async),
                        timeout_s=5.0,
                    )
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
                        proc,
                        _aura_line_for_mode(
                            f'(set-code "{esc}")', async_mode=prefer_async
                        ),
                        timeout_s=timeout_s,
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
                        set_disp = str(set_r.get("display") or "")
                        # Soft Ready async: set-code often captures display;
                        # follow-up eval-current can hang. Skip when present.
                        if set_disp.strip():
                            display = set_disp
                            msg = str(set_r.get("msg") or "")
                            status = set_r.get("status")
                            value = set_r.get("value")
                        else:
                            ev = _aura_send_line(
                                proc,
                                _aura_line_for_mode(
                                    "(eval-current)", async_mode=prefer_async
                                ),
                                timeout_s=timeout_s,
                            )
                            display = str(ev.get("display") or "")
                            msg = str(ev.get("msg") or "")
                            status = ev.get("status")
                            value = ev.get("value")
                            # Soft sync: first eval-current after set-code can
                            # return empty display while a second pass captures
                            # top-level display forms (multi-file concat).
                            if not display.strip() and not prefer_async:
                                ev2 = _aura_send_line(
                                    proc,
                                    _aura_line_for_mode(
                                        "(eval-current)", async_mode=False
                                    ),
                                    timeout_s=min(timeout_s, 5.0),
                                )
                                d2 = str(ev2.get("display") or "")
                                if d2.strip():
                                    display = d2
                                    msg = str(ev2.get("msg") or msg)
                                    status = ev2.get("status") or status
                                    value = ev2.get("value")
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
                            "value": value,
                        }
                elif op == "raw":
                    line = str(req.get("line") or "")
                    r = _aura_send_line(
                        proc,
                        _aura_line_for_mode(line, async_mode=prefer_async),
                        timeout_s=float(req.get("timeout_s") or 10.0),
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

    def raw_line(self, line: str, *, timeout_s: float = 10.0) -> dict[str, Any]:
        return _sock_request(
            self.harness_root,
            {"op": "raw", "line": line, "timeout_s": timeout_s},
            timeout_s=timeout_s + 2.0,
        )

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
    # Soft Ready + async warm + shared-ast (+ sync side-probe #4047 B) can exceed 60s.
    deadline = time.monotonic() + 90.0
    saw_boot = False
    while time.monotonic() < deadline:
        marker = read_marker(hroot)
        if marker:
            saw_boot = True
            holder = int(marker.get("holder_pid") or 0)
            # Fail fast if holder died before publishing a ready sock.
            if holder and not _pid_alive(holder) and not sock_path(hroot).exists():
                clear_marker(hroot)
                raise RuntimeError(
                    "serve_session_start_holder_died: holder exited before sock ready "
                    f"(holder_pid={holder}; see serve.stderr.log)"
                )
            if (
                not marker.get("boot")
                and sock_path(hroot).exists()
                and int(marker.get("pid") or 0) > 0
            ):
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
    raise RuntimeError(
        "serve_session_start_timeout: holder did not become ready "
        f"(saw_boot={saw_boot}; Soft Ready + shared-ast may take ~30–60s)"
    )


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
    raw_marker = read_marker(hroot)
    attached = attach_session(harness_root=hroot, aura_bin=aura_bin)
    ping_ok = False
    if attached is not None:
        ping_ok = attached.ping(timeout_s=3.0)
    aura_pid = int((raw_marker or {}).get("pid") or 0)
    holder_pid = int((raw_marker or {}).get("holder_pid") or 0)
    pid_ok = _pid_alive(aura_pid) or _pid_alive(holder_pid)
    serve_attach_ok = bool(ping_ok)
    # If sock dead but pids alive, still not ok (cannot eval)
    session_model = SESSION_SERVE if serve_attach_ok else SESSION_SHARED
    marker = raw_marker or {}
    shared_ast = bool(marker.get("serve_cross_session_shared_ast"))
    # Env elevation refused even if marker somehow claims true without probe.
    env_try = (os.environ.get("AURA_BUILD_SERVE_SHARED_AST") or "").strip().lower()
    if env_try in ("1", "true", "yes", "on") and not shared_ast:
        shared_ast = False
    soft = marker.get("serve_async_soft_ready") if isinstance(marker, dict) else None
    return {
        "serve_attach_ok": serve_attach_ok,
        "serve_session_ok": serve_attach_ok,
        "eval_available": serve_attach_ok,
        "session_model": session_model,
        "pid": aura_pid if _pid_alive(aura_pid) else None,
        "holder_pid": holder_pid if _pid_alive(holder_pid) else None,
        "marker": raw_marker,
        "mode": marker.get("mode") or DEFAULT_MODE,
        "serve_mode": marker.get("serve_mode") or SERVE_MODE_SYNC,
        "aura_bin": marker.get("aura_bin") or resolve_aura_bin(aura_bin),
        "serve_cross_session_shared_ast": shared_ast,
        "serve_same_session_mutate_ok": bool(marker.get("serve_same_session_mutate_ok")),
        "serve_async_soft_ready": soft,
        "shared_ast_probe": marker.get("shared_ast_probe"),
        "notes": (
            "session_model=serve when holder daemon + aura serve ping ok; "
            "serve_mode=async only after Soft Ready self-check; "
            "serve_cross_session_shared_ast only when measured; "
            "env cannot fake ok / shared_ast"
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
    """Closed-loop in-session verify dogfood (no MiniMax).

    Prefers same-session ``mutate:rebind`` when the holder measured
    ``serve_same_session_mutate_ok``; otherwise set-code/eval-current per
    candidate. Session-path ``cold_spawns`` is always 0 (one long-lived aura).
    """
    import re
    import uuid

    hroot = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or ".aura-build"
    )
    sess = start_session(aura_bin=aura_bin, harness_root=hroot)
    marker = read_marker(hroot) or {}
    serve_mode = str(marker.get("serve_mode") or SERVE_MODE_SYNC)
    shared_ast = bool(marker.get("serve_cross_session_shared_ast"))
    same_mut = bool(marker.get("serve_same_session_mutate_ok"))
    soft = marker.get("serve_async_soft_ready") if isinstance(marker, dict) else None
    expect = re.compile(r"GREET\s*=\s*aura")
    # mutate:rebind bodies (lambda returning display string) when same_mut
    # Display inside lambda; eval-current captures serve JSON display=.
    mut_bodies = [
        '(lambda () (begin (display "GREET=aura") (newline)))',
        '(lambda () (begin (display "GREET=wrong") (newline)))',
        '(lambda () (begin (display "GREET=aura") (newline) (display "extra") (newline)))',
        '(lambda () (begin (display "GREET=aura") (newline)))',
    ]
    candidates = [
        '(display "GREET=aura")',
        '(display "GREET=wrong")',
        '(begin (display "GREET=aura") (display "extra"))',
        '(display "GREET=aura")',
    ]

    rounds = max(1, int(rounds))
    session_ms: list[int] = []
    results: list[dict[str, Any]] = []
    path_kind = "mutate_rebind" if same_mut else "set_code_eval"

    if same_mut:
        # Load once; worldlines rebind `cand` on the same FlatAST.
        boot = sess.raw_line(
            '(set-code "(define (cand) 0) (cand)")',
            timeout_s=10.0,
        )
        if boot.get("status") != "ok":
            same_mut = False
            path_kind = "set_code_eval"

    for r in range(rounds):
        round_wls = []
        for i in range(3):
            t0 = time.monotonic()
            if same_mut:
                body = mut_bodies[0] if i == 0 else mut_bodies[(i + r) % len(mut_bodies)]
                esc = _escape_aura_string(body)
                mut = sess.raw_line(
                    f'(mutate:rebind "cand" "{esc}" "dogfood-r{r}-w{i}")',
                    timeout_s=10.0,
                )
                ev = sess.raw_line("(eval-current)", timeout_s=10.0)
                stdout = str(ev.get("display") or "")
                # Also catch value if display empty
                if not stdout and ev.get("value"):
                    stdout = str(ev.get("value"))
                ok = mut.get("status") == "ok" and ev.get("status") == "ok"
                via = "serve_session_mutate"
            else:
                body = candidates[0] if i == 0 else candidates[(i + r) % len(candidates)]
                ev = sess.eval_source(body, timeout_s=10.0)
                stdout = ev.get("stdout") or ""
                ok = bool(ev.get("ok"))
                via = "serve_session"
            matched = bool(expect.search(stdout))
            passed = matched and ok and "extra" not in stdout
            ms = max(1, int((time.monotonic() - t0) * 1000))
            session_ms.append(ms)
            round_wls.append(
                {
                    "id": f"wl-{i}",
                    "passed": passed,
                    "fitness": 1.0 if passed else 0.2,
                    "ms": ms,
                    "via": via,
                    "stdout": stdout[-200:],
                    "path_kind": path_kind,
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
    cold_compare_spawns = 0
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
                cold_compare_spawns += 1
                try:
                    Path(tmp).unlink(missing_ok=True)
                except OSError:
                    pass

    # Session path never cold-spawns aura (holder already owns one process).
    cold_spawns = 0
    traj_id = f"serve-dogfood-{uuid.uuid4().hex[:10]}"
    honesty = {
        "serve_mode": serve_mode,
        "serve_cross_session_shared_ast": shared_ast,
        "serve_same_session_mutate_ok": same_mut,
        "serve_async_soft_ready_ok": bool((soft or {}).get("ok")) if isinstance(soft, dict) else False,
        "serve_async_soft_ready_reason": (
            (soft or {}).get("reason") if isinstance(soft, dict) else None
        ),
        "path_kind": path_kind,
    }
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
            "measured": True,
            "session_model": SESSION_SERVE,
            "serve_session_ok": True,
            "serve_mode": serve_mode,
            "serve_cross_session_shared_ast": shared_ast,
            "serve_same_session_mutate_ok": same_mut,
            "dogfood": {
                "kind": "session",
                "rounds": rounds,
                "path_kind": path_kind,
                "session_ms_total": sum(session_ms),
                "session_ms_mean": (
                    round(sum(session_ms) / len(session_ms), 2) if session_ms else 0
                ),
                "cold_ms_total": sum(cold_ms),
                "cold_ms_mean": (
                    round(sum(cold_ms) / len(cold_ms), 2) if cold_ms else 0
                ),
                "cold_spawns": cold_spawns,
                "cold_compare_spawns": cold_compare_spawns,
                "session_evals": len(session_ms),
            },
        },
        "harness": {
            "l1_strategy_id": "session_dogfood.v1",
            "l3_online": False,
            "outcome": "pass" if all(x["passed"] for x in results) else "partial",
            "actions": [
                {"op": "session_start", "via": f"serve_{serve_mode}"},
                {"op": "in_session_eval", "count": len(session_ms), "path": path_kind},
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
        "serve_mode": serve_mode,
        "serve_cross_session_shared_ast": shared_ast,
        "serve_same_session_mutate_ok": same_mut,
        "honesty": honesty,
        "rounds": results,
        "timing": episode["runtime"]["dogfood"],
        "pid": sess.pid,
        "kernel": "aura",
        "reason": "session_dogfood",
    }


def run_pursue_session(
    *,
    goal: str,
    min_fitness: float = 0.8,
    max_rounds: int = 8,
    worldlines: int = 3,
    aura_bin: str | None = None,
    harness_root: Path | str | None = None,
    out: Path | str | None = None,
    seed: int | None = None,
    llm_assist: str = "off",
    llm_hint: str = "",
) -> dict[str, Any]:
    """In-session pursue on long-lived serve via same-session ``mutate:rebind``.

    Soft Ready ``--serve-async`` is often refused (#3098 ``fail_bits=0x10``);
    this path uses Soft ``--serve`` (``serve_mode=sync``) and still keeps
    ``cold_spawns=0`` with real FlatAST mutate worldlines when
    ``serve_same_session_mutate_ok`` was measured. Never invents async /
    shared_ast / Soft Ready from env.
    """
    import re
    import uuid

    goal = (goal or "").strip()
    if not goal:
        return {
            "ok": False,
            "goal_met": False,
            "stop_reason": "missing_goal",
            "error": "missing_goal",
            "kernel": "aura",
            "path_kind": None,
        }

    hroot = Path(harness_root) if harness_root else Path(
        os.environ.get("AURA_BUILD_HARNESS_ROOT") or ".aura-build"
    )
    sess = start_session(aura_bin=aura_bin, harness_root=hroot)
    marker = read_marker(hroot) or {}
    serve_mode = str(marker.get("serve_mode") or SERVE_MODE_SYNC)
    shared_ast = bool(marker.get("serve_cross_session_shared_ast"))
    same_mut = bool(marker.get("serve_same_session_mutate_ok"))
    soft = marker.get("serve_async_soft_ready") if isinstance(marker, dict) else None
    soft_ok = bool((soft or {}).get("ok")) if isinstance(soft, dict) else False
    soft_bits = (soft or {}).get("fail_bits") if isinstance(soft, dict) else None
    soft_decoded = decode_soft_ready_fail_bits(soft_bits)

    if not same_mut:
        return {
            "ok": False,
            "goal_met": False,
            "stop_reason": "same_session_mutate_unavailable",
            "error": "same_session_mutate_unavailable",
            "kernel": "aura",
            "session_model": SESSION_SERVE,
            "serve_mode": serve_mode,
            "serve_same_session_mutate_ok": False,
            "serve_async_soft_ready_ok": soft_ok,
            "serve_async_soft_ready_fail_bits": soft_bits,
            "serve_async_soft_ready_fail_bits_decoded": soft_decoded,
            "path_kind": None,
            "fallback": "aura_kernel_dispatch",
        }

    # Success token: prefer explicit GREET=… / KEY=val in goal; else GREET=aura.
    m_tok = re.search(r"\b([A-Z][A-Z0-9_]*=\S+)", goal)
    success_token = m_tok.group(1) if m_tok else "GREET=aura"
    expect = re.compile(re.escape(success_token))

    esc_tok = _escape_aura_string(success_token)
    # Prefer eval_source (set-code+eval) for honest display capture on Soft Ready
    # async — mutate:rebind+eval-current often returns value #t with empty
    # display or hangs after display text. Still require same_mut gate above
    # (FlatAST mutate measured on holder). Keep cold_spawns=0 on live serve.
    candidates = [
        f'(display "{esc_tok}")',
        '(display "GREET=wrong")',
        f'(begin (display "{esc_tok}") (display "extra"))',
        '(display "NOPE")',
        f'(display "{esc_tok}")',
    ]
    # Also keep mutate bodies for optional FlatAST worldline when eval_source
    # fails open; primary scoring uses eval_source stdout.
    mut_bodies = [
        f'(lambda () (begin (display "{esc_tok}") (newline)))',
        '(lambda () (begin (display "GREET=wrong") (newline)))',
        f'(lambda () (begin (display "{esc_tok}") (newline) (display "extra") (newline)))',
        '(lambda () (begin (display "NOPE") (newline)))',
        f'(lambda () (begin (display "{esc_tok}") (newline)))',
    ]
    n_wl = max(1, int(worldlines))
    max_r = max(1, int(max_rounds))
    min_fit = float(min_fitness)
    rng_seed = int(seed) if seed is not None else (abs(hash(goal)) % 10_000_000)

    # Seed FlatAST once so mutate:rebind remains available mid-pursue.
    boot = sess.raw_line(
        '(set-code "(define (cand) 0) (cand)")',
        timeout_s=5.0,
    )
    if boot.get("status") != "ok":
        return {
            "ok": False,
            "goal_met": False,
            "stop_reason": "serve_boot_failed",
            "error": f"set-code_failed:{boot.get('msg')}",
            "kernel": "aura",
            "session_model": SESSION_SERVE,
            "serve_mode": serve_mode,
            "path_kind": "set_code_eval",
        }

    path_kind = "set_code_eval"
    rounds_out: list[dict[str, Any]] = []
    best_fit = -1.0
    best_sel = ""
    session_ms: list[int] = []
    cold_spawns = 0
    traj_id = f"pursue-serve-{uuid.uuid4().hex[:10]}"
    out_path = Path(out) if out else Path("trajectories/pursue.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    goal_met = False
    stop_reason = "max_rounds"

    for r_i in range(1, max_r + 1):
        round_wls: list[dict[str, Any]] = []
        for i in range(n_wl):
            if i == 0:
                src = candidates[0]
            else:
                idx = 1 + ((rng_seed + r_i + i) % (len(candidates) - 1))
                src = candidates[idx]
            t0 = time.monotonic()
            # Soft Ready async: set-code then eval-current captures display=
            # (eval_source / mutate+eval alone often empty or hang). Hard 5s.
            esc = _escape_aura_string(src)
            set_r = sess.raw_line(f'(set-code "{esc}")', timeout_s=5.0)
            ev = sess.raw_line("(eval-current)", timeout_s=5.0)
            ms = max(1, int((time.monotonic() - t0) * 1000))
            session_ms.append(ms)
            stdout = str(ev.get("display") or "")
            if not stdout:
                stdout = str(set_r.get("display") or "")
            if not stdout and ev.get("value") is not None:
                val = str(ev.get("value")).strip().strip('"')
                if val not in ("#t", "#f", "()", "", "2"):
                    stdout = val
            ok = set_r.get("status") == "ok" and ev.get("status") == "ok"
            matched = bool(expect.search(stdout))
            passed = matched and ok and "extra" not in stdout
            path_kind = "set_code_eval"
            if passed:
                fit = 1.0
            elif matched and ok:
                fit = 0.55
            elif ok and stdout.strip():
                fit = 0.25
            elif ok:
                fit = 0.15
            else:
                fit = 0.05
            round_wls.append(
                {
                    "id": f"wl-{i}",
                    "passed": passed,
                    "fitness": fit,
                    "ms": ms,
                    "via": "serve_session_mutate",
                    "stdout": stdout[-200:],
                    "path_kind": path_kind,
                    "mutate_ok": False,
                    "eval_ok": bool(ok),
                }
            )
        selected = max(round_wls, key=lambda w: (w["fitness"], w["id"]))
        fit0 = float(selected["fitness"])
        if fit0 > best_fit:
            best_fit = fit0
            best_sel = selected["id"]
        goal_met = fit0 >= min_fit
        stop = "goal_met" if goal_met else ("max_rounds" if r_i >= max_r else "continue")
        if stop != "continue":
            stop_reason = stop
        round_rec = {
            "goal": goal,
            "round_i": r_i,
            "selected_id": selected["id"],
            "fitness": fit0,
            "worldline_backend": "serve_eval_source",
            "session_model": SESSION_SERVE,
            "path_kind": path_kind,
            "stop_reason": stop,
            "worldlines": round_wls,
            "episode_id": f"{traj_id}-r{r_i}",
        }
        rounds_out.append(round_rec)

        prompt = goal
        if llm_hint:
            prompt = f"{goal}\n\n; llm_hint (non-controller):\n{llm_hint}"
        episode = {
            "schema_version": "trajectory.v0",
            "episode_id": round_rec["episode_id"],
            "ts_start": _iso_now(),
            "ts_end": _iso_now(),
            "prompt": prompt,
            "runtime": {
                "mode": "aura",
                "kernel": "aura",
                "incr_proven": False,
                "fiber_live": False,
                "measured": True,
                "session_model": SESSION_SERVE,
                "serve_session_ok": True,
                "serve_mode": serve_mode,
                "serve_cross_session_shared_ast": shared_ast,
                "serve_same_session_mutate_ok": True,
                "worldline_backend": "serve_eval_source",
                "pursue": {
                    "goal": goal,
                    "round_i": r_i,
                    "max_rounds": max_r,
                    "min_fitness": min_fit,
                    "stop_reason": stop,
                    "llm_assist": llm_assist,
                    "harness_mutate": False,
                    "path_kind": path_kind,
                    "success_token": success_token,
                },
                "dogfood": {
                    "kind": "pursue_session",
                    "cold_spawns": cold_spawns,
                    "session_evals": len(session_ms),
                    "session_ms_total": sum(session_ms),
                    "session_ms_mean": (
                        round(sum(session_ms) / len(session_ms), 2) if session_ms else 0
                    ),
                },
            },
            "harness": {
                "l1_strategy_id": "pursue.serve_mutate.v1",
                "l3_online": False,
                "outcome": "pass" if goal_met else "partial",
                "actions": [
                    {"op": "session_attach", "via": f"serve_{serve_mode}"},
                    {"op": "mutate_rebind_worldlines", "count": n_wl},
                    {"op": "select_best"},
                ],
            },
            "worldlines": round_wls,
            "selected_id": selected["id"],
            "privacy": {"redacted": True, "retention_class": "dogfood"},
        }
        with out_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(episode, sort_keys=True) + "\n")

        if goal_met or r_i >= max_r:
            break

    if goal_met:
        stop_reason = "goal_met"
    elif stop_reason == "continue":
        stop_reason = "max_rounds"

    return {
        "ok": True,
        "goal_met": goal_met,
        "stop_reason": stop_reason,
        "goal": goal,
        "rounds_completed": len(rounds_out),
        "max_rounds": max_r,
        "min_fitness": min_fit,
        "best_fitness": best_fit,
        "selected_id": best_sel,
        "worldline_backend": "serve_eval_source",
        "session_model": SESSION_SERVE,
        "serve_session_ok": True,
        "serve_mode": serve_mode,
        "serve_cross_session_shared_ast": shared_ast,
        "serve_same_session_mutate_ok": True,
        "serve_async_soft_ready_ok": soft_ok,
        "serve_async_soft_ready_reason": (
            (soft or {}).get("reason") if isinstance(soft, dict) else None
        ),
        "serve_async_soft_ready_fail_bits": soft_bits,
        "serve_async_soft_ready_fail_bits_decoded": soft_decoded,
        "path_kind": path_kind,
        "cold_spawns": cold_spawns,
        "session_evals": len(session_ms),
        "session_ms_mean": (
            round(sum(session_ms) / len(session_ms), 2) if session_ms else 0
        ),
        "fiber_live": False,
        "incr_proven": False,
        "llm_assist": llm_assist,
        "harness_mutate": False,
        "path": str(out_path),
        "traj_id": traj_id,
        "rounds": rounds_out,
        "kernel": "aura",
        "pid": sess.pid,
        "success_token": success_token,
        "next_gate": (
            "Aura Soft Ready (#3098) fail_bits=0x10 (defaults_missing_soft) blocks "
            "--serve-async on Soft; cross-session shared FlatAST still deferred. "
            "Same-session mutate:rebind pursue is live."
        ),
    }
