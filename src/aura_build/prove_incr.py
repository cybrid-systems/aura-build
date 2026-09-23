"""Host prove refuse report + doctor snapshot (no Python storm orch).

Product prove-incr lives in ``aura/prove.aura``. Without Aura, write an honest
fail-closed refuse report — never simulate incr_proven / fiber_live.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aura_build.deprecated import KERNEL_TAG
from aura_build.harness import default_root

__all__ = ["ProveReport", "doctor_snapshot", "write_refuse_report", "write_report"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProveReport:
    schema_version: str = "prove_incr.v0"
    incr_proven: bool = False
    measured: bool = False
    fiber_live: bool = False
    aura_healthy: bool = False
    session_model: str = "shared_workspace_subprocess"
    reason: str = "aura_binary_missing"
    ts: str = field(default_factory=_utc_now)
    cycles_ok: int = 0
    cycles_completed: int = 0
    cycles_incr_valid: int = 0
    kernel: str = KERNEL_TAG

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write_report(
    report: ProveReport | dict[str, Any],
    path: Path | str | None = None,
    root: Path | str | None = None,
) -> Path:
    if path is not None:
        out = Path(path)
    else:
        base = Path(root) if root is not None else default_root()
        out = base / "prove-incr-latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict() if isinstance(report, ProveReport) else dict(report)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def write_refuse_report(
    *,
    reason: str = "aura_binary_missing",
    path: Path | str | None = None,
    root: Path | str | None = None,
    cycles: int = 0,
    worldlines: int = 0,
) -> tuple[ProveReport, Path]:
    """Honest fail-closed refuse — no Python storm loop."""
    report = ProveReport(reason=reason, kernel=KERNEL_TAG)
    payload = report.to_dict()
    payload["requested_cycles"] = int(cycles)
    payload["requested_worldlines"] = int(worldlines)
    return report, write_report(payload, path=path, root=root)


def doctor_snapshot(
    root: Path | str | None = None,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
    run_probe: bool = True,
) -> dict[str, Any]:
    """Cheap host doctor: paths + last report. Optional probe via runtime."""
    from aura_build.runtime import probe_aura, resolve_aura_bin

    base = Path(root) if root else default_root()
    report_path = base / "prove-incr-latest.json"
    latest = None
    if report_path.is_file():
        try:
            latest = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            latest = None
    bin_path = resolve_aura_bin(aura_bin, aura_ref)
    probe_ok = False
    probe_err = None
    if run_probe and bin_path:
        probe_ok, probe_err = probe_aura(bin_path)
    elif not bin_path:
        probe_err = "aura_binary_missing"
    honesty = {
        "incr_proven": bool(latest.get("incr_proven")) if isinstance(latest, dict) else False,
        "fiber_live": bool(latest.get("fiber_live")) if isinstance(latest, dict) else False,
        "session_model": (
            latest.get("session_model", "shared_workspace_subprocess")
            if isinstance(latest, dict)
            else "shared_workspace_subprocess"
        ),
        "l3_online": False,
        "kernel": "aura" if probe_ok else KERNEL_TAG,
    }
    return {
        "aura_bin": bin_path,
        "aura_probe_ok": probe_ok,
        "aura_probe_error": probe_err,
        "prove_incr_report_path": str(report_path),
        "prove_incr_latest": latest,
        "honesty": honesty,
        "tips": [
            "Product prove-incr is aura/prove.aura — set AURA_BIN",
            "Never invent incr_proven / fiber_live",
        ],
        "kernel": honesty["kernel"],
    }
