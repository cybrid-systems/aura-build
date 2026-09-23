"""M1 RuntimeBackend: mode honesty, aura fail-closed, select-best intact."""

from __future__ import annotations

from typing import Any

import pytest

from aura_build.orch import OrchConfig, run_episode, select_best, Worldline
from aura_build.runtime import (
    AuraUnavailable,
    SimulatedBackend,
    resolve_backend,
)
from aura_build.schema import validate_episode


class _FakeAuraBackend:
    """Minimal RuntimeBackend that reports mode=aura without a real binary."""

    mode = "aura"
    aura_ref = "/fake/aura-ref"

    def mutate_worldlines(self, prompt: str, seed: int, n: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i in range(n):
            out.append(
                {
                    "id": f"wl-{i}",
                    "parent_id": None,
                    "mutations": [
                        {
                            "op": "aura_mutate_rebind",
                            "target_id": f"m1-cand:{i}",
                            "summary": f"fake rebind {i}",
                            "bump": i + 1,
                        }
                    ],
                }
            )
        return out

    def eval_worldline(
        self,
        wl: dict[str, Any],
        prompt: str,
        seed: int,
        index: int,
    ) -> dict[str, Any]:
        fitness = round(0.75 + 0.05 * (index % 4), 4)
        return {
            "id": wl["id"],
            "parent_id": wl.get("parent_id"),
            "mutations": list(wl.get("mutations") or []),
            "eval": {
                "fitness": fitness,
                "passed": True,
                "metrics": {
                    "tests_passed": 1,
                    "tests_total": 1,
                    "incr_compile_ms": 1,
                    "audit_ok": True,
                },
                "notes": "fake aura",
            },
        }


def test_simulated_mode_in_trajectory():
    result = run_episode("x", OrchConfig(seed=1, mode="simulated", n_worldlines=2))
    validate_episode(result.episode)
    assert result.episode["runtime"]["mode"] == "simulated"
    assert result.episode["runtime"]["requested_mode"] == "simulated"


def test_forced_simulated_via_resolve():
    b = resolve_backend("simulated")
    assert isinstance(b, SimulatedBackend)
    assert b.mode == "simulated"


def test_aura_mode_fail_closed_missing_bin(monkeypatch):
    monkeypatch.delenv("AURA_BIN", raising=False)
    monkeypatch.setattr(
        "aura_build.runtime.resolve_aura_bin",
        lambda explicit=None, aura_ref=None: None,
    )
    with pytest.raises(AuraUnavailable):
        resolve_backend("aura")


def test_auto_falls_back_to_simulated(monkeypatch):
    monkeypatch.delenv("AURA_BIN", raising=False)
    monkeypatch.setattr(
        "aura_build.runtime.resolve_aura_bin",
        lambda explicit=None, aura_ref=None: None,
    )
    b = resolve_backend("auto")
    assert b.mode == "simulated"
    result = run_episode("auto", OrchConfig(mode="auto", seed=2, n_worldlines=2))
    assert result.episode["runtime"]["mode"] == "simulated"
    assert result.episode["runtime"]["requested_mode"] == "auto"


def test_aura_backend_sets_mode_aura():
    result = run_episode(
        "live-ish",
        OrchConfig(mode="aura", seed=3, n_worldlines=3, backend=_FakeAuraBackend()),
    )
    validate_episode(result.episode)
    assert result.episode["runtime"]["mode"] == "aura"
    assert result.episode["runtime"]["aura_ref"] == "/fake/aura-ref"
    assert all(
        w["mutations"][0]["op"] == "aura_mutate_rebind"
        for w in result.episode["worldlines"]
    )
    assert result.selected.id in {w["id"] for w in result.episode["worldlines"]}


def test_select_best_still_works_with_aura_shaped_evals():
    wls = [
        Worldline("wl-0", None, [], {"fitness": 0.75, "passed": True}),
        Worldline("wl-1", None, [], {"fitness": 0.8, "passed": True}),
        Worldline("wl-2", None, [], {"fitness": 0.1, "passed": False}),
    ]
    best, reason = select_best(wls)
    assert best.id == "wl-1"
    assert reason == "max_fitness"


def test_cli_mode_flag(tmp_path):
    from aura_build.cli import main
    import json

    out = tmp_path / "ep.jsonl"
    rc = main(
        [
            "run",
            "--prompt",
            "cli mode",
            "--seed",
            "9",
            "--mode",
            "simulated",
            "--out",
            str(out),
            "--json",
        ]
    )
    assert rc == 0
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["runtime"]["mode"] == "simulated"


def test_cli_aura_missing_exits_nonzero(monkeypatch, tmp_path):
    from aura_build.cli import main

    monkeypatch.delenv("AURA_BIN", raising=False)
    monkeypatch.setattr(
        "aura_build.runtime.resolve_aura_bin",
        lambda explicit=None, aura_ref=None: None,
    )
    rc = main(
        [
            "run",
            "--prompt",
            "need aura",
            "--mode",
            "aura",
            "--out",
            str(tmp_path / "x.jsonl"),
        ]
    )
    assert rc == 2
