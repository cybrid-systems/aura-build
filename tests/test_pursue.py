"""pursue CLI surface + optional Aura kernel smoke."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from aura_build.cli_parser import build_parser
from aura_build.kernel import kernel_available, try_invoke_aura
from aura_build.runtime import resolve_aura_bin
from aura_build.serve_session import stop_session

def resolve_aura_bin_safe() -> bool:
    return bool(resolve_aura_bin(None))


def test_pursue_parser_flags() -> None:
    p = build_parser()
    args = p.parse_args(
        [
            "pursue",
            "--goal",
            "demo",
            "--max-rounds",
            "2",
            "--worldlines",
            "2",
            "--min-fitness",
            "0.5",
            "--mode",
            "simulated",
            "--json",
        ]
    )
    assert args.cmd == "pursue"
    assert args.goal == "demo"
    assert args.max_rounds == 2
    assert args.worldlines == 2
    assert args.min_fitness == 0.5
    assert args.mode == "simulated"
    assert args.with_llm is False
    assert args.harness_mutate is False
    assert args.prefer_session is True
    assert args.force_kernel is False


@pytest.mark.skipif(not kernel_available()[0], reason="Aura binary/kernel unavailable")
def test_pursue_kernel_short(tmp_path: Path) -> None:
    out = tmp_path / "pursue.jsonl"
    root = tmp_path / "harness"
    root.mkdir()
    kr = try_invoke_aura(
        "pursue",
        {
            "AURA_BUILD_GOAL": "pytest pursue smoke",
            "AURA_BUILD_PROMPT": "pytest pursue smoke",
            "AURA_BUILD_MAX_ROUNDS": "1",
            "AURA_BUILD_WORLDLINES": "2",
            "AURA_BUILD_MIN_FITNESS": "0.99",
            "AURA_BUILD_PREDICATE": "fitness_ge:0.99",
            "AURA_BUILD_MODE": "simulated",
            "AURA_BUILD_OUT": str(out),
            "AURA_BUILD_LLM_ASSIST": "off",
            "AURA_BUILD_PURSUE_HARNESS_MUTATE": "0",
            "AURA_BUILD_ATTACH_PROVE": "1",
            "AURA_BUILD_SEED": "1",
        },
        harness_root=root,
        timeout_s=180.0,
    )
    assert kr is not None
    assert kr.response.get("cmd") == "pursue"
    assert "worldline_backend" in kr.response
    assert "stop_reason" in kr.response
    assert kr.response.get("kernel") == "aura"
    # Never invent fiber_graph without fiber_live
    backend = kr.response.get("worldline_backend")
    fiber = kr.response.get("fiber_live")
    if backend == "fiber_graph":
        assert fiber is True
    assert out.is_file() or kr.response.get("ok") is False


@pytest.mark.skipif(not resolve_aura_bin_safe(), reason="Aura binary unavailable")
def test_pursue_cli_prefer_session(tmp_path: Path) -> None:
    from aura_build.cli import main

    out = tmp_path / "pursue.jsonl"
    code = main(
        [
            "pursue",
            "--goal",
            "emit GREET=aura",
            "--min-fitness",
            "0.8",
            "--max-rounds",
            "2",
            "--worldlines",
            "3",
            "--seed",
            "3",
            "--out",
            str(out),
            "--json",
            "--harness-root",
            str(tmp_path),
        ]
    )
    assert code == 0
    assert out.is_file()
    ep = json.loads(out.read_text().splitlines()[0])
    assert ep["runtime"]["session_model"] == "serve"
    assert ep["runtime"]["worldline_backend"] == "serve_mutate_rebind"
    assert ep["runtime"]["dogfood"]["cold_spawns"] == 0
    stop_session(harness_root=tmp_path)
