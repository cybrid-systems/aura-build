"""Headless CLI — `aura-build run --prompt ...`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aura_build import __version__
from aura_build.orch import OrchConfig, run_episode
from aura_build.trajectory import TrajectoryWriter


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aura-build",
        description="Dev-time room on the Aura FlatAST floor (M0 stub).",
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
        "--json",
        action="store_true",
        help="print full episode JSON to stdout",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "run":
        cfg = OrchConfig(n_worldlines=args.worldlines, seed=args.seed, mode="simulated")
        result = run_episode(args.prompt, cfg)
        writer = TrajectoryWriter(args.out)
        path = writer.append(result.episode)
        if args.json:
            print(json.dumps(result.episode, ensure_ascii=False, indent=2))
        else:
            sel = result.selected
            print(
                f"selected={sel.id} fitness={sel.eval['fitness']} "
                f"episode={result.episode['episode_id']} wrote={path}"
            )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
