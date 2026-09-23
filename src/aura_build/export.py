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
    "complete_export_cli",
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


def complete_export_cli(
    *,
    out_json: Path,
    cwd: Path,
    include_raw: bool,
    no_parquet: bool,
    parquet_arg: Path | None,
    as_json: bool,
    result_meta: dict[str, Any],
    print_kernel_stdout: str | None = None,
) -> int:
    """Parquet adapter + optional JSON summary after Aura export kernel.

    ``print_kernel_stdout`` is cleaned kernel text to emit when not ``as_json``.
    """
    import sys

    if print_kernel_stdout and not as_json:
        print(print_kernel_stdout)

    parquet_path = None
    parquet_written = False
    parquet_skip_reason = result_meta.get("parquet_skip_reason")
    if not no_parquet:
        try:
            episodes = episodes_from_json_array(out_json)
        except (OSError, json.JSONDecodeError, TypeError):
            episodes = []
        pq = Path(parquet_arg) if parquet_arg is not None else out_json.with_suffix(".parquet")
        if not pq.is_absolute():
            pq = cwd / pq
        parquet_path, parquet_skip_reason = write_parquet(episodes, pq)
        parquet_written = parquet_path is not None
        if parquet_written and not as_json:
            print(f"parquet={parquet_path}")
        elif parquet_skip_reason and not as_json:
            print(parquet_skip_reason, file=sys.stderr)

    if as_json:
        payload = {
            "json": str(out_json),
            "parquet": str(parquet_path) if parquet_path else None,
            "files_read": result_meta.get("files_read", 0),
            "episodes_exported": result_meta.get("episodes_exported", 0),
            "episodes_skipped_invalid": result_meta.get("episodes_skipped_invalid", 0),
            "redacted": result_meta.get("redacted", not include_raw),
            "parquet_written": parquet_written,
            "parquet_skip_reason": parquet_skip_reason,
            "kernel": "aura",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if result_meta.get("ok", True) else 2
