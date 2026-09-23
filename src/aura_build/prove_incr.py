"""Storm-still-incr measurement harness (Post-M5) — prove-or-refuse.

Honesty contract
----------------
* Never set ``incr_proven=true`` unless a healthy Aura runtime was measured
  under this process and every storm cycle reported an explicit incr-valid
  signal. Absence of telemetry ⇒ refuse (``incr_proven=false``).
* Unhealthy / missing Aura (GLIBCXX, not found, probe fail) ⇒ **fail-closed**:
  write a report with ``incr_proven=false`` and a clear reason. Exit 0 for the
  refuse path so CI stays green; the report is the truth surface.
* Fiber / long-lived session: probe only. Keep
  ``session_model=shared_workspace_subprocess`` unless a real fiber session
  works. Never claim ``fiber_live`` from a failed or skipped probe.

Orch episodes auto-attach the latest report via ``attach_prove_metadata``
(``--attach-prove``, default ON). Attachment never invents ``true``: env gates
``AURA_BUILD_INCR_VALID`` / ``AURA_BUILD_FIBER_SESSION_OK`` alone cannot elevate
``incr_proven`` / ``fiber_live``.
"""

from __future__ import annotations

import json
import os
import concurrent.futures
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from aura_build.harness import default_root
from aura_build.runtime import (
    AuraBackend,
    AuraUnavailable,
    probe_aura,
    resolve_aura_bin,
)
from aura_build.worldline import (
    SESSION_LONG_LIVED_AURA,
    SESSION_SHARED_SUBPROCESS,
)

__all__ = [
    "ENV_FIBER_SESSION_OK",
    "ENV_INCR_VALID",
    "FiberProbeResult",
    "ProveIncrReport",
    "StormCycleResult",
    "attach_prove_metadata",
    "classify_unhealthy_reason",
    "default_report_path",
    "doctor_snapshot",
    "env_flag_truthy",
    "load_latest_report",
    "merge_prove_into_runtime",
    "probe_fiber_session",
    "prove_or_refuse",
    "run_storm",
    "write_report",
]

REPORT_SCHEMA = "prove_incr.v0"
INCR_VALID_MARKER = "AURA_BUILD_INCR_VALID"
# Env gates (read-only honor): document future healthy boxes; cannot alone
# elevate incr_proven / fiber_live when attaching trajectory metadata.
ENV_INCR_VALID = "AURA_BUILD_INCR_VALID"
ENV_FIBER_SESSION_OK = "AURA_BUILD_FIBER_SESSION_OK"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_report_path(root: Path | str | None = None) -> Path:
    """Report path under harness root (same semantics as ``--harness-root``).

    Explicit ``root`` is the ``.aura-build`` directory itself (or a test
    substitute). ``None`` → ``default_root()`` (``cwd/.aura-build``).
    """
    base = Path(root) if root is not None else default_root()
    return base / "prove-incr-latest.json"


def classify_unhealthy_reason(probe_error: str | None, *, bin_path: str | None) -> str:
    """Map probe failure text to a stable refuse reason string."""
    if not bin_path:
        return "aura_binary_missing"
    err = (probe_error or "").strip()
    upper = err.upper()
    if "GLIBCXX" in upper:
        return "aura_glibcxx_mismatch"
    if "not found" in err.lower() or "no such file" in err.lower():
        return "aura_binary_missing"
    if "not executable" in err.lower():
        return "aura_binary_not_executable"
    if "timed out" in err.lower():
        return "aura_probe_timeout"
    if err:
        return f"aura_probe_failed:{err[:180]}"
    return "aura_unhealthy"


@dataclass
class StormCycleResult:
    index: int
    ok: bool
    elapsed_ms: int
    incr_valid: bool
    notes: str = ""
    aura_value: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FiberProbeResult:
    available: bool
    session_model: str
    notes: str
    probed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProveIncrReport:
    """Canonical prove-or-refuse artifact (also written under .aura-build/)."""

    schema_version: str = REPORT_SCHEMA
    ts: str = field(default_factory=_utc_now)
    incr_proven: bool = False
    reason: str = "not_run"
    measured: bool = False
    aura_healthy: bool = False
    aura_bin: str | None = None
    probe_error: str | None = None
    session_model: str = SESSION_SHARED_SUBPROCESS
    fiber_live: bool = False
    fiber_probe: dict[str, Any] = field(default_factory=dict)
    cycles_requested: int = 0
    cycles_completed: int = 0
    cycles_ok: int = 0
    cycles_incr_valid: int = 0
    worldline_pressure: int = 0
    storm: list[dict[str, Any]] = field(default_factory=list)
    honesty: dict[str, Any] = field(
        default_factory=lambda: {
            "never_claim_without_measure": True,
            "fail_closed_on_unhealthy": True,
            "incr_valid_requires_explicit_signal": True,
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


EvalFn = Callable[[int, int], StormCycleResult]
# (cycle_index, worldline_index) -> StormCycleResult


def probe_fiber_session(
    aura_bin: str | None,
    *,
    timeout_s: float = 15.0,
) -> FiberProbeResult:
    """Detect whether a long-lived multi-eval / shared-AST session exists.

    Current AuraBackend is one short subprocess per eval. Without an explicit
    long-lived session API succeeding here, we keep
    ``shared_workspace_subprocess`` and ``fiber_live=false``.
    """
    if not aura_bin:
        return FiberProbeResult(
            available=False,
            session_model=SESSION_SHARED_SUBPROCESS,
            notes="no aura_bin; fiber session not probed",
            probed=False,
        )
    ok, err = probe_aura(aura_bin, timeout_s=min(10.0, timeout_s))
    if not ok:
        return FiberProbeResult(
            available=False,
            session_model=SESSION_SHARED_SUBPROCESS,
            notes=f"aura unhealthy; skip fiber probe: {err}",
            probed=True,
        )

    # Honest probe: try two sequential -e evals in one process via a tiny
    # program. Aura CLI today is still one-shot; success of two evals in one
    # invocation does NOT prove a fiber-hosted shared AST across host calls.
    # We only flip available if an explicit marker appears (future wire).
    env = os.environ.copy()
    env.setdefault("AURA_BIN", aura_bin)
    env.setdefault("AURA_PIPELINE_STRICT", "0")
    env.setdefault("AURA_SANDBOX", "off")
    program = (
        '; aura-build fiber session probe — two evals one process\n'
        '(display "AURA_BUILD_FIBER_PROBE ")(display (+ 1 1))(newline)\n'
        '(display "AURA_BUILD_FIBER_PROBE ")(display (+ 2 2))(newline)\n'
    )
    import subprocess
    import tempfile

    try:
        with tempfile.TemporaryDirectory(prefix="aura-build-fiber-") as tmp:
            path = Path(tmp) / "fiber_probe.aura"
            path.write_text(program, encoding="utf-8")
            proc = subprocess.run(
                [aura_bin, str(path)],
                capture_output=True,
                text=True,
                timeout=timeout_s,
                env=env,
                check=False,
            )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return FiberProbeResult(
            available=False,
            session_model=SESSION_SHARED_SUBPROCESS,
            notes=f"fiber probe exec failed: {exc}",
            probed=True,
        )

    stdout = proc.stdout or ""
    hits = stdout.count("AURA_BUILD_FIBER_PROBE")
    # Marker AURA_BUILD_FIBER_SESSION_OK would mean a real long-lived API.
    if "AURA_BUILD_FIBER_SESSION_OK" in stdout and proc.returncode == 0:
        return FiberProbeResult(
            available=True,
            session_model=SESSION_LONG_LIVED_AURA,
            notes="explicit AURA_BUILD_FIBER_SESSION_OK from aura",
            probed=True,
        )
    return FiberProbeResult(
        available=False,
        session_model=SESSION_SHARED_SUBPROCESS,
        notes=(
            f"one-shot multi-eval in single process "
            f"(rc={proc.returncode}, probe_hits={hits}); "
            "no long-lived fiber session API — keep shared_workspace_subprocess"
        ),
        probed=True,
    )


def _default_aura_eval_fn(backend: AuraBackend) -> EvalFn:
    def _eval(cycle: int, wl: int) -> StormCycleResult:
        t0 = time.perf_counter()
        try:
            muts = backend.mutate_worldlines(f"storm-{cycle}", seed=cycle, n=1)
            got = backend.eval_worldline(muts[0], f"storm-{cycle}", cycle, wl)
        except AuraUnavailable as exc:
            elapsed = int((time.perf_counter() - t0) * 1000)
            return StormCycleResult(
                index=cycle,
                ok=False,
                elapsed_ms=elapsed,
                incr_valid=False,
                notes=f"AuraUnavailable: {exc}",
            )
        except Exception as exc:  # noqa: BLE001 — record; refuse proven
            elapsed = int((time.perf_counter() - t0) * 1000)
            return StormCycleResult(
                index=cycle,
                ok=False,
                elapsed_ms=elapsed,
                incr_valid=False,
                notes=f"eval error: {exc}",
            )
        elapsed = int((time.perf_counter() - t0) * 1000)
        ev = got.get("eval") or {}
        metrics = ev.get("metrics") or {}
        notes = str(ev.get("notes") or "")
        # Explicit signal only — wall-clock alone never proves incr.
        incr_valid = bool(
            metrics.get("incr_valid")
            or metrics.get("incr_proven")
            or (INCR_VALID_MARKER in notes)
        )
        return StormCycleResult(
            index=cycle,
            ok=bool(ev.get("passed")),
            elapsed_ms=elapsed,
            incr_valid=incr_valid,
            notes=notes,
            aura_value=metrics.get("aura_value"),
        )

    return _eval


def run_storm(
    *,
    cycles: int,
    worldline_pressure: int,
    eval_fn: EvalFn,
) -> list[StormCycleResult]:
    """Run N rapid mutate+eval cycles under concurrent worldline pressure.

    ``worldline_pressure`` workers may run in parallel within a cycle; results
    are flattened one StormCycleResult per (cycle, worker) pair using the
    cycle index (worker notes recorded in ``notes``).
    """
    if cycles < 1:
        raise ValueError("cycles must be >= 1")
    if worldline_pressure < 1:
        raise ValueError("worldline_pressure must be >= 1")

    results: list[StormCycleResult] = []
    for c in range(cycles):
        if worldline_pressure == 1:
            results.append(eval_fn(c, 0))
            continue
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=worldline_pressure
        ) as pool:
            futs = [
                pool.submit(eval_fn, c, w) for w in range(worldline_pressure)
            ]
            for fut in concurrent.futures.as_completed(futs):
                results.append(fut.result())
    return results


def prove_or_refuse(
    *,
    cycles: int = 8,
    worldline_pressure: int = 3,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
    timeout_s: float = 30.0,
    probe_fiber: bool = True,
    eval_fn: EvalFn | None = None,
    force_unhealthy: bool | None = None,
    unhealthy_reason: str | None = None,
) -> ProveIncrReport:
    """Measure storm-still-incr or refuse honestly.

    ``eval_fn`` / ``force_unhealthy`` exist for tests (simulated fail-closed and
    simulated storm without a real binary). Production callers leave them None.
    """
    report = ProveIncrReport(
        cycles_requested=cycles,
        worldline_pressure=worldline_pressure,
    )

    bin_path = aura_bin or resolve_aura_bin(None, aura_ref)

    if force_unhealthy is True:
        report.aura_bin = bin_path
        report.aura_healthy = False
        report.probe_error = unhealthy_reason or "forced_unhealthy"
        report.reason = classify_unhealthy_reason(
            report.probe_error, bin_path=bin_path
        )
        report.incr_proven = False
        report.measured = False
        report.session_model = SESSION_SHARED_SUBPROCESS
        report.fiber_live = False
        report.fiber_probe = FiberProbeResult(
            available=False,
            session_model=SESSION_SHARED_SUBPROCESS,
            notes="skipped: aura unhealthy (forced)",
            probed=False,
        ).to_dict()
        return report

    if eval_fn is None:
        if not bin_path:
            report.aura_healthy = False
            report.probe_error = "no aura binary resolved"
            report.reason = "aura_binary_missing"
            report.incr_proven = False
            report.measured = False
            report.fiber_probe = FiberProbeResult(
                available=False,
                session_model=SESSION_SHARED_SUBPROCESS,
                notes="no aura_bin",
                probed=False,
            ).to_dict()
            return report

        ok, err = probe_aura(bin_path, timeout_s=min(10.0, timeout_s))
        report.aura_bin = bin_path
        report.probe_error = err
        if not ok:
            report.aura_healthy = False
            report.reason = classify_unhealthy_reason(err, bin_path=bin_path)
            report.incr_proven = False
            report.measured = False
            report.fiber_probe = FiberProbeResult(
                available=False,
                session_model=SESSION_SHARED_SUBPROCESS,
                notes=f"skipped: {report.reason}",
                probed=True,
            ).to_dict()
            return report

        report.aura_healthy = True
        backend = AuraBackend(
            aura_bin=bin_path, aura_ref=aura_ref, timeout_s=timeout_s
        )
        try:
            backend.ensure_available()
        except AuraUnavailable as exc:
            report.aura_healthy = False
            report.probe_error = str(exc)
            report.reason = classify_unhealthy_reason(
                str(exc), bin_path=bin_path
            )
            report.incr_proven = False
            report.measured = False
            return report
        eval_fn = _default_aura_eval_fn(backend)
    else:
        # Injected eval path (tests): treat as "healthy enough to measure"
        # unless force_unhealthy already returned.
        report.aura_bin = bin_path
        report.aura_healthy = True

    if probe_fiber:
        fiber = probe_fiber_session(bin_path, timeout_s=min(15.0, timeout_s))
    else:
        fiber = FiberProbeResult(
            available=False,
            session_model=SESSION_SHARED_SUBPROCESS,
            notes="fiber probe skipped by caller",
            probed=False,
        )
    report.fiber_probe = fiber.to_dict()
    report.session_model = fiber.session_model
    report.fiber_live = bool(fiber.available)

    storm = run_storm(
        cycles=cycles,
        worldline_pressure=worldline_pressure,
        eval_fn=eval_fn,
    )
    report.storm = [s.to_dict() for s in storm]
    report.cycles_completed = len(storm)
    report.cycles_ok = sum(1 for s in storm if s.ok)
    report.cycles_incr_valid = sum(1 for s in storm if s.incr_valid)
    report.measured = True

    all_ok = report.cycles_ok == report.cycles_completed and report.cycles_completed > 0
    all_incr = (
        report.cycles_incr_valid == report.cycles_completed
        and report.cycles_completed > 0
    )

    if all_ok and all_incr:
        # Only path that may set incr_proven=true — explicit signal every cycle.
        report.incr_proven = True
        report.reason = "storm_still_incr_measured"
    elif all_ok and not all_incr:
        report.incr_proven = False
        report.reason = (
            "storm_cycles_ok_but_no_incr_valid_signal:"
            f"{report.cycles_incr_valid}/{report.cycles_completed} "
            "(refuse — wall-clock alone is not proof)"
        )
    else:
        report.incr_proven = False
        report.reason = (
            f"storm_cycles_failed:"
            f"{report.cycles_ok}/{report.cycles_completed} ok"
        )

    # Belt-and-suspenders: never claim fiber_live without fiber.available.
    if not fiber.available:
        report.fiber_live = False
        if report.session_model == SESSION_LONG_LIVED_AURA:
            report.session_model = SESSION_SHARED_SUBPROCESS

    return report


def write_report(
    report: ProveIncrReport,
    path: Path | str | None = None,
    *,
    root: Path | str | None = None,
) -> Path:
    """Persist report JSON; returns path written."""
    out = Path(path) if path is not None else default_report_path(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out


def load_latest_report(
    root: Path | str | None = None,
    path: Path | str | None = None,
) -> ProveIncrReport | None:
    """Load last prove-incr report if present."""
    p = Path(path) if path is not None else default_report_path(root)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return ProveIncrReport(
        schema_version=str(data.get("schema_version") or REPORT_SCHEMA),
        ts=str(data.get("ts") or ""),
        incr_proven=bool(data.get("incr_proven", False)),
        reason=str(data.get("reason") or ""),
        measured=bool(data.get("measured", False)),
        aura_healthy=bool(data.get("aura_healthy", False)),
        aura_bin=data.get("aura_bin"),
        probe_error=data.get("probe_error"),
        session_model=str(
            data.get("session_model") or SESSION_SHARED_SUBPROCESS
        ),
        fiber_live=bool(data.get("fiber_live", False)),
        fiber_probe=dict(data.get("fiber_probe") or {}),
        cycles_requested=int(data.get("cycles_requested") or 0),
        cycles_completed=int(data.get("cycles_completed") or 0),
        cycles_ok=int(data.get("cycles_ok") or 0),
        cycles_incr_valid=int(data.get("cycles_incr_valid") or 0),
        worldline_pressure=int(data.get("worldline_pressure") or 0),
        storm=list(data.get("storm") or []),
        honesty=dict(data.get("honesty") or {}),
    )


def doctor_snapshot(
    *,
    root: Path | str | None = None,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
    run_probe: bool = True,
) -> dict[str, Any]:
    """Aggregate health + last prove-incr report for ``aura-build doctor``."""
    bin_path = aura_bin or resolve_aura_bin(None, aura_ref)
    probe_ok: bool | None = None
    probe_err: str | None = None
    if run_probe and bin_path:
        probe_ok, probe_err = probe_aura(bin_path)
    elif run_probe and not bin_path:
        probe_ok, probe_err = False, "no aura binary resolved"

    latest = load_latest_report(root=root)
    latest_dict = latest.to_dict() if latest else None

    incr_proven = bool(latest.incr_proven) if latest else False
    fiber_live = bool(latest.fiber_live) if latest else False
    session_model = (
        latest.session_model if latest else SESSION_SHARED_SUBPROCESS
    )

    return {
        "aura_bin": bin_path,
        "aura_probe_ok": probe_ok,
        "aura_probe_error": probe_err,
        "prove_incr_report_path": str(default_report_path(root)),
        "prove_incr_latest": latest_dict,
        "honesty": {
            "incr_proven": incr_proven,
            "fiber_live": fiber_live,
            "session_model": session_model,
            "l3_online": False,
            "note": (
                "incr_proven/fiber_live only true when last prove-incr "
                "measurement says so; unset report ⇒ false"
            ),
        },
        "tips": [
            "aura-build prove-incr",
            "aura-build prove-incr --json",
            "aura-build doctor --json",
            "docs/storm-still-incr.md",
        ],
    }


def env_flag_truthy(name: str, *, environ: dict[str, str] | None = None) -> bool:
    """True when env var is set to a common truthy token (1/true/yes/on)."""
    env = environ if environ is not None else os.environ
    raw = str(env.get(name, "")).strip().lower()
    return raw in ("1", "true", "yes", "on")


def attach_prove_metadata(
    *,
    root: Path | str | None = None,
    report: ProveIncrReport | None = None,
    use_doctor_fallback: bool = True,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build honesty fields for episode ``runtime`` (never invent true).

    Prefers the latest prove-incr report under ``root``. If missing and
    ``use_doctor_fallback``, uses a lightweight ``doctor_snapshot`` (no Aura
    probe) so trajectories still carry explicit refuse defaults.

    Env gates ``AURA_BUILD_INCR_VALID`` / ``AURA_BUILD_FIBER_SESSION_OK`` are
    **read-only**: if set while the harness/report says false, fields stay
    false and ``env_notes`` records ``env_ignored_unproven`` /
    ``env_fiber_ignored_unproven``. They never alone set ``incr_proven`` or
    ``fiber_live`` true.
    """
    env = environ if environ is not None else os.environ
    source = "none"
    reason = "no_prove_incr_report"
    incr_proven = False
    measured = False
    fiber_live = False
    session_model = SESSION_SHARED_SUBPROCESS
    report_path = str(default_report_path(root))
    loaded = report

    if loaded is None:
        loaded = load_latest_report(root=root)

    if loaded is not None:
        source = "prove-incr-latest"
        incr_proven = bool(loaded.incr_proven)
        measured = bool(loaded.measured)
        fiber_live = bool(loaded.fiber_live)
        session_model = str(loaded.session_model or SESSION_SHARED_SUBPROCESS)
        reason = str(loaded.reason or "unknown")
        # Belt: never claim fiber_live without available/session proof.
        if not fiber_live and session_model == SESSION_LONG_LIVED_AURA:
            session_model = SESSION_SHARED_SUBPROCESS
    elif use_doctor_fallback:
        snap = doctor_snapshot(root=root, run_probe=False)
        source = "doctor_snapshot"
        h = snap.get("honesty") or {}
        incr_proven = bool(h.get("incr_proven", False))
        fiber_live = bool(h.get("fiber_live", False))
        session_model = str(h.get("session_model") or SESSION_SHARED_SUBPROCESS)
        measured = False
        reason = "no_prove_incr_report"
        latest = snap.get("prove_incr_latest")
        if isinstance(latest, dict):
            # Should not happen when load_latest_report returned None, but
            # keep fail-closed defaults if doctor somehow saw stale data.
            incr_proven = bool(latest.get("incr_proven", False))
            measured = bool(latest.get("measured", False))
            fiber_live = bool(latest.get("fiber_live", False))
            session_model = str(
                latest.get("session_model") or SESSION_SHARED_SUBPROCESS
            )
            reason = str(latest.get("reason") or reason)
            source = "doctor_snapshot+report"

    env_notes: list[str] = []
    if env_flag_truthy(ENV_INCR_VALID, environ=env):
        if incr_proven and measured:
            env_notes.append("env_agrees_proven")
        else:
            # Prefer keep false + note — env alone cannot elevate.
            incr_proven = False
            env_notes.append("env_ignored_unproven")
    if env_flag_truthy(ENV_FIBER_SESSION_OK, environ=env):
        if fiber_live:
            env_notes.append("env_fiber_agrees")
        else:
            fiber_live = False
            if session_model == SESSION_LONG_LIVED_AURA:
                session_model = SESSION_SHARED_SUBPROCESS
            env_notes.append("env_fiber_ignored_unproven")

    # Final fail-closed clamps.
    if not measured:
        incr_proven = False
    if not fiber_live and session_model == SESSION_LONG_LIVED_AURA:
        session_model = SESSION_SHARED_SUBPROCESS

    return {
        "incr_proven": bool(incr_proven),
        "measured": bool(measured),
        "fiber_live": bool(fiber_live),
        "session_model": session_model,
        "reason": reason,
        "source": source,
        "report_path": report_path,
        "env_notes": env_notes,
        "attached": True,
        "env_gates": {
            ENV_INCR_VALID: env_flag_truthy(ENV_INCR_VALID, environ=env),
            ENV_FIBER_SESSION_OK: env_flag_truthy(
                ENV_FIBER_SESSION_OK, environ=env
            ),
        },
    }


def merge_prove_into_runtime(
    runtime: dict[str, Any],
    fields: dict[str, Any],
) -> dict[str, Any]:
    """Merge attach fields into episode ``runtime`` (mutates and returns it).

    Top-level honesty mirrors: ``incr_proven``, ``measured``, ``fiber_live``.
    ``session_model`` elevates to long-lived only when ``fiber_live``; otherwise
    keeps an existing workspace session_model or sets the refuse default.
    Nested ``runtime.prove_incr`` holds the full attach block including
    ``reason``.
    """
    runtime["incr_proven"] = bool(fields.get("incr_proven", False))
    runtime["measured"] = bool(fields.get("measured", False))
    runtime["fiber_live"] = bool(fields.get("fiber_live", False))
    runtime["prove_incr"] = dict(fields)

    want_session = str(fields.get("session_model") or SESSION_SHARED_SUBPROCESS)
    fiber_live = bool(fields.get("fiber_live", False))
    existing = runtime.get("session_model")
    if fiber_live and want_session == SESSION_LONG_LIVED_AURA:
        runtime["session_model"] = SESSION_LONG_LIVED_AURA
    elif existing is None:
        runtime["session_model"] = want_session
    elif existing == SESSION_LONG_LIVED_AURA and not fiber_live:
        runtime["session_model"] = SESSION_SHARED_SUBPROCESS
    # else: keep existing shared_workspace_subprocess (or other refuse model)

    return runtime
