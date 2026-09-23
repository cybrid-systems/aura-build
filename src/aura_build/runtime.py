"""Runtime backends: SimulatedBackend (M0) and AuraBackend (M1 shell bridge).

Integration points (AuraBackend → live FlatAST)
-----------------------------------------------
1. Binary resolution (first hit wins):
   - ``OrchConfig.aura_bin`` / ``--aura-bin``
   - env ``AURA_BIN``
   - ``{aura_ref}/build/aura`` when ``aura_ref`` is a checkout
   - well-known local paths (``/workspace/aura-grok/build/aura``, …)

2. Minimal Aura program (mutate + eval-current):
   - shipped as ``scripts/aura_m1_mutate_eval.aura``
   - or generated per-worldline via ``_program_for``
   - primitives: ``set-code``, ``mutate:rebind``, ``eval-current``

3. Invocation:
   - ``aura <file.aura>`` (preferred) or ``aura -e '…'``
   - success marker on stdout: ``AURA_BUILD_OK <int>``
   - incr-valid marker (optional, honest only): ``AURA_BUILD_INCR_VALID 1``
     and/or ``AURA_INCR_VALID=1`` on stdout/stderr after measuring Aura
     ``compile:epoch`` / ``query:jit-stats-hash`` deltas across mutate:rebind
   - non-zero exit or missing OK marker ⇒ eval failed (no silent simulated fill)

4. Honesty rules:
   - ``runtime.mode`` in trajectories is the backend actually used
   - ``mode=aura`` never falls back to simulated (raises ``AuraUnavailable``)
   - ``mode=auto`` may fall back; trajectory still says ``simulated``

5. M2 (see ``worldline.py`` + ``profile_aura_repo.py``, not this module):
   - shared workspace + stable-ref fan-out + discard losers
   - aura-repo ``build.py`` fitness hooks (``incr_proven=false`` until proven)
   - still **not** fiber-live FlatAST; session_model=shared_workspace_subprocess
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

OK_MARKER = "AURA_BUILD_OK"
_OK_RE = re.compile(rf"{re.escape(OK_MARKER)}\s+(-?\d+)")

# Incr-valid probe contract (see docs/storm-still-incr.md):
# Aura mutate+eval programs emit an explicit marker when FlatAST/compile
# surfaces show a real delta (compile:epoch / hotswap-invalidate-total /
# mutation-epoch). aura-build never invents this — parse stdout/stderr only.
INCR_VALID_MARKER = "AURA_BUILD_INCR_VALID"
INCR_VALID_ENV_LINE = "AURA_INCR_VALID=1"
_INCR_VALID_RE = re.compile(rf"{re.escape(INCR_VALID_MARKER)}\s+1\b")


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


_DEFAULT_BIN_CANDIDATES = (
    "/workspace/aura-grok/build/aura",
    "/workspace/aura-redis/.deps/aura/build/aura",
    "/workspace/aura-redis-ci/.deps/aura/build/aura",
)

# Host boxes often ship GCC 14 (libstdc++ ≤ GLIBCXX_3.4.33) while Aura is
# built with GCC 16 (needs GLIBCXX_3.4.35). Sidecar dirs hold a matching
# libstdc++.so.6; see docs/storm-still-incr.md + scripts/fetch-gcc16-libstdcxx.sh.
_ENV_LIBSTDCXX_DIR = "AURA_LIBSTDCXX_DIR"
_DEFAULT_LIBSTDCXX_CANDIDATES = (
    "/workspace/aura-redis/.deps/gcc16-libstdcxx",
    "/workspace/aura-redis-ci/.deps/gcc16-libstdcxx",
    "/workspace/aura-grok/.deps/gcc16-libstdcxx",
)


class AuraUnavailable(RuntimeError):
    """Aura was requested but the binary/probe is missing or broken."""


@runtime_checkable
class RuntimeBackend(Protocol):
    """Protocol behind orch mutate/eval (M1)."""

    @property
    def mode(self) -> str:
        """``simulated`` or ``aura`` — written into trajectory runtime.mode."""

    @property
    def aura_ref(self) -> str | None:
        ...

    def mutate_worldlines(self, prompt: str, seed: int, n: int) -> list[dict[str, Any]]:
        ...

    def eval_worldline(
        self,
        wl: dict[str, Any],
        prompt: str,
        seed: int,
        index: int,
    ) -> dict[str, Any]:
        """Return a Worldline-shaped dict: id, parent_id, mutations, eval."""


def _default_fitness(prompt: str, seed: int, index: int) -> float:
    h = hashlib.sha256(f"{seed}:{index}:{prompt}".encode()).hexdigest()
    base = int(h[:6], 16) / float(0xFFFFFF)
    bump = 0.15 if index == 1 else 0.0
    return round(min(1.0, base * 0.85 + bump), 4)


@dataclass
class SimulatedBackend:
    """M0 deterministic fake worldlines (always available)."""

    fitness_fn: Callable[[str, int, int], float] | None = None
    strategy_note: str = "m0 simulated eval"

    @property
    def mode(self) -> str:
        return "simulated"

    @property
    def aura_ref(self) -> str | None:
        return None

    def mutate_worldlines(self, prompt: str, seed: int, n: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i in range(n):
            out.append(
                {
                    "id": f"wl-{i}",
                    "parent_id": None,
                    "mutations": [
                        {
                            "op": "simulated_edit",
                            "target_id": f"node:demo:{i}",
                            "summary": f"candidate {i} for: {prompt[:80]}",
                        }
                    ],
                }
            )
        return out

    def eval_worldline(
        self,
        wl: dict[str, Any],
        prompt: str,
        seed: int,
        index: int,
    ) -> dict[str, Any]:
        fn = self.fitness_fn or _default_fitness
        fitness = fn(prompt, seed, index)
        passed = fitness >= 0.3
        return {
            "id": wl["id"],
            "parent_id": wl.get("parent_id"),
            "mutations": list(wl.get("mutations") or []),
            "eval": {
                "fitness": fitness,
                "passed": passed,
                "metrics": {
                    "tests_passed": 1 if passed else 0,
                    "tests_total": 1,
                    "incr_compile_ms": 5 + index * 3,
                    "audit_ok": True,
                },
                "notes": self.strategy_note,
            },
        }


@dataclass
class AuraBackend:
    """Shell bridge to an Aura binary for mutate:rebind + eval-current.

    Does **not** claim live fiber worldlines — each candidate is a short
    subprocess. Multi-candidate incr-compile on a shared workspace is M2.
    """

    aura_bin: str
    aura_ref: str | None = None
    timeout_s: float = 30.0
    lib_path: str | None = None
    _probed_ok: bool | None = field(default=None, init=False, repr=False)
    _probe_error: str | None = field(default=None, init=False, repr=False)

    @property
    def mode(self) -> str:
        return "aura"

    def mutate_worldlines(self, prompt: str, seed: int, n: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i in range(n):
            bump = i + 1
            out.append(
                {
                    "id": f"wl-{i}",
                    "parent_id": None,
                    "mutations": [
                        {
                            "op": "aura_mutate_rebind",
                            "target_id": f"m1-cand:{i}",
                            "summary": (
                                f"mutate:rebind m1-cand → (+ n {bump}); "
                                f"prompt={prompt[:60]}"
                            ),
                            "bump": bump,
                        }
                    ],
                }
            )
        return out

    def eval_worldline(
        self,
        wl: dict[str, Any],
        prompt: str,
        seed: int,
        index: int,
    ) -> dict[str, Any]:
        self.ensure_available()
        mutations = list(wl.get("mutations") or [])
        bump = int(mutations[0].get("bump", index + 1)) if mutations else index + 1
        t0 = time.perf_counter()
        result = self._run_mutate_eval(bump=bump, index=index, seed=seed)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        ok = result["ok"]
        value = result.get("value")
        expected = 40 + bump
        if ok and value == expected:
            fitness = round(0.75 + 0.05 * (index % 4), 4)
        elif ok:
            fitness = 0.45
        else:
            fitness = 0.1
        incr_valid = bool(result.get("incr_valid"))
        notes = str(result.get("notes") or "aura mutate+eval-current")
        if incr_valid and INCR_VALID_MARKER not in notes:
            notes = f"{notes}; {INCR_VALID_MARKER}"
        return {
            "id": wl["id"],
            "parent_id": wl.get("parent_id"),
            "mutations": mutations,
            "eval": {
                "fitness": fitness,
                "passed": ok,
                "metrics": {
                    "tests_passed": 1 if ok else 0,
                    "tests_total": 1,
                    "incr_compile_ms": elapsed_ms,
                    "audit_ok": ok,
                    "aura_exit": result.get("exit_code"),
                    "aura_value": value,
                    "incr_valid": incr_valid,
                },
                "notes": notes,
            },
        }

    def ensure_available(self) -> None:
        if self._probed_ok is True:
            return
        if self._probed_ok is False:
            raise AuraUnavailable(self._probe_error or "aura probe failed")
        ok, err = probe_aura(self.aura_bin, timeout_s=min(10.0, self.timeout_s))
        self._probed_ok = ok
        self._probe_error = err
        if not ok:
            raise AuraUnavailable(err or f"aura not usable: {self.aura_bin}")

    def _run_mutate_eval(self, *, bump: int, index: int, seed: int) -> dict[str, Any]:
        program = _program_for(bump=bump, index=index, seed=seed)
        env = aura_subprocess_env(
            self.aura_bin,
            lib_path=self.lib_path,
            aura_ref=self.aura_ref,
        )

        with tempfile.TemporaryDirectory(prefix="aura-build-m1-") as tmp:
            path = Path(tmp) / "m1_mutate_eval.aura"
            path.write_text(program, encoding="utf-8")
            try:
                proc = subprocess.run(
                    [self.aura_bin, str(path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_s,
                    env=env,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return {
                    "ok": False,
                    "exit_code": None,
                    "value": None,
                    "notes": f"aura timeout after {self.timeout_s}s: {exc}",
                }
            except OSError as exc:
                return {
                    "ok": False,
                    "exit_code": None,
                    "value": None,
                    "notes": f"aura exec failed: {exc}",
                }

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        match = _OK_RE.search(stdout)
        value = int(match.group(1)) if match else None
        ok = proc.returncode == 0 and match is not None
        incr_valid = parse_incr_valid_signal(stdout, stderr)
        notes = "aura mutate+eval-current"
        if incr_valid:
            notes = f"aura mutate+eval-current; {INCR_VALID_MARKER}"
        if not ok:
            tail = (stderr or stdout)[-400:].strip()
            notes = f"aura failed rc={proc.returncode}: {tail}"
            incr_valid = False  # fail-closed: failed eval is never incr-valid
        return {
            "ok": ok,
            "exit_code": proc.returncode,
            "value": value,
            "notes": notes,
            "incr_valid": incr_valid,
            "stdout_tail": stdout[-500:],
            "stderr_tail": stderr[-500:],
        }


def _program_for(*, bump: int, index: int, seed: int) -> str:
    """Tiny Aura program: mutate:rebind + eval-current + incr-valid probe.

    Probe contract (language-wide Aura stats — not Redis-specific):
    record ``compile:epoch`` / ``query:jit-stats-hash`` (hotswap-invalidate-total,
    mutation-epoch) *before* rebind; after ``eval-current``, emit
    ``AURA_BUILD_INCR_VALID 1`` + ``AURA_INCR_VALID=1`` only when a delta proves
    incremental compile/invalidate work. See docs/storm-still-incr.md.
    """
    return f"""; aura-build M1 — mutate:rebind + eval-current + incr probe (wl={index} seed={seed})
(set-code "(define (m1-cand n) (+ n 0))")
(eval-current)
(define epoch0 (or (stats:get "compile:epoch") 0))
(define h0 (stats:get "query:jit-stats-hash"))
(define inv0 (or (hash-ref h0 "hotswap-invalidate-total") 0))
(define mut0 (or (hash-ref h0 "mutation-epoch") 0))
(mutate:rebind "m1-cand" "(lambda (n) (+ n {bump}))" "aura-build-m1-wl-{index}")
(eval-current)
(define epoch1 (or (stats:get "compile:epoch") 0))
(define h1 (stats:get "query:jit-stats-hash"))
(define inv1 (or (hash-ref h1 "hotswap-invalidate-total") 0))
(define mut1 (or (hash-ref h1 "mutation-epoch") 0))
(display "{OK_MARKER} ")
(display (m1-cand 40))
(newline)
(display "AURA_INCR_META epoch=")(display epoch0)(display "->")(display epoch1)
(display " inv=")(display inv0)(display "->")(display inv1)
(display " mut=")(display mut0)(display "->")(display mut1)
(newline)
(if (or (> epoch1 epoch0) (> inv1 inv0) (> mut1 mut0))
  (begin
    (display "{INCR_VALID_MARKER} 1")(newline)
    (display "{INCR_VALID_ENV_LINE}")(newline))
  (begin
    (display "{INCR_VALID_MARKER} 0")(newline)))
"""



def resolve_libstdcxx_dir(
    aura_bin: str | None = None,
    *,
    environ: dict[str, str] | None = None,
) -> str | None:
    """Locate a directory with libstdc++.so.6 new enough for a GCC16 Aura binary.

    Order: ``AURA_LIBSTDCXX_DIR`` → sibling ``.deps/gcc16-libstdcxx`` next to
    the aura checkout → well-known workspace paths. Returns None when absent
    (caller keeps host default; probe will then surface GLIBCXX honestly).
    """
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
        # …/aura/build/aura → …/gcc16-libstdcxx (redis .deps layout)
        # …/aura/build/aura → parent=build, parent2=aura, parent3=.deps
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
        # de-dupe preserving order
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


def resolve_backend(
    mode: str,
    *,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
    fitness_fn: Callable[[str, int, int], float] | None = None,
    backend: RuntimeBackend | None = None,
) -> RuntimeBackend:
    """Pick backend from mode. ``aura`` never silently degrades to simulated."""
    if backend is not None:
        return backend

    mode = (mode or "simulated").lower().strip()
    if mode == "simulated":
        return SimulatedBackend(fitness_fn=fitness_fn)

    if mode not in ("aura", "auto"):
        raise ValueError(f"unknown runtime mode: {mode!r} (expected simulated|aura|auto)")

    bin_path = resolve_aura_bin(aura_bin, aura_ref)
    if not bin_path:
        if mode == "aura":
            raise AuraUnavailable(
                "mode=aura but no aura binary found "
                "(set --aura-bin or AURA_BIN, or clone aura under aura_ref)"
            )
        return SimulatedBackend(fitness_fn=fitness_fn)

    aura = AuraBackend(aura_bin=bin_path, aura_ref=aura_ref)
    try:
        aura.ensure_available()
    except AuraUnavailable:
        if mode == "aura":
            raise
        return SimulatedBackend(fitness_fn=fitness_fn)
    return aura
