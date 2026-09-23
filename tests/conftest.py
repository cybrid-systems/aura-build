"""Isolate harness roots from dogfood `.aura-build/` during pytest."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_aura_build_root(tmp_path_factory, monkeypatch):
    root = tmp_path_factory.mktemp("aura-build-test-root") / ".aura-build"
    root.mkdir(parents=True, exist_ok=True)

    def _root(cwd=None):  # noqa: ANN001
        return root

    monkeypatch.setattr("aura_build.harness.default_root", _root)
    monkeypatch.setattr("aura_build.prove_incr.default_root", _root)
    return root
