"""Headless CLI — `aura-build run --prompt ...`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aura_build import __version__
from aura_build.orch import AuraUnavailable, OrchConfig, run_episode
from aura_build.trajectory import TrajectoryWriter


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aura-build",
        description="Dev-time room on the Aura FlatAST floor (M1 runtime backends).",
    )
    p.add_argument("--version", action="version", version=f"aura-build {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="scout→mutate→eval→select-best episode")
    run_p.add_argument("--prompt", required=True, help="task prompt")
    run_p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="trajectory JSONL path (default: trajectories/episodes.jsonl)",
    )
    run_p.add_argument("--seed", type=int, default=None, help="deterministic seed")
    run_p.add_argument(
        "--worldlines",
        type=int,
        default=3,
        help="number of candidate worldlines (default 3)",
    )
    run_p.add_argument(
        "--mode",
        choices=("simulated", "aura", "auto"),
        default="simulated",
        help="runtime backend: simulated (default), aura (fail if missing), "
        "auto (aura if probe ok else simulated; trajectory records actual mode)",
    )
    run_p.add_argument(
        "--aura-bin",
        default=None,
        help="path to aura binary (else AURA_BIN / discovery)",
    )
    run_p.add_argument(
        "--aura-ref",
        default=None,
        help="aura checkout path for lib/ + build/aura discovery",
    )
    run_p.add_argument(
        "--json",
        action="store_true",
        help="print full episode JSON to stdout",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """CLI entry used by tests; returns process exit code."""
    args = build_parser().parse_args(argv)
    if args.cmd == "run":
        cfg = OrchConfig(
            n_worldlines=args.worldlines,
            seed=args.seed,
            mode=args.mode,
            aura_bin=args.aura_bin,
            aura_ref=args.aura_ref,
        )
        try:
            result = run_episode(args.prompt, cfg)
        except AuraUnavailable as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        writer = TrajectoryWriter(args.out)
        path = writer.append(result.episode)
        if args.json:
            print(json.dumps(result.episode, ensure_ascii=False, indent=2))
        else:
            sel = result.selected
            mode = result.episode["runtime"]["mode"]
            print(
                f"selected={sel.id} fitness={sel.eval['fitness']} "
                f"mode={mode} episode={result.episode['episode_id']} wrote={path}"
            )
        return 0
    return 2


def console_main() -> None:
    """setuptools console_scripts entry — propagates exit code."""
    raise SystemExit(main())


if __name__ == "__main__":
    console_main()
