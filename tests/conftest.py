"""Isolate harness/prove roots from dogfood `.aura-build/` during pytest.

A live `prove-incr` on the box may leave `incr_proven=true` under the repo
`.aura-build/`. Tests that omit `harness_root` would otherwise attach that
report and spuriously fail honesty asserts. Redirect `default_root` to a
tmp path for the whole session.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_aura_build_root(tmp_path_factory, monkeypatch):
    root = tmp_path_factory.mktemp("aura-build-test-root") / ".aura-build"
    root.mkdir(parents=True, exist_ok=True)

    def _root(cwd=None):  # noqa: ANN001
        return root

    monkeypatch.setattr("aura_build.harness.default_root", _root)
    # prove_incr / orch import default_root by name — patch both call sites.
    monkeypatch.setattr("aura_build.prove_incr.default_root", _root)
    monkeypatch.setattr("aura_build.orch.default_root", _root)
    return root
