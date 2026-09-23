# Specialist training notes (M4)

Offline notes for distillers / RL jobs that consume `aura-build export` corpora.
**No training loop lives in this repo.** L2 remains stub-by-id; L3 online is refused.

## What to train on

Prefer **on-runtime** episodes (`trajectory.v0`) over chat logs, raw diffs, or
Postman-style request dumps (see devaluation in [trajectory-protocol-v0.md](trajectory-protocol-v0.md)).

### Fields distillers need

| Field | Role |
|-------|------|
| `worldlines[].mutations[]` | **Actions** — ops / target_id / summary (policy targets) |
| `worldlines[].eval.fitness` + `metrics` | Reward / outcome signal within an episode |
| `worldlines[].eval.passed` | Binary gate alongside scalar fitness |
| `selected_id` / `selection_reason` | Which candidate won and why |
| `discarded[]` | Losers (negative / contrastive pairs) |
| `runtime.mode` | `simulated` vs `aura` — do not mix blindly |
| `runtime.incr_proven` | **Must stay false** until storm-still-incr is measured; never treat as proven incr |
| `harness.mid` + `harness.actions[]` | Harness canary propose/canary/commit/heal/discard tape |
| `harness.outcome` / `autopropote` / `committed` | L1 promotion decision (default autopropote off) |
| `harness.l1_strategy_id` | Strategy code id that produced the policy |
| `harness.l2_weights_id` / `l2_ref` | Offline specialist id (stub until real loader) |
| `harness.l3_online` | Quarantine if `true`; default corpora require `false` |
| `privacy.redacted` / `retention_class` | Export filter honesty; customer class ≠ shared L2 |
| `runtime.profile` / `session_model` | Profile context; `shared_workspace_subprocess` ≠ fiber-live |

### Honesty flags (do not “fix” in labels)

- **`incr_proven=false`** — always in M0–M4 dogfood. Distillers must not invent
  incremental-compile wins from placeholders.
- **No fiber-live FlatAST claim** — `stable_ref` / shared workspace are subprocess
  continuity, not multi-worldline fibers on one FlatAST.
- **No online L3 weight updates** — export is batch/offline only. Episodes with
  `l3_online=true` stay out of default L2 promotion sets.

## Export pipeline

```bash
# Default: redact abs paths + secret patterns; JSON array always
aura-build export --out trajectories/export.json

# Explicit inputs (files and/or dirs under .aura-build/ or trajectories/)
aura-build export trajectories/ .aura-build/trajectories/ \
  --out /tmp/aura-export.json --parquet /tmp/aura-export.parquet

# Local dogfood only — keep raw paths/secrets
aura-build export --include-raw --out trajectories/export.raw.json
```

- **JSON array** — always written; validates each episode as `trajectory.v0`.
- **Parquet** — optional; requires `pandas` + `pyarrow` (`pip install 'aura-build[export]'`).
  If missing, export prints a clear skip message and still returns 0 for JSON.

## L2 weight artifacts (plug points)

Keep resolving by **id** (`resolve_l2_weights`). Real weights would plug at:

1. Artifact dir / object key = `weights_id`
2. Manifest (corpus export SHA, metrics, retention)
3. Loader beside the stub (`load_l2_weights`) — **not implemented**; no training here

See module docstring in `src/aura_build/l2_weights.py`.

## Retention / privacy

| Class | Train shared L2? |
|-------|------------------|
| `dogfood` / `ci` | Yes after redaction (default export filter) |
| `customer` | Only under explicit contract |
| `ephemeral` | No long-term corpus |

Default export sets `privacy.redacted=true` and `export_filter=m4.default`.

## Deferred to M5+

- TUI / ACP surfaces (headless remains SSOT)
- Real L2 tensor load + offline promotion automation
- Fiber-live multi-worldline / `incr_proven=true`
- Online L3 (still experimental / refused in orch)
