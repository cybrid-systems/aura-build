"""Tiny host JSONL helper for tests/fixtures (product write is aura/traj.aura)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aura_build.schema import validate_episode

DEFAULT_DIR = Path("trajectories")


class TrajectoryWriter:
    """Append validated episodes to JSONL (host test helper only)."""

    def __init__(self, path: Path | str | None = None) -> None:
        if path is None:
            path = DEFAULT_DIR / "episodes.jsonl"
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, episode: dict[str, Any]) -> Path:
        validate_episode(episode)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(episode, ensure_ascii=False, sort_keys=True) + "\n")
        return self.path

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                ep = json.loads(line)
                validate_episode(ep)
                out.append(ep)
        return out
