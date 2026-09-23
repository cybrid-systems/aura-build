"""Post-M5 prove-incr: fail-closed path CI-green; never lie about incr_proven."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aura_build.prove_incr import (
    INCR_VALID_MARKER,
    StormCycleResult,
    classify_unhealthy_reason,
    doctor_snapshot,
    load_latest_report,
    prove_or_refuse,
    run_storm,
    write_report,
)
from aura_build.worldline import SESSION_SHARED_SUBPROCESS


def test_classify_glibcxx():
    assert (
        classify_unhealthy_reason(
            "version `GLIBCXX_3.4.35' not found", bin_path="/x/aura"
        )
        == "aura_glibcxx_mismatch"
    )


def test_classify_missing():
    assert classify_unhealthy_reason(None, bin_path=None) == "aura_binary_missing"


def test_fail_closed_forced_glibcxx(tmp_path: Path):
    report = prove_or_refuse(
        cycles=4,
        worldline_pressure=2,
        force_unhealthy=True,
        unhealthy_reason="GLIBCXX_3.4.35 not found (required by aura)",
        aura_bin="/fake/aura",
        probe_fiber=False,
    )
    assert report.incr_proven is False
    assert report.measured is False
    assert report.aura_healthy is False
    assert report.reason == "aura_glibcxx_mismatch"
    assert report.fiber_live is False
    assert report.session_model == SESSION_SHARED_SUBPROCESS
    path = write_report(report, root=tmp_path)
    assert path.is_file()
    loaded = load_latest_report(root=tmp_path)
    assert loaded is not None
    assert loaded.incr_proven is False
    assert loaded.reason == "aura_glibcxx_mismatch"


def test_fail_closed_missing_bin(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("AURA_BIN", raising=False)
    monkeypatch.setattr(
        "aura_build.prove_incr.resolve_aura_bin",
        lambda explicit=None, aura_ref=None: None,
    )
    report = prove_or_refuse(cycles=2, worldline_pressure=1, probe_fiber=False)
    assert report.incr_proven is False
    assert report.reason == "aura_binary_missing"
    assert report.measured is False
    write_report(report, root=tmp_path)


def test_storm_ok_without_incr_signal_refuses():
    def eval_fn(cycle: int, wl: int) -> StormCycleResult:
        return StormCycleResult(
            index=cycle,
            ok=True,
            elapsed_ms=1,
            incr_valid=False,
            notes="fast but no marker",
        )

    report = prove_or_refuse(
        cycles=3,
        worldline_pressure=2,
        eval_fn=eval_fn,
        probe_fiber=False,
        aura_bin="/injected",
    )
    assert report.measured is True
    assert report.aura_healthy is True
    assert report.cycles_ok == 6  # 3 cycles * 2 pressure
    assert report.cycles_incr_valid == 0
    assert report.incr_proven is False
    assert "no_incr_valid_signal" in report.reason


def test_storm_with_explicit_incr_signal_proves():
    def eval_fn(cycle: int, wl: int) -> StormCycleResult:
        return StormCycleResult(
            index=cycle,
            ok=True,
            elapsed_ms=1,
            incr_valid=True,
            notes=f"{INCR_VALID_MARKER} cycle={cycle}",
        )

    report = prove_or_refuse(
        cycles=2,
        worldline_pressure=1,
        eval_fn=eval_fn,
        probe_fiber=False,
        aura_bin="/injected",
    )
    assert report.incr_proven is True
    assert report.reason == "storm_still_incr_measured"
    assert report.cycles_incr_valid == 2


def test_storm_partial_failure_refuses():
    def eval_fn(cycle: int, wl: int) -> StormCycleResult:
        ok = cycle != 1
        return StormCycleResult(
            index=cycle,
            ok=ok,
            elapsed_ms=1,
            incr_valid=ok,
            notes="x",
        )

    report = prove_or_refuse(
        cycles=3,
        worldline_pressure=1,
        eval_fn=eval_fn,
        probe_fiber=False,
    )
    assert report.incr_proven is False
    assert report.reason.startswith("storm_cycles_failed:")


def test_run_storm_pressure():
    seen: list[tuple[int, int]] = []

    def eval_fn(cycle: int, wl: int) -> StormCycleResult:
        seen.append((cycle, wl))
        return StormCycleResult(cycle, True, 0, False)

    out = run_storm(cycles=2, worldline_pressure=3, eval_fn=eval_fn)
    assert len(out) == 6
    assert sorted(seen) == sorted((c, w) for c in range(2) for w in range(3))


def test_cli_prove_incr_fail_closed(monkeypatch, tmp_path: Path):
    from aura_build.cli import main

    monkeypatch.setattr(
        "aura_build.cli.prove_or_refuse",
        lambda **kwargs: prove_or_refuse(
            force_unhealthy=True,
            unhealthy_reason="GLIBCXX_3.4.35 not found",
            aura_bin="/x",
            probe_fiber=False,
            cycles=kwargs.get("cycles", 8),
            worldline_pressure=kwargs.get("worldline_pressure", 3),
        ),
    )
    out = tmp_path / "report.json"
    rc = main(
        [
            "prove-incr",
            "--cycles",
            "2",
            "--worldlines",
            "1",
            "--out",
            str(out),
            "--harness-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert rc == 0
    data = json.loads(out.read_text())
    assert data["incr_proven"] is False
    assert data["reason"] == "aura_glibcxx_mismatch"


def test_cli_doctor(tmp_path: Path, monkeypatch):
    from aura_build.cli import main

    report = prove_or_refuse(
        force_unhealthy=True,
        unhealthy_reason="GLIBCXX_3.4.35",
        aura_bin="/x",
        probe_fiber=False,
    )
    write_report(report, root=tmp_path)
    monkeypatch.setattr(
        "aura_build.cli.doctor_snapshot",
        lambda **kwargs: doctor_snapshot(
            root=tmp_path, run_probe=False, aura_bin=None
        ),
    )
    rc = main(["doctor", "--skip-probe", "--harness-root", str(tmp_path), "--json"])
    assert rc == 0


def test_doctor_snapshot_honesty_from_report(tmp_path: Path):
    report = prove_or_refuse(
        force_unhealthy=True,
        unhealthy_reason="missing",
        aura_bin=None,
        probe_fiber=False,
    )
    write_report(report, root=tmp_path)
    snap = doctor_snapshot(root=tmp_path, run_probe=False)
    assert snap["honesty"]["incr_proven"] is False
    assert snap["prove_incr_latest"]["reason"] in (
        "aura_binary_missing",
        "aura_glibcxx_mismatch",
        "aura_unhealthy",
    ) or snap["prove_incr_latest"]["reason"].startswith("aura_")
