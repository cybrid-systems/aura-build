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

__all__ = [
    "ProveReport",
    "cli_refuse_prove",
    "doctor_snapshot",
    "format_doctor_text",
    "write_refuse_report",
    "write_report",
]


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


def cli_refuse_prove(
    *,
    reason_hint: str | None = None,
    aura_bin: str | None = None,
    aura_ref: str | None = None,
    out: Path | str | None = None,
    root: Path | str | None = None,
    cycles: int = 0,
    worldlines: int = 0,
    as_json: bool = False,
) -> int:
    """Honest refuse report path when Aura kernel is unavailable. Exit 0."""
    from aura_build.kernel import kernel_available

    reason = reason_hint or "aura_binary_missing"
    ok, _bin, err = kernel_available(aura_bin, aura_ref)
    if err:
        reason = err if "missing" in (err or "") else (err or reason)
        if not ok and err and "GLIBCXX" in err:
            reason = "aura_glibcxx_mismatch"
        elif not ok and err:
            reason = "aura_unhealthy"
    report, path = write_refuse_report(
        reason=reason, path=out, root=root, cycles=cycles, worldlines=worldlines
    )
    payload = report.to_dict()
    payload["report_path"] = str(path)
    payload["kernel"] = KERNEL_TAG
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"incr_proven={report.incr_proven} measured={report.measured} "
            f"aura_healthy={report.aura_healthy} reason={report.reason} "
            f"session_model={report.session_model} fiber_live={report.fiber_live} "
            f"kernel={KERNEL_TAG} report={path}"
        )
    return 0


def format_doctor_text(snap: dict[str, Any]) -> str:
    h = snap["honesty"]
    lines = [
        "aura-build doctor",
        f"  aura_bin        = {snap.get('aura_bin') or '-'}",
        f"  aura_probe_ok   = {snap.get('aura_probe_ok')}",
    ]
    err = snap.get("aura_probe_error")
    if err:
        lines.append(f"  aura_probe_error= {str(err)[:200]}")
    lines.append(f"  prove_report    = {snap.get('prove_incr_report_path')}")
    latest = snap.get("prove_incr_latest")
    if latest:
        lines.append(
            f"  last_prove      = incr_proven={latest.get('incr_proven')} "
            f"reason={latest.get('reason')} measured={latest.get('measured')}"
        )
    else:
        lines.append("  last_prove      = (none — run aura-build prove-incr)")
    lines.append(
        f"  honesty         = incr_proven={h.get('incr_proven')} "
        f"fiber_live={h.get('fiber_live')} "
        f"session_model={h.get('session_model')} "
        f"l3_online={h.get('l3_online')} kernel={snap.get('kernel')}"
    )
    lines.append("  tips: " + " | ".join(snap.get("tips") or []))
    return "\n".join(lines)
