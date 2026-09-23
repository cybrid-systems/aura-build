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
        description=(
            "Dev-time room on the Aura FlatAST floor "
            "(M2: worldline workspace + aura-repo profile)."
        ),
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
        help="aura checkout path (also used for aura-repo profile detection)",
    )
    run_p.add_argument(
        "--profile",
        choices=("aura-repo",),
        default=None,
        help="optional dogfood profile (aura-repo: shared workspace + build.py fitness)",
    )
    run_p.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="shared worldline workspace dir (default: ephemeral temp)",
    )
    run_p.add_argument(
        "--keep-workspace",
        action="store_true",
        help="retain workspace dir after episode (implies useful with --workspace)",
    )
    run_p.add_argument(
        "--no-live-build",
        action="store_true",
        help="aura-repo: skip build.py hook; simulated fitness only",
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
            profile=args.profile,
            workspace_dir=args.workspace,
            keep_workspace=args.keep_workspace,
            try_live_build=not args.no_live_build,
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
            prof = result.episode["runtime"].get("profile")
            prof_s = prof.get("id") if isinstance(prof, dict) else (args.profile or "-")
            discarded_n = len(result.episode.get("discarded") or [])
            print(
                f"selected={sel.id} fitness={sel.eval['fitness']} "
                f"mode={mode} profile={prof_s} discarded={discarded_n} "
                f"incr_proven={result.episode['runtime'].get('incr_proven', False)} "
                f"episode={result.episode['episode_id']} wrote={path}"
            )
        return 0
    return 2


def console_main() -> None:
    """setuptools console_scripts entry — propagates exit code."""
    raise SystemExit(main())


if __name__ == "__main__":
    console_main()
