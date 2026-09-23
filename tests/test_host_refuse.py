"""Host honesty: --help works; orch refuses without Aura / with FORCE_PYTHON."""

from __future__ import annotations

from aura_build.cli import build_parser, main
from aura_build.deprecated import KERNEL_TAG


def test_help_ok():
    p = build_parser()
    help_text = p.format_help()
    assert "aura-build" in help_text
    assert "run" in help_text


def test_force_python_refuses_acp(monkeypatch, tmp_path):
    monkeypatch.setenv("AURA_BUILD_FORCE_PYTHON", "1")
    rc = main(["acp", "status", "--harness-root", str(tmp_path)])
    assert rc == 2


def test_force_python_refuses_tui(monkeypatch, tmp_path):
    monkeypatch.setenv("AURA_BUILD_FORCE_PYTHON", "1")
    rc = main(["tui", "--harness-root", str(tmp_path)])
    assert rc == 2


def test_kernel_tag():
    assert KERNEL_TAG == "python_deprecated"
