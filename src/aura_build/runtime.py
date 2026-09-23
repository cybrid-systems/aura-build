"""Host bridge helpers: Aura binary probe + GCC16 libstdc++ sidecar.

Product mutate/eval backends live in the Aura kernel (`aura/*.aura`).
This module only resolves/probes the binary for `kernel.py`.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

OK_MARKER = "AURA_BUILD_OK"
_OK_RE = re.compile(rf"{re.escape(OK_MARKER)}\s+(-?\d+)")

INCR_VALID_MARKER = "AURA_BUILD_INCR_VALID"
INCR_VALID_ENV_LINE = "AURA_INCR_VALID=1"
_INCR_VALID_RE = re.compile(rf"{re.escape(INCR_VALID_MARKER)}\s+1\b")

_DEFAULT_BIN_CANDIDATES = (
    "/workspace/aura-grok/build/aura",
    "/workspace/aura-redis/.deps/aura/build/aura",
    "/workspace/aura-redis-ci/.deps/aura/build/aura",
)

_ENV_LIBSTDCXX_DIR = "AURA_LIBSTDCXX_DIR"
_DEFAULT_LIBSTDCXX_CANDIDATES = (
    "/workspace/aura-redis/.deps/gcc16-libstdcxx",
    "/workspace/aura-redis-ci/.deps/gcc16-libstdcxx",
    "/workspace/aura-grok/.deps/gcc16-libstdcxx",
)


class AuraUnavailable(RuntimeError):
    """Aura was requested but the binary/probe is missing or broken."""


def parse_incr_valid_signal(stdout: str = "", stderr: str = "") -> bool:
    """Return True only when Aura emitted an explicit incr-valid marker.

    Accepted forms (stdout or stderr):
    - ``AURA_BUILD_INCR_VALID 1`` (value must be exactly 1)
    - ``AURA_INCR_VALID=1``

    ``AURA_BUILD_INCR_VALID 0`` / missing marker ⇒ False. Never invent True.
    """
    blob = f"{stdout or ''}\n{stderr or ''}"
    if INCR_VALID_ENV_LINE in blob:
        return True
    return _INCR_VALID_RE.search(blob) is not None


def resolve_libstdcxx_dir(
    aura_bin: str | None = None,
    *,
    environ: dict[str, str] | None = None,
) -> str | None:
    """Locate a directory with libstdc++.so.6 new enough for a GCC16 Aura binary."""
    env = environ if environ is not None else os.environ
    explicit = (env.get(_ENV_LIBSTDCXX_DIR) or "").strip()
    if explicit:
        p = Path(explicit)
        if (p / "libstdc++.so.6").is_file() or (p / "libstdc++.so.6.0.35").is_file():
            return str(p.resolve())
        return None

    candidates: list[Path] = []
    if aura_bin:
        bin_path = Path(aura_bin).resolve()
        build_dir = bin_path.parent
        aura_root = build_dir.parent
        deps_root = aura_root.parent
        candidates.append(deps_root / "gcc16-libstdcxx")
        candidates.append(aura_root / ".deps" / "gcc16-libstdcxx")
        candidates.append(build_dir / "gcc16-libstdcxx")
    for c in _DEFAULT_LIBSTDCXX_CANDIDATES:
        candidates.append(Path(c))

    seen: set[str] = set()
    for c in candidates:
        key = str(c)
        if key in seen:
            continue
        seen.add(key)
        if (c / "libstdc++.so.6").is_file() or (c / "libstdc++.so.6.0.35").is_file():
            return str(c.resolve())
    return None


def aura_subprocess_env(
    aura_bin: str,
    *,
    base: dict[str, str] | None = None,
    lib_path: str | None = None,
    aura_ref: str | None = None,
) -> dict[str, str]:
    """Env for aura subprocesses: sandbox off + optional GCC16 libstdc++ sidecar."""
    env = dict(base) if base is not None else os.environ.copy()
    env.setdefault("AURA_BIN", aura_bin)
    env.setdefault("AURA_PIPELINE_STRICT", "0")
    env.setdefault("AURA_SANDBOX", "off")
    if lib_path:
        env["AURA_PATH"] = lib_path
    elif aura_ref:
        lib = Path(aura_ref) / "lib"
        if lib.is_dir():
            env.setdefault("AURA_PATH", str(lib))
    libdir = resolve_libstdcxx_dir(aura_bin, environ=env)
    if libdir:
        prev = env.get("LD_LIBRARY_PATH", "")
        parts = [libdir] + ([p for p in prev.split(":") if p] if prev else [])
        out: list[str] = []
        seen: set[str] = set()
        for p in parts:
            if p not in seen:
                seen.add(p)
                out.append(p)
        env["LD_LIBRARY_PATH"] = ":".join(out)
    return env


def probe_aura(aura_bin: str, *, timeout_s: float = 10.0) -> tuple[bool, str | None]:
    """Return (ok, error_message). ok means binary runs a trivial -e form."""
    if not aura_bin:
        return False, "empty aura_bin"
    path = Path(aura_bin)
    if not path.is_file():
        return False, f"aura binary not found: {aura_bin}"
    if not os.access(path, os.X_OK):
        return False, f"aura binary not executable: {aura_bin}"
    env = aura_subprocess_env(str(path))
    try:
        proc = subprocess.run(
            [str(path), "-e", "(+ 1 2)"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, f"aura probe timed out: {aura_bin}"
    except OSError as exc:
        return False, f"aura probe exec error: {exc}"
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[:300]
        return False, f"aura probe rc={proc.returncode}: {err}"
    return True, None


def resolve_aura_bin(
    explicit: str | None = None,
    aura_ref: str | None = None,
) -> str | None:
    """Locate an aura binary; None if nothing looks present (no probe yet)."""
    if explicit:
        return explicit
    env = os.environ.get("AURA_BIN")
    if env:
        return env
    which = shutil.which("aura")
    if which:
        return which
    if aura_ref:
        cand = Path(aura_ref) / "build" / "aura"
        if cand.is_file():
            return str(cand)
    for c in _DEFAULT_BIN_CANDIDATES:
        if Path(c).is_file():
            return c
    return None
