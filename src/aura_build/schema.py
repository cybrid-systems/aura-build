"""Minimal trajectory.v0 gate for host smoke / refuse messages.

Product validation lives in ``aura/export.aura`` (``episode-ok?``). Python keeps
only what host tests and smoke need to assert honesty flags on written episodes.
"""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "trajectory.v0"

_REQUIRED_TOP = (
    "schema_version",
    "episode_id",
    "ts_start",
    "ts_end",
    "prompt",
    "runtime",
    "harness",
    "worldlines",
    "selected_id",
)


class SchemaError(ValueError):
    """Episode failed trajectory.v0 validation."""


def validate_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Light host check; raise SchemaError on failure."""
    if not isinstance(episode, dict):
        raise SchemaError("episode must be a dict")
    for key in _REQUIRED_TOP:
        if key not in episode:
            raise SchemaError(f"missing required field: {key}")
    if episode["schema_version"] != SCHEMA_VERSION:
        raise SchemaError(
            f"unsupported schema_version: {episode['schema_version']!r} "
            f"(expected {SCHEMA_VERSION!r})"
        )
    runtime = episode["runtime"]
    if not isinstance(runtime, dict) or "mode" not in runtime:
        raise SchemaError("runtime.mode is required")
    if runtime["mode"] not in ("simulated", "aura"):
        raise SchemaError(f"runtime.mode must be simulated|aura, got {runtime['mode']!r}")
    harness = episode["harness"]
    if not isinstance(harness, dict) or "l3_online" not in harness:
        raise SchemaError("harness.l3_online is required")
    if not isinstance(harness["l3_online"], bool):
        raise SchemaError("harness.l3_online must be bool")
    worldlines = episode["worldlines"]
    if not isinstance(worldlines, list) or len(worldlines) < 1:
        raise SchemaError("worldlines must be a non-empty list")
    ids: set[str] = set()
    for i, wl in enumerate(worldlines):
        if not isinstance(wl, dict) or "id" not in wl:
            raise SchemaError(f"worldlines[{i}].id is required")
        wid = wl["id"]
        if wid in ids:
            raise SchemaError(f"duplicate worldline id: {wid!r}")
        ids.add(wid)
        ev = wl.get("eval")
        if not isinstance(ev, dict) or "fitness" not in ev:
            raise SchemaError(f"worldlines[{i}].eval.fitness is required")
        if not isinstance(ev["fitness"], (int, float)):
            raise SchemaError(f"worldlines[{i}].eval.fitness must be numeric")
    if episode["selected_id"] not in ids:
        raise SchemaError(f"selected_id {episode['selected_id']!r} not in worldlines")
    return episode
