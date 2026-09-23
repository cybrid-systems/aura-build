"""M4 batch trajectory export for offline RL / specialist distillation.

Reads JSONL episode files, validates against trajectory.v0, applies privacy
filters (default ON), and writes a JSON array (always). Optionally writes
Parquet when pyarrow/pandas are installed; otherwise degrades with a clear
message — no hard dependency.

Honesty
-------
- Export is **offline**. No online L3 weight updates.
- ``incr_proven`` stays false in source episodes; export does not flip it.
- Does not claim fiber-live FlatAST.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from aura_build.schema import SchemaError, validate_episode

__all__ = [
    "DEFAULT_TRAJ_GLOBS",
    "ExportResult",
    "ExportStats",
    "collect_jsonl_paths",
    "export_trajectories",
    "load_episodes",
    "redact_episode",
    "write_json_array",
    "write_parquet",
]

# Default search roots relative to cwd / configured dirs.
DEFAULT_TRAJ_GLOBS = (
    "trajectories/*.jsonl",
    ".aura-build/trajectories/*.jsonl",
    ".aura-build/**/*.jsonl",
)

# Absolute path shaped strings (POSIX + Windows drive).
_ABS_PATH_RE = re.compile(
    r"(?P<path>"
    r"(?:/[A-Za-z0-9._~/-]+)"  # /home/... or /workspace/...
    r"|(?:[A-Za-z]:\\[A-Za-z0-9._\\-]+)"  # C:\...
    r")"
)

# Env / secret patterns (case-insensitive).
_SECRET_KV_RE = re.compile(
    r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|bearer|"
    r"secret|password|passwd|private[_-]?key|aws[_-]?secret|"
    r"xai[_-]?api[_-]?key|openai[_-]?api[_-]?key|gh[_-]?token|"
    r"github[_-]?token|authorization)\b"
    r"(\s*[=:]\s*)([^\s\"',;]+)"
)
_SECRET_TOKEN_RE = re.compile(
    r"(?i)\b(sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|"
    r"gho_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})\b"
)
_BEARER_RE = re.compile(r"(?i)\b(Bearer)\s+([A-Za-z0-9._\-+/=]{8,})")

@dataclass
class ExportStats:
    """Counters for one export run."""

    files_read: int = 0
    episodes_loaded: int = 0
    episodes_exported: int = 0
    episodes_skipped_invalid: int = 0
    redacted: bool = True
    parquet_written: bool = False
    parquet_skip_reason: str | None = None


@dataclass
class ExportResult:
    """Paths and stats from ``export_trajectories``."""

    json_path: Path
    parquet_path: Path | None
    stats: ExportStats
    episodes: list[dict[str, Any]] = field(default_factory=list)


def collect_jsonl_paths(
    inputs: Iterable[Path | str] | None = None,
    *,
    cwd: Path | str | None = None,
) -> list[Path]:
    """Resolve JSONL sources from explicit paths/dirs or default globs.

    - File path → that file
    - Directory → ``**/*.jsonl`` under it (sorted)
    - ``None`` / empty → default globs under ``cwd``
    """
    base = Path(cwd) if cwd is not None else Path.cwd()
    found: list[Path] = []
    seen: set[Path] = set()

    def _add(p: Path) -> None:
        try:
            rp = p.resolve()
        except OSError:
            rp = p
        if rp in seen or not p.is_file():
            return
        if p.suffix.lower() != ".jsonl":
            return
        seen.add(rp)
        found.append(p)

    items = list(inputs) if inputs else []
    if not items:
        for pattern in DEFAULT_TRAJ_GLOBS:
            for p in sorted(base.glob(pattern)):
                _add(p)
        return found

    for raw in items:
        path = Path(raw)
        if not path.is_absolute():
            path = base / path
        if path.is_dir():
            for p in sorted(path.rglob("*.jsonl")):
                _add(p)
        else:
            _add(path)
    return found


def load_episodes(
    paths: Iterable[Path],
    *,
    skip_invalid: bool = True,
) -> tuple[list[dict[str, Any]], ExportStats]:
    """Load and validate episodes from JSONL files."""
    stats = ExportStats()
    episodes: list[dict[str, Any]] = []
    for path in paths:
        stats.files_read += 1
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                validate_episode(obj)
            except (json.JSONDecodeError, SchemaError, TypeError, ValueError) as exc:
                stats.episodes_skipped_invalid += 1
                if skip_invalid:
                    continue
                raise SchemaError(
                    f"{path}:{line_no}: invalid episode ({exc})"
                ) from exc
            stats.episodes_loaded += 1
            episodes.append(obj)
    return episodes, stats




def _placeholder_for_path(value: str) -> str:
    """Map an absolute-looking path to a basename placeholder."""
    name = value.rstrip("/\\")
    for sep in ("/", "\\"):
        if sep in name:
            name = name.rsplit(sep, 1)[-1]
    if not name:
        name = "path"
    return f"<redacted:path:{name}>"


def _redact_string(s: str) -> str:
    out = _SECRET_KV_RE.sub(
        lambda m: f"{m.group(1)}{m.group(2)}<redacted:secret>",
        s,
    )
    out = _SECRET_TOKEN_RE.sub("<redacted:secret>", out)
    out = _BEARER_RE.sub(r"\1 <redacted:secret>", out)

    def _path_sub(m: re.Match[str]) -> str:
        return _placeholder_for_path(m.group("path"))

    out = _ABS_PATH_RE.sub(_path_sub, out)
    return out


def _redact_value(key: str | None, value: Any) -> Any:
    if isinstance(value, str):
        # Single pass: secrets + absolute paths (avoid double-wrapping placeholders).
        return _redact_string(value)
    if isinstance(value, list):
        return [_redact_value(key, v) for v in value]
    if isinstance(value, dict):
        return {k: _redact_value(k, v) for k, v in value.items()}
    return value


def redact_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a deep-copied episode with paths/secrets scrubbed.

    Sets ``privacy.redacted=true``. Does not alter ``incr_proven`` or
    ``harness.l3_online``.
    """
    ep = deepcopy(episode)
    redacted = _redact_value(None, ep)
    if not isinstance(redacted, dict):
        raise TypeError("redact_episode expected dict")
    privacy = redacted.get("privacy")
    if not isinstance(privacy, dict):
        privacy = {}
        redacted["privacy"] = privacy
    privacy["redacted"] = True
    privacy.setdefault("retention_class", "dogfood")
    privacy["export_filter"] = "m4.default"
    return redacted


def write_json_array(episodes: list[dict[str, Any]], path: Path | str) -> Path:
    """Write episodes as a JSON array."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(episodes, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    return out


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


def export_trajectories(
    *,
    inputs: Iterable[Path | str] | None = None,
    out_json: Path | str,
    out_parquet: Path | str | None = None,
    redact: bool = True,
    include_raw: bool = False,
    skip_invalid: bool = True,
    cwd: Path | str | None = None,
    want_parquet: bool = True,
) -> ExportResult:
    """Load → filter → write JSON (+ optional Parquet).

    Parameters
    ----------
    redact:
        Default True. Strip absolute paths and secret patterns.
    include_raw:
        If True, skip redaction (local dogfood only). Overrides ``redact``.
    want_parquet:
        Attempt Parquet when True (path = ``out_parquet`` or beside JSON).
    """
    paths = collect_jsonl_paths(inputs, cwd=cwd)
    episodes, stats = load_episodes(paths, skip_invalid=skip_invalid)

    do_redact = redact and not include_raw
    stats.redacted = do_redact
    if do_redact:
        episodes = [redact_episode(ep) for ep in episodes]
        for ep in episodes:
            validate_episode(ep)

    json_path = write_json_array(episodes, out_json)
    stats.episodes_exported = len(episodes)

    parquet_path: Path | None = None
    if want_parquet:
        pq = (
            Path(out_parquet)
            if out_parquet is not None
            else Path(out_json).with_suffix(".parquet")
        )
        parquet_path, reason = write_parquet(episodes, pq)
        stats.parquet_written = parquet_path is not None
        stats.parquet_skip_reason = reason

    return ExportResult(
        json_path=json_path,
        parquet_path=parquet_path,
        stats=stats,
        episodes=episodes,
    )
