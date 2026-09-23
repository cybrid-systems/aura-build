"""Thin Parquet adapter for Aura-exported trajectory JSON.

Product JSON export + redaction + trajectory.v0 gate live in ``aura/export.aura``.
This module only converts an already-written JSON array (or in-memory episodes)
to Parquet when pandas+pyarrow are installed — no redaction, no schema product
logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "episodes_from_json_array",
    "write_parquet",
]


def episodes_from_json_array(path: Path | str) -> list[dict[str, Any]]:
    """Load a JSON array of episodes written by the Aura export kernel."""
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        return []
    data = json.loads(text)
    if not isinstance(data, list):
        raise TypeError(f"expected JSON array at {path}")
    return [ep for ep in data if isinstance(ep, dict)]


def write_parquet(
    episodes: list[dict[str, Any]], path: Path | str
) -> tuple[Path | None, str | None]:
    """Write Parquet when pandas+pyarrow available; else (None, reason)."""
    out = Path(path)
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        return None, (
            "Parquet skipped: pandas not installed "
            "(optional: pip install 'aura-build[export]' or pandas+pyarrow)"
        )
    try:
        import pyarrow  # noqa: F401  # type: ignore
    except ImportError:
        return None, (
            "Parquet skipped: pyarrow not installed "
            "(optional: pip install 'aura-build[export]' or pandas+pyarrow)"
        )

    rows: list[dict[str, Any]] = []
    for ep in episodes:
        wl = ep.get("worldlines") or []
        selected = next(
            (w for w in wl if w.get("id") == ep.get("selected_id")), None
        )
        fitness = None
        if isinstance(selected, dict):
            ev = selected.get("eval") or {}
            fitness = ev.get("fitness")
        harness = ep.get("harness") or {}
        runtime = ep.get("runtime") or {}
        privacy = ep.get("privacy") or {}
        rows.append(
            {
                "episode_id": ep.get("episode_id"),
                "schema_version": ep.get("schema_version"),
                "ts_start": ep.get("ts_start"),
                "ts_end": ep.get("ts_end"),
                "prompt": ep.get("prompt"),
                "selected_id": ep.get("selected_id"),
                "selection_reason": ep.get("selection_reason"),
                "selected_fitness": fitness,
                "runtime_mode": runtime.get("mode"),
                "incr_proven": bool(runtime.get("incr_proven", False)),
                "l1_strategy_id": harness.get("l1_strategy_id"),
                "l2_weights_id": harness.get("l2_weights_id"),
                "l3_online": bool(harness.get("l3_online", False)),
                "harness_mid": harness.get("mid"),
                "harness_outcome": harness.get("outcome"),
                "n_worldlines": len(wl),
                "n_discarded": len(ep.get("discarded") or []),
                "privacy_redacted": bool(privacy.get("redacted", False)),
                "retention_class": privacy.get("retention_class"),
                "episode_json": json.dumps(ep, ensure_ascii=False, sort_keys=True),
            }
        )
    df = pd.DataFrame(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return out, None
