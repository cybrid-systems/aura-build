# Specialist training notes (M4)

Offline notes for distillers / RL jobs that consume `aura-build export` corpora.
**No training loop lives in this repo.** L2 is metadata-only under `.aura-build/weights/<id>.json`; L3 online is refused.

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
| `harness.l2_weights_id` / `l2_ref` | Offline specialist id; `stub=True`, `artifact_present` when JSON loaded |
| `harness.l3_online` | Quarantine if `true`; default corpora require `false` |
| `privacy.redacted` / `retention_class` | Export filter honesty; customer class ≠ shared L2 |
| `runtime.profile` / `session_model` | Profile context; `shared_workspace_subprocess` ≠ fiber-live |

### Honesty flags (do not “fix” in labels)

- **`incr_proven=false`** — always in M0–M5 dogfood. Distillers must not invent
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

## L2 weight artifacts (M5 metadata plug)

```bash
aura-build l2 promote --id specialist.stub.v0 --notes "offline demo"
aura-build l2 promote --id specialist.from.export.v0 --from-export trajectories/export.json
aura-build l2 show --id specialist.stub.v0
```

- Path: `.aura-build/weights/<id>.json` with `{id, created, notes}` only
- `resolve_l2_weights` / `load_l2_artifact` set `artifact_present=True` when JSON loads
- **`stub=True` always** in M5 — no tensor bytes; do not claim weights are in memory
- Promote with `--from-export` **refuses** any episode where `harness.l3_online=true`
- Future (past M5): mmap/read real bytes → `stub=False`; still no online L3 in default orch

See `src/aura_build/l2_weights.py` and `examples/weights.specialist.stub.v0.json`.

## Retention / privacy

| Class | Train shared L2? |
|-------|------------------|
| `dogfood` / `ci` | Yes after redaction (default export filter) |
| `customer` | Only under explicit contract |
| `ephemeral` | No long-term corpus |

Default export sets `privacy.redacted=true` and `export_filter=m4.default`.

## Deferred past M5

- Full TUI (Textual/rich) / editor ACP embed (M5 ships status stub + hook CLI only)
- Real L2 tensor/mmap load (`stub=False`)
- Fiber-live multi-worldline / `incr_proven=true`
- Online L3 (still experimental / refused in orch)

## Post-M5 prove-incr

Distillers may read `.aura-build/prove-incr-latest.json` as an honesty side-channel.
Do **not** treat orch `runtime.incr_proven` as true unless that report (or an
explicit episode field) says so after a measured storm. See
[storm-still-incr.md](storm-still-incr.md).

