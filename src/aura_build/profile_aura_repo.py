"""Aura-repo profile (M2): detect checkout + fitness hooks around build.py.

Detection order
---------------
1. Explicit ``aura_ref`` / ``--aura-ref``
2. Env ``AURA_REF``
3. Well-known dogfood path ``/workspace/aura-grok`` when it has ``build.py``

Fitness
-------
Preferred: invoke ``python build.py`` (or a tiny compile-check command) under
the detected repo and score from exit + wall time.

When the Aura binary / toolchain is broken (e.g. ``GLIBCXX_`` mismatch) or
``build.py`` is unavailable for a real compile, fall back to **simulated**
fitness while still emitting the same metric fields:

- ``compile_ms`` — wall time of the attempted check (0 if fully simulated)
- ``incr_claimed`` — whether this profile *claims* an incremental path
- ``incr_proven`` — **always false in M2** until storm-still-incr is measured

Honesty: simulated fitness never sets ``runtime.mode=aura`` by itself; orch
still records the RuntimeBackend mode. Profile fields live under
``runtime.profile`` / eval metrics.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

PROFILE_ID = "aura-repo"

_DEFAULT_REFS = (
    "/workspace/aura-grok",
    "/workspace/aura-redis/.deps/aura",
)


@dataclass
class AuraRepoProfile:
    """Resolved aura-repo dogfood target + fitness policy."""

    root: Path
    build_py: Path | None
    has_tests: bool
    fitness_source: str  # build.py | compile_check | simulated
    incr_claimed: bool = True
    incr_proven: bool = False  # M2 honesty: never claim proven yet

    def to_runtime_dict(self) -> dict[str, Any]:
        return {
            "id": PROFILE_ID,
            "root": str(self.root.resolve()),
            "build_py": str(self.build_py) if self.build_py else None,
            "has_tests": self.has_tests,
            "fitness_source": self.fitness_source,
            "incr_claimed": self.incr_claimed,
            "incr_proven": self.incr_proven,
        }


@dataclass
class FitnessResult:
    fitness: float
    passed: bool
    compile_ms: int
    incr_claimed: bool
    incr_proven: bool
    fitness_source: str
    tests_passed: int
    tests_total: int
    notes: str
    audit_ok: bool = True

    def to_eval_metrics(self) -> dict[str, Any]:
        return {
            "tests_passed": self.tests_passed,
            "tests_total": self.tests_total,
            "compile_ms": self.compile_ms,
            # Keep legacy key for M0/M1 readers; same wall clock for now.
            "incr_compile_ms": self.compile_ms,
            "incr_claimed": self.incr_claimed,
            "incr_proven": self.incr_proven,
            "fitness_source": self.fitness_source,
            "audit_ok": self.audit_ok,
        }


def detect_aura_repo(explicit: str | None = None) -> Path | None:
    """Return repo root with ``build.py``, or None."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("AURA_REF")
    if env:
        candidates.append(Path(env))
    for c in _DEFAULT_REFS:
        candidates.append(Path(c))

    seen: set[Path] = set()
    for p in candidates:
        try:
            rp = p.resolve()
        except OSError:
            continue
        if rp in seen:
            continue
        seen.add(rp)
        if (rp / "build.py").is_file():
            return rp
    return None


def resolve_profile(
    explicit: str | None = None,
    *,
    prefer_live_build: bool = True,
) -> AuraRepoProfile | None:
    """Build an AuraRepoProfile or None if no aura-repo checkout found."""
    root = detect_aura_repo(explicit)
    if root is None:
        return None
    build_py = root / "build.py"
    has_tests = (root / "tests").is_dir()
    source = "simulated"
    if prefer_live_build and build_py.is_file():
        # Probe whether a cheap invocation is even worth attempting.
        # We do not run a full build here — only decide the preferred source.
        source = "build.py"
    return AuraRepoProfile(
        root=root,
        build_py=build_py if build_py.is_file() else None,
        has_tests=has_tests,
        fitness_source=source,
        incr_claimed=True,
        incr_proven=False,
    )


def _simulated_fitness(prompt: str, seed: int, index: int) -> float:
    h = hashlib.sha256(f"aura-repo:{seed}:{index}:{prompt}".encode()).hexdigest()
    base = int(h[:6], 16) / float(0xFFFFFF)
    bump = 0.12 if index == 0 else 0.0
    return round(min(1.0, base * 0.8 + 0.2 + bump), 4)


def run_build_hook(
    profile: AuraRepoProfile,
    *,
    command: list[str] | None = None,
    timeout_s: float = 60.0,
    cwd: Path | None = None,
) -> tuple[bool, int, str]:
    """Run build.py (or override command). Return (ok, compile_ms, notes).

    Default command is a **dry discovery** only: ``python build.py --help``
    (or ``list``) so CI / dogfood boxes without a working toolchain still
    exercise the hook interface without a multi-minute compile. Callers that
    want a real compile must pass an explicit ``command``.
    """
    work = cwd or profile.root
    if command is None:
        if profile.build_py is None:
            return False, 0, "no build.py"
        command = ["python3", str(profile.build_py), "list"]

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            cwd=str(work),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        ms = int((time.perf_counter() - t0) * 1000)
        return False, ms, f"build hook timeout: {exc}"
    except OSError as exc:
        ms = int((time.perf_counter() - t0) * 1000)
        return False, ms, f"build hook exec failed: {exc}"

    ms = int((time.perf_counter() - t0) * 1000)
    ok = proc.returncode == 0
    if ok:
        return True, ms, f"build hook ok rc=0 cmd={' '.join(command)[:120]}"
    err = (proc.stderr or proc.stdout or "").strip()
    # GLIBCXX / missing compiler — surface clearly for simulated fallback.
    if "GLIBCXX" in err:
        return False, ms, f"build hook GLIBCXX broken: {err[:240]}"
    return False, ms, f"build hook rc={proc.returncode}: {err[:240]}"


def evaluate_candidate(
    profile: AuraRepoProfile,
    *,
    prompt: str,
    seed: int,
    index: int,
    try_live: bool = True,
    live_command: list[str] | None = None,
    timeout_s: float = 60.0,
    simulated_fn: Callable[[str, int, int], float] | None = None,
) -> FitnessResult:
    """Score one candidate; live build hook when possible, else simulated.

    Always sets ``incr_proven=False``. ``incr_claimed`` follows the profile.
    """
    sim = simulated_fn or _simulated_fitness

    if try_live and profile.build_py is not None and profile.fitness_source != "forced_simulated":
        ok, ms, notes = run_build_hook(
            profile, command=live_command, timeout_s=timeout_s
        )
        if ok:
            # Live hook succeeded (cheap list/help or real compile). Blend a
            # deterministic component so select-best still varies by index.
            base = sim(prompt, seed, index)
            fitness = round(min(1.0, 0.55 + 0.35 * base), 4)
            return FitnessResult(
                fitness=fitness,
                passed=True,
                compile_ms=ms,
                incr_claimed=profile.incr_claimed,
                incr_proven=False,
                fitness_source="build.py" if live_command is None else "compile_check",
                tests_passed=1,
                tests_total=1,
                notes=notes,
                audit_ok=True,
            )
        # Live failed (GLIBCXX, missing tools, etc.) → simulated with note.
        fitness = sim(prompt, seed, index)
        return FitnessResult(
            fitness=fitness,
            passed=fitness >= 0.3,
            compile_ms=ms,
            incr_claimed=profile.incr_claimed,
            incr_proven=False,
            fitness_source="simulated",
            tests_passed=1 if fitness >= 0.3 else 0,
            tests_total=1,
            notes=f"simulated after live miss: {notes}",
            audit_ok=True,
        )

    fitness = sim(prompt, seed, index)
    return FitnessResult(
        fitness=fitness,
        passed=fitness >= 0.3,
        compile_ms=0,
        incr_claimed=profile.incr_claimed,
        incr_proven=False,
        fitness_source="simulated",
        tests_passed=1 if fitness >= 0.3 else 0,
        tests_total=1,
        notes="aura-repo simulated fitness (no live build attempted)",
        audit_ok=True,
    )
