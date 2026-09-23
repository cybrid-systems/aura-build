"""Thin host bridge: invoke the Aura kernel (aura/main.aura).

Product orchestration lives in ``aura/*.aura``. This module only:
- resolves the aura binary + GCC16 libstdc++ sidecar
- sets AURA_BUILD_* env from a request dict
- shells out to ``aura aura/main.aura``
- returns stdout + parsed kernel-response.json

``AURA_BUILD_FORCE_PYTHON`` is debug-only / deprecated: it disables the Aura
prefer path so the CLI can refuse honestly. It does **not** restore Python orch.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aura_build.runtime import (
    AuraUnavailable,
    aura_subprocess_env,
    probe_aura,
    resolve_aura_bin,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
AURA_KERNEL_MAIN = REPO_ROOT / "aura" / "main.aura"


@dataclass
class KernelResult:
    ok: bool
    exit_code: int
    stdout: str
    stderr: str
    response: dict[str, Any]
    via: str  # "aura"


def repo_root() -> Path:
    return REPO_ROOT


def aura_path_env(aura_bin: str | None = None) -> str:
    """Module search path: repo aura/ + discovered Aura stdlib."""
    parts: list[str] = [str(REPO_ROOT / "aura")]
    candidates = [
        Path("/workspace/aura-redis/.deps/aura/lib"),
        Path("/workspace/aura-grok/lib"),
    ]
    if aura_bin:
        b = Path(aura_bin).resolve()
        candidates.insert(0, b.parent.parent / "lib")
        candidates.insert(0, b.parent.parent.parent / "aura" / "lib")
    for c in candidates:
        if c.is_dir() and (c / "std").is_dir():
            parts.append(str(c))
            break
    prev = os.environ.get("AURA_PATH", "")
    if prev:
        parts.append(prev)
    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return ":".join(out)


def kernel_available(
    aura_bin: str | None = None,
    aura_ref: str | None = None,
) -> tuple[bool, str | None, str | None]:
    """Return (ok, bin_path, error)."""
    bin_path = resolve_aura_bin(aura_bin, aura_ref)
    if not bin_path:
        return False, None, "aura_binary_missing"
    if not AURA_KERNEL_MAIN.is_file():
        return False, bin_path, f"kernel missing: {AURA_KERNEL_MAIN}"
    ok, err = probe_aura(bin_path)
    if not ok:
        return False, bin_path, err
    return True, bin_path, None


def invoke_aura_kernel(
    cmd: str,
    env_vars: dict[str, str] | None = None,
    *,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
    timeout_s: float = 120.0,
    harness_root: Path | str | None = None,
) -> KernelResult:
    """Run ``aura aura/main.aura`` with AURA_BUILD_CMD=cmd + env_vars."""
    ok, bin_path, err = kernel_available(aura_bin, aura_ref)
    if not ok or not bin_path:
        raise AuraUnavailable(err or "aura kernel unavailable")

    root = Path(harness_root) if harness_root else Path.cwd() / ".aura-build"
    root.mkdir(parents=True, exist_ok=True)
    response_path = root / "kernel-response.json"
    if response_path.exists():
        response_path.unlink()

    env = aura_subprocess_env(bin_path, aura_ref=aura_ref)
    env["AURA_PATH"] = aura_path_env(bin_path)
    env["AURA_BUILD_CMD"] = cmd
    env["AURA_BUILD_REPO_ROOT"] = str(REPO_ROOT)
    env["AURA_BUILD_HARNESS_ROOT"] = str(root)
    env["AURA_BUILD_RESPONSE"] = str(response_path)
    if env_vars:
        for k, v in env_vars.items():
            if v is None:
                continue
            env[str(k)] = str(v)

    try:
        proc = subprocess.run(
            [bin_path, str(AURA_KERNEL_MAIN)],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            check=False,
            cwd=str(REPO_ROOT),
        )
    except subprocess.TimeoutExpired as exc:
        raise AuraUnavailable(f"aura kernel timeout: {exc}") from exc
    except OSError as exc:
        raise AuraUnavailable(f"aura kernel exec failed: {exc}") from exc

    response: dict[str, Any] = {}
    if response_path.is_file():
        try:
            response = json.loads(response_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            response = {"ok": False, "error": "invalid_kernel_response"}

    exit_code = 0
    if cmd == "harness-mutate" and response.get("accepted") is False:
        exit_code = 1
    elif response.get("ok") is False:
        exit_code = 2 if response.get("error") else 1
    elif proc.returncode not in (0, None) and not response:
        exit_code = proc.returncode

    return KernelResult(
        ok=bool(response.get("ok", proc.returncode == 0)),
        exit_code=exit_code,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        response=response,
        via="aura",
    )


def prefer_aura_kernel() -> bool:
    """Host policy: use Aura kernel when binary+probe OK (default ON).

    ``AURA_BUILD_FORCE_PYTHON=1`` is deprecated: disables Aura prefer so the
    CLI refuses instead of silently pretending Python is the product.
    """
    raw = os.environ.get("AURA_BUILD_FORCE_PYTHON", "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return False
    return True


def clean_kernel_text(s: str) -> str:
    """Strip Aura REPL noise; normalize #t/#f in KEY=VAL lines for host stdout."""
    out: list[str] = []
    for ln in (s or "").splitlines():
        if not ln.strip() or ln.strip() == "#t":
            continue
        ln = (
            ln.replace("=#t", "=True")
            .replace("=#f", "=False")
            .replace("= #t", "= True")
            .replace("= #f", "= False")
        )
        out.append(ln)
    return "\n".join(out)


def emit_kernel_io(result: KernelResult) -> None:
    """Print cleaned kernel stdout/stderr to the host process streams."""
    out = clean_kernel_text(result.stdout)
    if out:
        print(out)
    err = clean_kernel_text(result.stderr)
    if err:
        print(err, file=sys.stderr)


def try_invoke_aura(
    cmd: str,
    env_vars: dict[str, str] | None = None,
    *,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
    harness_root: Path | str | None = None,
    timeout_s: float = 120.0,
) -> KernelResult | None:
    """Invoke Aura when preferred+available; None ⇒ host refuse or host-only fallback.

    Raises AuraUnavailable only if availability passed but exec/timeout failed.
    """
    if not prefer_aura_kernel():
        return None
    ok, _bin, _err = kernel_available(aura_bin, aura_ref)
    if not ok:
        return None
    return invoke_aura_kernel(
        cmd,
        env_vars,
        aura_bin=aura_bin,
        aura_ref=aura_ref,
        harness_root=harness_root,
        timeout_s=timeout_s,
    )


def kernel_exit_code(result: KernelResult) -> int:
    if result.exit_code is not None:
        return int(result.exit_code)
    return 0 if result.ok else 2


