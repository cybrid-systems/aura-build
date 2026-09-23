"""Host prove refuse report — no Python storm orch."""

from __future__ import annotations

import json
from pathlib import Path

from aura_build.cli import main
from aura_build.deprecated import KERNEL_TAG
from aura_build.prove_incr import doctor_snapshot, write_refuse_report


def test_write_refuse_report(tmp_path: Path):
    report, path = write_refuse_report(
        reason="aura_binary_missing",
        root=tmp_path,
        cycles=2,
        worldlines=1,
    )
    assert path.is_file()
    data = json.loads(path.read_text())
    assert data["incr_proven"] is False
    assert data["measured"] is False
    assert data["fiber_live"] is False
    assert data["kernel"] == KERNEL_TAG
    assert report.incr_proven is False


def test_cli_prove_missing_bin_refuse(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("AURA_BIN", raising=False)
    monkeypatch.setenv("AURA_BUILD_FORCE_PYTHON", "1")  # deprecated: forces refuse path
    rc = main(
        [
            "prove-incr",
            "--cycles",
            "2",
            "--worldlines",
            "1",
            "--aura-bin",
            "/nonexistent/aura-missing",
            "--no-fiber-probe",
            "--harness-root",
            str(tmp_path),
            "--out",
            str(tmp_path / "prove-incr-latest.json"),
        ]
    )
    assert rc == 0
    data = json.loads((tmp_path / "prove-incr-latest.json").read_text())
    assert data["incr_proven"] is False
    assert data["measured"] is False
    assert data["fiber_live"] is False
    assert data.get("session_model") == "shared_workspace_subprocess"
    assert data.get("kernel") == KERNEL_TAG


def test_doctor_skip_probe(tmp_path: Path):
    write_refuse_report(root=tmp_path, reason="fixture")
    snap = doctor_snapshot(root=tmp_path, run_probe=False)
    assert snap["honesty"]["incr_proven"] is False
    assert snap["honesty"]["fiber_live"] is False
    assert snap["prove_incr_latest"]["reason"] == "fixture"


def test_cli_run_refuses_without_aura(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AURA_BUILD_FORCE_PYTHON", "1")
    rc = main(
        [
            "run",
            "--prompt",
            "no orch",
            "--mode",
            "simulated",
            "--harness-root",
            str(tmp_path),
        ]
    )
    assert rc == 2
