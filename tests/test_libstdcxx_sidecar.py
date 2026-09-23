"""GCC16 libstdc++ sidecar discovery for host GLIBCXX dogfood."""

from __future__ import annotations

from pathlib import Path

from aura_build.runtime import (
    aura_subprocess_env,
    resolve_libstdcxx_dir,
)


def test_resolve_explicit_env(tmp_path: Path, monkeypatch):
    lib = tmp_path / "gcc16"
    lib.mkdir()
    (lib / "libstdc++.so.6").write_bytes(b"fake")
    monkeypatch.setenv("AURA_LIBSTDCXX_DIR", str(lib))
    assert resolve_libstdcxx_dir(None) == str(lib.resolve())


def test_resolve_missing_returns_none(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("AURA_LIBSTDCXX_DIR", raising=False)
    # Point env at empty dir → None (no so)
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("AURA_LIBSTDCXX_DIR", str(empty))
    assert resolve_libstdcxx_dir(None) is None


def test_resolve_sibling_of_aura_bin(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("AURA_LIBSTDCXX_DIR", raising=False)
    deps = tmp_path / ".deps"
    aura_root = deps / "aura"
    build = aura_root / "build"
    build.mkdir(parents=True)
    bin_path = build / "aura"
    bin_path.write_text("#!/bin/sh\n", encoding="utf-8")
    bin_path.chmod(0o755)
    side = deps / "gcc16-libstdcxx"
    side.mkdir()
    (side / "libstdc++.so.6").write_bytes(b"fake")
    got = resolve_libstdcxx_dir(str(bin_path), environ={})
    assert got == str(side.resolve())


def test_aura_subprocess_env_prepends_ld_library_path(tmp_path: Path, monkeypatch):
    lib = tmp_path / "gcc16"
    lib.mkdir()
    (lib / "libstdc++.so.6").write_bytes(b"fake")
    monkeypatch.setenv("AURA_LIBSTDCXX_DIR", str(lib))
    monkeypatch.setenv("LD_LIBRARY_PATH", "/already/there")
    env = aura_subprocess_env(str(tmp_path / "aura"))
    assert env["LD_LIBRARY_PATH"].startswith(str(lib.resolve()))
    assert "/already/there" in env["LD_LIBRARY_PATH"]
    assert env["AURA_SANDBOX"] == "off"
