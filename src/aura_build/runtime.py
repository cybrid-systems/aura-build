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
   - non-zero exit or missing marker ⇒ eval failed (no silent simulated fill)

4. Honesty rules:
   - ``runtime.mode`` in trajectories is the backend actually used
   - ``mode=aura`` never falls back to simulated (raises ``AuraUnavailable``)
   - ``mode=auto`` may fall back; trajectory still says ``simulated``

5. M2 gaps (not this module):
   - multi-candidate incr-compile fitness from aura-repo ``build.py``
   - fiber fan-out of live worldlines (not N sequential shell procs)
   - durable workspace / stable-ref continuity across candidates
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

_DEFAULT_BIN_CANDIDATES = (
    "/workspace/aura-grok/build/aura",
    "/workspace/aura-redis/.deps/aura/build/aura",
    "/workspace/aura-redis-ci/.deps/aura/build/aura",
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
                },
                "notes": result.get("notes", "aura mutate+eval-current"),
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
        env = os.environ.copy()
        env.setdefault("AURA_BIN", self.aura_bin)
        env.setdefault("AURA_PIPELINE_STRICT", "0")
        env.setdefault("AURA_SANDBOX", "off")
        if self.lib_path:
            env["AURA_PATH"] = self.lib_path
        elif self.aura_ref:
            lib = Path(self.aura_ref) / "lib"
            if lib.is_dir():
                env.setdefault("AURA_PATH", str(lib))

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
        notes = "aura mutate+eval-current"
        if not ok:
            tail = (stderr or stdout)[-400:].strip()
            notes = f"aura failed rc={proc.returncode}: {tail}"
        return {
            "ok": ok,
            "exit_code": proc.returncode,
            "value": value,
            "notes": notes,
        }


def _program_for(*, bump: int, index: int, seed: int) -> str:
    """Tiny Aura program: set-code → eval-current → mutate:rebind → eval-current."""
    return f"""; aura-build M1 — mutate:rebind + eval-current (wl={index} seed={seed})
(set-code "(define (m1-cand n) (+ n 0))")
(eval-current)
(mutate:rebind "m1-cand" "(lambda (n) (+ n {bump}))" "aura-build-m1-wl-{index}")
(eval-current)
(display "{OK_MARKER} ")
(display (m1-cand 40))
(newline)
"""


def probe_aura(aura_bin: str, *, timeout_s: float = 10.0) -> tuple[bool, str | None]:
    """Return (ok, error_message). ok means binary runs a trivial -e form."""
    if not aura_bin:
        return False, "empty aura_bin"
    path = Path(aura_bin)
    if not path.is_file():
        return False, f"aura binary not found: {aura_bin}"
    if not os.access(path, os.X_OK):
        return False, f"aura binary not executable: {aura_bin}"
    env = os.environ.copy()
    env.setdefault("AURA_BIN", str(path))
    env.setdefault("AURA_PIPELINE_STRICT", "0")
    env.setdefault("AURA_SANDBOX", "off")
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
